// Authentication middleware for extracting and validating JWT tokens
use actix_web::{
    dev::{forward_ready, Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage, HttpResponse, body::EitherBody,
};
use futures::future::LocalBoxFuture;
use log::warn;
use std::rc::Rc;

pub struct AuthMiddleware;

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
        }))
    }
}

pub struct AuthMiddlewareService<S> {
    service: Rc<S>,
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
        // Skip auth for health and oauth endpoints
        let path = req.path();
        if path == "/health" || path.starts_with("/oauth2") || path.starts_with("/auth/") {
            let service = self.service.clone();
            return Box::pin(async move {
                service
                    .call(req)
                    .await
                    .map(|res| res.map_into_left_body())
            });
        }

        // Extract bearer token
        let auth_header = req.headers().get("Authorization");
        
        let token = match auth_header {
            Some(header) => {
                match header.to_str() {
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
                                            "error": "Invalid authorization header format",
                                            "status": 401
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
                                        "error": "Invalid authorization header",
                                        "status": 401
                                    }))
                                    .map_into_right_body(),
                            ))
                        });
                    }
                }
            }
            None => {
                warn!("Missing Authorization header on protected route: {}", path);
                return Box::pin(async move {
                    let (http_req, _) = req.into_parts();
                    Ok(ServiceResponse::new(
                        http_req,
                        HttpResponse::Unauthorized()
                            .json(serde_json::json!({
                                "error": "Missing authorization header",
                                "status": 401
                            }))
                            .map_into_right_body(),
                    ))
                });
            }
        };

        // TODO: Verify token here
        // For now, we'll just attach the token to the request
        req.extensions_mut().insert(token);

        let service = self.service.clone();
        Box::pin(async move {
            service
                .call(req)
                .await
                .map(|res| res.map_into_left_body())
        })
    }
}
