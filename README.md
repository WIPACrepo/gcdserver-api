# WARNING THIS IS COMPLETELY VIBE CODED AT THE MOMENT.... DO NOT DEPLOY

# GCDServer REST API

A Rust-based RESTful API for interacting with GCDServer data, abstracting away direct MongoDB interactions.

## Features

- RESTful API endpoints for Calibration, Geometry, Detector Status, and Configuration data
- **Keycloak OAuth2 authentication** - Direct token validation with RSA public keys
- **Streamlined auth flow** - No intermediate JWT wrapping, uses Keycloak tokens directly
- MongoDB integration with proper error handling
- Structured logging with environment-based configuration
- Actix-web framework for high performance
- Type-safe database operations with Serde serialization
- Role-based access control (RBAC) via Keycloak realm roles
- Token validation middleware for protected endpoints

## Project Structure

```
src/
├── main.rs              # Application entry point
├── api/                 # REST API endpoints
│   ├── mod.rs
│   ├── auth.rs          # Authentication endpoints (Keycloak OAuth2)
│   ├── calibration.rs   # Calibration endpoints
│   ├── geometry.rs      # Geometry endpoints
│   ├── detector_status.rs # Detector status endpoints
│   ├── configuration.rs  # Configuration endpoints
│   └── health.rs        # Health check endpoint
├── auth/                # Authentication & OAuth2
│   ├── mod.rs
│   ├── middleware.rs    # Token validation middleware (RSA verification)
│   └── oauth2.rs        # Keycloak OAuth2 integration
├── db.rs                # MongoDB client wrapper
├── errors.rs            # Error handling and API responses
└── models.rs            # Data models and request/response types
```

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Authentication
- `POST /auth/login` - Initiate OAuth2 login (returns authorization URL)
- `GET /auth/callback?code=...&state=...` - OAuth2 callback endpoint (exchanges code for Keycloak token)
- `GET /auth/verify` - Verify Keycloak token validity (requires Bearer token)

### Calibration (requires authentication)
- `GET /calibration` - Get all calibrations
- `POST /calibration` - Create new calibration
- `GET /calibration/{dom_id}` - Get calibration for DOM
- `PUT /calibration/{dom_id}` - Update calibration
- `DELETE /calibration/{dom_id}` - Delete calibration
- `GET /calibration/latest/{dom_id}` - Get latest calibration

### Geometry
- `GET /geometry` - Get all geometry entries
- `POST /geometry` - Create new geometry entry
- `GET /geometry/{string}/{position}` - Get geometry by location
- `PUT /geometry/{string}/{position}` - Update geometry
- `DELETE /geometry/{string}/{position}` - Delete geometry
- `GET /geometry/string/{string}` - Get all geometry for a string

### Detector Status
- `GET /detector-status` - Get all detector statuses
- `POST /detector-status` - Create new detector status
- `GET /detector-status/{dom_id}` - Get status for DOM
- `PUT /detector-status/{dom_id}` - Update detector status
- `DELETE /detector-status/{dom_id}` - Delete detector status
- `GET /detector-status/bad-doms` - Get all bad DOMs

### Configuration
- `GET /config` - Get all configurations
- `POST /config` - Create new configuration
- `GET /config/{key}` - Get configuration by key
- `PUT /config/{key}` - Update configuration
- `DELETE /config/{key}` - Delete configuration

## Installation

### Prerequisites
- Rust 1.70+
- MongoDB 4.0+

### Building

```bash
# Clone or navigate to the project directory
cd gcdserver_rust_api

# Build the project
cargo build --release
```

## Configuration

The API uses environment variables for configuration. Create a `.env` file in the project root:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=gcdserver

# Keycloak OAuth2
KEYCLOAK_ISSUER_URL=http://localhost:8080/auth/realms/gcdserver
KEYCLOAK_CLIENT_ID=gcdserver-api
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret
KEYCLOAK_REDIRECT_URI=http://localhost:8080/auth/callback
```

**Note:** The API validates Keycloak tokens using RSA public keys fetched from Keycloak's discovery endpoint. No additional JWT secret configuration is needed.

### Keycloak Setup

For detailed Keycloak setup instructions, see [KEYCLOAK_SETUP.md](KEYCLOAK_SETUP.md).

**Quick Start:**
```bash
# Start Keycloak with Docker
docker run -d \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev

# Then configure client credentials in Keycloak admin console
# and update .env file
```

## Running

```bash
# Development
cargo run

# Release build
cargo run --release

# With custom environment
MONGODB_URI=mongodb://db-server:27017 cargo run
```

The API will start on `http://0.0.0.0:8080`

## Example Requests

### 1. Keycloak OAuth2 Login Flow

```bash
# 1. Get login authorization URL
curl -X POST http://localhost:8080/auth/login

# Response includes authorization URL
{
  "authorization_url": "http://localhost:8080/auth/realms/gcdserver/protocol/openid-connect/auth?...",
  "state": "random-state"
}

# 2. User visits authorization_url and logs in with Keycloak
# 3. Keycloak redirects to callback: http://localhost:8080/auth/callback?code=AUTH_CODE&state=STATE
# 4. Exchange code for Keycloak token
curl -X GET "http://localhost:8080/auth/callback?code=AUTH_CODE&state=STATE"

# Response includes Keycloak access token
{
  "access_token": "eyJhbGciOiJSUzI1NiI...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiI...",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "name": "User Name",
    "username": "username",
    "roles": ["user", "admin"]
  }
}
```

### 2. Using Keycloak Bearer Token

```bash
# Store token from OAuth2 callback response
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Verify token validity
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/auth/verify

# Response shows token validity and claims
{
  "valid": true,
  "user_id": "user-uuid",
  "email": "user@example.com",
  "roles": ["user", "admin"]
}

# Use token for authenticated API calls
curl -X POST http://localhost:8080/calibration \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dom_id": 12345,
    "domcal": {
      "atwd_gain": [1.0, 1.1, 1.2, 1.3],
      "atwd_freq": [50.0, 50.1, 50.2, 50.3],
      "fadc_gain": 1.0,
      "fadc_freq": 50.0,
      "pmt_gain": 1.0,
      "transit_time": 1.0,
      "relative_pmt_gain": 1.0
    }
  }'

# Note: Token refresh is handled by Keycloak
# Use the refresh_token from callback response if token expires
```

### Create Calibration
```bash
curl -X POST http://localhost:8080/calibration \
  -H "Content-Type: application/json" \
  -d '{
    "dom_id": 12345,
    "domcal": {
      "atwd_gain": [1.0, 1.1, 1.2, 1.3],
      "atwd_freq": [50.0, 50.1, 50.2, 50.3],
      "fadc_gain": 1.0,
      "fadc_freq": 50.0,
      "pmt_gain": 1.0,
      "transit_time": 1.0,
      "relative_pmt_gain": 1.0
    }
  }'
```

### Get Calibration
```bash
curl http://localhost:8080/calibration/12345
```

### Create Geometry
```bash
curl -X POST http://localhost:8080/geometry \
  -H "Content-Type: application/json" \
  -d '{
    "string": 1,
    "position": 1,
    "location": {
      "x": 100.0,
      "y": 200.0,
      "z": -500.0
    }
  }'
```

### Create Configuration
```bash
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "detector_name",
    "value": "IceCube"
  }'
```

## Error Handling

The API returns structured error responses:

```json
{
  "error": "Not found: Configuration not found for key 'missing_key'",
  "status": 404
}
```

### Authentication Errors

```json
{
  "error": "Missing authorization header",
  "status": 401
}
```

```json
{
  "error": "Invalid or expired token",
  "status": 401
}
```

## Logging

Set `RUST_LOG` environment variable to control logging:

```bash
RUST_LOG=debug cargo run
RUST_LOG=info,actix_web=debug cargo run
```

## Performance Considerations

- The server uses Actix-web for high-concurrency async handling
- MongoDB connection pooling is handled by the MongoDB driver
- All database operations are async and non-blocking

## Integration with Python GCDServer

The Python GCDServer client can be updated to use this REST API instead of directly accessing MongoDB:

```python
import requests

BASE_URL = "http://localhost:8080"

# Get calibration
response = requests.get(f"{BASE_URL}/calibration/12345")
calibration = response.json()["data"]

# Create geometry
requests.post(
    f"{BASE_URL}/geometry",
    json={
        "string": 1,
        "position": 1,
        "location": {"x": 100.0, "y": 200.0, "z": -500.0}
    }
)
```

## Authentication Architecture

### Token Flow
1. **Login Request** → Client requests authorization URL from `/auth/login`
2. **User Authentication** → User logs in via Keycloak
3. **Authorization Code** → Keycloak redirects with authorization code
4. **Token Exchange** → API exchanges code for Keycloak token at `/auth/callback`
5. **Token Validation** → Middleware validates RSA-signed token on protected endpoints
6. **Claims Extraction** → Validated claims attached to request for handler access

### Token Validation
- Keycloak tokens are RSA-256 signed
- Public keys fetched from Keycloak's JWKS endpoint
- Signature verification ensures token authenticity
- Expiration checked automatically by middleware
- Realm roles extracted from token claims

## Future Enhancements

- Token blacklisting/revocation support
- Batch operations support
- Query filtering and pagination
- Database migration tools
- Performance monitoring and metrics
- WebSocket support for real-time updates
- GraphQL interface
- API rate limiting
- Request signing for service-to-service authentication
- Multi-realm Keycloak support

## License

See LICENSE file for details

## Development

### Running Tests

```bash
cargo test
```

### Code Formatting

```bash
cargo fmt
```

### Linting

```bash
cargo clippy
```
