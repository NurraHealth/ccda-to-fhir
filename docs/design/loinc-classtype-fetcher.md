# Design: LOINC CLASSTYPE Fetcher Interface

**Status**: Proposed
**Author**: Design Discussion
**Date**: 2025-12-16
**Version**: 1.0

---

## 1. Problem Statement

### Current State

The observation converter uses **template-based categorization** to assign FHIR `Observation.category` values:

```python
def _determine_category(self, observation: Observation) -> JSONObject | None:
    """Determine observation category based on template ID."""
    if template.root == TemplateIds.VITAL_SIGN_OBSERVATION:
        return {"coding": [{"code": "vital-signs", ...}]}
    elif template.root == TemplateIds.RESULT_OBSERVATION:
        return {"coding": [{"code": "laboratory", ...}]}
    # etc.
```

**Coverage**: ~95% of real-world C-CDA observations (all standard templates covered)

**Gap**: Generic observations without recognized template IDs cannot be categorized.

### Enhancement Opportunity

LOINC codes have a `CLASSTYPE` property that maps to FHIR categories:

| LOINC CLASSTYPE | FHIR Category |
|-----------------|---------------|
| 1 | `laboratory` |
| 2 | `clinical` |
| 3 | `claims-attachment` |
| 4 | `survey` |

**Challenge**: CLASSTYPE requires external data source (LOINC database, API, or file).

---

## 2. Design Goals

### Primary Goals

1. **Zero Dependencies**: Library should not depend on any specific LOINC data source
2. **User Control**: Users provide their own LOINC lookup implementation
3. **Optional Enhancement**: Fallback to template-based categorization if no fetcher provided
4. **Performance**: Avoid blocking I/O in the conversion pipeline
5. **Testability**: Easy to mock for unit tests

### Non-Goals

- Bundling LOINC database with the library (licensing, size, maintenance)
- Implementing specific LOINC data source integrations
- Caching strategy (delegated to user implementation)

---

## 3. Proposed Architecture

### 3.1 Fetcher Interface

Define an abstract interface that users implement:

```python
# ccda_to_fhir/terminology/loinc_fetcher.py

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LoincCode:
    """LOINC code information."""
    code: str
    display: str | None = None
    classtype: int | None = None  # 1=Laboratory, 2=Clinical, 3=Claims, 4=Survey
    component: str | None = None
    property: str | None = None
    time_aspect: str | None = None
    system: str | None = None
    scale_type: str | None = None
    method_type: str | None = None


class LoincFetcher(ABC):
    """Abstract interface for LOINC code lookup.

    Users implement this interface to provide LOINC data from their preferred source:
    - Local database (PostgreSQL, SQLite, etc.)
    - REST API (LOINC API, internal terminology server)
    - Static reference file (CSV, JSON, Parquet)
    - In-memory cache with fallback
    """

    @abstractmethod
    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        """Fetch LOINC code information.

        Args:
            loinc_code: LOINC code (e.g., "8480-6")

        Returns:
            LoincCode object with CLASSTYPE and other properties, or None if not found

        Note:
            Implementations should handle:
            - Caching for performance
            - Error handling (network failures, missing data)
            - Logging for debugging
        """
        pass
```

### 3.2 Integration with Converter

Modify `ObservationConverter` to accept optional fetcher:

```python
# ccda_to_fhir/converters/observation.py

class ObservationConverter(BaseConverter[Observation]):
    """Convert C-CDA Observation to FHIR Observation resource."""

    def __init__(
        self,
        section_name: str | None = None,
        loinc_fetcher: LoincFetcher | None = None
    ):
        """Initialize converter.

        Args:
            section_name: Name of the containing section
            loinc_fetcher: Optional LOINC code fetcher for enhanced categorization
        """
        super().__init__()
        self.section_name = section_name
        self.loinc_fetcher = loinc_fetcher

    def _determine_category(self, observation: Observation) -> JSONObject | None:
        """Determine observation category.

        Strategy:
        1. Try template-based categorization (primary method)
        2. If no template match and fetcher available, try LOINC CLASSTYPE
        3. Return None if both methods fail
        """
        if not observation.template_id:
            # No template ID - try LOINC CLASSTYPE if available
            return self._category_from_loinc_classtype(observation)

        # Check template IDs (existing logic)
        for template in observation.template_id:
            if template.root == TemplateIds.VITAL_SIGN_OBSERVATION:
                return self._create_category("vital-signs", "Vital Signs")
            elif template.root == TemplateIds.RESULT_OBSERVATION:
                return self._create_category("laboratory", "Laboratory")
            # ... other templates

        # Unknown template - try LOINC CLASSTYPE as fallback
        return self._category_from_loinc_classtype(observation)

    def _category_from_loinc_classtype(self, observation: Observation) -> JSONObject | None:
        """Derive category from LOINC CLASSTYPE using fetcher.

        Args:
            observation: C-CDA Observation with code element

        Returns:
            FHIR category CodeableConcept, or None if fetcher unavailable or lookup fails
        """
        if not self.loinc_fetcher:
            return None

        # Extract LOINC code from observation.code
        if not observation.code or observation.code.code_system != "2.16.840.1.113883.6.1":
            return None  # Not a LOINC code

        loinc_code = observation.code.code

        try:
            loinc_info = self.loinc_fetcher.get_code(loinc_code)
            if not loinc_info or loinc_info.classtype is None:
                return None

            # Map CLASSTYPE to FHIR category
            category_map = {
                1: ("laboratory", "Laboratory"),
                2: ("exam", "Exam"),  # CLASSTYPE 2 is clinical/exam
                3: ("procedure", "Procedure"),  # Claims attachment
                4: ("survey", "Survey"),
            }

            if loinc_info.classtype in category_map:
                code, display = category_map[loinc_info.classtype]
                return self._create_category(code, display)

        except Exception as e:
            # Log error but don't fail conversion
            import logging
            logging.warning(f"LOINC fetcher error for code {loinc_code}: {e}")

        return None

    def _create_category(self, code: str, display: str) -> JSONObject:
        """Helper to create category CodeableConcept."""
        return {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": code,
                "display": display,
            }]
        }
```

### 3.3 Document Converter Integration

Pass fetcher through the conversion pipeline:

```python
# ccda_to_fhir/convert.py

def convert_document(
    ccda_xml: str,
    loinc_fetcher: LoincFetcher | None = None,
) -> JSONObject:
    """Convert C-CDA document to FHIR Bundle.

    Args:
        ccda_xml: C-CDA XML document string
        loinc_fetcher: Optional LOINC code fetcher for enhanced categorization

    Returns:
        FHIR Bundle resource
    """
    # ... existing parsing logic ...

    # Pass fetcher to observation converter
    obs_converter = ObservationConverter(
        section_name=section.title,
        loinc_fetcher=loinc_fetcher
    )

    # ... rest of conversion ...
```

---

## 4. Example Implementations

### 4.1 In-Memory Dictionary (Simple)

```python
# example_fetchers/memory_fetcher.py

from ccda_to_fhir.terminology import LoincFetcher, LoincCode

class InMemoryLoincFetcher(LoincFetcher):
    """Simple in-memory LOINC fetcher using a dictionary.

    Suitable for:
    - Small number of codes
    - Testing
    - Demonstrations
    """

    def __init__(self, codes: dict[str, int]):
        """Initialize with code->CLASSTYPE mapping.

        Args:
            codes: Dictionary mapping LOINC codes to CLASSTYPE values
                   e.g., {"8480-6": 2, "2345-7": 1}
        """
        self.codes = codes

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        classtype = self.codes.get(loinc_code)
        if classtype is None:
            return None

        return LoincCode(code=loinc_code, classtype=classtype)


# Usage
fetcher = InMemoryLoincFetcher({
    "8480-6": 2,   # Systolic BP - Clinical
    "2345-7": 1,   # Glucose - Laboratory
    "8867-4": 2,   # Heart rate - Clinical
})

bundle = convert_document(ccda_xml, loinc_fetcher=fetcher)
```

### 4.2 SQLite Database (Medium)

```python
# example_fetchers/sqlite_fetcher.py

import sqlite3
from ccda_to_fhir.terminology import LoincFetcher, LoincCode

class SqliteLoincFetcher(LoincFetcher):
    """LOINC fetcher using SQLite database.

    Suitable for:
    - Medium-sized datasets (~100k codes)
    - Offline applications
    - Embedded systems

    Database schema:
        CREATE TABLE loinc (
            code TEXT PRIMARY KEY,
            display TEXT,
            classtype INTEGER,
            component TEXT,
            property TEXT
        );
    """

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        cursor = self.conn.execute(
            "SELECT * FROM loinc WHERE code = ?",
            (loinc_code,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        return LoincCode(
            code=row["code"],
            display=row["display"],
            classtype=row["classtype"],
            component=row["component"],
            property=row["property"],
        )

    def __del__(self):
        self.conn.close()


# Usage
fetcher = SqliteLoincFetcher("/path/to/loinc.db")
bundle = convert_document(ccda_xml, loinc_fetcher=fetcher)
```

### 4.3 REST API with Caching (Production)

```python
# example_fetchers/api_fetcher.py

import requests
from functools import lru_cache
from ccda_to_fhir.terminology import LoincFetcher, LoincCode

class ApiLoincFetcher(LoincFetcher):
    """LOINC fetcher using REST API with LRU cache.

    Suitable for:
    - Production systems
    - Large datasets
    - Always up-to-date data

    Features:
    - LRU cache (default 10,000 codes)
    - Timeout handling
    - Error resilience
    """

    def __init__(self, api_url: str, api_key: str | None = None, cache_size: int = 10000):
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

        # Wrap get_code_impl with LRU cache
        self._cached_get = lru_cache(maxsize=cache_size)(self._get_code_impl)

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        return self._cached_get(loinc_code)

    def _get_code_impl(self, loinc_code: str) -> Optional[LoincCode]:
        """Implementation without caching (for LRU wrapper)."""
        try:
            response = self.session.get(
                f"{self.api_url}/loinc/{loinc_code}",
                timeout=2.0  # Fast timeout to avoid blocking
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            return LoincCode(
                code=data["code"],
                display=data.get("display"),
                classtype=data.get("classtype"),
                component=data.get("component"),
                property=data.get("property"),
            )

        except (requests.RequestException, KeyError, ValueError) as e:
            import logging
            logging.warning(f"LOINC API error for {loinc_code}: {e}")
            return None


# Usage
fetcher = ApiLoincFetcher(
    api_url="https://terminology-server.example.com/api",
    api_key="your-api-key",
    cache_size=10000
)
bundle = convert_document(ccda_xml, loinc_fetcher=fetcher)
```

### 4.4 CSV File (Static Reference)

```python
# example_fetchers/csv_fetcher.py

import csv
from pathlib import Path
from ccda_to_fhir.terminology import LoincFetcher, LoincCode

class CsvLoincFetcher(LoincFetcher):
    """LOINC fetcher using CSV file.

    Suitable for:
    - Static reference data
    - Offline applications
    - Simple deployments

    CSV format:
        code,display,classtype
        8480-6,Systolic blood pressure,2
        2345-7,Glucose [Mass/volume] in Serum or Plasma,1
    """

    def __init__(self, csv_path: str | Path):
        self.codes: dict[str, LoincCode] = {}

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.codes[row["code"]] = LoincCode(
                    code=row["code"],
                    display=row.get("display"),
                    classtype=int(row["classtype"]) if row.get("classtype") else None,
                )

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        return self.codes.get(loinc_code)


# Usage
fetcher = CsvLoincFetcher("loinc_classtype.csv")
bundle = convert_document(ccda_xml, loinc_fetcher=fetcher)
```

---

## 5. Testing Strategy

### 5.1 Mock Fetcher for Unit Tests

```python
# tests/test_observation_category_classtype.py

class MockLoincFetcher(LoincFetcher):
    """Test double for LOINC fetcher."""

    def __init__(self, code_map: dict[str, int]):
        self.code_map = code_map
        self.call_count = 0

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        self.call_count += 1
        classtype = self.code_map.get(loinc_code)
        return LoincCode(code=loinc_code, classtype=classtype) if classtype else None


def test_category_from_loinc_classtype_laboratory():
    """Test CLASSTYPE 1 (Laboratory) → laboratory category."""
    fetcher = MockLoincFetcher({"2345-7": 1})  # Glucose - Laboratory

    observation_xml = """
    <observation classCode="OBS" moodCode="EVN">
        <code code="2345-7" codeSystem="2.16.840.1.113883.6.1"
              displayName="Glucose [Mass/volume] in Serum or Plasma"/>
        <statusCode code="completed"/>
        <value xsi:type="PQ" value="95" unit="mg/dL"/>
    </observation>
    """

    converter = ObservationConverter(loinc_fetcher=fetcher)
    fhir_obs = converter.convert(parse_observation(observation_xml))

    assert fhir_obs["category"][0]["coding"][0]["code"] == "laboratory"
    assert fetcher.call_count == 1


def test_category_fallback_when_fetcher_returns_none():
    """Test graceful fallback when LOINC code not found."""
    fetcher = MockLoincFetcher({})  # Empty - all lookups fail

    observation_xml = """
    <observation classCode="OBS" moodCode="EVN">
        <code code="UNKNOWN-CODE" codeSystem="2.16.840.1.113883.6.1"/>
        <statusCode code="completed"/>
    </observation>
    """

    converter = ObservationConverter(loinc_fetcher=fetcher)
    fhir_obs = converter.convert(parse_observation(observation_xml))

    # Should return None gracefully, not crash
    assert fhir_obs.get("category") is None


def test_template_based_takes_precedence():
    """Test template-based categorization has priority over CLASSTYPE."""
    fetcher = MockLoincFetcher({"8480-6": 2})  # Systolic BP

    observation_xml = """
    <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.27"/>  <!-- Vital Sign -->
        <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
        <statusCode code="completed"/>
    </observation>
    """

    converter = ObservationConverter(loinc_fetcher=fetcher)
    fhir_obs = converter.convert(parse_observation(observation_xml))

    # Should use template-based "vital-signs", not CLASSTYPE "exam"
    assert fhir_obs["category"][0]["coding"][0]["code"] == "vital-signs"
    assert fetcher.call_count == 0  # Fetcher not called due to template match
```

---

## 6. Performance Considerations

### 6.1 Caching Strategy

**Problem**: Network I/O or database queries can be slow.

**Solution**: Implement caching in the fetcher, not the converter.

```python
class CachedLoincFetcher(LoincFetcher):
    """Wrapper that adds caching to any fetcher."""

    def __init__(self, delegate: LoincFetcher, cache_size: int = 10000):
        self.delegate = delegate
        self._cached_get = lru_cache(maxsize=cache_size)(self._fetch)

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        return self._cached_get(loinc_code)

    def _fetch(self, loinc_code: str) -> Optional[LoincCode]:
        return self.delegate.get_code(loinc_code)
```

### 6.2 Batch Fetching

For high-volume conversions, pre-fetch common codes:

```python
class BatchLoincFetcher(LoincFetcher):
    """Fetcher that supports batch pre-loading."""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.cache: dict[str, LoincCode] = {}

    def preload(self, codes: list[str]) -> None:
        """Pre-fetch multiple codes in one API call."""
        response = requests.post(
            f"{self.api_url}/loinc/batch",
            json={"codes": codes}
        )
        for item in response.json():
            self.cache[item["code"]] = LoincCode(**item)

    def get_code(self, loinc_code: str) -> Optional[LoincCode]:
        return self.cache.get(loinc_code)


# Usage
fetcher = BatchLoincFetcher("https://api.example.com")
fetcher.preload(["8480-6", "8462-4", "2345-7"])  # Common codes
bundle = convert_document(ccda_xml, loinc_fetcher=fetcher)
```

---

## 7. Migration Path

### Phase 1: Add Interface (Non-Breaking)

1. Add `LoincFetcher` interface to `ccda_to_fhir.terminology`
2. Update `ObservationConverter` to accept optional `loinc_fetcher` parameter
3. Implement `_category_from_loinc_classtype()` method
4. **No breaking changes** - fetcher is optional

### Phase 2: Documentation & Examples

1. Add example implementations to `examples/` directory
2. Update README with usage guide
3. Add section to docs on LOINC integration

### Phase 3: Community Contributions

1. Encourage users to share their fetcher implementations
2. Create registry of community fetchers (GitHub wiki?)
3. Consider packaging common fetchers as optional extras (`pip install ccda-to-fhir[loinc-sqlite]`)

---

## 8. Trade-offs & Alternatives

### Chosen Approach: Fetcher Interface

**Pros:**
- Zero dependencies on LOINC data sources
- Maximum flexibility for users
- Easy to test with mocks
- No licensing concerns
- No maintenance burden for LOINC data updates

**Cons:**
- Users must implement/configure fetcher
- Extra setup step
- Not "batteries included"

### Alternative 1: Bundle Static File

Bundle a CSV file with LOINC CLASSTYPE mappings.

**Pros:**
- Works out of the box
- No user configuration

**Cons:**
- Library size increases (~1-5MB)
- LOINC licensing restrictions
- Data goes stale
- Maintenance burden for updates

**Verdict**: ❌ Rejected (licensing, maintenance)

### Alternative 2: Hard-Code Common Codes

Hard-code CLASSTYPE for top 100 codes.

**Pros:**
- No dependencies
- Fast lookups
- Simple implementation

**Cons:**
- Incomplete coverage
- Magic numbers in code
- Maintenance burden

**Verdict**: ⚠️ Possible as fallback, but not primary solution

### Alternative 3: Plugin System

Support pluggable terminology backends via entry points.

**Pros:**
- Discoverability
- Easy to swap implementations

**Cons:**
- Over-engineered for simple use case
- Complexity

**Verdict**: ❌ Rejected (YAGNI)

---

## 9. Open Questions

1. **Should we provide a default no-op fetcher?**
   - Pro: Cleaner API (`loinc_fetcher=NoOpFetcher()` vs `loinc_fetcher=None`)
   - Con: Extra class for minimal benefit
   - **Decision**: No, `None` is pythonic

2. **Should we log when CLASSTYPE lookup is skipped?**
   - Pro: Helps users debug
   - Con: Noisy logs
   - **Decision**: Yes, at DEBUG level only

3. **Should we support async fetchers for I/O-bound lookups?**
   - Pro: Better performance for high-volume conversions
   - Con: Complexity, requires async/await throughout pipeline
   - **Decision**: No for v1, revisit if needed

---

## 10. Implementation Checklist

- [ ] Define `LoincFetcher` interface in `ccda_to_fhir/terminology/loinc_fetcher.py`
- [ ] Define `LoincCode` dataclass
- [ ] Add `loinc_fetcher` parameter to `ObservationConverter.__init__()`
- [ ] Implement `_category_from_loinc_classtype()` method
- [ ] Update `_determine_category()` to use CLASSTYPE fallback
- [ ] Add unit tests with mock fetcher
- [ ] Add integration tests with real fetcher implementations
- [ ] Document fetcher interface in docstrings
- [ ] Create example implementations:
  - [ ] `InMemoryLoincFetcher`
  - [ ] `CsvLoincFetcher`
  - [ ] `SqliteLoincFetcher`
  - [ ] `ApiLoincFetcher`
- [ ] Update README with usage guide
- [ ] Add design doc to `docs/design/`
- [ ] Add migration guide for users

---

## 11. Conclusion

The **Fetcher Interface** pattern provides a clean, flexible solution for LOINC CLASSTYPE integration:

- ✅ **Zero dependencies**: No hard coupling to LOINC data sources
- ✅ **User control**: Users choose their own data source
- ✅ **Optional**: Works without fetcher (template-based fallback)
- ✅ **Testable**: Easy to mock for unit tests
- ✅ **Extensible**: Users can implement custom fetchers

This design follows the **Dependency Inversion Principle** - the library depends on an abstraction (interface), not a concrete implementation (specific database/API).

**Next Steps**: Implement Phase 1 (interface + core logic) and gather user feedback before proceeding to Phase 2/3.
