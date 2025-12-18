// Data models
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use bson::oid::ObjectId;

// Calibration Models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Calibration {
    #[serde(rename = "_id", skip_serializing_if = "Option::is_none")]
    pub id: Option<ObjectId>,
    pub dom_id: u32,
    pub domcal: DOMCal,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DOMCal {
    pub atwd_gain: Vec<f64>,
    pub atwd_freq: Vec<f64>,
    pub fadc_gain: f64,
    pub fadc_freq: f64,
    pub pmt_gain: f64,
    pub transit_time: f64,
    pub relative_pmt_gain: f64,
}

// Geometry Models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Geometry {
    #[serde(rename = "_id", skip_serializing_if = "Option::is_none")]
    pub id: Option<ObjectId>,
    pub string: u32,
    pub position: u32,
    pub location: GeoLocation,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeoLocation {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

// Detector Status Models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectorStatus {
    #[serde(rename = "_id", skip_serializing_if = "Option::is_none")]
    pub id: Option<ObjectId>,
    pub dom_id: u32,
    pub status: String,
    pub is_bad: bool,
    pub timestamp: DateTime<Utc>,
}

// Configuration Models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Configuration {
    #[serde(rename = "_id", skip_serializing_if = "Option::is_none")]
    pub id: Option<ObjectId>,
    pub key: String,
    pub value: serde_json::Value,
    pub timestamp: DateTime<Utc>,
}

// Request/Response Models
#[derive(Debug, Deserialize)]
pub struct CreateCalibrationRequest {
    pub dom_id: u32,
    pub domcal: DOMCal,
}

#[derive(Debug, Deserialize)]
pub struct CreateGeometryRequest {
    pub string: u32,
    pub position: u32,
    pub location: GeoLocation,
}

#[derive(Debug, Deserialize)]
pub struct CreateDetectorStatusRequest {
    pub dom_id: u32,
    pub status: String,
    pub is_bad: bool,
}

#[derive(Debug, Deserialize)]
pub struct CreateConfigurationRequest {
    pub key: String,
    pub value: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T: Serialize> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        ApiResponse {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(error: String) -> ApiResponse<()> {
        ApiResponse {
            success: false,
            data: None,
            error: Some(error),
        }
    }
}
