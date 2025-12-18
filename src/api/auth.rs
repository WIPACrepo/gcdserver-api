// OAuth2 and Authentication endpoints with Keycloak OpenID Connect support
use actix_web::{web, HttpResponse, HttpRequest};
use serde_json::json;
use uuid::Uuid;
use log::info;

use crate::auth::jwt::JwtManager;
use crate::auth::oauth2::{OpenIDProvider, OpenIDConfig};
use crate::errors::{ApiError, ApiResult};

#[derive(serde::Deserialize)]
pub struct OAuth2CallbackQuery {
    pub code: String,
    pub state: String,
}

#[derive(serde::Deserialize)]
pub struct LoginRequest {
    pub nonce: Option<String>,
}

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/auth")
            .route("/login", web::post().to(login))
            .route("/callback", web::get().to(oauth2_callback))
            .route("/refresh", web::post().to(refresh_token))
            .route("/logout", web::post().to(logout))
            .route("/verify", web::get().to(verify_token))
    );
}

async fn login(
    _jwt_manager: web::Data<JwtManager>,
    req: web::Json<LoginRequest>,
) -> ApiResult<HttpResponse> {
    let keycloak_issuer = std::env::var("KEYCLOAK_ISSUER_URL")
        .unwrap_or_else(|_| "http://localhost:8080/auth/realms/master".to_string());
    let keycloak_client_id = std::env::var("KEYCLOAK_CLIENT_ID")
        .unwrap_or_else(|_| "gcdserver-api".to_string());
    let keycloak_client_secret = std::env::var("KEYCLOAK_CLIENT_SECRET")
        .unwrap_or_else(|_| "change-me-in-production".to_string());
    let redirect_uri = std::env::var("KEYCLOAK_REDIRECT_URI")
        .unwrap_or_else(|_| "http://localhost:8080/auth/callback".to_string());

    let config = OpenIDConfig {
        issuer_url: keycloak_issuer,
        client_id: keycloak_client_id,
        client_secret: keycloak_client_secret,
        redirect_uri,
        realm: None,
    };

    // Initialize OpenID Connect provider
    let provider = OpenIDProvider::from_keycloak(config).await?;

    let nonce = req.nonce.clone().unwrap_or_else(|| Uuid::new_v4().to_string());
    let state = Uuid::new_v4().to_string();
    
    let (auth_url, _pkce_verifier) = provider.get_authorization_url(&nonce, &state);

    info!("Generated OpenID Connect authorization URL");
    Ok(HttpResponse::Ok().json(json!({
        "authorization_url": auth_url,
        "state": state,
        "nonce": nonce
    })))
}

async fn oauth2_callback(
    query: web::Query<OAuth2CallbackQuery>,
    jwt_manager: web::Data<JwtManager>,
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

    let config = OpenIDConfig {
        issuer_url: keycloak_issuer,
        client_id: keycloak_client_id,
        client_secret: keycloak_client_secret,
        redirect_uri,
        realm: None,
    };

    // Initialize OpenID Connect provider
    let provider = OpenIDProvider::from_keycloak(config).await?;

    // Exchange authorization code for tokens
    let token_response = provider
        .exchange_code_for_token(&query.code, "")
        .await?;

    // Get user info from Keycloak
    let user_info = provider.get_user_info(&token_response.access_token).await?;

    info!("Successfully authenticated user: {}", user_info.email);

    // Map Keycloak roles to API scopes
    let scopes = user_info
        .realm_access
        .map(|ra| ra.roles)
        .unwrap_or_else(|| vec!["read".to_string()]);

    // Generate our internal JWT token
    let jwt_token = jwt_manager.generate_token(
        &user_info.sub,
        &user_info.email,
        scopes,
        "keycloak",
    )?;

    Ok(HttpResponse::Ok().json(json!({
        "access_token": jwt_token.access_token,
        "token_type": jwt_token.token_type,
        "expires_in": jwt_token.expires_in,
        "user": {
            "id": user_info.sub,
            "email": user_info.email,
            "name": user_info.name,
            "username": user_info.preferred_username,
        }
    })))
}

async fn refresh_token(
    jwt_manager: web::Data<JwtManager>,
    req: HttpRequest,
) -> ApiResult<HttpResponse> {
    // Extract refresh token from request
    let auth_header = req
        .headers()
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .ok_or_else(|| ApiError::InternalError("Missing refresh token".to_string()))?;

    if !auth_header.starts_with("Bearer ") {
        return Err(ApiError::InternalError("Invalid token format".to_string()));
    }

    let refresh_token = auth_header.trim_start_matches("Bearer ");
    
    // Verify the refresh token
    let claims = jwt_manager.verify_token(refresh_token)?;

    // Generate new access token
    let token_response = jwt_manager.generate_token(
        &claims.sub,
        &claims.email,
        claims.scopes,
        &claims.provider,
    )?;

    info!("Token refreshed for user: {}", claims.sub);
    Ok(HttpResponse::Ok().json(token_response))
}

async fn logout(req: HttpRequest) -> ApiResult<HttpResponse> {
    // Extract token
    let _auth_header = req
        .headers()
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .ok_or_else(|| ApiError::InternalError("Missing token".to_string()))?;

    // In production, invalidate token in blacklist/cache
    info!("User logged out");
    Ok(HttpResponse::Ok().json(json!({
        "message": "Successfully logged out"
    })))
}

async fn verify_token(
    jwt_manager: web::Data<JwtManager>,
    req: HttpRequest,
) -> ApiResult<HttpResponse> {
    let auth_header = req
        .headers()
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .ok_or_else(|| ApiError::InternalError("Missing token".to_string()))?;

    if !auth_header.starts_with("Bearer ") {
        return Err(ApiError::InternalError("Invalid token format".to_string()));
    }

    let token = auth_header.trim_start_matches("Bearer ");
    let claims = jwt_manager.verify_token(token)?;

    info!("Token verified for user: {}", claims.sub);
    Ok(HttpResponse::Ok().json(json!({
        "valid": true,
        "user_id": claims.sub,
        "email": claims.email,
        "scopes": claims.scopes,
        "provider": claims.provider,
    })))
}
