// Error handling module
use actix_web::{error::ResponseError, http::StatusCode, HttpResponse};
use serde_json::json;
use std::fmt;

#[derive(Debug)]
pub enum ApiError {
    DatabaseError(String),
    NotFound(String),
    ValidationError(String),
    InternalError(String),
    MongoError(mongodb::error::Error),
}

impl fmt::Display for ApiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ApiError::DatabaseError(msg) => write!(f, "Database error: {}", msg),
            ApiError::NotFound(msg) => write!(f, "Not found: {}", msg),
            ApiError::ValidationError(msg) => write!(f, "Validation error: {}", msg),
            ApiError::InternalError(msg) => write!(f, "Internal error: {}", msg),
            ApiError::MongoError(err) => write!(f, "MongoDB error: {}", err),
        }
    }
}

impl ResponseError for ApiError {
    fn status_code(&self) -> StatusCode {
        match self {
            ApiError::NotFound(_) => StatusCode::NOT_FOUND,
            ApiError::ValidationError(_) => StatusCode::BAD_REQUEST,
            ApiError::DatabaseError(_) | ApiError::InternalError(_) => StatusCode::INTERNAL_SERVER_ERROR,
            ApiError::MongoError(_) => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }

    fn error_response(&self) -> HttpResponse {
        let status = self.status_code();
        HttpResponse::build(status).json(json!({
            "error": self.to_string(),
            "status": status.as_u16(),
        }))
    }
}

impl From<mongodb::error::Error> for ApiError {
    fn from(err: mongodb::error::Error) -> Self {
        ApiError::MongoError(err)
    }
}

impl From<mongodb::bson::ser::Error> for ApiError {
    fn from(err: mongodb::bson::ser::Error) -> Self {
        ApiError::InternalError(format!("BSON serialization error: {}", err))
    }
}

pub type ApiResult<T> = Result<T, ApiError>;
