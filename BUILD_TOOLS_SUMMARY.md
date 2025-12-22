# GCD REST API Build Tools - Summary

## Overview

Three new Python tools have been created to replace the original `BuildGCD.py` workflow, enabling GCD file generation through the Rust REST API instead of direct MongoDB access.

## New Files

### 1. `resources/build_gcd_rest.py`
**Purpose:** Command-line tool for building GCD files  
**Language:** Python 3  
**Dependencies:** requests library

**Usage:**
```bash
python resources/build_gcd_rest.py -r 137292 -o gcd.json --api-url http://localhost:8080 --token YOUR_TOKEN
```

**Features:**
- Simple command-line interface
- Generates complete GCD collection for a run
- Outputs JSON file with all components
- Health check and token verification
- Progress logging

### 2. `resources/gcd_rest_client.py`
**Purpose:** Full-featured Python client library  
**Language:** Python 3  
**Dependencies:** requests library

**Key Classes:**
- `GCDAPIConfig` - Configuration container
- `GCDRestClient` - Main API client with all CRUD operations
- `GCDBuilder` - High-level GCD builder
- `APIError` - Custom exception class

**Features:**
- Complete REST API wrapper
- CRUD operations for all endpoints
- Session management
- Comprehensive error handling
- Logging support
- Type hints for IDE support

**Usage:**
```python
from resources.gcd_rest_client import GCDRestClient, GCDAPIConfig

config = GCDAPIConfig(
    api_url="http://localhost:8080",
    bearer_token="your-token"
)
client = GCDRestClient(config)

# Access all API endpoints
calibrations = client.get_calibrations()
geometry = client.get_geometry()
gcd = client.generate_gcd_collection(137292)
```

### 3. `resources/gcd_build_examples.py`
**Purpose:** Comprehensive usage examples  
**Language:** Python 3  

**Examples Included:**
1. Basic GCD generation
2. Save GCD to file
3. Get GCD summary
4. Access GCD components
5. Run-specific data (snow height, configuration)
6. Batch operations
7. Error handling patterns
8. Retrieve previous collections

## Key Differences from Original BuildGCD.py

### Original Approach
```python
# Direct MongoDB access
from icecube.gcdserver.MongoDB import getDB
db = getDB(host, user, password)
buildGCD(db, i3livehost, run_number, output_file)
```

### REST API Approach
```python
# HTTP API access
from resources.gcd_rest_client import GCDRestClient, GCDBuilder, GCDAPIConfig

config = GCDAPIConfig(api_url="http://localhost:8080", bearer_token=token)
client = GCDRestClient(config)
builder = GCDBuilder(client)
builder.build_and_save(run_number, output_file)
```

## Advantages

| Aspect | REST API |
|--------|----------|
| **Authentication** | Modern OAuth2/Keycloak |
| **Network** | Works over HTTP, supports remote servers |
| **Dependencies** | Minimal (just requests library) |
| **Containerization** | Native support for Docker/K8s |
| **CI/CD** | Integrates easily with pipelines |
| **Load Balancing** | Multiple API servers supported |
| **Scalability** | Distributed architecture ready |
| **Auditability** | Full request/response logging |

## Installation & Setup

### Prerequisites
```bash
pip install requests
```

### Environment Setup
```bash
# Set API token
export GCD_API_TOKEN="your-keycloak-token"

# Or pass via command-line
python resources/build_gcd_rest.py -r 137292 -o gcd.json --token YOUR_TOKEN
```

### Running the Tools

**Command-line (simplest):**
```bash
python resources/build_gcd_rest.py -r 137292 -o gcd.json
```

**Python API (programmatic):**
```python
from resources.gcd_rest_client import GCDBuilder, GCDRestClient, GCDAPIConfig

config = GCDAPIConfig(api_url="http://localhost:8080", bearer_token="token")
client = GCDRestClient(config)
builder = GCDBuilder(client)
builder.build_and_save(137292, "gcd.json")
```

**With examples:**
```bash
python resources/gcd_build_examples.py
# (Uncomment examples in main section)
```

## Output Format

The generated GCD file is a JSON document containing:

```json
{
  "run_number": 137292,
  "generated_at": "2025-12-21T10:30:00Z",
  "generated_by": "user@example.com",
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "calibrations": [
    {
      "id": {...},
      "dom_id": 161,
      "domcal": {...},
      "timestamp": "..."
    }
  ],
  "geometry": [
    {
      "string": 1,
      "position": 61,
      "location": {"x": 10.0, "y": 20.0, "z": -500.0}
    }
  ],
  "detector_status": [
    {
      "dom_id": 161,
      "status": "operational",
      "is_bad": false
    }
  ]
}
```

## Error Handling

All tools include comprehensive error handling:

```python
from resources.gcd_rest_client import GCDRestClient, APIError, GCDAPIConfig

try:
    config = GCDAPIConfig(api_url="http://localhost:8080", bearer_token=token)
    client = GCDRestClient(config)
    
    # Check health
    if not client.health_check():
        print("API server is not responding")
        exit(1)
    
    # Check token
    if not client.verify_token():
        print("Authentication token is invalid")
        exit(1)
    
    # Generate GCD
    gcd = client.generate_gcd_collection(137292)
    
except APIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Integration Points

### CI/CD Pipelines
```yaml
# Example: Generate GCD before running analysis
stages:
  - build_gcd:
      script: |
        python resources/build_gcd_rest.py -r $RUN_NUMBER -o gcd.json
        # Use gcd.json in downstream tasks
```

### Docker/Kubernetes
```dockerfile
# Dockerfile
RUN pip install requests
COPY resources/ /app/resources/
ENTRYPOINT ["python", "resources/build_gcd_rest.py"]
```

### Web Services
```python
# Flask/FastAPI integration
@app.route('/api/gcd/<int:run_number>')
def get_gcd(run_number):
    config = GCDAPIConfig(api_url=GCD_API_URL, bearer_token=token)
    client = GCDRestClient(config)
    return client.generate_gcd_collection(run_number)
```

## Testing

Included test data in `tests/test_data.rs`:
- Baseline calibration data (DOM 1-61, 1-62)
- VEM calibration data
- SPE calibration data
- Geometry entries
- Detector status data
- Snow height records

Run tests:
```bash
cargo test --test test_data
```

## Documentation

- **Implementation Details:** See docstrings in `gcd_rest_client.py`
- **Command-line Help:** `python resources/build_gcd_rest.py --help`
- **Usage Examples:** `resources/gcd_build_examples.py`
- **API Reference:** Main `README.md`

## Next Steps

1. Replace old BuildGCD.py usage with new tools
2. Update CI/CD pipelines to use `build_gcd_rest.py`
3. Migrate existing scripts to use `gcd_rest_client.py`
4. Add unit tests for build workflow
5. Set up monitoring for GCD generation jobs
