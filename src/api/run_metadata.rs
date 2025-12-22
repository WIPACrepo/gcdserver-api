// Run metadata endpoints - Store run-specific context (start time, end time, configuration)
// Used by GCD generator to intelligently filter calibrations and other time-dependent data
use actix_web::{web, HttpResponse, HttpRequest, HttpMessage};
use mongodb::bson::{doc, to_document};
use log::info;
use serde_json::json;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::{ApiError, ApiResult};
use crate::models::{RunMetadata, CreateRunMetadataRequest, ApiResponse};
use crate::auth::middleware::KeycloakClaims;

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/run-metadata")
            .route("", web::get().to(get_all_run_metadata))
            .route("/{run_number}", web::get().to(get_run_metadata))
            .route("", web::post().to(create_run_metadata))
            .route("/{run_number}", web::put().to(update_run_metadata))
            .route("/{run_number}", web::delete().to(delete_run_metadata))
    );
}

/// Get all run metadata entries
async fn get_all_run_metadata(
    mongo: web::Data<MongoClient>,
    _req: HttpRequest,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<RunMetadata>("run_metadata");

    let metadata = collection
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} run metadata entries", metadata.len());

    Ok(HttpResponse::Ok().json(ApiResponse::success(metadata)))
}

/// Get metadata for a specific run number
async fn get_run_metadata(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
    _req: HttpRequest,
) -> ApiResult<HttpResponse> {
    let run_num = run_number.into_inner();
    let db = mongo.get_database();
    let collection = db.collection::<RunMetadata>("run_metadata");

    let metadata = collection
        .find_one(doc! { "run_number": run_num as i32 }, None)
        .await?
        .ok_or_else(|| ApiError::NotFound(format!("Run {} not found", run_num)))?;

    info!("Retrieved metadata for run {}", run_num);

    Ok(HttpResponse::Ok().json(ApiResponse::success(metadata)))
}

/// Create a new run metadata entry
async fn create_run_metadata(
    mongo: web::Data<MongoClient>,
    req: HttpRequest,
    body: web::Json<CreateRunMetadataRequest>,
) -> ApiResult<HttpResponse> {
    // Extract claims for authorization
    let _claims = req
        .extensions()
        .get::<KeycloakClaims>()
        .cloned()
        .ok_or_else(|| ApiError::InternalError("Authentication required".to_string()))?;

    let db = mongo.get_database();
    let collection = db.collection::<RunMetadata>("run_metadata");

    // Check if run metadata already exists
    let existing = collection
        .find_one(doc! { "run_number": body.run_number as i32 }, None)
        .await?;

    if existing.is_some() {
        return Err(ApiError::ValidationError(
            format!("Run metadata for run {} already exists", body.run_number),
        ));
    }

    let metadata = RunMetadata {
        id: None,
        run_number: body.run_number,
        start_time: body.start_time,
        end_time: body.end_time,
        configuration_name: body.configuration_name.clone(),
        timestamp: chrono::Utc::now(),
    };

    let result = collection.insert_one(&metadata, None).await?;
    info!("Created run metadata for run {} with id {:?}", body.run_number, result.inserted_id);

    Ok(HttpResponse::Created().json(ApiResponse::success(metadata)))
}

/// Update an existing run metadata entry
async fn update_run_metadata(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
    req: HttpRequest,
    body: web::Json<CreateRunMetadataRequest>,
) -> ApiResult<HttpResponse> {
    // Extract claims for authorization
    let _claims = req
        .extensions()
        .get::<KeycloakClaims>()
        .cloned()
        .ok_or_else(|| ApiError::InternalError("Authentication required".to_string()))?;

    let run_num = run_number.into_inner();
    let db = mongo.get_database();
    let collection = db.collection::<RunMetadata>("run_metadata");

    // Check if metadata exists
    let _existing = collection
        .find_one(doc! { "run_number": run_num as i32 }, None)
        .await?
        .ok_or_else(|| ApiError::NotFound(format!("Run {} not found", run_num)))?;

    // Update the document
    let updated_doc = doc! {
        "$set": to_document(&RunMetadata {
            id: None,
            run_number: body.run_number,
            start_time: body.start_time,
            end_time: body.end_time,
            configuration_name: body.configuration_name.clone(),
            timestamp: chrono::Utc::now(),
        })?
    };

    collection
        .update_one(doc! { "run_number": run_num as i32 }, updated_doc, None)
        .await?;

    // Fetch and return the updated document
    let updated = collection
        .find_one(doc! { "run_number": run_num as i32 }, None)
        .await?
        .ok_or_else(|| ApiError::NotFound(format!("Run {} not found", run_num)))?;

    info!("Updated run metadata for run {}", run_num);

    Ok(HttpResponse::Ok().json(ApiResponse::success(updated)))
}

/// Delete a run metadata entry
async fn delete_run_metadata(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
    req: HttpRequest,
) -> ApiResult<HttpResponse> {
    // Extract claims for authorization
    let _claims = req
        .extensions()
        .get::<KeycloakClaims>()
        .cloned()
        .ok_or_else(|| ApiError::InternalError("Authentication required".to_string()))?;

    let run_num = run_number.into_inner();
    let db = mongo.get_database();
    let collection = db.collection::<RunMetadata>("run_metadata");

    let result = collection
        .delete_one(doc! { "run_number": run_num as i32 }, None)
        .await?;

    if result.deleted_count == 0 {
        return Err(ApiError::NotFound(format!("Run {} not found", run_num)));
    }

    info!("Deleted run metadata for run {}", run_num);

    Ok(HttpResponse::Ok().json(ApiResponse::success(json!({
        "deleted_count": result.deleted_count,
        "run_number": run_num
    }))))
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    #[test]
    fn test_run_metadata_creation() {
        let req = CreateRunMetadataRequest {
            run_number: 137292,
            start_time: Utc::now(),
            end_time: None,
            configuration_name: Some("test_config".to_string()),
        };

        assert_eq!(req.run_number, 137292);
        assert_eq!(req.configuration_name, Some("test_config".to_string()));
    }
}
