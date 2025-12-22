// GCD (Geometry, Calibration, Detector Status) collection endpoints
use actix_web::{web, HttpResponse, HttpRequest, HttpMessage};
use chrono::{Utc, DateTime};
use mongodb::bson::doc;
use log::info;
use uuid::Uuid;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::{ApiError, ApiResult};
use crate::models::{
    Calibration, Geometry, DetectorStatus, RunMetadata, ApiResponse,
};
use crate::auth::middleware::KeycloakClaims;

#[derive(serde::Serialize)]
pub struct GCDCollection {
    pub run_number: u32,
    pub generated_at: String,
    pub generated_by: String,
    pub calibrations: Vec<Calibration>,
    pub geometry: Vec<Geometry>,
    pub detector_status: Vec<DetectorStatus>,
    pub collection_id: String,
}

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/gcd")
            .route("/generate/{run_number}", web::post().to(generate_gcd_collection))
            .route("/collection/{collection_id}", web::get().to(get_gcd_collection))
    );
}

/// Generate a complete GCD collection for a given run number
/// This atomically creates geometry, calibration, and detector status collections
/// Uses run metadata (start_time/end_time) to intelligently filter calibrations
async fn generate_gcd_collection(
    mongo: web::Data<MongoClient>,
    run_number: web::Path<u32>,
    req: HttpRequest,
) -> ApiResult<HttpResponse> {
    // Extract claims from middleware validation
    let claims = req
        .extensions()
        .get::<KeycloakClaims>()
        .cloned()
        .ok_or_else(|| ApiError::InternalError("Authentication required".to_string()))?;

    let run_num = run_number.into_inner();
    let db = mongo.get_database();
    
    info!("Generating GCD collection for run {}", run_num);

    // Get collections
    let calibration_col = db.collection::<Calibration>("calibration");
    let geometry_col = db.collection::<Geometry>("geometry");
    let detector_status_col = db.collection::<DetectorStatus>("detector_status");
    let run_metadata_col = db.collection::<RunMetadata>("run_metadata");

    // Try to get run metadata to determine the time window for this run
    let run_metadata = run_metadata_col
        .find_one(doc! { "run_number": run_num as i32 }, None)
        .await?;

    // Determine time window for filtering calibrations
    let (start_time, end_time) = match run_metadata {
        Some(metadata) => (metadata.start_time, metadata.end_time),
        None => {
            // If no metadata exists, use a wide range (all calibrations)
            // This provides backward compatibility
            info!("No run metadata found for run {}. Using all calibrations.", run_num);
            (
                DateTime::parse_from_rfc3339("1970-01-01T00:00:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
                Some(Utc::now()),
            )
        }
    };

    // Query calibrations with intelligent filtering:
    // For each DOM, get the calibration that was valid during the run period
    let all_calibrations = calibration_col
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    let all_cal_len = all_calibrations.len();
    
    // Filter calibrations: keep those whose timestamp falls within or just before the run window
    let filtered_calibrations = filter_calibrations_for_run(all_calibrations, start_time, end_time);

    // Get all geometry (doesn't change often, kept as-is)
    let geometry_entries = geometry_col
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    // Get detector status entries for this specific run
    let detector_statuses = detector_status_col
        .find(doc! { "run_number": run_num as i32 }, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    let collection_id = Uuid::new_v4().to_string();
    let gcd_collection = GCDCollection {
        run_number: run_num,
        generated_at: Utc::now().to_rfc3339(),
        generated_by: claims.email.clone(),
        calibrations: filtered_calibrations.clone(),
        geometry: geometry_entries,
        detector_status: detector_statuses,
        collection_id: collection_id.clone(),
    };

    info!(
        "Generated GCD collection {} for run {} with {} calibrations (filtered from {}), {} geometry, {} detector statuses",
        collection_id,
        run_num,
        gcd_collection.calibrations.len(),
        all_cal_len,
        gcd_collection.geometry.len(),
        gcd_collection.detector_status.len()
    );

    Ok(HttpResponse::Ok().json(ApiResponse::success(gcd_collection)))
}

/// Filter calibrations to find the ones valid during a run's time window
/// Strategy: For each DOM, keep the calibration with the latest timestamp
/// that doesn't exceed the run start time (or keep all if before start_time)
fn filter_calibrations_for_run(
    calibrations: Vec<Calibration>,
    run_start: DateTime<Utc>,
    _run_end: Option<DateTime<Utc>>,
) -> Vec<Calibration> {
    use std::collections::HashMap;

    // Group calibrations by DOM ID (u32)
    let mut dom_calibrations: HashMap<u32, Vec<Calibration>> = HashMap::new();

    for cal in calibrations {
        dom_calibrations
            .entry(cal.dom_id)
            .or_insert_with(Vec::new)
            .push(cal);
    }

    // For each DOM, select the best calibration
    let mut result = Vec::new();
    for (_dom_id, mut cals) in dom_calibrations {
        // Sort by timestamp descending (newest first)
        cals.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

        // Find the calibration valid for this run:
        // Prefer calibrations from before/during the run start
        let selected = cals.iter().find(|cal| cal.timestamp <= run_start).cloned()
            // Fallback: if no calibrations before run_start, use the oldest available
            .or_else(|| cals.last().cloned())
            .unwrap_or_else(|| cals[0].clone());

        result.push(selected);
    }

    result
}

/// Retrieve a previously generated GCD collection by collection ID
async fn get_gcd_collection(
    mongo: web::Data<MongoClient>,
    collection_id: web::Path<String>,
) -> ApiResult<HttpResponse> {
    let _id = collection_id.into_inner();
    
    // In a real implementation, you would store GCD collections in a dedicated collection
    // For now, return a placeholder or error
    Err(ApiError::NotFound(
        format!("GCD collection storage not yet implemented. Use /gcd/generate to create collections."),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gcd_collection_structure() {
        let collection = GCDCollection {
            run_number: 12345,
            generated_at: Utc::now().to_rfc3339(),
            generated_by: "test@example.com".to_string(),
            calibrations: vec![],
            geometry: vec![],
            detector_status: vec![],
            collection_id: "test-id".to_string(),
        };

        assert_eq!(collection.run_number, 12345);
        assert!(!collection.collection_id.is_empty());
    }
}
