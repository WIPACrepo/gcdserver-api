// JWT token handling
use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use log::{info, error};

use crate::errors::{ApiError, ApiResult};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,           // Subject (user ID)
    pub email: String,
    pub scopes: Vec<String>,   // OAuth2 scopes
    pub exp: i64,              // Expiration time
    pub iat: i64,              // Issued at
    pub jti: String,           // JWT ID (unique token identifier)
    pub provider: String,      // OAuth2 provider (e.g., "google", "github")
}

#[derive(Debug, Serialize)]
pub struct TokenResponse {
    pub access_token: String,
    pub token_type: String,
    pub expires_in: i64,
    pub refresh_token: Option<String>,
}

pub struct JwtManager {
    encoding_key: EncodingKey,
    decoding_key: DecodingKey,
    expiration_hours: i64,
}

impl JwtManager {
    pub fn new(secret: &str, expiration_hours: i64) -> Self {
        JwtManager {
            encoding_key: EncodingKey::from_secret(secret.as_ref()),
            decoding_key: DecodingKey::from_secret(secret.as_ref()),
            expiration_hours,
        }
    }

    pub fn generate_token(
        &self,
        user_id: &str,
        email: &str,
        scopes: Vec<String>,
        provider: &str,
    ) -> ApiResult<TokenResponse> {
        let now = Utc::now();
        let expires_at = now + Duration::hours(self.expiration_hours);

        let claims = Claims {
            sub: user_id.to_string(),
            email: email.to_string(),
            scopes,
            exp: expires_at.timestamp(),
            iat: now.timestamp(),
            jti: Uuid::new_v4().to_string(),
            provider: provider.to_string(),
        };

        let token = encode(&Header::default(), &claims, &self.encoding_key)
            .map_err(|e| {
                error!("Failed to generate JWT: {}", e);
                ApiError::InternalError("Failed to generate token".to_string())
            })?;

        info!("Generated JWT token for user: {}", user_id);

        Ok(TokenResponse {
            access_token: token,
            token_type: "Bearer".to_string(),
            expires_in: self.expiration_hours * 3600,
            refresh_token: None,
        })
    }

    pub fn verify_token(&self, token: &str) -> ApiResult<Claims> {
        decode::<Claims>(token, &self.decoding_key, &Validation::default())
            .map(|data| data.claims)
            .map_err(|e| {
                error!("Failed to verify JWT: {}", e);
                ApiError::InternalError("Invalid or expired token".to_string())
            })
    }

    pub fn has_scope(&self, claims: &Claims, required_scope: &str) -> bool {
        claims.scopes.iter().any(|s| s == required_scope)
    }

    pub fn has_any_scope(&self, claims: &Claims, required_scopes: &[&str]) -> bool {
        claims.scopes.iter().any(|s| required_scopes.contains(&s.as_str()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_generation_and_verification() {
        let jwt_manager = JwtManager::new("test_secret", 1);
        
        let token_response = jwt_manager
            .generate_token("user123", "user@example.com", vec!["read".to_string()], "test_provider")
            .expect("Failed to generate token");
        
        let claims = jwt_manager
            .verify_token(&token_response.access_token)
            .expect("Failed to verify token");
        
        assert_eq!(claims.sub, "user123");
        assert_eq!(claims.email, "user@example.com");
        assert!(claims.scopes.contains(&"read".to_string()));
    }
}
