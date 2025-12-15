# Production Deployment Guide

This guide covers deploying the C-CDA to FHIR converter in production environments with proper logging, validation, and monitoring.

## Table of Contents

- [Quick Start](#quick-start)
- [Logging Configuration](#logging-configuration)
- [FHIR Resource Validation](#fhir-resource-validation)
- [Performance Monitoring](#performance-monitoring)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Basic Usage

```python
from ccda_to_fhir import convert_document

# Convert C-CDA XML to FHIR Bundle
xml_content = open("patient_document.xml").read()
bundle = convert_document(xml_content)

# Bundle contains all converted FHIR resources
print(f"Converted {len(bundle['entry'])} resources")
```

### Production-Ready Usage

```python
from ccda_to_fhir import convert_document
from ccda_to_fhir.logging_config import setup_logging, get_logger
from ccda_to_fhir.validation import get_validator
from ccda_to_fhir.profiling import profile_operation, get_metrics

# Setup logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Enable validation
validator = get_validator(strict=False)

# Convert with profiling
with profile_operation("document_conversion"):
    bundle = convert_document(xml_content)

# Validate output
validator.validate_bundle(bundle)

# Log performance metrics
get_metrics().report()
```

## Logging Configuration

### Basic Logging Setup

```python
from ccda_to_fhir.logging_config import setup_logging
import logging

# Configure logging level and format
setup_logging(
    level=logging.INFO,     # DEBUG, INFO, WARNING, ERROR
    detailed=False          # Include file/line numbers
)
```

### Structured Logging with Correlation IDs

```python
from ccda_to_fhir.logging_config import get_logger

# Get logger with correlation ID for tracking
logger = get_logger(__name__, correlation_id="req-12345")

# All log messages will include the correlation ID
logger.info("Starting conversion")  # [req-12345] Starting conversion
logger.error("Conversion failed", exc_info=True)
```

### Log Levels

- **DEBUG**: Detailed information for debugging (includes validation passes)
- **INFO**: General information (conversion progress, metrics)
- **WARNING**: Warning messages (non-critical issues, fallbacks)
- **ERROR**: Error messages with stack traces

### Production Logging Best Practices

1. **Use INFO level** in production to avoid verbose DEBUG logs
2. **Enable detailed format** for debugging issues
3. **Use correlation IDs** to track requests across services
4. **Integrate with centralized logging** (Elasticsearch, Splunk, etc.)

Example integration with Python logging handlers:

```python
import logging
from logging.handlers import RotatingFileHandler

# Add file handler
file_handler = RotatingFileHandler(
    "ccda_conversion.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

logging.getLogger().addHandler(file_handler)
```

## FHIR Resource Validation

### Validation Modes

The converter supports two validation modes:

1. **Non-Strict Mode** (default): Logs validation errors but continues processing
2. **Strict Mode**: Raises exceptions on validation failures

### Basic Validation

```python
from ccda_to_fhir.validation import get_validator

# Non-strict validation (logs errors, continues)
validator = get_validator(strict=False)
bundle = convert_document(xml_content)
validator.validate_bundle(bundle)

# Check validation statistics
stats = validator.get_stats()
print(f"Validated: {stats['validated']}, "
      f"Passed: {stats['passed']}, "
      f"Failed: {stats['failed']}")
```

### Strict Validation

```python
from ccda_to_fhir.validation import get_validator, ValidationError

# Strict validation (raises on errors)
validator = get_validator(strict=True)

try:
    bundle = convert_document(xml_content)
    validator.validate_bundle(bundle)
except ValidationError as e:
    print(f"Validation failed: {e.resource_type}")
    print(f"Errors: {e.errors}")
```

### Validating Individual Resources

```python
from fhir.resources.patient import Patient
from ccda_to_fhir.validation import validate_resource

# Validate a single resource
patient_dict = {
    "resourceType": "Patient",
    "id": "patient-1",
    # ... patient data
}

validated = validate_resource(patient_dict, Patient, strict=False)
if validated:
    print("Patient is valid!")
```

### When to Use Validation

- **Development**: Use strict mode to catch issues early
- **Testing**: Always validate in integration tests
- **Production**: Use non-strict mode with monitoring of validation stats
- **High-Compliance Environments**: Use strict mode for regulated industries

## Performance Monitoring

### Basic Profiling

```python
from ccda_to_fhir.profiling import profile_operation

# Profile a specific operation
with profile_operation("parse_xml"):
    doc = parse_ccda(xml_content)

with profile_operation("convert_resources"):
    bundle = converter.convert(doc)
```

### Function Profiling Decorator

```python
from ccda_to_fhir.profiling import profile

@profile("custom_conversion", log_result=True)
def convert_custom_section(section):
    # Your conversion logic
    return resources
```

### Detailed Conversion Profiling

```python
from ccda_to_fhir.profiling import ConversionProfiler

profiler = ConversionProfiler()
profiler.start()

# Your conversion code here
bundle = convert_document(xml_content)

profiler.finish()
profiler.log_report()

# Get detailed report
report = profiler.get_report()
print(f"Total time: {report['total_time']:.3f}s")
print(f"Resource counts: {report['resources']}")
```

### Metrics Reporting

```python
from ccda_to_fhir.profiling import get_metrics

# Get global metrics instance
metrics = get_metrics()

# Process multiple documents
for xml_file in xml_files:
    with profile_operation("convert_document"):
        convert_document(xml_file.read_text())

# Report all metrics
metrics.report()

# Get stats for specific operation
stats = metrics.get_stats("convert_document")
print(f"Average time: {stats['avg']:.3f}s")
print(f"Total calls: {stats['count']}")

# Reset metrics for new batch
metrics.reset()
```

### Performance Best Practices

1. **Batch Processing**: Process documents in batches to amortize overhead
2. **Monitor Metrics**: Track average conversion time and resource counts
3. **Set Alerts**: Alert on conversion times exceeding thresholds
4. **Profile Regularly**: Use profiling to identify bottlenecks

### Expected Performance

Typical conversion performance on standard hardware:

- **Small documents** (<50KB, <10 resources): 50-150ms
- **Medium documents** (50-200KB, 10-50 resources): 150-500ms
- **Large documents** (>200KB, >50 resources): 500ms-2s

Factors affecting performance:
- Document size and complexity
- Number of sections and entries
- Validation enabled (adds ~10-20% overhead)
- I/O for reading XML files

## Error Handling

### Graceful Degradation

The converter is designed to continue processing even when individual resource conversions fail:

```python
# Even if Patient conversion fails, other resources will still be converted
bundle = convert_document(xml_content)

# Check logs for any errors
# Errors are logged with full stack traces but don't stop conversion
```

### Handling Conversion Failures

```python
from ccda_to_fhir import convert_document
from ccda_to_fhir.logging_config import get_logger

logger = get_logger(__name__)

try:
    bundle = convert_document(xml_content)

    # Check if bundle has minimum required resources
    if len(bundle.get("entry", [])) == 0:
        logger.error("Conversion produced no resources")
        raise ValueError("Empty bundle")

    # Proceed with valid bundle

except Exception as e:
    logger.error("Document conversion failed", exc_info=True)
    # Handle failure (retry, dead letter queue, etc.)
```

### Common Error Scenarios

1. **Invalid XML**: Raised during parsing
2. **Missing Required Elements**: Logged but conversion continues
3. **Invalid Codes**: OIDs are mapped, unknown codes use `urn:oid:` format
4. **Validation Failures**: Logged in non-strict mode, raised in strict mode

## Best Practices

### 1. Always Configure Logging

```python
# At application startup
from ccda_to_fhir.logging_config import setup_logging
import logging

setup_logging(level=logging.INFO)
```

### 2. Use Validation in Non-Production Environments

```python
# Development and testing
validator = get_validator(strict=True)

# Production
validator = get_validator(strict=False)
# Monitor validation stats for issues
```

### 3. Monitor Performance

```python
# Track conversion time
with profile_operation("conversion"):
    bundle = convert_document(xml)

# Review metrics periodically
if metrics.get_stats("conversion")["avg"] > 1.0:
    logger.warning("Conversion time exceeds threshold")
```

### 4. Handle Errors Appropriately

```python
try:
    bundle = convert_document(xml)
except Exception as e:
    logger.error("Conversion failed", exc_info=True)
    # Implement retry logic, dead letter queue, etc.
```

### 5. Validate Input

```python
# Check XML is well-formed before conversion
from ccda_to_fhir.ccda.parser import parse_ccda

try:
    doc = parse_ccda(xml_content)
    # Validation passed, proceed with conversion
except Exception as e:
    logger.error("Invalid C-CDA XML", exc_info=True)
    # Reject invalid input
```

## Deployment Checklist

- [ ] Configure logging with appropriate level (INFO for production)
- [ ] Enable FHIR validation (non-strict mode recommended)
- [ ] Set up performance monitoring
- [ ] Configure error handling and retries
- [ ] Set up health check endpoints
- [ ] Monitor conversion metrics
- [ ] Configure alerting for failures
- [ ] Test with representative documents
- [ ] Document any customizations
- [ ] Set up log aggregation

## Troubleshooting

### High Memory Usage

**Symptoms**: Memory consumption increases with document size

**Solutions**:
- Process documents individually rather than in batches
- Implement streaming for very large documents (future enhancement)
- Increase available memory

### Slow Conversion Times

**Symptoms**: Conversion takes longer than expected

**Solutions**:
- Profile to identify bottlenecks
- Disable validation if not needed
- Check for I/O bottlenecks (network, disk)
- Consider caching parsed documents

### Validation Failures

**Symptoms**: Resources fail FHIR validation

**Solutions**:
- Check logs for specific validation errors
- Verify input C-CDA conforms to specification
- Use non-strict validation to continue processing
- Report issues for investigation

### Missing Resources

**Symptoms**: Expected resources not in bundle

**Solutions**:
- Check logs for conversion errors
- Verify C-CDA contains the expected sections
- Check template IDs match expected values
- Enable DEBUG logging for detailed information

## Support

For issues and questions:

1. Check logs for error messages
2. Enable DEBUG logging for more details
3. Review this documentation
4. Check GitHub issues
5. Submit a bug report with:
   - Log output
   - Sample C-CDA document (if possible)
   - Expected vs actual behavior
