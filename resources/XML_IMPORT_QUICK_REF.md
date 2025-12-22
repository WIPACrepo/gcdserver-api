# XML Import Quick Reference

**Status**: ✅ Production Ready | **Languages**: Python 3.7+ | **Dependencies**: None (stdlib only)

## One-Minute Quick Start

```bash
# 1. Convert XML to JSON (validate format)
python3 xml_to_json_converter.py input.xml -o output.json --pretty

# 2. Get authentication token
export TOKEN=$(curl -s https://keycloak.example.com/auth/realms/icecube/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=gcdserver-api" \
  -d "client_secret=your-secret" | jq -r '.access_token')

# 3. Import to REST API
python3 gcd_xml_import.py input.xml --token $TOKEN

# Done! Data is now in MongoDB, ready for GCD generation
```

## Tool Reference

### xml_to_json_converter.py
**Convert XML files to JSON format**

```bash
# Basic usage
python3 xml_to_json_converter.py input.xml [-o output.json]

# Options
  -o, --output FILE      Save to file (default: stdout)
  --type TYPE            Specify format: VEMCalibOm, baselines, DOMCalibration, SPEFit, geometry
  --pretty               Pretty-print JSON output
  -h, --help             Show help message

# Examples
python3 xml_to_json_converter.py vem_calib.xml -o output.json
python3 xml_to_json_converter.py input.xml --pretty | less
cat input.xml | python3 xml_to_json_converter.py -o output.json
```

### gcd_xml_import.py
**Convert and import XML to REST API**

```bash
# Basic usage
python3 gcd_xml_import.py FILE [OPTIONS]

# Options
  --token TOKEN          Keycloak OAuth2 bearer token (required for upload)
  --api-url URL          REST API base URL (default: http://localhost:8080)
  --convert-only         Convert to JSON without uploading
  -o, --output FILE      Save JSON to file
  --batch                Process multiple files (supports wildcards)
  --endpoint ENDPOINT    Force specific endpoint
  --pretty               Pretty-print JSON output
  -h, --help             Show help message

# Examples
python3 gcd_xml_import.py vem_calib.xml --token $TOKEN
python3 gcd_xml_import.py *.xml --batch --token $TOKEN
python3 gcd_xml_import.py input.xml --convert-only -o output.json
python3 gcd_xml_import.py input.xml --token $TOKEN --api-url https://api.example.com
```

## Supported XML Formats

| Format | Root Element | Example File |
|--------|-------------|--------------|
| VEM Calibration | `<VEMCalibOm>` | vem_calib.xml |
| ATWD/FADC Baseline | `<baselines>` | baseline.xml |
| DOM Calibration | `<DOMCalibration>` | domcal.xml |
| SPE Fit | `<SPEFit>` | spefit.xml |
| Geometry | `<geometry>` | geometry.xml |

## Common Commands

### Single File Conversion
```bash
# Standalone conversion (no API needed)
python3 xml_to_json_converter.py input.xml -o output.json --pretty

# Review JSON
cat output.json
```

### Single File Import
```bash
# Convert and upload in one command
python3 gcd_xml_import.py input.xml --token $TOKEN

# Success: Returns JSON with upload status
# Check curl response: HTTP 201 = Success
```

### Batch Import
```bash
# Import all XML files in current directory
python3 gcd_xml_import.py *.xml --batch --token $TOKEN

# Result: Multiple files processed, results reported
```

### Validation Before Import
```bash
# Convert and save (don't upload)
python3 gcd_xml_import.py input.xml --convert-only -o output.json

# Inspect output
cat output.json | python3 -m json.tool | head -50

# If format looks good, upload
python3 gcd_xml_import.py output.json --token $TOKEN
```

### Using with REST API Client
```bash
# Get token using rest client
TOKEN=$(python3 -c "from gcd_rest_client import GCDRestClient; \
  c = GCDRestClient(); print(c.token)")

# Import XML
python3 gcd_xml_import.py *.xml --batch --token $TOKEN

# Query imported data
python3 build_gcd_rest.py --run 123614 --token $TOKEN
```

## Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Unknown XML type` | Unsupported root element | Use `--type` flag or check format |
| `Could not parse XML` | Malformed XML | Validate with `xmllint input.xml` |
| `Upload failed: 401` | Invalid token | Refresh token from Keycloak |
| `Upload failed: 400` | JSON format mismatch | Use `--convert-only` to inspect |
| `Connection refused` | API not running | Check API URL and server status |

## Authentication

### Get Keycloak Token
```bash
# Using curl
TOKEN=$(curl -s https://keycloak.example.com/auth/realms/icecube/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=gcdserver-api" \
  -d "client_secret=your-secret" | jq -r '.access_token')

# Using gcd_rest_client.py
TOKEN=$(python3 -c "from gcd_rest_client import GCDRestClient; print(GCDRestClient().token)")

# Save to environment
export KEYCLOAK_TOKEN=$TOKEN
```

### Token Expiration
- Tokens expire after ~1 hour
- Refresh before running long operations
- Check expiration: `echo $KEYCLOAK_TOKEN | jq -R 'split(".")[1] | @base64d' | jq`

## Workflow Patterns

### Pattern A: Validate Before Import
```bash
# 1. Convert without uploading
python3 xml_to_json_converter.py input.xml -o output.json --pretty

# 2. Inspect JSON (number of records, structure)
cat output.json | head -100

# 3. If satisfied, import via API
python3 gcd_xml_import.py input.xml --token $TOKEN
```

### Pattern B: Batch Import with Metadata
```bash
# 1. Create run metadata
curl -X POST http://localhost:8080/run-metadata \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"run_number": 123614, "config_name": "Stable", ...}'

# 2. Import all calibrations for that run
python3 gcd_xml_import.py *.xml --batch --token $TOKEN

# 3. Generate GCD with intelligent filtering
curl -X POST http://localhost:8080/gcd/generate/123614 \
  -H "Authorization: Bearer $TOKEN"
```

### Pattern C: Python Integration
```python
from xml_to_json_converter import AutoDetectConverter
from pathlib import Path

# Convert
xml = Path('input.xml').read_text()
data = AutoDetectConverter.convert(xml)

# Process
for record in data['calibrations']:
    print(f"DOM {record['dom_id']}: {record['pe_per_vem']}")

# Upload (if needed)
# ... use gcd_xml_import.XMLUploader
```

## Performance Tips

### For Large Files
```bash
# Convert without pretty-printing (faster)
python3 xml_to_json_converter.py huge.xml -o output.json

# Batch multiple files
python3 gcd_xml_import.py file1.xml file2.xml file3.xml --batch --token $TOKEN
```

### For Testing
```bash
# Small test conversion
python3 xml_to_json_converter.py test.xml --pretty | head -100

# Convert-only mode (no network I/O)
python3 gcd_xml_import.py input.xml --convert-only -o test.json
```

## File Locations

```
gcdserver_rust_api/
└── resources/
    ├── xml_to_json_converter.py         # XML to JSON tool
    ├── gcd_xml_import.py                # XML to REST API tool
    ├── xml_import_examples.py           # 8 practical examples
    ├── gcd_rest_client.py               # Python REST client
    ├── build_gcd_rest.py                # GCD builder CLI
    ├── XML_IMPORT_INDEX.md              # Main guide (START HERE)
    ├── XML_TO_JSON_GUIDE.md             # Detailed format guide
    ├── XML_IMPORT_ARCHITECTURE.md       # Technical reference
    └── XML_IMPORT_DELIVERY.md           # Delivery summary
```

## Documentation Links

| Document | Contents |
|----------|----------|
| [XML_IMPORT_INDEX.md](XML_IMPORT_INDEX.md) | **START HERE** - Complete overview |
| [XML_TO_JSON_GUIDE.md](XML_TO_JSON_GUIDE.md) | Detailed format specifications |
| [XML_IMPORT_ARCHITECTURE.md](XML_IMPORT_ARCHITECTURE.md) | Technical architecture & internals |
| [xml_import_examples.py](xml_import_examples.py) | 8 working code examples |
| [KEYCLOAK_SETUP.md](../KEYCLOAK_SETUP.md) | OAuth2 authentication setup |

## Testing

```bash
# Run example scripts to test tools
python3 xml_import_examples.py

# Expected output:
# ✓ 8 examples run successfully
# ✓ Basic conversion works
# ✓ Auto-detection works
# ✓ Error handling works
# ✓ Data access works
```

## Environment Setup

```bash
# Verify Python version
python3 --version      # Need 3.7+

# Verify tools are accessible
ls -la xml_to_json_converter.py gcd_xml_import.py

# Set up authentication
export KEYCLOAK_TOKEN="your-token-here"
export API_URL="http://localhost:8080"

# Test connection
curl $API_URL/health -H "Authorization: Bearer $KEYCLOAK_TOKEN"
```

## Keyboard Shortcuts / Aliases

```bash
# Create convenient aliases
alias xml2json='python3 xml_to_json_converter.py'
alias xml-import='python3 gcd_xml_import.py'

# Or create wrapper scripts
cat > ~/bin/xml-convert.sh << 'EOF'
#!/bin/bash
python3 /path/to/xml_to_json_converter.py "$@"
EOF
chmod +x ~/bin/xml-convert.sh
```

## Troubleshooting Checklist

- [ ] Python 3.7+ installed: `python3 --version`
- [ ] Files in resources/ directory: `ls resources/xml*.py`
- [ ] Keycloak token obtained: `echo $KEYCLOAK_TOKEN`
- [ ] Token not expired: Check with jq (see Authentication section)
- [ ] API server running: `curl http://localhost:8080/health`
- [ ] XML file readable: `xmllint input.xml`
- [ ] JSON format valid: `python3 xml_to_json_converter.py input.xml --pretty | python3 -m json.tool`

## Quick Help

```bash
# Show tool help
python3 xml_to_json_converter.py --help
python3 gcd_xml_import.py --help

# Run examples
python3 xml_import_examples.py

# Read main guide
less XML_IMPORT_INDEX.md
```

---

**Last Updated**: 2024 | **Status**: ✅ Production Ready | **Support**: See documentation files
