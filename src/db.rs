// Database module - MongoDB abstraction
use mongodb::{Client, Database};
use crate::errors::{ApiError, ApiResult};
use log::info;

pub struct MongoClient {
    client: Client,
    db: Database,
}

impl MongoClient {
    pub async fn new(uri: &str, db_name: &str) -> ApiResult<Self> {
        let client = Client::with_uri_str(uri)
            .await
            .map_err(|e| ApiError::DatabaseError(format!("Failed to connect to MongoDB: {}", e)))?;

        info!("Successfully connected to MongoDB");
        
        let db = client.database(db_name);
        
        Ok(MongoClient { client, db })
    }

    pub fn get_database(&self) -> &Database {
        &self.db
    }

    pub fn get_client(&self) -> &Client {
        &self.client
    }
}
