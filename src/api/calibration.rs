// Calibration endpoints
use actix_web::{web, HttpResponse};
use chrono::Utc;
use mongodb::bson::{doc, to_document};
use log::info;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::{ApiError, ApiResult};
use crate::models::{Calibration, CreateCalibrationRequest, ApiResponse};

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/calibration")
            .route("", web::get().to(get_all_calibrations))
            .route("", web::post().to(create_calibration))
            .route("/{dom_id}", web::get().to(get_calibration_by_dom))
            .route("/{dom_id}", web::put().to(update_calibration))
            .route("/{dom_id}", web::delete().to(delete_calibration))
            .route("/latest/{dom_id}", web::get().to(get_latest_calibration))
    );
}

async fn get_all_calibrations(
    mongo: web::Data<MongoClient>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Calibration>("calibration");

    let calibrations = collection
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} calibrations", calibrations.len());
    Ok(HttpResponse::Ok().json(ApiResponse::success(calibrations)))
}

async fn create_calibration(
    mongo: web::Data<MongoClient>,
    req: web::Json<CreateCalibrationRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Calibration>("calibration");

    let calibration = Calibration {
        id: None,
        dom_id: req.dom_id,
        domcal: req.domcal.clone(),
        timestamp: Utc::now(),
    };

    let result = collection.insert_one(&calibration, None).await?;
    info!("Created calibration for DOM {}: {:?}", req.dom_id, result.inserted_id);

    Ok(HttpResponse::Created().json(ApiResponse::success(calibration)))
}

async fn get_calibration_by_dom(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Calibration>("calibration");

    let calibration = collection
        .find_one(doc! { "dom_id": *dom_id }, None)
        .await?
        .ok_or_else(|| ApiError::NotFound(format!("Calibration not found for DOM {}", dom_id)))?;

    info!("Retrieved calibration for DOM {}", dom_id);
    Ok(HttpResponse::Ok().json(ApiResponse::success(calibration)))
}

async fn update_calibration(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
    req: web::Json<CreateCalibrationRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Calibration>("calibration");

    let updated_calibration = Calibration {
        id: None,
        dom_id: *dom_id,
        domcal: req.domcal.clone(),
        timestamp: Utc::now(),
    };

    collection
        .update_one(
            doc! { "dom_id": *dom_id },
            doc! { "$set": to_document(&updated_calibration)? },
            None,
        )
        .await?;

    info!("Updated calibration for DOM {}", dom_id);
    Ok(HttpResponse::Ok().json(ApiResponse::success(updated_calibration)))
}

async fn delete_calibration(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Calibration>("calibration");

    collection
        .delete_one(doc! { "dom_id": *dom_id }, None)
        .await?;

    info!("Deleted calibration for DOM {}", dom_id);
    Ok(HttpResponse::NoContent().finish())
}

async fn get_latest_calibration(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Calibration>("calibration");

    let calibration = collection
        .find_one(doc! { "dom_id": *dom_id }, None)
        .await?
        .ok_or_else(|| ApiError::NotFound(format!("Calibration not found for DOM {}", dom_id)))?;

    info!("Retrieved latest calibration for DOM {}", dom_id);
    Ok(HttpResponse::Ok().json(ApiResponse::success(calibration)))
}
