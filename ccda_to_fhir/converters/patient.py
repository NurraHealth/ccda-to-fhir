"""Patient converter: C-CDA recordTarget to FHIR Patient resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import CE, II
from ccda_to_fhir.ccda.models.record_target import (
    Guardian,
    LanguageCommunication,
    Patient,
    Place,
    RecordTarget,
)
from ccda_to_fhir.constants import (
    ADMINISTRATIVE_GENDER_MAP,
    OMB_ETHNICITY_CATEGORIES,
    OMB_RACE_CATEGORIES,
    CodeSystemOIDs,
    FHIRCodes,
    FHIRSystems,
    V2IdentifierTypes,
    V3RoleCodes,
)
from ccda_to_fhir.exceptions import MissingRequiredFieldError
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter


class PatientConverter(BaseConverter[RecordTarget]):
    """Convert C-CDA recordTarget to FHIR Patient resource.

    This converter handles the full mapping from C-CDA recordTarget/patientRole
    to a FHIR R4B Patient resource, including US Core extensions for race,
    ethnicity, and birthsex.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-patient.html
    """

    def convert(self, record_target: RecordTarget) -> FHIRResourceDict:
        """Convert a C-CDA recordTarget to a FHIR Patient resource.

        Args:
            record_target: The C-CDA recordTarget element

        Returns:
            FHIR Patient resource as a dictionary

        Raises:
            ConversionError: If conversion fails
        """
        if not record_target.patient_role:
            raise MissingRequiredFieldError(
                field_name="patientRole",
                resource_type="Patient",
                details="RecordTarget must have a patientRole element",
            )

        patient_role = record_target.patient_role
        patient_data = patient_role.patient

        if not patient_data:
            raise MissingRequiredFieldError(
                field_name="patient",
                resource_type="Patient",
                details="PatientRole must have patient demographics",
            )

        patient: JSONObject = {
            "resourceType": "Patient",
        }

        # Generate ID from patient identifier
        if patient_role.id and len(patient_role.id) > 0:
            first_id = patient_role.id[0]
            patient["id"] = self._generate_patient_id(first_id)

        # Identifiers
        if patient_role.id:
            patient["identifier"] = self._convert_identifiers(patient_role.id)

        # Names
        if patient_data.name:
            patient["name"] = self.convert_human_names(patient_data.name)

        # Telecom
        if patient_role.telecom:
            patient["telecom"] = self.convert_telecom(patient_role.telecom)

        # Gender
        if patient_data.administrative_gender_code:
            gender = self._convert_gender(patient_data.administrative_gender_code)
            if gender:
                patient["gender"] = gender

        # Birth date and birthTime extension
        if patient_data.birth_time:
            birth_date, birth_time_ext = self._extract_birth_date_and_time(patient_data.birth_time)
            if birth_date:
                patient["birthDate"] = birth_date
                # Attach birthTime extension to _birthDate element
                if birth_time_ext:
                    patient["_birthDate"] = {
                        "extension": [birth_time_ext]
                    }

        # Deceased
        deceased = self._convert_deceased(patient_data)
        if deceased:
            patient.update(deceased)

        # Address
        if patient_role.addr:
            patient["address"] = self.convert_addresses(patient_role.addr, include_type=True)

        # Marital status
        if patient_data.marital_status_code:
            marital_status = self.create_codeable_concept(
                code=patient_data.marital_status_code.code,
                code_system=patient_data.marital_status_code.code_system,
                display_name=patient_data.marital_status_code.display_name,
            )
            if marital_status:
                patient["maritalStatus"] = marital_status

        # Multiple birth
        if patient_data.sdtc_multiple_birth_ind or patient_data.sdtc_multiple_birth_order_number:
            if patient_data.sdtc_multiple_birth_order_number:
                patient["multipleBirthInteger"] = patient_data.sdtc_multiple_birth_order_number
            elif patient_data.sdtc_multiple_birth_ind:
                patient["multipleBirthBoolean"] = patient_data.sdtc_multiple_birth_ind

        # Contact (Guardian)
        if patient_data.guardian:
            patient["contact"] = self._convert_guardians(patient_data.guardian)

        # Communication
        if patient_data.language_communication:
            patient["communication"] = self._convert_communication(
                patient_data.language_communication
            )

        # Managing organization
        if patient_role.provider_organization:
            # Create a reference - in full document conversion, this would be resolved
            org_name = None
            if patient_role.provider_organization.name:
                org_name = patient_role.provider_organization.name[0]
                if isinstance(org_name, str):
                    pass
                else:
                    org_name = org_name.value if hasattr(org_name, 'value') else str(org_name)

            patient["managingOrganization"] = {"display": org_name} if org_name else {}

        # US Core and other extensions
        extensions = []

        # Race extension
        race_ext = self._create_race_extension(patient_data)
        if race_ext:
            extensions.append(race_ext)

        # Ethnicity extension
        ethnicity_ext = self._create_ethnicity_extension(patient_data)
        if ethnicity_ext:
            extensions.append(ethnicity_ext)

        # Birthplace extension
        if patient_data.birthplace and patient_data.birthplace.place:
            birthplace_ext = self._create_birthplace_extension(patient_data.birthplace.place)
            if birthplace_ext:
                extensions.append(birthplace_ext)

        # Religion extension
        if patient_data.religious_affiliation_code:
            religion_codeable = self.create_codeable_concept(
                code=patient_data.religious_affiliation_code.code,
                code_system=patient_data.religious_affiliation_code.code_system,
                display_name=patient_data.religious_affiliation_code.display_name,
            )
            if religion_codeable:
                religion_ext = {
                    "url": FHIRSystems.PATIENT_RELIGION,
                    "valueCodeableConcept": religion_codeable,
                }
                extensions.append(religion_ext)

        if extensions:
            patient["extension"] = extensions

        return patient

    def _generate_patient_id(self, identifier: II) -> str:
        """Generate FHIR Patient ID using cached UUID v4 from C-CDA identifier.

        Args:
            identifier: C-CDA II identifier

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        root = identifier.root if identifier.root else None
        extension = identifier.extension if identifier.extension else None

        return generate_id_from_identifiers("Patient", root, extension)

    def _extract_birth_date_and_time(self, birth_time) -> tuple[str | None, JSONObject | None]:
        """Extract birthDate and optionally patient-birthTime extension.

        If the C-CDA birthTime includes a time component (not just date),
        return both the date for birthDate and an extension for full timestamp.

        Args:
            birth_time: C-CDA birth_time element (TS type)

        Returns:
            Tuple of (birthDate string, birthTime extension dict or None)
        """
        if not birth_time or not birth_time.value:
            return None, None

        birth_time_str = birth_time.value

        # Check if it has time component (more than 8 digits = YYYYMMDD)
        # Time component would be like: 20000101120000-0500 (14+ digits)
        has_time = len(birth_time_str) > 8

        # Extract date portion for birthDate (only YYYYMMDD, no time)
        date_portion = birth_time_str[:8]  # First 8 characters
        birth_date = self.convert_date(date_portion)

        # If has time component, create extension
        birth_time_ext = None
        if has_time:
            # Convert full timestamp to datetime format
            birth_date_time = self.convert_date(birth_time_str)
            if birth_date_time:
                birth_time_ext = {
                    "url": FHIRSystems.PATIENT_BIRTH_TIME,
                    "valueDateTime": birth_date_time
                }

        return birth_date, birth_time_ext

    def _convert_identifiers(self, ids: list[II]) -> list[FHIRResourceDict]:
        """Convert C-CDA IDs to FHIR identifiers.

        Args:
            ids: List of C-CDA II identifiers

        Returns:
            List of FHIR Identifier dicts
        """
        identifiers = []

        for id_elem in ids:
            if not id_elem.root:
                continue

            identifier = self.create_identifier(id_elem.root, id_elem.extension)

            # Add type for known identifier systems
            if id_elem.root == CodeSystemOIDs.SSN:
                identifier["type"] = {
                    "coding": [
                        {
                            "system": FHIRSystems.V2_IDENTIFIER_TYPE,
                            "code": V2IdentifierTypes.SOCIAL_SECURITY,
                            "display": "Social Security Number",
                        }
                    ]
                }
            elif id_elem.root == CodeSystemOIDs.NPI:
                identifier["type"] = {
                    "coding": [
                        {
                            "system": FHIRSystems.V2_IDENTIFIER_TYPE,
                            "code": V2IdentifierTypes.NATIONAL_PROVIDER_ID,
                            "display": "National Provider Identifier",
                        }
                    ]
                }
            else:
                # Medical Record Number (MRN) for other identifiers
                identifier["type"] = {
                    "coding": [
                        {
                            "system": FHIRSystems.V2_IDENTIFIER_TYPE,
                            "code": V2IdentifierTypes.MEDICAL_RECORD,
                            "display": "Medical Record Number",
                        }
                    ]
                }

            identifiers.append(identifier)

        return identifiers

    def _convert_gender(self, gender_code: CE) -> str | None:
        """Convert C-CDA administrative gender to FHIR gender.

        Args:
            gender_code: C-CDA administrative gender code

        Returns:
            FHIR gender code (male, female, other, unknown)
        """
        if not gender_code.code:
            return None

        return ADMINISTRATIVE_GENDER_MAP.get(gender_code.code, FHIRCodes.PatientGender.UNKNOWN)

    def _convert_deceased(self, patient_data: Patient) -> FHIRResourceDict:
        """Convert deceased indicator and time to FHIR deceased[x].

        Args:
            patient_data: The C-CDA Patient model

        Returns:
            Dict with deceasedBoolean or deceasedDateTime
        """
        result = {}

        # Prefer deceasedTime over deceasedInd
        if patient_data.sdtc_deceased_time and patient_data.sdtc_deceased_time.value:
            deceased_date = self.convert_date(patient_data.sdtc_deceased_time.value)
            if deceased_date:
                result["deceasedDateTime"] = deceased_date
        elif patient_data.sdtc_deceased_ind is not None:
            result["deceasedBoolean"] = patient_data.sdtc_deceased_ind

        return result

    def _convert_guardians(self, guardians: list[Guardian]) -> list[FHIRResourceDict]:
        """Convert C-CDA guardians to FHIR Patient.contact.

        Args:
            guardians: List of C-CDA Guardian elements

        Returns:
            List of FHIR contact dicts
        """
        contacts = []

        for guardian in guardians:
            contact: JSONObject = {}

            # Relationship - specific code first (if available), then GUARD
            relationships = []

            # Add specific relationship code if provided (primary)
            if guardian.code and guardian.code.code:
                specific_coding = self.create_codeable_concept(
                    code=guardian.code.code,
                    code_system=guardian.code.code_system,
                    display_name=guardian.code.display_name,
                )
                if specific_coding and specific_coding.get("coding"):
                    relationships.append(specific_coding)

            # Always add generic GUARD code
            guard_coding = {
                "system": FHIRSystems.V3_ROLE_CODE,
                "code": V3RoleCodes.GUARDIAN,
                "display": "Guardian",
            }
            relationships.append({"coding": [guard_coding]})

            contact["relationship"] = relationships

            # Name
            if guardian.guardian_person and guardian.guardian_person.name:
                names = self.convert_human_names(guardian.guardian_person.name)
                if names:
                    contact["name"] = names[0]

            # Telecom
            if guardian.telecom:
                contact["telecom"] = self.convert_telecom(guardian.telecom)

            # Address
            if guardian.addr:
                addresses = self.convert_addresses(guardian.addr, include_type=True)
                if addresses:
                    contact["address"] = addresses[0]

            contacts.append(contact)

        return contacts

    def _convert_communication(
        self, communications: list[LanguageCommunication]
    ) -> list[FHIRResourceDict]:
        """Convert C-CDA language communication to FHIR Patient.communication.

        Args:
            communications: List of C-CDA LanguageCommunication elements

        Returns:
            List of FHIR communication dicts
        """
        fhir_communications = []

        for comm in communications:
            fhir_comm: JSONObject = {}

            # Language
            if comm.language_code and comm.language_code.code:
                fhir_comm["language"] = {
                    "coding": [
                        {
                            "system": FHIRSystems.BCP_47,
                            "code": comm.language_code.code,
                        }
                    ]
                }

            # Preferred
            if comm.preference_ind is not None:
                fhir_comm["preferred"] = comm.preference_ind

            # Extensions for mode and proficiency
            extensions = []

            if comm.mode_code or comm.proficiency_level_code:
                proficiency_ext: JSONObject = {
                    "url": FHIRSystems.PATIENT_PROFICIENCY,
                    "extension": [],
                }

                if comm.mode_code:
                    mode_sub_ext = {
                        "url": "type",
                        "valueCoding": {
                            "system": self.map_oid_to_uri(comm.mode_code.code_system)
                            if comm.mode_code.code_system
                            else FHIRSystems.V3_LANGUAGE_ABILITY_MODE,
                            "code": comm.mode_code.code,
                        },
                    }
                    if comm.mode_code.display_name:
                        mode_sub_ext["valueCoding"]["display"] = comm.mode_code.display_name
                    proficiency_ext["extension"].append(mode_sub_ext)

                if comm.proficiency_level_code:
                    level_sub_ext = {
                        "url": "level",
                        "valueCoding": {
                            "system": self.map_oid_to_uri(
                                comm.proficiency_level_code.code_system
                            )
                            if comm.proficiency_level_code.code_system
                            else FHIRSystems.V3_LANGUAGE_ABILITY_PROFICIENCY,
                            "code": comm.proficiency_level_code.code,
                        },
                    }
                    if comm.proficiency_level_code.display_name:
                        level_sub_ext["valueCoding"][
                            "display"
                        ] = comm.proficiency_level_code.display_name
                    proficiency_ext["extension"].append(level_sub_ext)

                if proficiency_ext["extension"]:
                    extensions.append(proficiency_ext)

            if extensions:
                fhir_comm["extension"] = extensions

            # FHIR R4B requires Patient.communication.language (1..1)
            # Only add communication entry if language is present
            # Skip entries with only preferred/extensions (nullFlavor language in C-CDA)
            if "language" in fhir_comm:
                fhir_communications.append(fhir_comm)

        return fhir_communications

    def _create_race_extension(self, patient_data: Patient) -> JSONObject | None:
        """Create US Core race extension.

        Args:
            patient_data: The C-CDA Patient model

        Returns:
            FHIR extension dict or None
        """
        # Collect all race codes (primary + sdtc extensions)
        race_codes = []
        if patient_data.race_code and patient_data.race_code.code:
            race_codes.append(patient_data.race_code)
        if patient_data.sdtc_race_code:
            race_codes.extend(patient_data.sdtc_race_code)

        if not race_codes:
            return None

        extension: JSONObject = {
            "url": FHIRSystems.US_CORE_RACE,
            "extension": [],
        }

        # Categorize codes into OMB and detailed
        omb_categories = []
        detailed_categories = []
        text_parts = []

        for race_code in race_codes:
            if not race_code.code:
                continue

            coding = {
                "system": FHIRSystems.CDC_RACE_ETHNICITY,
                "code": race_code.code,
            }
            if race_code.display_name:
                coding["display"] = race_code.display_name
                text_parts.append(race_code.display_name)

            if race_code.code in OMB_RACE_CATEGORIES:
                omb_categories.append(
                    {"url": "ombCategory", "valueCoding": coding}
                )
            else:
                detailed_categories.append(
                    {"url": "detailed", "valueCoding": coding}
                )

        extension["extension"].extend(omb_categories)
        extension["extension"].extend(detailed_categories)

        # Text element (required)
        text = ", ".join(text_parts) if text_parts else "Unknown"
        extension["extension"].append({"url": "text", "valueString": text})

        return extension

    def _create_ethnicity_extension(self, patient_data: Patient) -> JSONObject | None:
        """Create US Core ethnicity extension.

        Args:
            patient_data: The C-CDA Patient model

        Returns:
            FHIR extension dict or None
        """
        # Collect all ethnicity codes
        ethnicity_codes = []
        if patient_data.ethnic_group_code and patient_data.ethnic_group_code.code:
            ethnicity_codes.append(patient_data.ethnic_group_code)
        if patient_data.sdtc_ethnic_group_code:
            ethnicity_codes.extend(patient_data.sdtc_ethnic_group_code)

        if not ethnicity_codes:
            return None

        extension: JSONObject = {
            "url": FHIRSystems.US_CORE_ETHNICITY,
            "extension": [],
        }

        # Categorize codes
        omb_categories = []
        detailed_categories = []
        text_parts = []

        for ethnicity_code in ethnicity_codes:
            if not ethnicity_code.code:
                continue

            coding = {
                "system": FHIRSystems.CDC_RACE_ETHNICITY,
                "code": ethnicity_code.code,
            }
            if ethnicity_code.display_name:
                coding["display"] = ethnicity_code.display_name
                text_parts.append(ethnicity_code.display_name)

            if ethnicity_code.code in OMB_ETHNICITY_CATEGORIES:
                omb_categories.append(
                    {"url": "ombCategory", "valueCoding": coding}
                )
            else:
                detailed_categories.append(
                    {"url": "detailed", "valueCoding": coding}
                )

        extension["extension"].extend(omb_categories)
        extension["extension"].extend(detailed_categories)

        # Text element (required)
        text = ", ".join(text_parts) if text_parts else "Unknown"
        extension["extension"].append({"url": "text", "valueString": text})

        return extension

    def _create_birthplace_extension(self, place: Place) -> JSONObject | None:
        """Create patient-birthPlace extension.

        Args:
            place: The C-CDA Place element

        Returns:
            FHIR extension dict or None
        """
        if not place.addr:
            return None

        addresses = self.convert_addresses([place.addr], include_type=True)
        if not addresses:
            return None

        return {
            "url": FHIRSystems.PATIENT_BIRTHPLACE,
            "valueAddress": addresses[0],
        }
