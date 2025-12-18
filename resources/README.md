# GCDServer API Python Client

A comprehensive Python client library for interacting with the GCDServer REST API. This replaces direct MongoDB database calls with secure, authenticated REST API calls.

## Overview

This client library provides a Pythonic interface to perform all CRUD operations on GCDServer data (Calibrations, Geometry, Detector Status, and Configuration) through the REST API rather than direct database access.

## Files

- **`gcdserver_api_client.py`** - Main client library with all API operations
- **`examples.py`** - Comprehensive examples demonstrating usage
- **`README.md`** - This file

## Installation

### Prerequisites

- Python 3.7+
- `requests` library

### Setup

```bash
# Install dependencies
pip install requests

# Or with poetry
poetry add requests
```

## Quick Start

### 1. Basic Usage

```python
from gcdserver_api_client import GCDServerClient, DOMCal

# Initialize client
client = GCDServerClient(base_url="http://localhost:8080")

# Get authentication token (see Authentication section below)
token = "your-oauth2-token"

# Get all calibrations
calibrations = client.get_calibrations(token)

# Get specific calibration
cal = client.get_calibration(token, dom_id=12345)

# Create new calibration
domcal = DOMCal(
    atwd_gain=[1.0, 1.1, 1.2, 1.3],
    atwd_freq=[50.0, 50.1, 50.2, 50.3],
    fadc_gain=1.0,
    fadc_freq=50.0,
    pmt_gain=1.0,
    transit_time=1.0,
    relative_pmt_gain=1.0
)
new_cal = client.create_calibration(token, dom_id=12345, domcal=domcal)
```

### 2. Running Examples

```bash
# Run all examples (requires GCDSERVER_TOKEN environment variable for authenticated operations)
export GCDSERVER_TOKEN="your-access-token"
python examples.py

# Or with custom API URL
export GCDSERVER_API_URL="http://api.example.com"
export GCDSERVER_TOKEN="your-access-token"
python examples.py
```

## Authentication

The API uses OAuth2 with JWT tokens. You need a valid access token to make authenticated requests.

### Getting a Token

The typical OAuth2 flow:

```python
client = GCDServerClient()

# Step 1: Initiate login
login_response = client.login()
authorization_url = login_response['authorization_url']

# Step 2: Redirect user to authorization_url
# User logs in and authorizes access
# Provider redirects back to callback endpoint with authorization code

# Step 3: Exchange code for token (typically handled by callback endpoint)
# The /auth/callback endpoint returns the access token
```

For a local Keycloak setup, see the [OAUTH2_GUIDE.md](../gcdserver_rust_api/OAUTH2_GUIDE.md).

### Using the Token

Once you have an access token:

```python
client = GCDServerClient()

# Verify token is valid
verification = client.verify_token(token)
print(f"Valid: {verification['valid']}")
print(f"User: {verification['email']}")
print(f"Scopes: {verification['scopes']}")

# Use token for all operations
calibrations = client.get_calibrations(token)

# Refresh token if needed
new_token = client.refresh_token(token)

# Logout when done
client.logout(token)
```

## API Operations

### Calibration Operations

```python
# Get all calibrations
calibrations = client.get_calibrations(token)

# Get calibration for specific DOM
cal = client.get_calibration(token, dom_id=12345)

# Get latest calibration for DOM
latest = client.get_latest_calibration(token, dom_id=12345)

# Create calibration
domcal = DOMCal(...)
new_cal = client.create_calibration(token, dom_id=12345, domcal=domcal)

# Update calibration
updated_cal = client.update_calibration(token, dom_id=12345, domcal=updated_domcal)

# Delete calibration
success = client.delete_calibration(token, dom_id=12345)
```

### Geometry Operations

```python
# Get all geometries
geometries = client.get_geometries(token)

# Get geometry for specific location
geom = client.get_geometry(token, string=34, position=50)

# Get all geometry for a string
string_geoms = client.get_string_geometry(token, string=34)

# Create geometry
location = GeoLocation(x=100.0, y=200.0, z=300.0)
new_geom = client.create_geometry(token, string=34, position=50, location=location)

# Update geometry
updated_geom = client.update_geometry(token, string=34, position=50, location=updated_location)

# Delete geometry
success = client.delete_geometry(token, string=34, position=50)
```

### Detector Status Operations

```python
# Get all detector statuses
statuses = client.get_detector_statuses(token)

# Get status for specific DOM
status = client.get_detector_status(token, dom_id=67890)

# Get all bad DOMs
bad_doms = client.get_bad_doms(token)

# Create detector status
new_status = client.create_detector_status(
    token, dom_id=67890, status="operational", is_bad=False
)

# Update detector status
updated_status = client.update_detector_status(
    token, dom_id=67890, status="maintenance", is_bad=True
)

# Delete detector status
success = client.delete_detector_status(token, dom_id=67890)
```

### Configuration Operations

```python
# Get all configurations
configs = client.get_configurations(token)

# Get specific configuration
config = client.get_configuration(token, key="detector_config")

# Create configuration
config_value = {"param1": "value1", "param2": 42}
new_config = client.create_configuration(token, key="detector_config", value=config_value)

# Update configuration
updated_config = client.update_configuration(token, key="detector_config", value=new_value)

# Delete configuration
success = client.delete_configuration(token, key="detector_config")
```

## Configuration

### Environment Variables

You can configure the client via environment variables:

```bash
# API Configuration
export GCDSERVER_API_URL="http://localhost:8080"

# OAuth2 Configuration (if needed)
export KEYCLOAK_ISSUER_URL="http://localhost:8080/auth/realms/master"
export KEYCLOAK_CLIENT_ID="gcdserver-api"
export KEYCLOAK_CLIENT_SECRET="your-secret"
export KEYCLOAK_REDIRECT_URI="http://localhost:8080/auth/callback"

# Logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# Token (for examples)
export GCDSERVER_TOKEN="your-access-token"
```

### Programmatic Configuration

```python
client = GCDServerClient(
    base_url="http://api.example.com",
    keycloak_issuer_url="http://keycloak.example.com/auth/realms/master",
    keycloak_client_id="my-client",
    keycloak_client_secret="my-secret",
    keycloak_redirect_uri="http://api.example.com/auth/callback"
)
```

## Error Handling

All API operations can raise `GCDServerAPIError`:

```python
from gcdserver_api_client import GCDServerAPIError

try:
    cal = client.get_calibration(token, dom_id=12345)
except GCDServerAPIError as e:
    print(f"API Error: {e}")
    # Handle error appropriately
```

## Data Models

### DOMCal

```python
@dataclass
class DOMCal:
    atwd_gain: List[float]          # ATWD gain values
    atwd_freq: List[float]          # ATWD frequency values
    fadc_gain: float                # FADC gain
    fadc_freq: float                # FADC frequency
    pmt_gain: float                 # PMT gain
    transit_time: float             # Transit time
    relative_pmt_gain: float        # Relative PMT gain
```

### GeoLocation

```python
@dataclass
class GeoLocation:
    x: float                        # X coordinate
    y: float                        # Y coordinate
    z: float                        # Z coordinate
```

### Calibration

```python
@dataclass
class Calibration:
    dom_id: int                     # DOM ID
    domcal: DOMCal                  # Calibration data
    timestamp: Optional[str]        # Creation timestamp
    id: Optional[str]               # MongoDB ID
```

### Geometry

```python
@dataclass
class Geometry:
    string: int                     # String number
    position: int                   # Position in string
    location: GeoLocation           # Geographic location
    timestamp: Optional[str]        # Creation timestamp
    id: Optional[str]               # MongoDB ID
```

### DetectorStatus

```python
@dataclass
class DetectorStatus:
    dom_id: int                     # DOM ID
    status: str                     # Status string
    is_bad: bool                    # Whether DOM is bad
    timestamp: Optional[str]        # Creation timestamp
    id: Optional[str]               # MongoDB ID
```

### Configuration

```python
@dataclass
class Configuration:
    key: str                        # Configuration key
    value: Dict[str, Any]           # Configuration value
    timestamp: Optional[str]        # Creation timestamp
    id: Optional[str]               # MongoDB ID
```

## Logging

The client uses Python's standard logging module. Configure logging as needed:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('gcdserver_api_client')
logger.setLevel(logging.DEBUG)
```

## Migrating from Direct Database Access

If you previously used direct MongoDB access, here's how to migrate:

### Before (Direct DB)
```python
from pymongo import MongoClient

db = MongoClient("mongodb://localhost:27017")
gcd_db = db["gcdserver"]

# Get calibrations
calibrations = list(gcd_db.calibrations.find())

# Create calibration
gcd_db.calibrations.insert_one({
    "dom_id": 12345,
    "domcal": {...}
})
```

### After (API Client)
```python
from gcdserver_api_client import GCDServerClient

client = GCDServerClient()
token = "oauth2-token"

# Get calibrations
calibrations = client.get_calibrations(token)

# Create calibration
new_cal = client.create_calibration(token, dom_id=12345, domcal=domcal)
```

## Benefits of API-Based Access

1. **Security**: OAuth2 authentication and JWT tokens
2. **Abstraction**: No direct database exposure
3. **Scalability**: Can load-balance API servers
4. **Auditability**: All operations logged via API
5. **Flexibility**: Can change backend without client changes
6. **Consistency**: Single source of truth through API
7. **Version Control**: API versioning for backward compatibility

## Troubleshooting

### Connection Refused
```
Error: Connection refused
```
**Solution**: Ensure the API server is running and accessible at the configured URL.

### Authentication Failed
```
Error: API Error 401: Unauthorized
```
**Solution**: Ensure you have a valid OAuth2 token. Refresh the token if expired.

### Invalid Token
```
Error: API Error 401: Invalid token
```
**Solution**: Your token may have expired. Request a new token.

### Resource Not Found
```
Error: API Error 404: Not found
```
**Solution**: The resource may not exist. Verify the ID or key is correct.

## API Documentation

For complete API documentation, see:
- [API README](../gcdserver_rust_api/README.md)
- [OAuth2 Guide](../gcdserver_rust_api/OAUTH2_GUIDE.md)

## Performance Tips

1. **Connection Pooling**: The client reuses HTTP connections via `requests.Session()`
2. **Batch Operations**: Consider batching multiple operations
3. **Caching**: Implement client-side caching for frequently accessed data
4. **Token Refresh**: Refresh tokens before they expire to avoid 401 errors

## Development

### Running Tests

```bash
# (Tests would go here)
pytest tests/
```

### Contributing

When modifying the client:
1. Update docstrings for new methods
2. Add examples to `examples.py`
3. Update this README
4. Test with actual API server

## License

[Same as parent project]

## Support

For issues, questions, or contributions, please refer to the main project repository.
