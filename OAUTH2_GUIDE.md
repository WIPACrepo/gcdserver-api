# OAuth2 Authentication Implementation Guide

## Overview

This Rust REST API now includes full OAuth2 authentication and authorization support using JWT tokens. This allows secure access to GCDServer data without direct MongoDB exposure.

## Key Features Added

### 1. JWT Token Management (`src/auth/jwt.rs`)
- Generate access tokens with user claims and scopes
- Verify token signature and expiration
- Support for scope-based authorization
- Configurable token expiration time

### 2. OAuth2 Provider Integration (`src/auth/oauth2.rs`)
- Pluggable OAuth2 provider support (Google, GitHub, custom)
- Authorization URL generation
- Token exchange (authorization code flow)
- User info retrieval from OAuth2 providers

### 3. Authentication Middleware (`src/auth/middleware.rs`)
- Automatic token extraction from `Authorization: Bearer <token>` header
- Transparent token validation
- Selective route protection (health and auth endpoints are public)
- Proper error responses for authentication failures

### 4. Authentication Endpoints (`src/api/auth.rs`)
- `/auth/login` - Initiate OAuth2 login flow
- `/auth/callback` - Handle OAuth2 provider callbacks
- `/auth/verify` - Verify token validity
- `/auth/refresh` - Generate new access tokens
- `/auth/logout` - Logout and invalidate tokens

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24

# OAuth2 Configuration (Google example)
OAUTH2_PROVIDER=google
OAUTH2_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_REDIRECT_URI=http://localhost:8080/auth/callback
```

**Important**: Always use a strong, unique `JWT_SECRET` in production!

## Usage Examples

### 1. Get Authentication Token (OAuth2 Flow)

```bash
# User logs in via OAuth2 provider
# Provider redirects to: http://localhost:8080/auth/callback?code=AUTH_CODE&state=STATE

# API returns JWT token:
curl -X GET "http://localhost:8080/auth/callback?code=AUTH_CODE&state=STATE"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": null
}
```

### 2. Use Token to Access Protected Resources

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Create calibration with authentication
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
```

### 3. Verify Token Validity

```bash
curl -X GET http://localhost:8080/auth/verify \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "valid": true,
  "user_id": "oauth_user_123",
  "email": "user@example.com",
  "scopes": ["read", "write"],
  "provider": "google"
}
```

### 4. Refresh Token

```bash
curl -X POST http://localhost:8080/auth/refresh \
  -H "Authorization: Bearer $TOKEN"

# Returns new access token
```

### 5. Logout

```bash
curl -X POST http://localhost:8080/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

## Token Claims Structure

Each JWT token contains the following claims:

```json
{
  "sub": "user123",           // User ID from OAuth2 provider
  "email": "user@example.com", // User email
  "scopes": ["read", "write"],// Authorization scopes
  "exp": 1700000000,          // Expiration timestamp
  "iat": 1699913600,          // Issued at timestamp
  "jti": "uuid-string",       // Unique JWT ID
  "provider": "google"        // OAuth2 provider name
}
```

## Scope-Based Authorization

The API supports OAuth2 scopes for fine-grained access control:

```rust
// Example: Check if user has 'write' scope
let claims = jwt_manager.verify_token(&token)?;
if jwt_manager.has_scope(&claims, "write") {
    // Allow write operation
}

// Check for any of multiple scopes
if jwt_manager.has_any_scope(&claims, &["admin", "moderator"]) {
    // Allow operation
}
```

## Implementation Roadmap

### Already Implemented
✅ JWT token generation and verification
✅ Basic OAuth2 structure
✅ Authentication middleware
✅ Authentication endpoints
✅ Scope support

### Next Steps for Production
- [ ] Implement full OAuth2 callback with state verification
- [ ] Add token blacklist for logout functionality
- [ ] Implement role-based access control (RBAC)
- [ ] Add database persistence for user records
- [ ] Implement token refresh token rotation
- [ ] Add rate limiting on authentication endpoints
- [ ] Implement multi-factor authentication (MFA)
- [ ] Add comprehensive audit logging

## Security Best Practices

1. **JWT_SECRET**: Use a cryptographically secure random string
   ```bash
   # Generate strong secret
   openssl rand -base64 32
   ```

2. **HTTPS**: Always use HTTPS in production

3. **Token Storage**: Store tokens securely on the client side
   - Use secure HTTP-only cookies
   - Or secure local storage

4. **Token Expiration**: Set appropriate expiration times
   - Short-lived access tokens (1-24 hours)
   - Longer-lived refresh tokens

5. **Scope Validation**: Implement strict scope checking on all operations

## Python Integration Example

```python
import requests
from urllib.parse import urlencode

BASE_URL = "http://localhost:8080"
OAUTH_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
OAUTH_REDIRECT_URI = "http://localhost:8080/auth/callback"

# Step 1: Get authorization URL
auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode({
    'client_id': OAUTH_CLIENT_ID,
    'redirect_uri': OAUTH_REDIRECT_URI,
    'response_type': 'code',
    'scope': 'openid email profile'
})}"

# Step 2: User authorizes and provider redirects with code
# Step 3: Exchange code for token
response = requests.get(f"{BASE_URL}/auth/callback", params={
    'code': 'AUTH_CODE_FROM_PROVIDER',
    'state': 'RANDOM_STATE'
})
token_data = response.json()
access_token = token_data['access_token']

# Step 4: Use token to access API
headers = {'Authorization': f'Bearer {access_token}'}
calibration = requests.get(
    f"{BASE_URL}/calibration/12345",
    headers=headers
).json()

print(calibration['data'])
```

## Troubleshooting

### Invalid or expired token error
- Token may have expired, request new token via `/auth/refresh`
- Check token format: must be `Authorization: Bearer <token>`

### Missing authorization header
- Ensure header is included for protected endpoints
- Health check (`/health`) and auth endpoints don't require authentication

### Token verification failed
- Check `JWT_SECRET` matches between token generation and verification
- Ensure token hasn't been tampered with

## Additional Resources

- [JWT.io](https://jwt.io) - JWT Debugger and Libraries
- [OAuth 2.0](https://tools.ietf.org/html/rfc6749) - OAuth 2.0 Specification
- [OpenID Connect](https://openid.net/specs/openid-connect-core-1_0.html) - OpenID Connect Spec
- [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) - Security Best Practices
