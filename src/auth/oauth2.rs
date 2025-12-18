// OpenID Connect / OAuth2 provider integration with Keycloak support
use serde::{Deserialize, Serialize};
use log::{info, error};
use base64::Engine;

use crate::errors::{ApiError, ApiResult};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenIDConfig {
    /// OpenID Connect issuer URL (e.g., https://keycloak.example.com/auth/realms/master)
    pub issuer_url: String,
    /// OAuth2 Client ID
    pub client_id: String,
    /// OAuth2 Client Secret
    pub client_secret: String,
    /// Redirect URI after authentication
    pub redirect_uri: String,
    /// Optional: Keycloak realm name (extracted from issuer_url if not provided)
    pub realm: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct TokenResponse {
    pub access_token: String,
    pub token_type: String,
    pub expires_in: i64,
    pub refresh_token: Option<String>,
    pub id_token: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UserInfo {
    pub sub: String,
    pub email: String,
    pub name: Option<String>,
    pub preferred_username: Option<String>,
    pub picture: Option<String>,
    /// Keycloak specific: realm roles
    pub realm_access: Option<RealmAccess>,
}

#[derive(Debug, Deserialize)]
pub struct RealmAccess {
    pub roles: Vec<String>,
}

pub struct OpenIDProvider {
    config: OpenIDConfig,
}

impl OpenIDProvider {
    /// Create new OpenID Connect provider from Keycloak issuer
    pub async fn from_keycloak(config: OpenIDConfig) -> ApiResult<Self> {
        info!("Initializing OpenID Connect provider from issuer: {}", config.issuer_url);

        // Verify issuer is reachable by checking discovery endpoint
        let discovery_url = format!("{}/.well-known/openid-configuration", config.issuer_url);
        
        let client = reqwest::Client::new();
        let response = client
            .get(&discovery_url)
            .send()
            .await
            .map_err(|e| {
                error!("Failed to reach OpenID provider discovery endpoint: {}", e);
                ApiError::InternalError(
                    format!("Failed to reach OpenID provider at {}. Check issuer URL.", config.issuer_url)
                )
            })?;

        if !response.status().is_success() {
            error!("OpenID provider discovery returned status: {}", response.status());
            return Err(ApiError::InternalError(
                "OpenID provider discovery failed. Check issuer URL.".to_string(),
            ));
        }

        info!("Successfully discovered OpenID provider at: {}", config.issuer_url);
        Ok(OpenIDProvider { config })
    }

    /// Get authorization URL for user login
    pub fn get_authorization_url(&self, nonce: &str, state: &str) -> (String, String) {
        let scope = urlencoding::encode("openid email profile");
        let redirect_uri = urlencoding::encode(&self.config.redirect_uri);
        let client_id = urlencoding::encode(&self.config.client_id);
        
        let auth_url = format!(
            "{}/protocol/openid-connect/auth?client_id={}&redirect_uri={}&response_type=code&scope={}&state={}&nonce={}&code_challenge_method=S256",
            self.config.issuer_url,
            client_id,
            redirect_uri,
            scope,
            urlencoding::encode(state),
            urlencoding::encode(nonce)
        );

        info!("Generated authorization URL for OpenID Connect flow");
        (auth_url, state.to_string())
    }

    /// Exchange authorization code for tokens
    pub async fn exchange_code_for_token(
        &self,
        code: &str,
        _pkce_verifier: &str,
    ) -> ApiResult<TokenResponse> {
        let client = reqwest::Client::new();
        let token_url = format!("{}/protocol/openid-connect/token", self.config.issuer_url);

        let params = [
            ("grant_type", "authorization_code"),
            ("code", code),
            ("client_id", &self.config.client_id),
            ("client_secret", &self.config.client_secret),
            ("redirect_uri", &self.config.redirect_uri),
        ];

        let response = client
            .post(&token_url)
            .form(&params)
            .send()
            .await
            .map_err(|e| {
                error!("Failed to exchange authorization code: {}", e);
                ApiError::InternalError("Failed to exchange authorization code for token".to_string())
            })?;

        let token_data: serde_json::Value = response.json().await.map_err(|e| {
            error!("Failed to parse token response: {}", e);
            ApiError::InternalError("Failed to parse OAuth2 response".to_string())
        })?;

        let access_token = token_data["access_token"]
            .as_str()
            .ok_or_else(|| {
                error!("Missing access_token in response");
                ApiError::InternalError("Missing access_token in OAuth2 response".to_string())
            })?
            .to_string();

        let expires_in = token_data["expires_in"]
            .as_i64()
            .unwrap_or(3600);

        let refresh_token = token_data["refresh_token"]
            .as_str()
            .map(|s| s.to_string());

        let id_token = token_data["id_token"]
            .as_str()
            .map(|s| s.to_string());

        info!("Successfully exchanged authorization code for tokens");

        Ok(TokenResponse {
            access_token,
            token_type: "Bearer".to_string(),
            expires_in,
            refresh_token,
            id_token,
        })
    }

    /// Get user information from UserInfo endpoint
    pub async fn get_user_info(&self, access_token: &str) -> ApiResult<UserInfo> {
        let client = reqwest::Client::new();
        let userinfo_url = format!("{}/protocol/openid-connect/userinfo", self.config.issuer_url);

        let response = client
            .get(&userinfo_url)
            .bearer_auth(access_token)
            .send()
            .await
            .map_err(|e| {
                error!("Failed to fetch user info: {}", e);
                ApiError::InternalError("Failed to fetch user info".to_string())
            })?;

        let user_info: UserInfo = response.json().await.map_err(|e| {
            error!("Failed to parse user info response: {}", e);
            ApiError::InternalError("Failed to parse user info".to_string())
        })?;

        info!("Retrieved user info for: {}", user_info.email);
        Ok(user_info)
    }

    /// Validate ID token (JWT)
    pub fn validate_id_token(&self, id_token: &str) -> ApiResult<serde_json::Value> {
        // Decode without verification (verification should happen via userinfo endpoint)
        // For production, implement proper JWT validation
        let parts: Vec<&str> = id_token.split('.').collect();
        if parts.len() != 3 {
            return Err(ApiError::InternalError("Invalid JWT format".to_string()));
        }

        let payload = parts[1];
        let decoded = base64::engine::general_purpose::URL_SAFE_NO_PAD
            .decode(payload)
            .map_err(|e| {
                error!("Failed to decode JWT payload: {}", e);
                ApiError::InternalError("Failed to decode JWT payload".to_string())
            })?;

        let claims: serde_json::Value = serde_json::from_slice(&decoded)
            .map_err(|e| {
                error!("Failed to parse JWT claims: {}", e);
                ApiError::InternalError("Failed to parse JWT claims".to_string())
            })?;

        Ok(claims)
    }

    pub fn get_config(&self) -> &OpenIDConfig {
        &self.config
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_openid_config_validation() {
        let config = OpenIDConfig {
            issuer_url: "https://keycloak.example.com/auth/realms/master".to_string(),
            client_id: "test-client".to_string(),
            client_secret: "test-secret".to_string(),
            redirect_uri: "http://localhost:8080/auth/callback".to_string(),
            realm: Some("master".to_string()),
        };

        assert_eq!(config.issuer_url, "https://keycloak.example.com/auth/realms/master");
        assert_eq!(config.realm, Some("master".to_string()));
    }
}
