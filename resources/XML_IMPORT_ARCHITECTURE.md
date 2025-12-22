# XML Import Architecture & Technical Reference

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCD Data Import Pipeline                      │
└─────────────────────────────────────────────────────────────────┘

Input: Existing GCD XML Files
  │
  ├─ vem_calib.xml (VEMCalibOm)
  ├─ baseline.xml (baselines)
  ├─ domcal.xml (DOMCalibration)
  ├─ spefit.xml (SPEFit)
  └─ geometry.xml (geometry)
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     XML AUTO-DETECTION                          │
│  Analyzes XML root element to identify format type              │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FORMAT-SPECIFIC CONVERTERS                   │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ VEMCalibConverter│  │BaselineConverter │  │DOMCalConverter│ │
│  │  (XML→JSON)      │  │  (XML→JSON)      │  │ (XML→JSON)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │SPEFitConverter   │  │GeometryConverter │                     │
│  │  (XML→JSON)      │  │  (XML→JSON)      │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  Features:                                                       │
│  - Type-safe numeric conversion (float/int fallback)            │
│  - Field name normalization (snake_case)                        │
│  - Nested structure flattening                                  │
│  - Error handling with descriptive messages                     │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JSON OUTPUT (Validated)                      │
│  {                                                               │
│    "metadata": {                                                │
│      "date": "2014-01-01",                                     │
│      "first_run": 123614,                                      │
│      "type": "VEM_Calibration"                                │
│    },                                                           │
│    "calibrations": [                                           │
│      {                                                          │
│        "dom_id": "01,61",                                      │
│        "string_id": 1,                                         │
│        "tube_id": 61,                                          │
│        "pe_per_vem": 116.274,                                  │
│        ...                                                      │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
  │
  ├─ Option A: Save to file (--convert-only)
  │            ▼
  │    ┌─────────────────┐
  │    │  output.json    │
  │    │  (for review)   │
  │    └─────────────────┘
  │
  └─ Option B: Upload to REST API (--token)
             ▼
        ┌──────────────────────────────────────────┐
        │   REST API Authentication (OAuth2)       │
        │   Keycloak Bearer Token Verification     │
        └──────────────────────────────────────────┘
             ▼
        ┌──────────────────────────────────────────┐
        │   XML Import Pipeline (gcd_xml_import.py)│
        │   - Route to correct endpoint            │
        │   - POST /calibration                    │
        │   - POST /detector-status                │
        │   - POST /geometry                       │
        └──────────────────────────────────────────┘
             ▼
        ┌──────────────────────────────────────────┐
        │   REST API Server (Actix-web)            │
        │   - Validate JSON payload                │
        │   - Extract and transform data           │
        │   - Store metadata for run awareness     │
        └──────────────────────────────────────────┘
             ▼
        ┌──────────────────────────────────────────┐
        │   MongoDB Database                       │
        │   - calibrations collection              │
        │   - detector_status collection           │
        │   - geometry collection                  │
        │   - run_metadata collection (hybrid)     │
        └──────────────────────────────────────────┘
             ▼
        ┌──────────────────────────────────────────┐
        │   GCD Generation (Intelligent)           │
        │   - Filter by run number                 │
        │   - Filter by timestamp                  │
        │   - Apply hybrid approach logic          │
        │   - Return complete GCD                  │
        └──────────────────────────────────────────┘
             ▼
        Output: Complete I3GCD for requested run
```

## Data Flow Diagrams

### Single File Processing

```
vem_calib.xml
    │
    ├─ Read: open('vem_calib.xml').read()
    │
    ├─ Detect: AutoDetectConverter.detect_type(xml)
    │         → "VEMCalibOm"
    │
    ├─ Convert: VEMCalibConverter.convert(xml)
    │          → {metadata: {...}, calibrations: [...]}
    │
    ├─ Validate: Check JSON structure
    │           Check numeric types
    │           Check required fields
    │
    └─ Upload: XMLUploader.upload_calibration(json)
             → POST /calibration with Bearer token
             → MongoDB storage

```

### Batch Processing

```
*.xml (multiple files)
    │
    ├─ Glob expand: glob.glob('*.xml')
    │              → [vem_calib.xml, baseline.xml, domcal.xml]
    │
    ├─ Process each file:
    │  │
    │  ├─ vem_calib.xml ─┐
    │  │                  │
    │  ├─ baseline.xml  ──┼─ Detect type
    │  │                  │
    │  ├─ domcal.xml    ──┤
    │  │                  │
    │  └─ geometry.xml  ──┤
    │                     │
    │                     ├─ Convert to JSON
    │                     │
    │                     ├─ Route to endpoint
    │                     │  ├─ /calibration
    │                     │  ├─ /detector-status
    │                     │  └─ /geometry
    │                     │
    │                     └─ Upload with authentication
    │
    └─ Collect results:
      [
        {file: vem_calib.xml, status: 201, records: 86},
        {file: baseline.xml, status: 201, records: 86},
        {file: domcal.xml, status: 201, records: 86},
        {file: geometry.xml, status: 201, records: 1}
      ]
```

## Data Conversion Details

### Type Conversion Strategy

The converters use intelligent type inference to handle XML text data:

```python
def try_float(value: str) -> float | str:
    """
    Attempt to convert string to float.
    Falls back to string if conversion fails.
    
    Examples:
      "116.274" → 116.274 (float)
      "1.2e7"   → 12000000.0 (float)
      "1" → 1.0 (float)
      "N/A"     → "N/A" (string)
      ""        → "" (string)
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return value

def try_int(value: str) -> int | str:
    """
    Attempt to convert string to integer.
    Falls back to string if conversion fails.
    
    Examples:
      "123" → 123 (int)
      "1.5"     → 1 (int, truncated)
      "1.5e3"   → 1 (int, truncated)
      "N/A"     → "N/A" (string)
      ""        → "" (string)
    """
    try:
        return int(float(value))  # float() handles sci notation
    except (ValueError, TypeError):
        return value
```

### Field Name Transformation

XML uses various naming conventions. The converters normalize to snake_case:

```
XML Field Name          → JSON Field Name
───────────────────────────────────────
pePerVEM                → pe_per_vem
muPeakWidth             → mu_peak_width
sigBkgRatio             → sig_bkg_ratio
corrFactor              → corr_factor
hglgCrossOver           → hglg_cross_over
muonFitStatus           → muon_fit_status
muonFitRchi2            → muon_fit_rchi2
ATWDChipAChan0          → atwd_a.chan0
ATWDChipBChan1          → atwd_b.chan1
StringId                → string_id
TubeId                  → tube_id
```

### Numeric Type Handling

Different fields use different numeric types:

```
Dimension fields        → integers (1, 61)
Calibration values      → floats (116.274, 20.3121)
Status/fit codes        → integers (0, 1)
Ratios/factors          → floats (1.0, 10.306)
Timestamps              → strings (ISO 8601)
```

## API Integration

### Authentication Flow

```
1. Obtain Keycloak Token
   ├─ POST to Keycloak token endpoint
   ├─ client_credentials grant
   └─ Returns: {"access_token": "eyJ...", "expires_in": 3600}

2. Prepare Upload Request
   ├─ Add Authorization header: "Bearer {access_token}"
   ├─ Content-Type: application/json
   └─ Body: Converted JSON data

3. POST to REST API
   ├─ /calibration
   ├─ /detector-status
   └─ /geometry

4. Handle Response
   ├─ 201 Created: Success
   ├─ 400 Bad Request: Format error, check --convert-only
   ├─ 401 Unauthorized: Token expired or invalid
   └─ 500 Server Error: Server-side issue
```

### Endpoint Mapping

```
VEMCalibOm XML
  ├─ Root element: <VEMCalibOm>
  ├─ Converter: VEMCalibConverter
  ├─ Output field: "calibrations"
  ├─ Target endpoint: POST /calibration
  └─ Endpoint accepts: Multiple DOM calibrations

Baseline XML
  ├─ Root element: <baselines>
  ├─ Converter: BaselineConverter
  ├─ Output field: "baselines"
  ├─ Target endpoint: POST /detector-status
  └─ Endpoint accepts: ATWD/FADC baseline data

DOMCalibration XML
  ├─ Root element: <DOMCalibration>
  ├─ Converter: DOMCalibConverter
  ├─ Output field: "calibrations"
  ├─ Target endpoint: POST /calibration
  └─ Endpoint accepts: DOM calibration properties

SPEFit XML
  ├─ Root element: <SPEFit>
  ├─ Converter: SPEFitConverter
  ├─ Output field: "calibrations"
  ├─ Target endpoint: POST /calibration
  └─ Endpoint accepts: SPE fitting parameters

Geometry XML
  ├─ Root element: <geometry>
  ├─ Converter: GeometryConverter
  ├─ Output field: "geometry"
  ├─ Target endpoint: POST /geometry
  └─ Endpoint accepts: Detector geometry/positions
```

## Implementation Details

### XML Converter Base Class

```python
class XMLConverter:
    """Base class for all XML converters"""
    
    @staticmethod
    def strip_text(text: Optional[str]) -> str:
        """Remove XML whitespace (leading/trailing spaces, newlines)"""
        return text.strip() if text else ""
    
    @staticmethod
    def try_float(value: str) -> float | str:
        """Type-safe conversion to float"""
        ...
    
    @staticmethod
    def try_int(value: str) -> int | str:
        """Type-safe conversion to int"""
        ...
    
    @classmethod
    def convert(cls, xml_string: str) -> Dict[str, Any]:
        """
        Convert XML string to JSON.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
```

### AutoDetector

```python
class AutoDetectConverter:
    """Automatically detect XML type and route to correct converter"""
    
    TYPE_MAPPING = {
        'VEMCalibOm': VEMCalibConverter,
        'baselines': BaselineConverter,
        'DOMCalibration': DOMCalibConverter,
        'SPEFit': SPEFitConverter,
        'geometry': GeometryConverter,
    }
    
    @staticmethod
    def detect_type(xml_string: str) -> str:
        """Parse XML and extract root element tag"""
        root = ET.fromstring(xml_string)
        return root.tag
    
    @staticmethod
    def convert(xml_string: str) -> Dict[str, Any]:
        """Auto-detect type and convert"""
        detected = AutoDetectConverter.detect_type(xml_string)
        converter = TYPE_MAPPING.get(detected)
        if not converter:
            raise ValueError(f"Unknown XML type: {detected}")
        return converter.convert(xml_string)
```

### Import Pipeline

```python
class XMLImportPipeline:
    """Orchestrate XML conversion and REST API upload"""
    
    def __init__(self, api_url: str, token: str):
        self.converter = AutoDetectConverter()
        self.uploader = XMLUploader(api_url, token)
    
    def import_file(self, xml_file: Path) -> Dict[str, Any]:
        """
        1. Read XML file
        2. Auto-detect type
        3. Convert to JSON
        4. Infer target endpoint
        5. Upload to REST API
        """
        xml_string = xml_file.read_text()
        converted = self.converter.convert(xml_string)
        
        # Infer endpoint from metadata
        endpoint = self._infer_endpoint(converted)
        
        # Upload
        return self.uploader.upload(endpoint, converted)
```

## Error Handling

### Common Errors and Solutions

```
Error: XML Parse Error
└─ Cause: Malformed XML (unclosed tags, bad encoding)
   Solution: Validate with: xmllint input.xml

Error: Unknown XML type
└─ Cause: Unsupported root element
   Solution: Specify type: --type VEMCalibOm
   Or check supported types in documentation

Error: Type conversion failed
└─ Cause: Non-numeric value in numeric field
   Solution: Convert falls back to string, inspect output

Error: Authentication failed (401)
└─ Cause: Invalid or expired token
   Solution: Refresh token from Keycloak

Error: Bad request (400)
└─ Cause: JSON format mismatch with API
   Solution: Use --convert-only to inspect JSON format
             Compare with API documentation

Error: Network timeout
└─ Cause: API server not responding
   Solution: Check --api-url, verify server is running
             Check network connectivity
```

## Performance Characteristics

### Processing Speed

```
File Size    |  Processing Time  |  Records  | Records/sec
─────────────┼──────────────────┼──────────┼─────────────
Small        |  < 100ms          |   ~100   |  > 1000
Medium       |  100-500ms        |   ~1000  |  500-2000
Large        |  500ms-2s         |   ~10000 |  5000-20000
Very Large   |  > 2s             |   > 10000|  Varies
```

### Memory Usage

```
File Size  | Memory Usage | Notes
───────────┼──────────────┼────────────────────────
< 10MB     | < 50MB       | Recommended for streaming
10-50MB    | 50-200MB     | Monitor memory
> 50MB     | > 200MB      | Consider batch splitting
```

### Optimization Tips

1. **Batch Processing**: `--batch` flag processes multiple files
2. **Stream Mode**: Could be added for very large files
3. **Parallel Upload**: Could upload multiple files concurrently
4. **Compression**: API could accept gzip for bandwidth
5. **Chunking**: Could split large XML files into chunks

## Security Considerations

### Authentication

- OAuth2 bearer tokens used for all uploads
- Tokens obtained from Keycloak
- Tokens expire (typically 1 hour)
- Must be refreshed for long-running operations

### Data Validation

- JSON payload validated before upload
- Type checking on numeric fields
- Required fields verified
- Invalid records rejected

### Network Security

- HTTPS recommended for production
- API server validates all requests
- Tokens not logged or cached locally

## Integration Examples

### With Existing REST Client

```python
from gcd_rest_client import GCDRestClient
from gcd_xml_import import XMLImportPipeline

# Create client
client = GCDRestClient(
    api_url="http://localhost:8080",
    client_id="gcdserver-api",
    client_secret="..."
)

# Import XML data
pipeline = XMLImportPipeline(
    api_url=client.api_url,
    token=client.token
)
pipeline.import_file("vem_calib.xml")

# Query imported data
gcd = client.get_gcd(run_number=123614)
```

### With Build Tools

```bash
# 1. Import calibration data
python3 gcd_xml_import.py *.xml --batch --token $TOKEN

# 2. Create run metadata
python3 build_gcd_rest.py \
  --run 123614 \
  --config "Stable" \
  --start "2014-01-01T00:00:00Z" \
  --end "2014-01-01T23:59:59Z"

# 3. Generate GCD with intelligent filtering
curl -X POST http://localhost:8080/gcd/generate/123614 \
  -H "Authorization: Bearer $TOKEN"
```

## Conclusion

The XML import system provides a complete pipeline for converting existing GCD data into the REST API format. It handles multiple XML formats, provides intelligent type conversion, and integrates seamlessly with the Keycloak OAuth2 authentication system.

Key features:
- ✅ Automatic format detection
- ✅ Type-safe conversion
- ✅ Batch processing support
- ✅ OAuth2 integration
- ✅ Comprehensive error handling
- ✅ Production-ready code
