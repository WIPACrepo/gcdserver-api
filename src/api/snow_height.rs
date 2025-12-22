// Snow height endpoints
use actix_web::{web, HttpResponse};
use chrono::Utc;
use mongodb::bson::{doc, to_document};
use log::info;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::{ApiError, ApiResult};
use crate::models::{SnowHeight, CreateSnowHeightRequest, ApiResponse};

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/snow-height")
            .route("", web::get().to(get_all_snow_heights))
            .route("", web::post().to(create_snow_height))
            .route("/{run_number}", web::get().to(get_snow_height_by_run))
            .route("/{run_number}", web::put().to(update_snow_height))
            .route("/{run_number}", web::delete().to(delete_snow_height))
    );
}

async fn get_all_snow_heights(
    mongo: web::Data<MongoClient>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<SnowHeight>("snow_height");

    let snow_heights = collection
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} snow height records", snow_heights.len());
    Ok(HttpResponse::Ok().json(ApiResponse::success(snow_heights)))
}

async fn create_snow_height(
    mongo: web::Data<MongoClient>,
    req: web::Json<CreateSnowHeightRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<SnowHeight>("snow_height");

    let snow_height = SnowHeight {
        id: None,
        run_number: req.run_number,
        height: req.height,
        timestamp: Utc::now(),
    };

    let result = collection.insert_one(&snow_height, None).await?;
    info!(
        "Created snow height record for run {}: {:?}",
        req.run_number, result.inserted_id
    );

    Ok(HttpResponse::Created().json(ApiResponse::success(snow_height)))
}

async fn get_snow_height_by_run(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<SnowHeight>("snow_height");

    let snow_height = collection
        .find_one(doc! { "run_number": *run_number }, None)
        .await?
        .ok_or_else(|| {
            ApiError::NotFound(format!("Snow height not found for run {}", run_number))
        })?;

    info!("Retrieved snow height for run {}", run_number);
    Ok(HttpResponse::Ok().json(ApiResponse::success(snow_height)))
}

async fn update_snow_height(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
    req: web::Json<CreateSnowHeightRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<SnowHeight>("snow_height");

    let updated_snow_height = SnowHeight {
        id: None,
        run_number: *run_number,
        height: req.height,
        timestamp: Utc::now(),
    };

    collection
        .update_one(
            doc! { "run_number": *run_number },
            doc! { "$set": to_document(&updated_snow_height)? },
            None,
        )
        .await?;

    info!("Updated snow height for run {}", run_number);
    Ok(HttpResponse::Ok().json(ApiResponse::success(updated_snow_height)))
}

async fn delete_snow_height(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<SnowHeight>("snow_height");

    let result = collection
        .delete_one(doc! { "run_number": *run_number }, None)
        .await?;

    if result.deleted_count == 0 {
        return Err(ApiError::NotFound(format!(
            "Snow height not found for run {}",
            run_number
        )));
    }

    info!("Deleted snow height for run {}", run_number);
    Ok(HttpResponse::Ok().json(ApiResponse::<()>::success(())))
}
