// Configuration endpoints
use actix_web::{web, HttpResponse};
use chrono::Utc;
use mongodb::bson::{doc, to_document};
use log::info;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::ApiResult;
use crate::models::{Configuration, CreateConfigurationRequest, ApiResponse};

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/config")
            .route("", web::get().to(get_all_config))
            .route("", web::post().to(create_config))
            .route("/{key}", web::get().to(get_config_by_key))
            .route("/{key}", web::put().to(update_config))
            .route("/{key}", web::delete().to(delete_config))
    );
}

async fn get_all_config(
    mongo: web::Data<MongoClient>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Configuration>("configuration");

    let configs = collection
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} configuration entries", configs.len());
    Ok(HttpResponse::Ok().json(ApiResponse::success(configs)))
}

async fn create_config(
    mongo: web::Data<MongoClient>,
    req: web::Json<CreateConfigurationRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Configuration>("configuration");

    let config = Configuration {
        id: None,
        key: req.key.clone(),
        value: req.value.clone(),
        timestamp: Utc::now(),
    };

    let result = collection.insert_one(&config, None).await?;
    info!("Created configuration '{}': {:?}", req.key, result.inserted_id);

    Ok(HttpResponse::Created().json(ApiResponse::success(config)))
}

async fn get_config_by_key(
    mongo: web::Data<MongoClient>,
    key: web::Path<String>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Configuration>("configuration");

    let config = collection
        .find_one(doc! { "key": key.as_str() }, None)
        .await?
        .ok_or_else(|| crate::errors::ApiError::NotFound(
            format!("Configuration not found for key '{}'", key)
        ))?;

    info!("Retrieved configuration for key '{}'", key);
    Ok(HttpResponse::Ok().json(ApiResponse::success(config)))
}

async fn update_config(
    mongo: web::Data<MongoClient>,
    key: web::Path<String>,
    req: web::Json<CreateConfigurationRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Configuration>("configuration");

    let updated_config = Configuration {
        id: None,
        key: key.to_string(),
        value: req.value.clone(),
        timestamp: Utc::now(),
    };

    collection
        .update_one(
            doc! { "key": key.as_str() },
            doc! { "$set": to_document(&updated_config)? },
            None,
        )
        .await?;

    info!("Updated configuration for key '{}'", key);
    Ok(HttpResponse::Ok().json(ApiResponse::success(updated_config)))
}

async fn delete_config(
    mongo: web::Data<MongoClient>,
    key: web::Path<String>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Configuration>("configuration");

    collection
        .delete_one(doc! { "key": key.as_str() }, None)
        .await?;

    info!("Deleted configuration for key '{}'", key);
    Ok(HttpResponse::NoContent().finish())
}
