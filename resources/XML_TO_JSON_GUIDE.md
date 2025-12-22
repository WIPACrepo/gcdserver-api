# XML to JSON Conversion Guide

## Overview

The GCD system uses multiple XML formats for configuration and calibration data. To integrate with the REST API, you need to convert these XML formats to JSON. This guide provides tools and examples for doing so.

## Supported XML Formats

### 1. VEMCalibOm (VEM Calibration)
**Source**: VEM (Veto Energy Measurement) calibration data  
**Format**: DOM-level calibration parameters

```xml
<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 00:39:07 </Date>
  <FirstRun> 123614 </FirstRun>
  <LastRun> 123968 </LastRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
    <muPeakWidth> 20.3121 </muPeakWidth>
    <sigBkgRatio> 10.306 </sigBkgRatio>
    <corrFactor> 1 </corrFactor>
    <hglgCrossOver> 2361.66 </hglgCrossOver>
    <muonFitStatus> 0 </muonFitStatus>
    <muonFitRchi2> 1.42718 </muonFitRchi2>
    <hglgFitStatus> 0 </hglgFitStatus>
    <hglgFitRchi2> 2.44815 </hglgFitRchi2>
  </DOM>
</VEMCalibOm>
```

**Converted JSON**:
```json
{
  "metadata": {
    "date": "2014-01-01 00:39:07",
    "first_run": 123614,
    "last_run": 123968,
    "type": "VEM_Calibration"
  },
  "calibrations": [
    {
      "dom_id": "01,61",
      "string_id": 1,
      "tube_id": 61,
      "pe_per_vem": 116.274,
      "mu_peak_width": 20.3121,
      "sig_bkg_ratio": 10.306,
      "corr_factor": 1.0,
      "hglg_crossover": 2361.66,
      "muon_fit_status": 0,
      "muon_fit_rchi2": 1.42718,
      "hglg_fit_status": 0,
      "hglg_fit_rchi2": 2.44815
    }
  ]
}
```

**REST API Endpoint**: `/calibration`  
**HTTP Method**: `POST` (once per DOM)

### 2. Baseline (ATWD/FADC Baselines)
**Source**: Electronic baseline measurements  
**Format**: Per-DOM ATWD and FADC baseline values

```xml
<?xml version="1.0" ?>
<baselines>
    <date>2016-03-18</date>
    <time>16:33:41</time>
    <dom StringId="1" TubeId="61">
        <ATWDChipAChan0>125.068580</ATWDChipAChan0>
        <ATWDChipAChan1>136.172671</ATWDChipAChan1>
        <ATWDChipAChan2>136.172799</ATWDChipAChan2>
        <ATWDChipBChan0>129.730441</ATWDChipBChan0>
        <ATWDChipBChan1>134.035253</ATWDChipBChan1>
        <ATWDChipBChan2>136.943712</ATWDChipBChan2>
        <FADC>137.185200</FADC>
    </dom>
</baselines>
```

**Converted JSON**:
```json
{
  "metadata": {
    "date": "2016-03-18",
    "time": "16:33:41",
    "timestamp": "2016-03-18 16:33:41",
    "type": "Baseline"
  },
  "baselines": [
    {
      "dom_id": "01,61",
      "string_id": 1,
      "tube_id": 61,
      "atwd_a": {
        "chan0": 125.068580,
        "chan1": 136.172671,
        "chan2": 136.172799
      },
      "atwd_b": {
        "chan0": 129.730441,
        "chan1": 134.035253,
        "chan2": 136.943712
      },
      "fadc": 137.185200
    }
  ]
}
```

**REST API Endpoint**: `/detector-status`  
**HTTP Method**: `POST` (once per DOM, requires run_number)

### 3. DOMCal (DOM Calibration Properties)
**Source**: DOM-level calibration including gains and frequencies  
**Format**: Digitizer calibration parameters per DOM

### 4. SPEFit (Single Photon Event Fitting)
**Source**: Fitted single photon event parameters  
**Format**: Chi-squared and fitting status per digitizer

### 5. Geometry
**Source**: Detector geometry (positions and orientations)  
**Format**: DOM positions, antenna angles, tank positions

## Tools Provided

### 1. `xml_to_json_converter.py` - Standalone Converter

Convert XML files to JSON independently (no upload).

**Installation**:
```bash
# No additional dependencies beyond standard library
python3 xml_to_json_converter.py --help
```

**Basic Usage**:
```bash
# Auto-detect type and print JSON
python3 xml_to_json_converter.py vem_calib.xml

# Specify type explicitly
python3 xml_to_json_converter.py vem_calib.xml --type vemcalibom

# Save to file
python3 xml_to_json_converter.py vem_calib.xml -o vem_calib.json

# Pretty-print
python3 xml_to_json_converter.py vem_calib.xml --pretty
```

**Command-line Options**:
```
-t, --type {vemcalibom,baseline,domcal,spefit,geometry}
    XML type (auto-detected if not specified)

-o, --output OUTPUT
    Output JSON file (default: stdout)

-p, --pretty
    Pretty-print JSON output
```

**Examples**:
```bash
# Convert baseline data and save
python3 xml_to_json_converter.py baseline.xml --type baseline -o baseline.json --pretty

# Auto-detect and print
python3 xml_to_json_converter.py unknown_format.xml

# Batch convert multiple files
for file in *.xml; do
  python3 xml_to_json_converter.py "$file" -o "${file%.xml}.json"
done
```

### 2. `gcd_xml_import.py` - Full Import Pipeline

Convert XML files and upload directly to REST API.

**Installation**:
```bash
pip install requests
```

**Basic Usage**:
```bash
# Upload VEM calibration
python3 gcd_xml_import.py vem_calib.xml \
  --api-url http://localhost:8080 \
  --token YOUR_OAUTH_TOKEN

# Convert only (no upload)
python3 gcd_xml_import.py vem_calib.xml --convert-only -o vem_calib.json

# Batch upload multiple files
python3 gcd_xml_import.py *.xml \
  --batch \
  --api-url http://localhost:8080 \
  --token YOUR_OAUTH_TOKEN
```

**Command-line Options**:
```
files                   Input XML file(s) to import (supports glob)
--api-url URL          GCDServer API URL (default: http://localhost:8080)
--token TOKEN          OAuth2 bearer token (required for upload)
-t, --type TYPE        XML type (auto-detected if not specified)
-e, --endpoint TARGET  Target endpoint (auto-detected if not specified)
-r, --run NUMBER       Run number (required for detector-status)
--convert-only         Convert to JSON without uploading
-o, --output FILE      Output JSON file (with --convert-only)
--batch                Process multiple files in batch
-p, --pretty           Pretty-print JSON output
```

**Examples**:
```bash
# Upload baseline data as detector status
python3 gcd_xml_import.py baseline.xml \
  --endpoint detector-status \
  --run 137292 \
  --token $TOKEN

# Convert and save without uploading
python3 gcd_xml_import.py vem_calib.xml --convert-only -o vem_calib.json

# Batch import all XML files
python3 gcd_xml_import.py *.xml --batch --token $TOKEN

# Upload with auto-type detection
python3 gcd_xml_import.py *.xml --batch --token $TOKEN
```

## Usage Workflows

### Workflow 1: Convert XML to JSON for Manual REST API Calls

```bash
# 1. Convert XML to JSON
python3 xml_to_json_converter.py vem_calib.xml -o vem_calib.json --pretty

# 2. Inspect the JSON
cat vem_calib.json | head -50

# 3. Use with curl to POST to API
curl -X POST http://localhost:8080/calibration \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @vem_calib.json
```

### Workflow 2: Automated Batch Import

```bash
# 1. Get OAuth2 token
TOKEN=$(python3 gcd_rest_client.py --get-token)

# 2. Batch import all XML files
python3 gcd_xml_import.py *.xml \
  --batch \
  --api-url http://localhost:8080 \
  --token $TOKEN

# 3. Verify in logs
```

### Workflow 3: Import with Run Metadata

```bash
# 1. Create run metadata
python3 gcd_xml_import.py baseline.xml \
  --convert-only -o run_metadata.json

# 2. Manually create run metadata entry
curl -X POST http://localhost:8080/run-metadata \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "run_number": 137292,
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T12:30:00Z",
    "configuration_name": "IC86_2023"
  }'

# 3. Import detector status with run context
python3 gcd_xml_import.py baseline.xml \
  --endpoint detector-status \
  --run 137292 \
  --token $TOKEN
```

### Workflow 4: Integration with Python Scripts

```python
from gcd_xml_import import XMLImportPipeline
from pathlib import Path

# Initialize pipeline
pipeline = XMLImportPipeline(
    api_url="http://localhost:8080",
    token="YOUR_OAUTH_TOKEN"
)

# Import single file
result = pipeline.import_file(
    Path("vem_calib.xml"),
    xml_type="vemcalibom",
    endpoint="calibration"
)

if result['success']:
    print(f"Imported {result['file']} successfully")
else:
    print(f"Error: {result['error']}")

# Batch import
for xml_file in Path('.').glob('*.xml'):
    result = pipeline.import_file(xml_file)
    print(f"{'✓' if result['success'] else '✗'} {xml_file}")
```

## Error Handling

### Common Issues

**1. Authentication Error (401)**
```
Error: Invalid token
Solution: Verify OAuth2 token is valid and not expired
```

**2. Auto-detection Failed**
```
Error: Could not auto-detect XML type
Solution: Explicitly specify --type with known format
```

**3. XML Parse Error**
```
Error: XML parsing failed
Solution: Verify XML file is well-formed (validate with xmllint)
```

**4. Missing Required Fields**
```
Error: Missing StringId or TubeId
Solution: Ensure all required elements are present in XML
```

### Validation

```bash
# Validate XML before conversion
xmllint --noout vem_calib.xml

# Validate JSON output
python3 -m json.tool vem_calib.json > /dev/null

# Check for required fields
python3 -c "import json; data = json.load(open('vem_calib.json')); print(f\"Found {len(data.get('calibrations', []))} calibrations\")"
```

## Type Conversion Details

### Numeric Types
- **Floats**: ATWD gains, FADC gains, positions, etc.
- **Integers**: String ID, Tube ID, Run numbers, status codes

```python
# Automatic conversion:
125.068580 → 125.06858 (float)
1          → 1 (int)
0          → 0 (int, not bool)
```

### DOM ID Format
- **Storage**: "01,61" format (string)
- **Extraction**: StringId and TubeId as separate fields
- **Usage**: Can query by either format

```python
# Both formats available:
"dom_id": "01,61"           # String format
"string_id": 1, "tube_id": 61  # Separate fields
```

### Timestamps
- **Format**: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- **Storage**: Separate date/time or combined
- **Example**: "2016-03-18T16:33:41Z"

## Python API Usage

### Direct Use

```python
from xml_to_json_converter import AutoDetectConverter, VEMCalibConverter

# Auto-detect and convert
xml_string = open('vem_calib.xml').read()
result = AutoDetectConverter.convert(xml_string)
print(result['metadata'])
print(len(result['calibrations']))

# Direct converter
result = VEMCalibConverter.convert(xml_string)
```

### With REST Client

```python
from gcd_rest_client import GCDRestClient, GCDAPIConfig
from gcd_xml_import import XMLImportPipeline
import json

config = GCDAPIConfig(...)
client = GCDRestClient(config)
pipeline = XMLImportPipeline(client.config.api_url, client.token)

# Import and use
result = pipeline.import_file(Path("vem_calib.xml"))
if result['success']:
    # Generate GCD collection
    gcd = client.session.post(
        f"{client.config.api_url}/gcd/generate/137292"
    ).json()
```

## Performance Notes

- **Conversion Speed**: ~10-100ms per file (depending on size)
- **Upload Speed**: ~100-500ms per payload (depending on network)
- **Memory Usage**: Minimal (all processing in-memory)
- **Batch Limits**: No hard limits, recommend batching 100+ files

## Troubleshooting

### Debug Conversion

```bash
# Enable verbose output
python3 xml_to_json_converter.py vem_calib.xml --pretty | head -100

# Count records
python3 -c "import json; d=json.load(open('vem_calib.json')); print(len(d.get('calibrations', [])))"

# Validate schema
python3 -c "import xml.etree.ElementTree as ET; ET.parse('vem_calib.xml')"
```

### Debug Upload

```bash
# Test connectivity
curl -I http://localhost:8080/health

# Test authentication
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/run-metadata

# Test with sample data
echo '{"string_id": 1, "tube_id": 61}' | curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- http://localhost:8080/calibration
```

## Next Steps

1. **Test Conversion**: Run `xml_to_json_converter.py` on sample files
2. **Verify Format**: Inspect JSON output matches schema
3. **Authenticate**: Obtain OAuth2 token from Keycloak
4. **Batch Import**: Use `gcd_xml_import.py` for production import
5. **Generate GCD**: Use `/gcd/generate/{run}` to create collections

## See Also

- [REST API Reference](HYBRID_APPROACH_QUICK_REFERENCE.md)
- [Python Client Library](gcd_rest_client.py)
- [GCD Import Guide](README_GCD_TOOLS.md)
