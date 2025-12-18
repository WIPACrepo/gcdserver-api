// Geometry endpoints
use actix_web::{web, HttpResponse};
use chrono::Utc;
use mongodb::bson::{doc, to_document};
use log::info;
use futures::TryStreamExt;

use crate::db::MongoClient;
use crate::errors::ApiResult;
use crate::models::{Geometry, CreateGeometryRequest, ApiResponse};

pub fn routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/geometry")
            .route("", web::get().to(get_all_geometry))
            .route("", web::post().to(create_geometry))
            .route("/{string}/{position}", web::get().to(get_geometry_by_location))
            .route("/{string}/{position}", web::put().to(update_geometry))
            .route("/{string}/{position}", web::delete().to(delete_geometry))
            .route("/string/{string}", web::get().to(get_geometry_by_string))
    );
}

async fn get_all_geometry(
    mongo: web::Data<MongoClient>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Geometry>("geometry");

    let geometries = collection
        .find(doc! {}, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} geometry entries", geometries.len());
    Ok(HttpResponse::Ok().json(ApiResponse::success(geometries)))
}

async fn create_geometry(
    mongo: web::Data<MongoClient>,
    req: web::Json<CreateGeometryRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Geometry>("geometry");

    let geometry = Geometry {
        id: None,
        string: req.string,
        position: req.position,
        location: req.location.clone(),
        timestamp: Utc::now(),
    };

    let result = collection.insert_one(&geometry, None).await?;
    info!("Created geometry for string {} position {}: {:?}", req.string, req.position, result.inserted_id);

    Ok(HttpResponse::Created().json(ApiResponse::success(geometry)))
}

async fn get_geometry_by_location(
    mongo: web::Data<MongoClient>,
    path: web::Path<(u32, u32)>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Geometry>("geometry");
    let (string, position) = path.into_inner();

    let geometry = collection
        .find_one(doc! { "string": string, "position": position }, None)
        .await?
        .ok_or_else(|| crate::errors::ApiError::NotFound(
            format!("Geometry not found for string {} position {}", string, position)
        ))?;

    info!("Retrieved geometry for string {} position {}", string, position);
    Ok(HttpResponse::Ok().json(ApiResponse::success(geometry)))
}

async fn update_geometry(
    mongo: web::Data<MongoClient>,
    path: web::Path<(u32, u32)>,
    req: web::Json<CreateGeometryRequest>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Geometry>("geometry");
    let (string, position) = path.into_inner();

    let updated_geometry = Geometry {
        id: None,
        string,
        position,
        location: req.location.clone(),
        timestamp: Utc::now(),
    };

    collection
        .update_one(
            doc! { "string": string, "position": position },
            doc! { "$set": to_document(&updated_geometry)? },
            None,
        )
        .await?;

    info!("Updated geometry for string {} position {}", string, position);
    Ok(HttpResponse::Ok().json(ApiResponse::success(updated_geometry)))
}

async fn delete_geometry(
    mongo: web::Data<MongoClient>,
    path: web::Path<(u32, u32)>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Geometry>("geometry");
    let (string, position) = path.into_inner();

    collection
        .delete_one(doc! { "string": string, "position": position }, None)
        .await?;

    info!("Deleted geometry for string {} position {}", string, position);
    Ok(HttpResponse::NoContent().finish())
}

async fn get_geometry_by_string(
    mongo: web::Data<MongoClient>,
    string: web::Path<u32>,
) -> ApiResult<HttpResponse> {
    let db = mongo.get_database();
    let collection = db.collection::<Geometry>("geometry");

    let geometries = collection
        .find(doc! { "string": *string }, None)
        .await?
        .try_collect::<Vec<_>>()
        .await?;

    info!("Retrieved {} geometry entries for string {}", geometries.len(), string);
    Ok(HttpResponse::Ok().json(ApiResponse::success(geometries)))
}
