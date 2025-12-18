# Keycloak OpenID Connect Integration Guide

## Overview

This REST API has been updated to support **Keycloak** as an OpenID Connect (OIDC) identity provider. Keycloak provides enterprise-grade identity and access management that's perfect for GCDServer.

## Why Keycloak?

✅ **Self-hosted**: Run on your own infrastructure  
✅ **Standards-based**: Full OpenID Connect and OAuth2 compliance  
✅ **Feature-rich**: Realm management, user federation, social login  
✅ **Zero Trust**: Fine-grained permissions and policies  
✅ **Enterprise Ready**: Used by major organizations  

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          GCDServer User                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │ 1. Login Request
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Rust REST API (8080)                          │
│  /auth/login ──────────────────────────────────────────┐         │
│  /auth/callback ◄─────────────────────────────────────┼─────┐   │
│  /calibration (+ JWT)                                  │     │   │
│  /geometry (+ JWT)                                     │     │   │
│  /detector-status (+ JWT)                              │     │   │
│  /config (+ JWT)                                       │     │   │
└──────────────────────────────────────────────────┬─────┼─────┘   │
                                                   │     │
                    2. Redirect to Keycloak        │     │
                    3. Get Authorization Code ◄───┘     │
                                                        │
┌───────────────────────────────────────────────────────┼──────────┐
│                    Keycloak Server                     │          │
│  /auth/realms/master                                  │          │
│  - User Directory                                     │          │
│  - OAuth2/OIDC Endpoints                              │          │
│  - Token Generation                                   │          │
│  - User Roles & Permissions                           │          │
│                    4. Exchange Code for Tokens ◄──────┘          │
│                    5. Return Access Token, ID Token              │
└──────────────────────────────────────────────────────────────────┘
                       │
                       │ 6. JWT Created from User Info
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MongoDB (27017)                               │
│  - Calibration Data                                             │
│  - Geometry Data                                                │
│  - Detector Status Data                                         │
│  - Configuration Data                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Install and Run Keycloak Locally

**Using Docker (Recommended):**
```bash
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev
```

**Using Docker Compose:**
```yaml
version: '3'
services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
    ports:
      - "8080:8080"
    command:
      - start-dev

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
```

Access Keycloak admin console: http://localhost:8080/admin

### 2. Configure Keycloak Realm and Client

**Step 1: Create a New Realm**
1. Go to http://localhost:8080/admin
2. Login with admin / admin
3. Click "Master" dropdown → "Create Realm"
4. Name: `gcdserver`
5. Click "Create"

**Step 2: Create a Client**
1. Go to Realm Settings → Clients
2. Click "Create client"
3. **Client ID**: `gcdserver-api`
4. **Name**: GCDServer API
5. Click "Next"

**Step 3: Configure Client Settings**
1. **Client Authentication**: ON
2. **Authorization**: ON
3. **Authentication flow**:
   - ✅ Standard flow enabled
   - ✅ Direct access grants enabled
4. Click "Save"

**Step 4: Set Redirect URIs**
1. Go to "Access settings" tab
2. **Valid redirect URIs**: `http://localhost:8080/auth/callback`
3. **Web origins**: `http://localhost:8080`
4. Click "Save"

**Step 5: Get Client Secret**
1. Go to "Credentials" tab
2. Copy the **Client Secret** (you'll need this)

**Step 6: Create Test User**
1. Go to Users → "Create new user"
2. **Username**: `testuser`
3. **Email**: `testuser@example.com`
4. **First Name**: Test
5. **Last Name**: User
6. Toggle "Email verified" ON
7. Click "Create"
8. Go to "Credentials" tab
9. Set password (e.g., `password123`)
10. Toggle "Temporary" OFF

### 3. Configure Environment Variables

Update `.env` file with Keycloak settings:

```env
# Keycloak OpenID Connect Configuration
KEYCLOAK_ISSUER_URL=http://localhost:8080/auth/realms/gcdserver
KEYCLOAK_CLIENT_ID=gcdserver-api
KEYCLOAK_CLIENT_SECRET=<copy-from-keycloak-credentials-tab>
KEYCLOAK_REDIRECT_URI=http://localhost:8080/auth/callback

# For production, use HTTPS:
# KEYCLOAK_ISSUER_URL=https://keycloak.example.com/auth/realms/gcdserver
# KEYCLOAK_REDIRECT_URI=https://api.example.com/auth/callback
```

## Usage

### 1. Get Authorization URL and Login

```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"nonce": "optional-nonce"}'

# Response:
{
  "authorization_url": "http://localhost:8080/auth/realms/gcdserver/protocol/openid-connect/auth?...",
  "state": "random-state-value",
  "nonce": "random-nonce"
}
```

**User then visits authorization_url and logs in with Keycloak credentials**

### 2. Exchange Authorization Code for Token

After user authenticates with Keycloak, they're redirected to:
```
http://localhost:8080/auth/callback?code=AUTHORIZATION_CODE&state=STATE
```

API automatically exchanges code for token.

### 3. Use Token to Access Protected Resources

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Get calibration
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/calibration/12345

# Create geometry
curl -X POST http://localhost:8080/geometry \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "string": 1,
    "position": 1,
    "location": {"x": 100.0, "y": 200.0, "z": -500.0}
  }'
```

## Advanced Keycloak Features

### 1. Role-Based Access Control (RBAC)

**In Keycloak:**
1. Go to Realm Roles
2. Create roles: `admin`, `data-analyst`, `viewer`
3. Go to Users → testuser → Role mapping
4. Assign roles

**In API:** Roles are automatically mapped to JWT scopes:
```json
{
  "sub": "user123",
  "email": "testuser@example.com",
  "scopes": ["admin", "data-analyst"],
  "provider": "keycloak"
}
```

### 2. User Federation

Link Keycloak to LDAP or Active Directory:
1. Go to Realm Settings → User Federation
2. Click "Add provider" → "ldap"
3. Configure LDAP connection details

### 3. Social Login

Add social identity providers:
1. Go to Realm Settings → Identity Providers
2. Click "Create" → Select provider (Google, GitHub, etc.)
3. Configure client credentials
4. Users can now login with social accounts

### 4. Multi-Factor Authentication

1. Go to Realm Settings → Authentication
2. Configure MFA requirements
3. Users must authenticate with secondary factor

## Token Flow Diagram

```
User Input                Keycloak                   API Server
   │                        │                            │
   │─ Click "Login" ─────────>                           │
   │                        │                            │
   │<─ Display Keycloak ────│                            │
   │   Login Form           │                            │
   │                        │                            │
   │─ Enter Credentials ───>│                            │
   │                        │                            │
   │<─ Redirect w/ Code ────────────────────────────────>│
   │                        │                            │
   │                        │<─ Exchange Code ──────────>│
   │                        │<─ for Access Token ───────│
   │                        │<─ and User Info ──────────│
   │                        │                            │
   │                        │<─ Return JWT Token ───────│
   │<─ JWT Token ───────────────────────────────────────│
   │                        │                            │
   │─ API Request w/ JWT ─────────────────────────────>│
   │  (Authorization Header)                            │
   │                        │                            │
   │<─ Response with Data ──────────────────────────────│
```

## Production Deployment

### 1. Keycloak with PostgreSQL

```yaml
version: '3'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  keycloak:
    image: quay.io/keycloak/keycloak:latest
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: secure-password
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin-secure-password
    ports:
      - "8080:8080"
    command:
      - start
    depends_on:
      - postgres
    volumes:
      - ./certificates:/opt/keycloak/conf/certs

volumes:
  postgres_data:
```

### 2. HTTPS Configuration

**Generate self-signed certificate:**
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```

**Update Keycloak startup:**
```bash
docker run -d \
  -e KC_HOSTNAME=keycloak.example.com \
  -e KC_HTTPS_CERTIFICATE_FILE=/opt/keycloak/conf/certs/cert.pem \
  -e KC_HTTPS_CERTIFICATE_KEY_FILE=/opt/keycloak/conf/certs/key.pem \
  -v ./certificates:/opt/keycloak/conf/certs \
  quay.io/keycloak/keycloak:latest \
  start
```

### 3. Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privatekey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### "Invalid issuer URL"
- Verify `KEYCLOAK_ISSUER_URL` is correct and reachable
- Check Keycloak is running and accessible
- Ensure realm name matches (e.g., `/realms/gcdserver`)

### "Redirect URI mismatch"
- Ensure `KEYCLOAK_REDIRECT_URI` matches Keycloak client configuration
- Check protocol (http vs https)
- Verify hostname and port

### "Failed to discover OpenID provider metadata"
- Check Keycloak is running: `curl http://localhost:8080/auth/realms/gcdserver/.well-known/openid-configuration`
- Verify issuer URL ends with realm name
- Check firewall/network connectivity

### Token validation fails
- Ensure `JWT_SECRET` is set and consistent
- Check token hasn't expired
- Verify Authorization header format: `Bearer <token>`

## Testing with cURL

```bash
# 1. Request authorization
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{}'

# Copy the authorization_url from response and visit in browser

# 2. After login, browser redirects to callback with code
# Extract code from redirect URL

# 3. Simulate callback (in real scenario, done automatically)
curl -X GET "http://localhost:8080/auth/callback?code=AUTH_CODE&state=STATE"

# 4. Use returned token
TOKEN=$(curl ... | jq -r '.access_token')

# 5. Access protected endpoints
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/calibration
```

## Python Client Example

```python
import requests
import webbrowser
from urllib.parse import parse_qs, urlparse

KEYCLOAK_URL = "http://localhost:8080"
CLIENT_ID = "gcdserver-api"
CLIENT_SECRET = "your-secret"
API_URL = "http://localhost:8080"

# Step 1: Get authorization URL
response = requests.post(f"{API_URL}/auth/login", json={})
auth_data = response.json()
auth_url = auth_data['authorization_url']
state = auth_data['state']

# Step 2: Open browser for user to login
webbrowser.open(auth_url)

# Step 3: Simulate receiving callback code
# (In real scenario, this would be from redirect)
input("Press Enter after logging in and copy the authorization code: ")
code = input("Enter authorization code: ")

# Step 4: Exchange code for token
callback_response = requests.get(
    f"{API_URL}/auth/callback",
    params={"code": code, "state": state}
)
token_data = callback_response.json()
access_token = token_data['access_token']

# Step 5: Use token to access API
headers = {"Authorization": f"Bearer {access_token}"}
calibration = requests.get(f"{API_URL}/calibration/12345", headers=headers)
print(calibration.json())
```

## Security Best Practices

1. **Use HTTPS in Production**
   - Never expose tokens over unencrypted connections
   - Use valid SSL certificates

2. **Strong Secrets**
   - Use cryptographically secure secrets for `KEYCLOAK_CLIENT_SECRET`
   - Rotate secrets regularly

3. **Token Expiration**
   - Keep `JWT_EXPIRATION_HOURS` reasonably short (1-24 hours)
   - Implement token refresh for long-lived sessions

4. **Scope Validation**
   - Always validate user scopes match operation requirements
   - Use Keycloak roles to control fine-grained permissions

5. **Network Security**
   - Keep Keycloak on private network or behind firewall
   - Use VPN/SSH tunneling for remote access

6. **Audit Logging**
   - Enable Keycloak audit logs
   - Log all API access with JWT claims

## Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Spec](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [JWT.io](https://jwt.io) - JWT Debugger

---

**Last Updated**: December 18, 2025  
**API Version**: 1.0.0  
**Keycloak Support**: 20.0+
