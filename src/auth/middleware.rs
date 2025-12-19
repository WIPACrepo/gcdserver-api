// Authentication middleware for validating Keycloak tokens
use actix_web::{
    dev::{forward_ready, Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage, HttpResponse, body::EitherBody,
};
use futures::future::LocalBoxFuture;
use jsonwebtoken::{decode, DecodingKey, Validation};
use serde::{Deserialize, Serialize};
use log::warn;
use std::rc::Rc;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct KeycloakClaims {
    pub sub: String,
    pub email: String,
    pub exp: i64,
    pub realm_access: Option<RealmAccess>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RealmAccess {
    pub roles: Vec<String>,
}

pub struct AuthMiddleware {
    /// Keycloak JWKS public key (fetched from issuer)
    public_key_pem: String,
}

impl AuthMiddleware {
    pub fn new(public_key_pem: String) -> Self {
        AuthMiddleware { public_key_pem }
    }
}

impl<S, B> Transform<S, ServiceRequest> for AuthMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<EitherBody<B>>;
    type Error = Error;
    type InitError = ();
    type Transform = AuthMiddlewareService<S>;
    type Future = std::future::Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        std::future::ready(Ok(AuthMiddlewareService {
            service: Rc::new(service),
            public_key_pem: self.public_key_pem.clone(),
        }))
    }
}

pub struct AuthMiddlewareService<S> {
    service: Rc<S>,
    public_key_pem: String,
}

impl<S, B> Service<ServiceRequest> for AuthMiddlewareService<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<EitherBody<B>>;
    type Error = Error;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    forward_ready!(service);

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let path = req.path();
        
        // Skip auth for public endpoints
        if path == "/health" || path.starts_with("/auth/") {
            let service = self.service.clone();
            return Box::pin(async move {
                service
                    .call(req)
                    .await
                    .map(|res| res.map_into_left_body())
            });
        }

        // Extract and validate bearer token
        let auth_header = match req.headers().get("Authorization") {
            Some(header) => match header.to_str() {
                Ok(value) => {
                    if value.starts_with("Bearer ") {
                        value.trim_start_matches("Bearer ").to_string()
                    } else {
                        warn!("Invalid Authorization header format");
                        return Box::pin(async move {
                            let (http_req, _) = req.into_parts();
                            Ok(ServiceResponse::new(
                                http_req,
                                HttpResponse::Unauthorized()
                                    .json(serde_json::json!({
                                        "error": "Invalid authorization header format"
                                    }))
                                    .map_into_right_body(),
                            ))
                        });
                    }
                }
                Err(_) => {
                    warn!("Failed to parse Authorization header");
                    return Box::pin(async move {
                        let (http_req, _) = req.into_parts();
                        Ok(ServiceResponse::new(
                            http_req,
                            HttpResponse::Unauthorized()
                                .json(serde_json::json!({
                                    "error": "Invalid authorization header"
                                }))
                                .map_into_right_body(),
                        ))
                    });
                }
            },
            None => {
                warn!("Missing Authorization header on protected route: {}", path);
                return Box::pin(async move {
                    let (http_req, _) = req.into_parts();
                    Ok(ServiceResponse::new(
                        http_req,
                        HttpResponse::Unauthorized()
                            .json(serde_json::json!({
                                "error": "Missing authorization header"
                            }))
                            .map_into_right_body(),
                    ))
                });
            }
        };

        // Validate token
        let public_key_pem = self.public_key_pem.clone();
        let token_validation = match DecodingKey::from_rsa_pem(public_key_pem.as_bytes()) {
            Ok(key) => key,
            Err(_) => {
                warn!("Failed to load public key");
                return Box::pin(async move {
                    let (http_req, _) = req.into_parts();
                    Ok(ServiceResponse::new(
                        http_req,
                        HttpResponse::InternalServerError()
                            .json(serde_json::json!({
                                "error": "Token validation unavailable"
                            }))
                            .map_into_right_body(),
                    ))
                });
            }
        };

        match decode::<KeycloakClaims>(
            &auth_header,
            &token_validation,
            &Validation::default(),
        ) {
            Ok(token_data) => {
                req.extensions_mut().insert(token_data.claims);
                let service = self.service.clone();
                Box::pin(async move {
                    service
                        .call(req)
                        .await
                        .map(|res| res.map_into_left_body())
                })
            }
            Err(_) => {
                warn!("Invalid or expired token");
                Box::pin(async move {
                    let (http_req, _) = req.into_parts();
                    Ok(ServiceResponse::new(
                        http_req,
                        HttpResponse::Unauthorized()
                            .json(serde_json::json!({
                                "error": "Invalid or expired token"
                            }))
                            .map_into_right_body(),
                    ))
                })
            }
        }
    }
}
