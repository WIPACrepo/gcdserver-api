// Keycloak OAuth2 integration
use serde::{Deserialize, Serialize};
use log::{info, error};

use crate::errors::{ApiError, ApiResult};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeycloakConfig {
    /// Keycloak issuer URL (e.g., https://keycloak.example.com/auth/realms/master)
    pub issuer_url: String,
    /// OAuth2 Client ID
    pub client_id: String,
    /// OAuth2 Client Secret
    pub client_secret: String,
    /// Redirect URI after authentication
    pub redirect_uri: String,
}

#[derive(Debug, Deserialize)]
pub struct TokenResponse {
    pub access_token: String,
    pub token_type: String,
    pub expires_in: i64,
    pub refresh_token: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UserInfo {
    pub sub: String,
    pub email: String,
    pub name: Option<String>,
    pub preferred_username: Option<String>,
    /// Keycloak specific: realm roles
    pub realm_access: Option<RealmAccess>,
}

#[derive(Debug, Deserialize)]
pub struct RealmAccess {
    pub roles: Vec<String>,
}

pub struct KeycloakProvider {
    config: KeycloakConfig,
}

impl KeycloakProvider {
    /// Create new Keycloak provider
    pub async fn new(config: KeycloakConfig) -> ApiResult<Self> {
        info!("Initializing Keycloak provider: {}", config.issuer_url);

        // Verify issuer is reachable
        let discovery_url = format!("{}/.well-known/openid-configuration", config.issuer_url);
        let response = reqwest::Client::new()
            .get(&discovery_url)
            .send()
            .await
            .map_err(|e| {
                error!("Failed to reach Keycloak: {}", e);
                ApiError::InternalError("Keycloak unreachable".to_string())
            })?;

        if !response.status().is_success() {
            error!("Keycloak discovery failed with status: {}", response.status());
            return Err(ApiError::InternalError(
                "Keycloak discovery failed".to_string(),
            ));
        }

        info!("Keycloak verified at: {}", config.issuer_url);
        Ok(KeycloakProvider { config })
    }

    /// Get authorization URL for user login
    pub fn authorization_url(&self, state: &str) -> String {
        let scope = urlencoding::encode("openid email profile");
        let redirect_uri = urlencoding::encode(&self.config.redirect_uri);
        let client_id = urlencoding::encode(&self.config.client_id);
        
        format!(
            "{}/protocol/openid-connect/auth?client_id={}&redirect_uri={}&response_type=code&scope={}",
            self.config.issuer_url, client_id, redirect_uri, scope
        )
    }

    /// Exchange authorization code for tokens
    pub async fn token_exchange(
        &self,
        code: &str,
    ) -> ApiResult<TokenResponse> {
        let token_url = format!("{}/protocol/openid-connect/token", self.config.issuer_url);

        let params = [
            ("grant_type", "authorization_code"),
            ("code", code),
            ("client_id", &self.config.client_id),
            ("client_secret", &self.config.client_secret),
            ("redirect_uri", &self.config.redirect_uri),
        ];

        let response = reqwest::Client::new()
            .post(&token_url)
            .form(&params)
            .send()
            .await
            .map_err(|e| {
                error!("Token exchange failed: {}", e);
                ApiError::InternalError("Token exchange failed".to_string())
            })?;

        let token_data: serde_json::Value = response.json().await.map_err(|e| {
            error!("Failed to parse token response: {}", e);
            ApiError::InternalError("Invalid token response".to_string())
        })?;

        let access_token = token_data["access_token"]
            .as_str()
            .ok_or_else(|| {
                error!("Missing access_token");
                ApiError::InternalError("Missing access_token".to_string())
            })?
            .to_string();

        let expires_in = token_data["expires_in"].as_i64().unwrap_or(3600);
        let refresh_token = token_data["refresh_token"].as_str().map(|s| s.to_string());

        info!("Token exchange successful");

        Ok(TokenResponse {
            access_token,
            token_type: "Bearer".to_string(),
            expires_in,
            refresh_token,
        })
    }

    /// Get user information from Keycloak userinfo endpoint
    pub async fn user_info(&self, access_token: &str) -> ApiResult<UserInfo> {
        let userinfo_url = format!("{}/protocol/openid-connect/userinfo", self.config.issuer_url);

        let response = reqwest::Client::new()
            .get(&userinfo_url)
            .bearer_auth(access_token)
            .send()
            .await
            .map_err(|e| {
                error!("Failed to fetch user info: {}", e);
                ApiError::InternalError("Failed to fetch user info".to_string())
            })?;

        let user_info: UserInfo = response.json().await.map_err(|e| {
            error!("Failed to parse user info: {}", e);
            ApiError::InternalError("Failed to parse user info".to_string())
        })?;

        info!("Retrieved user info for: {}", user_info.email);
        Ok(user_info)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_keycloak_config() {
        let config = KeycloakConfig {
            issuer_url: "https://keycloak.example.com/auth/realms/master".to_string(),
            client_id: "test-client".to_string(),
            client_secret: "test-secret".to_string(),
            redirect_uri: "http://localhost:8080/auth/callback".to_string(),
        };

        assert!(!config.issuer_url.is_empty());
        assert!(!config.client_id.is_empty());
    }
}
