# GCDServer API Python Client - Setup & Usage Guide

Welcome! This folder contains a complete Python client library for interacting with the GCDServer REST API instead of direct database access.

## 📁 What's Inside

- **`gcdserver_api_client.py`** - Main client library (796 lines, fully documented)
  - All CRUD operations for Calibrations, Geometry, Detector Status, Configuration
  - OAuth2 authentication with JWT tokens
  - Comprehensive error handling
  - Type hints and dataclasses for all models

- **`quickstart.py`** - Quick start examples (164 lines)
  - Common operations for all data types
  - Good starting point for new users
  
- **`examples.py`** - Comprehensive examples (368 lines)
  - Detailed examples for every API operation
  - Authentication flow examples
  - Error handling patterns
  
- **`migration_guide.py`** - Migration from direct DB to API (348 lines)
  - Side-by-side comparison of old vs new code
  - Migration checklist
  - Batch migration script template

- **`README.md`** - Full documentation
  - Complete API reference
  - Configuration options
  - Troubleshooting guide
  - Performance tips

- **`requirements.txt`** - Python dependencies
  - Just `requests>=2.28.0`

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export GCDSERVER_API_URL="http://localhost:8080"
export KEYCLOAK_ISSUER_URL="http://localhost:8080/auth/realms/master"
export KEYCLOAK_CLIENT_ID="gcdserver-api"
export KEYCLOAK_CLIENT_SECRET="your-secret"
export KEYCLOAK_REDIRECT_URI="http://localhost:8080/auth/callback"
```

### 3. Get an OAuth2 Token
```python
from gcdserver_api_client import GCDServerClient

client = GCDServerClient()

# Initiate OAuth2 login
login_info = client.login()
print(login_info['authorization_url'])

# User logs in and provides authorization code
# Extract token from /auth/callback response
```

### 4. Run Your First Script
```bash
export GCDSERVER_TOKEN="your-oauth2-token"
python quickstart.py
```

## 📚 Common Tasks

### Get All Calibrations
```python
from gcdserver_api_client import GCDServerClient

client = GCDServerClient()
token = "your-oauth2-token"

calibrations = client.get_calibrations(token)
for cal in calibrations:
    print(f"DOM {cal.dom_id}: {cal.timestamp}")
```

### Create a New Calibration
```python
from gcdserver_api_client import GCDServerClient, DOMCal

client = GCDServerClient()
token = "your-oauth2-token"

domcal = DOMCal(
    atwd_gain=[1.0, 1.1, 1.2, 1.3],
    atwd_freq=[50.0, 50.1, 50.2, 50.3],
    fadc_gain=1.0,
    fadc_freq=50.0,
    pmt_gain=1.0,
    transit_time=1.0,
    relative_pmt_gain=1.0
)

new_cal = client.create_calibration(
    token, dom_id=12345, domcal=domcal
)
print(f"Created: {new_cal.id}")
```

### Update Geometry
```python
from gcdserver_api_client import GCDServerClient, GeoLocation

client = GCDServerClient()
token = "your-oauth2-token"

# Get current geometry
geom = client.get_geometry(token, string=34, position=50)

# Modify location
geom.location.x += 10.0
geom.location.y += 20.0

# Update
updated = client.update_geometry(
    token, string=34, position=50, location=geom.location
)
```

### Find Bad DOMs
```python
from gcdserver_api_client import GCDServerClient

client = GCDServerClient()
token = "your-oauth2-token"

bad_doms = client.get_bad_doms(token)
print(f"Found {len(bad_doms)} bad DOMs")

for status in bad_doms:
    print(f"  DOM {status.dom_id}: {status.status}")
```

## 🔐 Authentication

The API uses **OAuth2 with JWT tokens**. You have two options:

### Option 1: Web Browser Flow (Interactive)
```python
from gcdserver_api_client import GCDServerClient
import webbrowser

client = GCDServerClient()

# Get authorization URL
login_info = client.login()
auth_url = login_info['authorization_url']

# Open in browser
webbrowser.open(auth_url)

# User logs in, gets redirected to /auth/callback
# Copy the access_token from the response
```

### Option 2: Environment Variable (Script)
```bash
# After getting token from browser or Keycloak admin
export GCDSERVER_TOKEN="eyJ0eXAiOiJKV1QiLC..."
python your_script.py
```

### Option 3: Token from Keycloak (If Configured)
```python
import requests

# Exchange credentials for token
resp = requests.post(
    "http://keycloak-server/auth/realms/master/protocol/openid-connect/token",
    data={
        "client_id": "gcdserver-api",
        "client_secret": "your-secret",
        "grant_type": "password",
        "username": "user",
        "password": "pass"
    }
)
token = resp.json()['access_token']
```

## 🛠️ Running Examples

### Health Check
```bash
python examples.py
# Shows what runs without authentication
```

### Full Examples with Token
```bash
export GCDSERVER_TOKEN="your-token"
python examples.py
# Runs all authentication and CRUD examples
```

### Quick Start
```bash
export GCDSERVER_TOKEN="your-token"
python quickstart.py
# Demonstrates basic operations
```

## 📊 Migration from Direct Database

If you're migrating from direct MongoDB access:

See `migration_guide.py` for:
- Side-by-side code comparisons (before/after)
- Migration checklist
- Batch migration template
- Error handling updates

## 🐛 Troubleshooting

### Connection Refused
```
Error: Connection refused at http://localhost:8080
```
**Fix:** Ensure the API server is running:
```bash
cd gcdserver_rust_api
cargo run
```

### Unauthorized (401)
```
Error: API Error 401: Unauthorized
```
**Fix:** Ensure you have a valid token:
```bash
export GCDSERVER_TOKEN="your-valid-token"
```

### Invalid Token
```
Error: API Error 401: Invalid token
```
**Fix:** Token may be expired. Get a new one via OAuth2 flow.

### Not Found (404)
```
Error: API Error 404: Not found
```
**Fix:** The resource doesn't exist. Check the ID/key is correct.

## 📖 Learning Paths

**Beginner:**
1. Read `quickstart.py`
2. Run `python quickstart.py` with a token
3. Try modifying one example

**Intermediate:**
1. Read `README.md`
2. Study `examples.py` 
3. Check `migration_guide.py` if migrating from DB

**Advanced:**
1. Read `gcdserver_api_client.py` source code
2. Implement custom caching/batching
3. Build production application using the client

## 🎯 Key Features

✅ **Full CRUD Operations** - Create, Read, Update, Delete for all data types
✅ **OAuth2 Support** - Secure token-based authentication
✅ **Type Safe** - Python dataclasses with type hints
✅ **Error Handling** - Consistent exception handling with `GCDServerAPIError`
✅ **Connection Pooling** - Efficient HTTP connection reuse
✅ **Comprehensive Docs** - Every method has detailed docstrings
✅ **Examples** - Working examples for all operations
✅ **Logging** - Built-in logging for debugging

## 📝 API Summary

### Calibration
- `get_calibrations()` - Get all
- `get_calibration(dom_id)` - Get specific
- `get_latest_calibration(dom_id)` - Get latest
- `create_calibration(dom_id, domcal)` - Create new
- `update_calibration(dom_id, domcal)` - Update existing
- `delete_calibration(dom_id)` - Delete

### Geometry
- `get_geometries()` - Get all
- `get_geometry(string, position)` - Get specific
- `get_string_geometry(string)` - Get for string
- `create_geometry(string, position, location)` - Create new
- `update_geometry(string, position, location)` - Update
- `delete_geometry(string, position)` - Delete

### Detector Status
- `get_detector_statuses()` - Get all
- `get_detector_status(dom_id)` - Get specific
- `get_bad_doms()` - Get all bad DOMs
- `create_detector_status(dom_id, status, is_bad)` - Create
- `update_detector_status(dom_id, status, is_bad)` - Update
- `delete_detector_status(dom_id)` - Delete

### Configuration
- `get_configurations()` - Get all
- `get_configuration(key)` - Get specific
- `create_configuration(key, value)` - Create new
- `update_configuration(key, value)` - Update
- `delete_configuration(key)` - Delete

### Authentication
- `login()` - Initiate OAuth2 flow
- `verify_token(token)` - Verify token validity
- `refresh_token(token)` - Get new token
- `logout(token)` - Logout

## 🔗 Links

- **Rust API Server**: See `../gcdserver_rust_api/`
- **Full Documentation**: See `README.md`
- **OAuth2 Setup**: See `../gcdserver_rust_api/OAUTH2_GUIDE.md`
- **Examples**: `examples.py`, `quickstart.py`
- **Migration Help**: `migration_guide.py`

## 💡 Tips & Best Practices

1. **Store Tokens Securely**
   - Use secure local storage or secure cookies
   - Never commit tokens to version control
   - Use environment variables for development

2. **Handle Token Expiration**
   - Check expiration before use
   - Implement token refresh logic
   - Have user re-authenticate if needed

3. **Implement Retries**
   - Network errors are transient
   - Add exponential backoff
   - Retry up to 3 times

4. **Cache Data**
   - Cache configuration data locally
   - Reduces API calls
   - Still get fresh data on refresh

5. **Use Batch Operations**
   - Group related operations
   - Reduces round trips
   - More efficient

6. **Monitor Performance**
   - Log response times
   - Alert on slow operations
   - Track error rates

## 📞 Support

For issues:
1. Check `README.md` troubleshooting section
2. Review examples in `examples.py`
3. Check Rust API logs on server
4. Verify OAuth2 token is valid
5. Test with curl first

## ✨ What's Next

Now that you have the client set up:

1. **Run an example**: `python quickstart.py`
2. **Read the docs**: Open `README.md`
3. **Explore**: Try different operations in `examples.py`
4. **Build**: Create your own scripts using the client
5. **Migrate**: If coming from direct DB, follow `migration_guide.py`

Happy coding! 🎉
