// Main entry point for GCDServer REST API
mod api;
mod auth;
mod db;
mod errors;
mod models;

use actix_web::{web, App, HttpServer, middleware};
use env_logger::Env;
use log::info;
use db::MongoClient;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv::dotenv().ok();
    env_logger::Builder::from_env(Env::default().default_filter_or("info")).init();

    let mongodb_uri = std::env::var("MONGODB_URI")
        .unwrap_or_else(|_| "mongodb://localhost:27017".to_string());
    let database_name = std::env::var("DATABASE_NAME")
        .unwrap_or_else(|_| "gcdserver".to_string());

    info!("Connecting to MongoDB at {}", mongodb_uri);
    
    let mongo_client = MongoClient::new(&mongodb_uri, &database_name)
        .await
        .expect("Failed to initialize MongoDB client");

    let mongo_data = web::Data::new(mongo_client);

    info!("Starting GCDServer REST API on http://0.0.0.0:8080");

    HttpServer::new(move || {
        App::new()
            .app_data(mongo_data.clone())
            .wrap(middleware::Logger::default())
            .configure(api::health::routes)
            .configure(api::auth::routes)
            .configure(api::gcd::routes)
            .configure(api::calibration::routes)
            .configure(api::geometry::routes)
            .configure(api::detector_status::routes)
            .configure(api::configuration::routes)
    })
    .bind("0.0.0.0:8080")?
    .run()
    .await
}
