// Keycloak authentication endpoints
use actix_web::{web, HttpResponse, HttpRequest};
use serde_json::json;
use uuid::Uuid;
use log::info;

use crate::auth::oauth2::{KeycloakProvider, KeycloakConfig};
use crate::auth::middleware::KeycloakClaims;
use crate::errors::{ApiError, ApiResult};

#[derive(serde::Deserialize)]
pub struct OAuth2CallbackQuery {
    pub code: String,
    pub state: String,
}

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/auth")
            .route("/login", web::post().to(login))
            .route("/callback", web::get().to(oauth2_callback))
            .route("/verify", web::get().to(verify_token))
    );
}

async fn login() -> ApiResult<HttpResponse> {
    let keycloak_issuer = std::env::var("KEYCLOAK_ISSUER_URL")
        .unwrap_or_else(|_| "http://localhost:8080/auth/realms/master".to_string());
    let keycloak_client_id = std::env::var("KEYCLOAK_CLIENT_ID")
        .unwrap_or_else(|_| "gcdserver-api".to_string());
    let keycloak_client_secret = std::env::var("KEYCLOAK_CLIENT_SECRET")
        .unwrap_or_else(|_| "change-me-in-production".to_string());
    let redirect_uri = std::env::var("KEYCLOAK_REDIRECT_URI")
        .unwrap_or_else(|_| "http://localhost:8080/auth/callback".to_string());

    let config = KeycloakConfig {
        issuer_url: keycloak_issuer,
        client_id: keycloak_client_id,
        client_secret: keycloak_client_secret,
        redirect_uri,
    };

    let provider = KeycloakProvider::new(config).await?;
    let state = Uuid::new_v4().to_string();
    let auth_url = provider.authorization_url(&state);

    info!("Generated authorization URL");
    Ok(HttpResponse::Ok().json(json!({
        "authorization_url": auth_url,
        "state": state
    })))
}

async fn oauth2_callback(
    query: web::Query<OAuth2CallbackQuery>,
) -> ApiResult<HttpResponse> {
    info!("OAuth2 callback received with state: {}", query.state);

    let keycloak_issuer = std::env::var("KEYCLOAK_ISSUER_URL")
        .unwrap_or_else(|_| "http://localhost:8080/auth/realms/master".to_string());
    let keycloak_client_id = std::env::var("KEYCLOAK_CLIENT_ID")
        .unwrap_or_else(|_| "gcdserver-api".to_string());
    let keycloak_client_secret = std::env::var("KEYCLOAK_CLIENT_SECRET")
        .unwrap_or_else(|_| "change-me-in-production".to_string());
    let redirect_uri = std::env::var("KEYCLOAK_REDIRECT_URI")
        .unwrap_or_else(|_| "http://localhost:8080/auth/callback".to_string());

    let config = KeycloakConfig {
        issuer_url: keycloak_issuer,
        client_id: keycloak_client_id,
        client_secret: keycloak_client_secret,
        redirect_uri,
    };

    let provider = KeycloakProvider::new(config).await?;

    // Exchange code for Keycloak tokens
    let token_response = provider.token_exchange(&query.code).await?;

    // Get user info
    let user_info = provider.user_info(&token_response.access_token).await?;

    info!("Successfully authenticated user: {}", user_info.email);

    Ok(HttpResponse::Ok().json(json!({
        "access_token": token_response.access_token,
        "token_type": token_response.token_type,
        "expires_in": token_response.expires_in,
        "refresh_token": token_response.refresh_token,
        "user": {
            "id": user_info.sub,
            "email": user_info.email,
            "name": user_info.name,
            "username": user_info.preferred_username,
            "roles": user_info.realm_access.map(|ra| ra.roles).unwrap_or_default()
        }
    })))
}

async fn verify_token(req: HttpRequest) -> ApiResult<HttpResponse> {
    // Extract claims from request extensions (inserted by middleware)
    let claims = req
        .extensions()
        .get::<KeycloakClaims>()
        .cloned()
        .ok_or_else(|| ApiError::InternalError("No valid token found".to_string()))?;

    info!("Token verified for user: {}", claims.sub);
    
    Ok(HttpResponse::Ok().json(json!({
        "valid": true,
        "user_id": claims.sub,
        "email": claims.email,
        "roles": claims.realm_access.map(|ra| ra.roles).unwrap_or_default()
    })))
}
