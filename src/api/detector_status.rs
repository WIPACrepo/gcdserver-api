// Detector Status endpoints
use actix_web::{web, HttpResponse};
use chrono::Utc;
use mongodb::bson::{doc, to_document};
use log::info;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::ApiResult;
use crate::models::{DetectorStatus, CreateDetectorStatusRequest, ApiResponse};

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/detector-status")
            .route("", web::get().to(get_all_detector_status))
            .route("", web::post().to(create_detector_status))
            .route("/{dom_id}", web::get().to(get_detector_status_by_dom))
            .route("/{dom_id}", web::put().to(update_detector_status))
            .route("/{dom_id}", web::delete().to(delete_detector_status))
            .route("/bad-doms", web::get().to(get_bad_doms))
    );
}

async fn get_all_detector_status(
    mongo: web::Data<MongoClient>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<DetectorStatus>("detector_status");

    let statuses = collection
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} detector status entries", statuses.len());
    Ok(HttpResponse::Ok().json(ApiResponse::success(statuses)))
}

async fn create_detector_status(
    mongo: web::Data<MongoClient>,
    req: web::Json<CreateDetectorStatusRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<DetectorStatus>("detector_status");

    let status = DetectorStatus {
        id: None,
        dom_id: req.dom_id,
        status: req.status.clone(),
        is_bad: req.is_bad,
        timestamp: Utc::now(),
    };

    let result = collection.insert_one(&status, None).await?;
    info!("Created detector status for DOM {}: {:?}", req.dom_id, result.inserted_id);

    Ok(HttpResponse::Created().json(ApiResponse::success(status)))
}

async fn get_detector_status_by_dom(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<DetectorStatus>("detector_status");

    let status = collection
        .find_one(doc! { "dom_id": *dom_id }, None)
        .await?
        .ok_or_else(|| crate::errors::ApiError::NotFound(
            format!("Detector status not found for DOM {}", dom_id)
        ))?;

    info!("Retrieved detector status for DOM {}", dom_id);
    Ok(HttpResponse::Ok().json(ApiResponse::success(status)))
}

async fn update_detector_status(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
    req: web::Json<CreateDetectorStatusRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<DetectorStatus>("detector_status");

    let updated_status = DetectorStatus {
        id: None,
        dom_id: *dom_id,
        status: req.status.clone(),
        is_bad: req.is_bad,
        timestamp: Utc::now(),
    };

    collection
        .update_one(
            doc! { "dom_id": *dom_id },
            doc! { "$set": to_document(&updated_status)? },
            None,
        )
        .await?;

    info!("Updated detector status for DOM {}", dom_id);
    Ok(HttpResponse::Ok().json(ApiResponse::success(updated_status)))
}

async fn delete_detector_status(
    mongo: web::Data<MongoClient>,
    dom_id: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<DetectorStatus>("detector_status");

    collection
        .delete_one(doc! { "dom_id": *dom_id }, None)
        .await?;

    info!("Deleted detector status for DOM {}", dom_id);
    Ok(HttpResponse::NoContent().finish())
}

async fn get_bad_doms(
    mongo: web::Data<MongoClient>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<DetectorStatus>("detector_status");

    let bad_doms = collection
        .find(doc! { "is_bad": true }, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} bad DOMs", bad_doms.len());
    Ok(HttpResponse::Ok().json(ApiResponse::success(bad_doms)))
}
