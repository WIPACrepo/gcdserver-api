# XML Data Import Tools

Complete toolkit for converting existing XML data into the REST API.

## Quick Start

```bash
# 1. Convert XML to JSON (no upload)
python3 xml_to_json_converter.py input.xml -o output.json

# 2. Convert and upload to REST API
python3 gcd_xml_import.py input.xml --token $KEYCLOAK_TOKEN

# 3. Batch process multiple files
python3 gcd_xml_import.py *.xml --batch --token $KEYCLOAK_TOKEN --api-url http://localhost:8080
```

## Tools Overview

### 1. `xml_to_json_converter.py` - XML to JSON Conversion
Converts XML files to JSON format.

**Supported XML Types:**
- `VEMCalibOm` - VEM calibration data
- `baselines` - ATWD/FADC baseline values
- `DOMCalibration` - DOM calibration properties
- `SPEFit` - Single photon event fitting data
- `geometry` - Detector geometry and positions

**Usage:**
```bash
# Auto-detect type and convert
python3 xml_to_json_converter.py input.xml -o output.json

# Specify type explicitly
python3 xml_to_json_converter.py input.xml --type VEMCalibOm -o output.json

# Pretty-print output
python3 xml_to_json_converter.py input.xml --pretty

# Read from stdin
cat input.xml | python3 xml_to_json_converter.py --pretty
```

**Output Format:**
```json
{
  "metadata": {
    "date": "2014-01-01",
    "first_run": 123614,
    "type": "VEM_Calibration"
  },
  "calibrations": [
    {
      "dom_id": "01,61",
      "string_id": 1,
      "tube_id": 61,
      "pe_per_vem": 116.274,
      ...
    }
  ]
}
```

### 2. `gcd_xml_import.py` - XML to REST API Import
Converts XML and uploads directly to REST API.

**Features:**
- Automatic XML format detection
- OAuth2 authentication with Keycloak
- Batch processing with glob patterns
- Convert-only mode for validation
- Support for multiple endpoints

**Usage:**
```bash
# Single file import
python3 gcd_xml_import.py vem_calib.xml --token $TOKEN

# Batch import multiple files
python3 gcd_xml_import.py *.xml --batch --token $TOKEN

# Convert without uploading
python3 gcd_xml_import.py input.xml --convert-only -o output.json

# Import to specific endpoint
python3 gcd_xml_import.py baseline.xml --token $TOKEN --endpoint detector-status

# Use custom API URL
python3 gcd_xml_import.py input.xml --token $TOKEN --api-url https://api.example.com
```

**Endpoints:**
- `/calibration` - for VEMCalibOm, DOMCalibration, SPEFit
- `/detector-status` - for baselines (requires run number)
- `/geometry` - for geometry data

### 3. `xml_import_examples.py` - Example Code
8 practical examples showing how to use the conversion tools.

**Included Examples:**
1. Basic XML to JSON conversion
2. Auto-detect XML type
3. Batch processing
4. Save to JSON files
5. Access converted data programmatically
6. Error handling
7. Baseline conversion
8. Building REST API payloads

**Run Examples:**
```bash
python3 xml_import_examples.py
```

## Detailed Guides

### [XML_TO_JSON_GUIDE.md](XML_TO_JSON_GUIDE.md)
Comprehensive guide covering:
- All 5 supported XML formats with examples
- Before/after conversion comparisons
- Complete workflow patterns
- Error handling and troubleshooting
- Performance notes
- Type conversion details

### [HYBRID_APPROACH_QUICK_REFERENCE.md](HYBRID_APPROACH_QUICK_REFERENCE.md)
REST API endpoint reference for the intelligent GCD generation system.

## Workflow Patterns

### Pattern 1: Standalone Conversion (Validation)
```bash
# Convert to JSON, save, inspect manually
python3 xml_to_json_converter.py input.xml -o output.json --pretty

# Verify output
cat output.json | python3 -m json.tool
```

### Pattern 2: Direct Import
```bash
# Automatic format detection and upload
python3 gcd_xml_import.py vem_calib.xml --token $TOKEN

# Check response
# HTTP 201 = Success, 400 = Format error, 401 = Auth error
```

### Pattern 3: Batch Import with Metadata
```bash
# Create run metadata first
curl -X POST http://localhost:8080/run-metadata \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "run_number": 123614,
    "config_name": "Stable",
    "start_time": "2014-01-01T00:00:00Z",
    "end_time": "2014-01-01T23:59:59Z"
  }'

# Import calibration data for that run
python3 gcd_xml_import.py vem_calib.xml --batch --token $TOKEN

# Generate GCD with intelligent filtering
curl -X POST http://localhost:8080/gcd/generate/123614 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "run_number": 123614,
    "include_types": ["VEM_Calibration", "Baseline", "Geometry"]
  }'
```

### Pattern 4: Python Integration
```python
from xml_to_json_converter import AutoDetectConverter
from gcd_xml_import import XMLImportPipeline

# Convert XML to JSON
xml_data = open('vem_calib.xml').read()
converted = AutoDetectConverter.convert(xml_data)

# Access converted data
metadata = converted['metadata']
records = converted['calibrations']

# Custom processing
for record in records:
    print(f"Processing {record['dom_id']}")
```

## Installation

```bash
# Verify Python 3.7+
python3 --version

# No external dependencies required
# Uses only Python standard library:
# - json
# - xml.etree.ElementTree
# - argparse
# - pathlib
# - glob
```

## Troubleshooting

**Error: "Unknown XML type"**
- XML root element not recognized
- Solution: Specify type explicitly with `--type` flag
- Supported types: VEMCalibOm, baselines, DOMCalibration, SPEFit, geometry

**Error: "Could not parse XML"**
- XML is malformed or not well-formed
- Solution: Validate XML with `xmllint input.xml`
- Check for missing closing tags, improper escaping

**Error: "Upload failed: 401"**
- Authentication failed (invalid token)
- Solution: Verify token with `echo $KEYCLOAK_TOKEN`
- Check token expiration

**Error: "Upload failed: 400"**
- Request payload format error
- Solution: Use `--convert-only` to validate JSON format
- Check API endpoint accepts this data type

**Performance: Processing large files**
- For files > 100MB, process in batches
- Use batch mode: `gcd_xml_import.py *.xml --batch`
- Or stream conversion and skip upload: `--convert-only`

## Reference

### Environment Variables

```bash
# Keycloak OAuth2 token (obtained from Keycloak server)
export KEYCLOAK_TOKEN="eyJhbGciOiJIUzI1NiIs..."

# API server URL
export API_URL="http://localhost:8080"
```

### Common Commands

```bash
# Get Keycloak token
curl -X POST https://keycloak.example.com/auth/realms/icecube/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=gcdserver-api" \
  -d "client_secret=your-secret" \
  | jq -r '.access_token'

# Save token to environment
export KEYCLOAK_TOKEN=$(curl -s ... | jq -r '.access_token')

# Verify token is set
echo "Token: ${KEYCLOAK_TOKEN:0:20}..."
```

### Next Steps

1. **Test Conversion**: Run `xml_import_examples.py` to see all examples
2. **Read Guide**: Review [XML_TO_JSON_GUIDE.md](XML_TO_JSON_GUIDE.md) for detailed information
3. **Convert Sample**: Use `xml_to_json_converter.py` on your XML files
4. **Validate Output**: Save as JSON, inspect format matches expectations
5. **Import Data**: Use `gcd_xml_import.py` to upload to REST API
6. **Verify**: Query REST API to confirm data was imported correctly

## Support

For detailed information about:
- XML format specifications: See [XML_TO_JSON_GUIDE.md](XML_TO_JSON_GUIDE.md)
- REST API endpoints: See [HYBRID_APPROACH_QUICK_REFERENCE.md](HYBRID_APPROACH_QUICK_REFERENCE.md)
- Integration patterns: See [xml_import_examples.py](xml_import_examples.py)
- Keycloak setup: See [KEYCLOAK_SETUP.md](../KEYCLOAK_SETUP.md)
