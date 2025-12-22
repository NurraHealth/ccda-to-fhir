# Design: Medical Code Enrichment and Terminology Crosswalking

**Status**: Proposed
**Author**: Design Discussion
**Date**: 2025-12-22
**Version**: 1.0

---

## 1. Problem Statement

### Current State

The ccda-to-fhir library performs **direct code mapping** from C-CDA to FHIR without terminology enrichment:

```python
# Current behavior: Direct passthrough
# C-CDA
<code code="386661006" codeSystem="2.16.840.1.113883.6.96"
      displayName="Fever"/>

# FHIR Output
{
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "386661006",
      "display": "Fever"
    }]
  }
}
```

**What's missing:**
- Additional code system crosswalks (ICD-10-CM, RxNorm, NDC)
- Code validation against terminology servers
- Code standardization and normalization
- Additional clinical context from code hierarchies
- Deprecated code detection and updating

### Use Cases for Enrichment

1. **Analytics and Reporting**: ICD-10-CM codes required for billing and quality measures
2. **Interoperability**: Multiple code systems increase data exchange compatibility
3. **Clinical Decision Support**: Standardized codes enable better CDS rules
4. **Data Quality**: Validate codes exist and are current
5. **Semantic Normalization**: Map local/proprietary codes to standard terminologies

### Example: Enhanced Output

```python
# With enrichment
{
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "386661006",
        "display": "Fever"
      },
      {
        "system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code": "R50.9",
        "display": "Fever, unspecified"
      }
    ]
  }
}
```

---

## 2. Terminology Systems Overview

### Primary Clinical Terminologies

| System | Purpose | Use in FHIR | Example Code |
|--------|---------|-------------|--------------|
| **SNOMED CT** | Clinical terms (diagnoses, procedures, findings) | Preferred for conditions, procedures | `386661006` (Fever) |
| **LOINC** | Laboratory and clinical observations | Required for lab results, vital signs | `8480-6` (Systolic BP) |
| **RxNorm** | Medications (ingredients, brands, packages) | Required for medications | `213269` (Lisinopril 10mg) |
| **ICD-10-CM** | Diagnoses (US billing) | Billing, quality measures | `R50.9` (Fever) |
| **CPT** | Procedures (US billing) | Billing for procedures | `99213` (Office visit) |
| **NDC** | Drug products (US) | Pharmacy dispensing | `00378-1805-10` |
| **CVX** | Vaccine products | Immunizations | `141` (Influenza vaccine) |

### Crosswalking Scenarios

**Common enrichment patterns:**

1. **Condition codes**: SNOMED CT → ICD-10-CM
   - SNOMED: `44054006` (Type 2 Diabetes)
   - ICD-10: `E11.9` (Type 2 diabetes without complications)

2. **Medication codes**: RxNorm → NDC
   - RxNorm: `213269` (Lisinopril 10mg tablet)
   - NDC: `00378-1805-10` (specific manufacturer product)

3. **Lab codes**: Local codes → LOINC
   - Local: `GLU` (site-specific)
   - LOINC: `2345-7` (Glucose [Mass/volume] in Serum)

4. **Procedure codes**: SNOMED CT → CPT
   - SNOMED: `80146002` (Appendectomy)
   - CPT: `44950` (Appendectomy)

---

## 3. Design Goals

### Primary Goals

1. **Optional & Non-Breaking**: Enrichment must be completely optional
2. **Zero Required Dependencies**: No mandatory external services
3. **Maintain "Fail Loud" Philosophy**: Report enrichment failures clearly
4. **Provider Agnostic**: Support multiple terminology service implementations
5. **Incremental Adoption**: Users can enrich specific code types or resources

### Non-Goals

1. **Not a terminology server**: We don't store or manage terminology data
2. **Not a UMLS replacement**: We integrate with existing services
3. **Not required for conversion**: Core C-CDA→FHIR works without enrichment

---

## 4. Architecture

### 4.1 High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                     User Application                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           ccda_to_fhir.convert(xml_content)             │
│              (Core conversion - no enrichment)          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼ Returns FHIR Bundle
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│         ccda_to_fhir.enrichment.enrich(bundle)          │
│                  (Optional enrichment)                   │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
  ┌──────────────┐ ┌──────────┐ ┌──────────────┐
  │ NLM UMLS API │ │ Local DB │ │ Custom Logic │
  └──────────────┘ └──────────┘ └──────────────┘
```

### 4.2 Module Structure

```
ccda_to_fhir/
├── enrichment/              # New optional module
│   ├── __init__.py         # Public API exports
│   ├── enricher.py         # Main enrichment orchestrator
│   ├── providers/          # Terminology service providers
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract base class
│   │   ├── umls.py         # NLM UMLS provider
│   │   ├── cached.py       # Local cache provider
│   │   └── noop.py         # No-op provider for testing
│   ├── strategies/         # Enrichment strategies
│   │   ├── __init__.py
│   │   ├── condition.py    # SNOMED→ICD-10 for Conditions
│   │   ├── medication.py   # RxNorm→NDC for Medications
│   │   ├── observation.py  # LOINC validation
│   │   └── procedure.py    # SNOMED→CPT for Procedures
│   └── exceptions.py       # Enrichment-specific exceptions
```

---

## 5. Core Interfaces

### 5.1 Terminology Provider Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class TerminologyMapping:
    """Result of a terminology lookup/crosswalk."""
    source_system: str
    source_code: str
    target_system: str
    target_code: str
    target_display: Optional[str] = None
    confidence: float = 1.0  # 0.0-1.0

@dataclass
class CodeValidation:
    """Result of code validation."""
    system: str
    code: str
    valid: bool
    display: Optional[str] = None
    status: Optional[str] = None  # "active", "deprecated", "retired"
    message: Optional[str] = None


class TerminologyProvider(ABC):
    """
    Abstract base class for terminology service providers.

    Implementations can use:
    - NLM UMLS API
    - Local terminology database
    - FHIR Terminology Service ($lookup, $translate)
    - Custom mapping tables
    """

    @abstractmethod
    def crosswalk(
        self,
        source_system: str,
        source_code: str,
        target_system: str
    ) -> List[TerminologyMapping]:
        """
        Find equivalent codes in target terminology system.

        Args:
            source_system: Source code system URI or OID
            source_code: Code in source system
            target_system: Target code system URI

        Returns:
            List of equivalent codes (may be empty, 1:1, or 1:many)

        Raises:
            TerminologyProviderError: On communication/auth errors
        """
        pass

    @abstractmethod
    def validate_code(
        self,
        system: str,
        code: str
    ) -> CodeValidation:
        """
        Validate a code exists in the terminology system.

        Args:
            system: Code system URI or OID
            code: Code to validate

        Returns:
            Validation result with status
        """
        pass

    @abstractmethod
    def get_preferred_display(
        self,
        system: str,
        code: str
    ) -> Optional[str]:
        """
        Get the preferred display name for a code.

        Args:
            system: Code system URI or OID
            code: Code to look up

        Returns:
            Preferred display name or None if not found
        """
        pass
```

### 5.2 Enrichment Orchestrator

```python
from typing import Optional, List
from fhir.resources.bundle import Bundle
from fhir.resources.domainresource import DomainResource

class CodeEnricher:
    """
    Orchestrates medical code enrichment for FHIR resources.

    Example:
        >>> from ccda_to_fhir import convert
        >>> from ccda_to_fhir.enrichment import CodeEnricher
        >>> from ccda_to_fhir.enrichment.providers import UMLSProvider
        >>>
        >>> # Standard conversion
        >>> bundle = convert(xml_content)
        >>>
        >>> # Optional enrichment
        >>> provider = UMLSProvider(api_key="your_key")
        >>> enricher = CodeEnricher(provider)
        >>> enriched = enricher.enrich(bundle,
        ...     resource_types=['Condition', 'Procedure'],
        ...     crosswalks={'snomed': 'icd10cm'})
    """

    def __init__(
        self,
        provider: TerminologyProvider,
        fail_on_error: bool = False
    ):
        """
        Initialize enricher with terminology provider.

        Args:
            provider: Terminology service provider
            fail_on_error: If True, raise on enrichment failures.
                          If False, log warnings and continue.
        """
        self.provider = provider
        self.fail_on_error = fail_on_error

    def enrich(
        self,
        bundle: Bundle,
        resource_types: Optional[List[str]] = None,
        crosswalks: Optional[dict[str, str]] = None,
        validate_codes: bool = False,
        update_displays: bool = False
    ) -> Bundle:
        """
        Enrich FHIR Bundle with additional terminology codes.

        Args:
            bundle: FHIR Bundle to enrich
            resource_types: List of resource types to enrich
                          (None = all supported types)
            crosswalks: Dict of source→target system mappings
                       e.g. {'snomed': 'icd10cm', 'rxnorm': 'ndc'}
            validate_codes: Validate existing codes against terminology
            update_displays: Update display names to preferred terms

        Returns:
            Enriched Bundle (mutates in place and returns)

        Raises:
            EnrichmentError: If fail_on_error=True and enrichment fails
        """
        pass

    def enrich_resource(
        self,
        resource: DomainResource,
        crosswalks: dict[str, str],
        validate_codes: bool = False
    ) -> DomainResource:
        """
        Enrich a single FHIR resource.

        Args:
            resource: FHIR resource to enrich
            crosswalks: Source→target system mappings
            validate_codes: Validate codes

        Returns:
            Enriched resource (mutates in place and returns)
        """
        pass
```

---

## 6. Implementation Strategies

### 6.1 Condition (Diagnosis) Enrichment

**Goal**: Add ICD-10-CM codes to Conditions with SNOMED codes

```python
# Input Condition
{
  "resourceType": "Condition",
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "44054006",
      "display": "Type 2 diabetes mellitus"
    }]
  }
}

# After enrichment
{
  "resourceType": "Condition",
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "44054006",
        "display": "Type 2 diabetes mellitus"
      },
      {
        "system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code": "E11.9",
        "display": "Type 2 diabetes mellitus without complications"
      }
    ]
  }
}
```

**Mapping challenges:**
- SNOMED→ICD-10 is often 1:many (requires clinical context)
- May need human review for accuracy
- Consider confidence scoring for automated mappings

### 6.2 Medication Enrichment

**Goal**: Add NDC codes to MedicationRequest with RxNorm codes

```python
# Input MedicationRequest
{
  "resourceType": "MedicationRequest",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197361",
      "display": "Lisinopril 10 MG Oral Tablet"
    }]
  }
}

# After enrichment (multiple NDCs possible)
{
  "resourceType": "MedicationRequest",
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "197361",
        "display": "Lisinopril 10 MG Oral Tablet"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "00378-1805-10",
        "display": "Lisinopril 10mg Tablet (Mylan)"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "68084-0198-01",
        "display": "Lisinopril 10mg Tablet (American Health)"
      }
    ]
  }
}
```

**Mapping challenges:**
- RxNorm→NDC is 1:many (multiple manufacturers)
- NDC codes change frequently (repackaging)
- May want to filter by availability or formulary

### 6.3 Observation Enrichment

**Goal**: Validate LOINC codes and add common names

```python
# Input Observation
{
  "resourceType": "Observation",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "2345-7"
      # Missing display
    }]
  }
}

# After enrichment
{
  "resourceType": "Observation",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "2345-7",
      "display": "Glucose [Mass/volume] in Serum or Plasma"
    }],
    "text": "Blood glucose"  # Added common name
  }
}
```

---

## 7. Terminology Service Providers

### 7.1 NLM UMLS Provider

```python
class UMLSProvider(TerminologyProvider):
    """
    Terminology provider using NLM UMLS Terminology Services API.

    Requires:
    - UMLS account (free for research/healthcare)
    - API key from https://uts.nlm.nih.gov/

    Supports:
    - Code validation
    - Crosswalks between standard terminologies
    - Display name lookup

    Rate limits:
    - 20 requests/second
    - Recommend local caching
    """

    def __init__(self, api_key: str, base_url: str = "https://uts-ws.nlm.nih.gov"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = self._init_session()

    def crosswalk(self, source_system: str, source_code: str,
                  target_system: str) -> List[TerminologyMapping]:
        """
        Use UMLS REST API to find crosswalks.

        Endpoint: /rest/crosswalk/current/source/{source}/id/{code}
        """
        # Implementation calls UMLS API
        pass
```

### 7.2 Cached Provider

```python
class CachedProvider(TerminologyProvider):
    """
    Wraps another provider with local caching.

    Uses:
    - SQLite database for persistence
    - TTL-based cache expiration
    - Background refresh for popular codes

    Example:
        >>> umls = UMLSProvider(api_key="key")
        >>> cached = CachedProvider(umls, cache_path="./term_cache.db")
        >>> enricher = CodeEnricher(cached)
    """

    def __init__(
        self,
        delegate: TerminologyProvider,
        cache_path: str,
        ttl_days: int = 30
    ):
        self.delegate = delegate
        self.cache = self._init_cache(cache_path)
        self.ttl_days = ttl_days
```

### 7.3 FHIR Terminology Service Provider

```python
class FHIRTerminologyProvider(TerminologyProvider):
    """
    Uses FHIR Terminology Service operations.

    Supports:
    - $lookup: Get code details
    - $translate: Crosswalk between value sets/code systems
    - $validate-code: Validate code membership

    Compatible with:
    - Ontoserver
    - HAPI FHIR JPA
    - tx.fhir.org (public test server)
    """

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token

    def crosswalk(self, source_system: str, source_code: str,
                  target_system: str) -> List[TerminologyMapping]:
        """
        Use $translate operation:
        POST [base]/ConceptMap/$translate
        {
          "system": "http://snomed.info/sct",
          "code": "44054006",
          "target": "http://hl7.org/fhir/sid/icd-10-cm"
        }
        """
        pass
```

---

## 8. Error Handling & Observability

### 8.1 Exception Hierarchy

```python
class EnrichmentError(Exception):
    """Base exception for enrichment errors."""
    pass

class TerminologyProviderError(EnrichmentError):
    """Error communicating with terminology service."""
    pass

class MappingNotFoundError(EnrichmentError):
    """No mapping found between code systems."""
    def __init__(self, source_system: str, source_code: str, target_system: str):
        self.source_system = source_system
        self.source_code = source_code
        self.target_system = target_system
        super().__init__(
            f"No mapping found: {source_system}#{source_code} → {target_system}"
        )

class AmbiguousMappingError(EnrichmentError):
    """Multiple possible mappings found, manual review needed."""
    def __init__(self, mappings: List[TerminologyMapping]):
        self.mappings = mappings
        super().__init__(f"Found {len(mappings)} possible mappings")
```

### 8.2 Logging Strategy

```python
import logging

logger = logging.getLogger("ccda_to_fhir.enrichment")

# Log enrichment attempts
logger.info(
    "Enriching Condition",
    extra={
        "resource_id": condition.id,
        "source_system": "snomed",
        "source_code": "44054006",
        "target_system": "icd10cm"
    }
)

# Log warnings for missing mappings
logger.warning(
    "No ICD-10-CM mapping found",
    extra={
        "source_code": "44054006",
        "source_system": "snomed"
    }
)

# Log errors for API failures
logger.error(
    "UMLS API request failed",
    extra={
        "status_code": 503,
        "retry_after": 60
    },
    exc_info=True
)
```

### 8.3 Metrics & Observability

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class EnrichmentStats:
    """Statistics from enrichment operation."""
    resources_processed: int
    resources_enriched: int
    codes_added: int
    codes_validated: int
    codes_invalid: int
    mappings_found: Dict[str, int]  # {'snomed→icd10cm': 42, ...}
    errors: int
    warnings: int
    duration_ms: float

    def success_rate(self) -> float:
        if self.resources_processed == 0:
            return 0.0
        return self.resources_enriched / self.resources_processed
```

---

## 9. Configuration & Usage Examples

### 9.1 Basic Usage

```python
from ccda_to_fhir import convert
from ccda_to_fhir.enrichment import CodeEnricher
from ccda_to_fhir.enrichment.providers import UMLSProvider

# Standard conversion
bundle = convert(xml_content)

# Enrich with UMLS
provider = UMLSProvider(api_key=os.environ["UMLS_API_KEY"])
enricher = CodeEnricher(provider)

# Add ICD-10-CM codes to all Conditions
enriched_bundle = enricher.enrich(
    bundle,
    resource_types=["Condition"],
    crosswalks={"snomed": "icd10cm"}
)
```

### 9.2 Advanced Usage with Caching

```python
from ccda_to_fhir.enrichment.providers import UMLSProvider, CachedProvider

# Setup cached provider
umls = UMLSProvider(api_key=os.environ["UMLS_API_KEY"])
provider = CachedProvider(
    delegate=umls,
    cache_path="./terminology_cache.db",
    ttl_days=30
)

# Enrich multiple resource types
enricher = CodeEnricher(provider, fail_on_error=False)
enriched = enricher.enrich(
    bundle,
    resource_types=["Condition", "Procedure", "MedicationRequest"],
    crosswalks={
        "snomed": "icd10cm",
        "rxnorm": "ndc",
        "cpt": "snomed"
    },
    validate_codes=True,
    update_displays=True
)

# Check statistics
stats = enricher.get_stats()
print(f"Enriched {stats.resources_enriched}/{stats.resources_processed} resources")
print(f"Added {stats.codes_added} additional codes")
print(f"Success rate: {stats.success_rate():.1%}")
```

### 9.3 Custom Provider Implementation

```python
from ccda_to_fhir.enrichment.providers import TerminologyProvider

class LocalMappingProvider(TerminologyProvider):
    """
    Simple provider using local CSV mapping tables.

    Good for:
    - Offline environments
    - Custom institutional mappings
    - Testing
    """

    def __init__(self, mapping_file: str):
        self.mappings = self._load_mappings(mapping_file)

    def crosswalk(self, source_system: str, source_code: str,
                  target_system: str) -> List[TerminologyMapping]:
        key = f"{source_system}|{source_code}|{target_system}"
        if key in self.mappings:
            return [self.mappings[key]]
        return []

    def _load_mappings(self, file: str) -> dict:
        # Load from CSV: source_system,source_code,target_system,target_code
        import csv
        mappings = {}
        with open(file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['source_system']}|{row['source_code']}|{row['target_system']}"
                mappings[key] = TerminologyMapping(
                    source_system=row['source_system'],
                    source_code=row['source_code'],
                    target_system=row['target_system'],
                    target_code=row['target_code'],
                    target_display=row.get('target_display')
                )
        return mappings

# Usage
provider = LocalMappingProvider("./my_mappings.csv")
enricher = CodeEnricher(provider)
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
def test_snomed_to_icd10_mapping():
    """Test SNOMED CT to ICD-10-CM crosswalk."""
    provider = MockProvider({
        ("snomed", "44054006", "icd10cm"): [
            TerminologyMapping(
                source_system="snomed",
                source_code="44054006",
                target_system="icd10cm",
                target_code="E11.9",
                target_display="Type 2 diabetes without complications"
            )
        ]
    })

    enricher = CodeEnricher(provider)
    condition = Condition(
        code=CodeableConcept(coding=[
            Coding(system="http://snomed.info/sct", code="44054006")
        ])
    )

    enriched = enricher.enrich_resource(
        condition,
        crosswalks={"snomed": "icd10cm"}
    )

    assert len(enriched.code.coding) == 2
    assert enriched.code.coding[1].code == "E11.9"
```

### 10.2 Integration Tests

```python
@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("UMLS_API_KEY"),
                   reason="UMLS_API_KEY not set")
def test_umls_provider_real_api():
    """Test against real UMLS API."""
    provider = UMLSProvider(api_key=os.environ["UMLS_API_KEY"])

    # Test known mapping
    mappings = provider.crosswalk(
        source_system="http://snomed.info/sct",
        source_code="44054006",
        target_system="http://hl7.org/fhir/sid/icd-10-cm"
    )

    assert len(mappings) > 0
    assert any(m.target_code == "E11.9" for m in mappings)
```

### 10.3 Performance Tests

```python
@pytest.mark.performance
def test_enrichment_performance():
    """Ensure enrichment completes in reasonable time."""
    # Load large test bundle (100+ resources)
    bundle = load_large_test_bundle()

    provider = CachedProvider(
        delegate=MockProvider(preloaded_mappings),
        cache_path=":memory:"
    )
    enricher = CodeEnricher(provider)

    start = time.time()
    enricher.enrich(bundle, crosswalks={"snomed": "icd10cm"})
    duration = time.time() - start

    # Should complete in < 5 seconds for 100 resources with cache
    assert duration < 5.0
```

---

## 11. Trade-offs & Considerations

### 11.1 Performance Impact

**Enrichment adds latency:**
- API calls: 100-500ms per code lookup
- Caching reduces to ~1ms for cache hits
- Batch processing amortizes overhead

**Mitigation strategies:**
- Local cache with high TTL
- Background enrichment (async)
- Batch API requests where supported
- Pre-populate cache for common codes

### 11.2 Data Quality vs. Automation

**Automated crosswalks may be inaccurate:**
- SNOMED→ICD-10: Often requires clinical context
- Context-free mapping can introduce errors
- Example: "Chest pain" → ICD-10 has 20+ codes

**Mitigation:**
- Confidence scoring (flag low-confidence mappings)
- Human review for critical data
- Conservative approach: Skip ambiguous mappings
- Document mapping limitations clearly

### 11.3 External Dependencies

**Terminology services introduce:**
- Network dependency (availability risk)
- API rate limits
- Authentication requirements
- Cost (some services charge per request)

**Mitigation:**
- Provider interface allows fallbacks
- Cached provider for offline resilience
- Graceful degradation (enrichment optional)
- Local mapping tables for critical codes

### 11.4 Maintenance Burden

**Terminologies change over time:**
- ICD-10-CM updates annually
- SNOMED CT updates biannually
- RxNorm updates monthly
- NDC codes change constantly

**Mitigation:**
- Cache TTL balances freshness vs. performance
- Document version dependencies
- Monitor for deprecated codes
- Provide code update utilities

---

## 12. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Define provider interface
- [ ] Implement NoOpProvider (testing)
- [ ] Implement CodeEnricher orchestrator
- [ ] Add Condition enrichment strategy
- [ ] Write unit tests
- [ ] Documentation

### Phase 2: First Provider (Weeks 3-4)
- [ ] Implement UMLSProvider
- [ ] Add caching layer
- [ ] Integration tests with UMLS
- [ ] Error handling and retries
- [ ] Rate limiting support

### Phase 3: Additional Strategies (Weeks 5-6)
- [ ] MedicationRequest enrichment (RxNorm→NDC)
- [ ] Procedure enrichment (SNOMED→CPT)
- [ ] Observation validation (LOINC)
- [ ] Display name updates

### Phase 4: Production Readiness (Weeks 7-8)
- [ ] Performance optimization
- [ ] Comprehensive error handling
- [ ] Metrics and observability
- [ ] Production documentation
- [ ] Example configurations

### Phase 5: Advanced Features (Future)
- [ ] FHIR Terminology Service provider
- [ ] Batch processing optimizations
- [ ] Background/async enrichment
- [ ] ConceptMap resource generation
- [ ] Enrichment audit trail

---

## 13. Security & Privacy Considerations

### 13.1 Data Exposure

**Risk**: Sending codes to external services may expose PHI context

**Mitigation:**
- Crosswalk requests only send codes (no patient data)
- Document data handling in privacy policy
- Support on-premise terminology servers
- Provide offline/local provider options

### 13.2 API Key Management

**Risk**: UMLS/terminology API keys in code

**Mitigation:**
```python
# Good: Environment variables
provider = UMLSProvider(api_key=os.environ["UMLS_API_KEY"])

# Bad: Hardcoded
provider = UMLSProvider(api_key="abc123")  # Never do this
```

### 13.3 Rate Limiting & DoS

**Risk**: Excessive API calls from enrichment

**Mitigation:**
- Implement client-side rate limiting
- Use cached provider for all production use
- Batch requests where possible
- Monitor API usage

---

## 14. Success Metrics

### 14.1 Adoption Metrics
- % of users enabling enrichment
- Most common crosswalk configurations
- Provider implementation diversity

### 14.2 Quality Metrics
- Mapping accuracy (validated sample)
- Confidence score distributions
- Error/warning rates

### 14.3 Performance Metrics
- Cache hit rate (target: >90%)
- Average enrichment time per resource
- API call volume and costs

---

## 15. Open Questions

1. **Mapping ambiguity**: How should we handle 1:many mappings?
   - Option A: Include all matches
   - Option B: Use confidence scores and threshold
   - Option C: Flag for human review

2. **Code versioning**: Should we track terminology version?
   - SNOMED CT releases twice/year
   - Could break mappings

3. **ConceptMap resources**: Generate FHIR ConceptMap resources?
   - Document mappings used
   - Enable reproducibility
   - Adds complexity

4. **Async enrichment**: Support background enrichment?
   - Better for large batches
   - Requires queue infrastructure
   - More complex API

---

## 16. References

### Standards & Specifications
- [FHIR Terminology Service](https://www.hl7.org/fhir/terminology-service.html)
- [UMLS Terminology Services API](https://documentation.uts.nlm.nih.gov/rest/home.html)
- [NLM Value Set Authority Center](https://vsac.nlm.nih.gov/)
- [SNOMED CT to ICD-10-CM Map](https://www.nlm.nih.gov/research/umls/mapping_projects/snomedct_to_icd10cm.html)

### Code Systems
- [SNOMED CT](https://www.snomed.org/)
- [LOINC](https://loinc.org/)
- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/)
- [ICD-10-CM](https://www.cdc.gov/nchs/icd/icd-10-cm.htm)

### Related Projects
- [FHIR ConceptMap](https://www.hl7.org/fhir/conceptmap.html)
- [Ontoserver](https://ontoserver.csiro.au/) (FHIR terminology server)
- [HAPI FHIR JPA](https://hapifhir.io/hapi-fhir/docs/server_jpa/terminology.html)

---

## 17. Conclusion

Medical code enrichment is a valuable **optional enhancement** to ccda-to-fhir that can:

1. **Improve interoperability** by providing multiple code system representations
2. **Enable analytics** through standardized billing codes (ICD-10-CM)
3. **Enhance data quality** via code validation and display name standardization
4. **Support decision support** with normalized terminology

The proposed design:
- ✅ Maintains library simplicity (optional module)
- ✅ Preserves "fail loud" philosophy (explicit errors)
- ✅ Supports multiple providers (flexible integration)
- ✅ Enables incremental adoption (per-resource enrichment)
- ✅ Stays MIT licensed (clean-room implementation)

**Recommendation**: Implement in phases, starting with Condition enrichment (SNOMED→ICD-10-CM) using UMLS provider with caching.
