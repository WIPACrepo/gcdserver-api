// Health check endpoint
use actix_web::{web, HttpResponse};
use serde_json::json;

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/health")
            .route("", web::get().to(health_check))
    );
}

async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(json!({
        "status": "healthy",
        "service": "gcdserver-api",
    }))
}
