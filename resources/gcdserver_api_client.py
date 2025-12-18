#!/usr/bin/env python3
"""
GCDServer API Client

A Python client for interacting with the GCDServer REST API.
Provides methods to perform the same operations as direct database calls,
but now abstracted through the REST API with OAuth2 authentication.

Usage:
    from gcdserver_api_client import GCDServerClient
    
    client = GCDServerClient(base_url="http://localhost:8080")
    token = client.get_token()  # Via OAuth2 flow
    
    # Calibration operations
    calibrations = client.get_calibrations(token)
    cal = client.get_calibration(token, dom_id=12345)
    new_cal = client.create_calibration(token, dom_id=12345, domcal_data)
    
    # Geometry operations
    geometries = client.get_geometries(token)
    geom = client.get_geometry(token, string=34, position=50)
    
    # Detector status operations
    statuses = client.get_detector_statuses(token)
    bad_doms = client.get_bad_doms(token)
    
    # Configuration operations
    configs = client.get_configurations(token)
    config = client.get_configuration(token, key="my_config")
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

import requests
from requests.exceptions import RequestException, HTTPError

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@dataclass
class DOMCal:
    """DOM Calibration data"""
    atwd_gain: List[float]
    atwd_freq: List[float]
    fadc_gain: float
    fadc_freq: float
    pmt_gain: float
    transit_time: float
    relative_pmt_gain: float


@dataclass
class GeoLocation:
    """Geographic location"""
    x: float
    y: float
    z: float


@dataclass
class Calibration:
    """Calibration record"""
    dom_id: int
    domcal: DOMCal
    timestamp: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self):
        return {
            "dom_id": self.dom_id,
            "domcal": asdict(self.domcal),
            "timestamp": self.timestamp,
        }


@dataclass
class Geometry:
    """Geometry record"""
    string: int
    position: int
    location: GeoLocation
    timestamp: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self):
        return {
            "string": self.string,
            "position": self.position,
            "location": asdict(self.location),
            "timestamp": self.timestamp,
        }


@dataclass
class DetectorStatus:
    """Detector status record"""
    dom_id: int
    status: str
    is_bad: bool
    timestamp: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self):
        return {
            "dom_id": self.dom_id,
            "status": self.status,
            "is_bad": self.is_bad,
            "timestamp": self.timestamp,
        }


@dataclass
class Configuration:
    """Configuration record"""
    key: str
    value: Dict[str, Any]
    timestamp: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
        }


class GCDServerAPIError(Exception):
    """Custom exception for API errors"""
    pass


class GCDServerClient:
    """
    Client for interacting with the GCDServer REST API.
    
    Handles authentication, token management, and all CRUD operations.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        keycloak_issuer_url: Optional[str] = None,
        keycloak_client_id: Optional[str] = None,
        keycloak_client_secret: Optional[str] = None,
        keycloak_redirect_uri: Optional[str] = None,
    ):
        """
        Initialize the GCDServer API client.
        
        Args:
            base_url: Base URL of the API server
            keycloak_issuer_url: Keycloak issuer URL for OAuth2
            keycloak_client_id: Keycloak client ID
            keycloak_client_secret: Keycloak client secret
            keycloak_redirect_uri: Redirect URI after OAuth2 login
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        
        # OAuth2 Configuration
        self.keycloak_issuer_url = (
            keycloak_issuer_url
            or os.getenv("KEYCLOAK_ISSUER_URL", "http://localhost:8080/auth/realms/master")
        )
        self.keycloak_client_id = (
            keycloak_client_id or os.getenv("KEYCLOAK_CLIENT_ID", "gcdserver-api")
        )
        self.keycloak_client_secret = (
            keycloak_client_secret
            or os.getenv("KEYCLOAK_CLIENT_SECRET", "change-me-in-production")
        )
        self.keycloak_redirect_uri = (
            keycloak_redirect_uri
            or os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8080/auth/callback")
        )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise errors if needed.
        
        Args:
            response: Response object from requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            GCDServerAPIError: If API returns an error
        """
        try:
            response.raise_for_status()
        except HTTPError as e:
            error_msg = f"API Error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise GCDServerAPIError(error_msg) from e

        try:
            return response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {response.text}")
            raise GCDServerAPIError("Invalid JSON response from API") from e

    def _make_request(
        self,
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            token: Bearer token for authentication
            data: JSON data to send in request body
            params: Query parameters
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"

        logger.debug(f"Making {method} request to {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30,
            )
            return self._handle_response(response)
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            raise GCDServerAPIError(f"Request failed: {e}") from e

    # ========================
    # Authentication Endpoints
    # ========================

    def login(self, nonce: Optional[str] = None) -> Dict[str, str]:
        """
        Initiate OAuth2 login flow.
        
        Args:
            nonce: Optional nonce value for OpenID Connect
            
        Returns:
            Dictionary with authorization_url, state, and nonce
        """
        logger.info("Initiating OAuth2 login flow")
        data = {}
        if nonce:
            data["nonce"] = nonce
        
        response = self._make_request("POST", "/auth/login", data=data)
        return response.get("data", response)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify that a token is valid.
        
        Args:
            token: Bearer token to verify
            
        Returns:
            Token verification response with user info
        """
        logger.info("Verifying token")
        response = self._make_request("GET", "/auth/verify", token=token)
        return response.get("data", response)

    def refresh_token(self, token: str) -> str:
        """
        Refresh an access token.
        
        Args:
            token: Current Bearer token
            
        Returns:
            New access token
        """
        logger.info("Refreshing access token")
        response = self._make_request("POST", "/auth/refresh", token=token)
        data = response.get("data", response)
        return data.get("access_token", data)

    def logout(self, token: str) -> bool:
        """
        Logout and invalidate the token.
        
        Args:
            token: Bearer token to invalidate
            
        Returns:
            True if logout was successful
        """
        logger.info("Logging out")
        response = self._make_request("POST", "/auth/logout", token=token)
        return response.get("success", True)

    # =========================
    # Calibration Endpoints
    # =========================

    def get_calibrations(self, token: str) -> List[Calibration]:
        """
        Get all calibrations.
        
        Args:
            token: Bearer token for authentication
            
        Returns:
            List of Calibration objects
        """
        logger.info("Fetching all calibrations")
        response = self._make_request("GET", "/calibration", token=token)
        calibrations = response.get("data", [])
        return [Calibration(**cal) for cal in calibrations]

    def get_calibration(self, token: str, dom_id: int) -> Optional[Calibration]:
        """
        Get calibration for a specific DOM.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            
        Returns:
            Calibration object or None if not found
        """
        logger.info(f"Fetching calibration for DOM {dom_id}")
        response = self._make_request("GET", f"/calibration/{dom_id}", token=token)
        data = response.get("data")
        return Calibration(**data) if data else None

    def get_latest_calibration(self, token: str, dom_id: int) -> Optional[Calibration]:
        """
        Get the latest calibration for a specific DOM.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            
        Returns:
            Latest Calibration object or None if not found
        """
        logger.info(f"Fetching latest calibration for DOM {dom_id}")
        response = self._make_request(
            "GET", f"/calibration/latest/{dom_id}", token=token
        )
        data = response.get("data")
        return Calibration(**data) if data else None

    def create_calibration(
        self, token: str, dom_id: int, domcal: DOMCal
    ) -> Calibration:
        """
        Create a new calibration.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            domcal: DOMCal object with calibration data
            
        Returns:
            Created Calibration object
        """
        logger.info(f"Creating calibration for DOM {dom_id}")
        data = {
            "dom_id": dom_id,
            "domcal": asdict(domcal),
        }
        response = self._make_request("POST", "/calibration", token=token, data=data)
        return Calibration(**response.get("data"))

    def update_calibration(
        self, token: str, dom_id: int, domcal: DOMCal
    ) -> Calibration:
        """
        Update an existing calibration.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            domcal: Updated DOMCal object
            
        Returns:
            Updated Calibration object
        """
        logger.info(f"Updating calibration for DOM {dom_id}")
        data = {
            "dom_id": dom_id,
            "domcal": asdict(domcal),
        }
        response = self._make_request(
            "PUT", f"/calibration/{dom_id}", token=token, data=data
        )
        return Calibration(**response.get("data"))

    def delete_calibration(self, token: str, dom_id: int) -> bool:
        """
        Delete a calibration.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            
        Returns:
            True if deletion was successful
        """
        logger.info(f"Deleting calibration for DOM {dom_id}")
        response = self._make_request(
            "DELETE", f"/calibration/{dom_id}", token=token
        )
        return response.get("success", True)

    # =========================
    # Geometry Endpoints
    # =========================

    def get_geometries(self, token: str) -> List[Geometry]:
        """
        Get all geometry entries.
        
        Args:
            token: Bearer token for authentication
            
        Returns:
            List of Geometry objects
        """
        logger.info("Fetching all geometries")
        response = self._make_request("GET", "/geometry", token=token)
        geometries = response.get("data", [])
        return [Geometry(**geom) for geom in geometries]

    def get_geometry(self, token: str, string: int, position: int) -> Optional[Geometry]:
        """
        Get geometry for a specific string and position.
        
        Args:
            token: Bearer token for authentication
            string: String number
            position: Position in string
            
        Returns:
            Geometry object or None if not found
        """
        logger.info(f"Fetching geometry for string {string}, position {position}")
        response = self._make_request(
            "GET", f"/geometry/{string}/{position}", token=token
        )
        data = response.get("data")
        return Geometry(**data) if data else None

    def get_string_geometry(self, token: str, string: int) -> List[Geometry]:
        """
        Get all geometry entries for a specific string.
        
        Args:
            token: Bearer token for authentication
            string: String number
            
        Returns:
            List of Geometry objects for the string
        """
        logger.info(f"Fetching all geometry for string {string}")
        response = self._make_request("GET", f"/geometry/string/{string}", token=token)
        geometries = response.get("data", [])
        return [Geometry(**geom) for geom in geometries]

    def create_geometry(
        self, token: str, string: int, position: int, location: GeoLocation
    ) -> Geometry:
        """
        Create a new geometry entry.
        
        Args:
            token: Bearer token for authentication
            string: String number
            position: Position in string
            location: GeoLocation object
            
        Returns:
            Created Geometry object
        """
        logger.info(f"Creating geometry for string {string}, position {position}")
        data = {
            "string": string,
            "position": position,
            "location": asdict(location),
        }
        response = self._make_request("POST", "/geometry", token=token, data=data)
        return Geometry(**response.get("data"))

    def update_geometry(
        self, token: str, string: int, position: int, location: GeoLocation
    ) -> Geometry:
        """
        Update an existing geometry entry.
        
        Args:
            token: Bearer token for authentication
            string: String number
            position: Position in string
            location: Updated GeoLocation object
            
        Returns:
            Updated Geometry object
        """
        logger.info(f"Updating geometry for string {string}, position {position}")
        data = {
            "string": string,
            "position": position,
            "location": asdict(location),
        }
        response = self._make_request(
            "PUT", f"/geometry/{string}/{position}", token=token, data=data
        )
        return Geometry(**response.get("data"))

    def delete_geometry(self, token: str, string: int, position: int) -> bool:
        """
        Delete a geometry entry.
        
        Args:
            token: Bearer token for authentication
            string: String number
            position: Position in string
            
        Returns:
            True if deletion was successful
        """
        logger.info(f"Deleting geometry for string {string}, position {position}")
        response = self._make_request(
            "DELETE", f"/geometry/{string}/{position}", token=token
        )
        return response.get("success", True)

    # =========================
    # Detector Status Endpoints
    # =========================

    def get_detector_statuses(self, token: str) -> List[DetectorStatus]:
        """
        Get all detector statuses.
        
        Args:
            token: Bearer token for authentication
            
        Returns:
            List of DetectorStatus objects
        """
        logger.info("Fetching all detector statuses")
        response = self._make_request("GET", "/detector-status", token=token)
        statuses = response.get("data", [])
        return [DetectorStatus(**status) for status in statuses]

    def get_detector_status(self, token: str, dom_id: int) -> Optional[DetectorStatus]:
        """
        Get detector status for a specific DOM.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            
        Returns:
            DetectorStatus object or None if not found
        """
        logger.info(f"Fetching detector status for DOM {dom_id}")
        response = self._make_request(
            "GET", f"/detector-status/{dom_id}", token=token
        )
        data = response.get("data")
        return DetectorStatus(**data) if data else None

    def get_bad_doms(self, token: str) -> List[DetectorStatus]:
        """
        Get all bad DOMs (detector statuses).
        
        Args:
            token: Bearer token for authentication
            
        Returns:
            List of DetectorStatus objects for bad DOMs
        """
        logger.info("Fetching all bad DOMs")
        response = self._make_request("GET", "/detector-status/bad-doms", token=token)
        bad_doms = response.get("data", [])
        return [DetectorStatus(**status) for status in bad_doms]

    def create_detector_status(
        self, token: str, dom_id: int, status: str, is_bad: bool = False
    ) -> DetectorStatus:
        """
        Create a new detector status entry.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            status: Status string
            is_bad: Whether the DOM is bad
            
        Returns:
            Created DetectorStatus object
        """
        logger.info(f"Creating detector status for DOM {dom_id}")
        data = {
            "dom_id": dom_id,
            "status": status,
            "is_bad": is_bad,
        }
        response = self._make_request("POST", "/detector-status", token=token, data=data)
        return DetectorStatus(**response.get("data"))

    def update_detector_status(
        self, token: str, dom_id: int, status: str, is_bad: bool = False
    ) -> DetectorStatus:
        """
        Update an existing detector status.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            status: Updated status string
            is_bad: Whether the DOM is bad
            
        Returns:
            Updated DetectorStatus object
        """
        logger.info(f"Updating detector status for DOM {dom_id}")
        data = {
            "dom_id": dom_id,
            "status": status,
            "is_bad": is_bad,
        }
        response = self._make_request(
            "PUT", f"/detector-status/{dom_id}", token=token, data=data
        )
        return DetectorStatus(**response.get("data"))

    def delete_detector_status(self, token: str, dom_id: int) -> bool:
        """
        Delete a detector status.
        
        Args:
            token: Bearer token for authentication
            dom_id: DOM ID
            
        Returns:
            True if deletion was successful
        """
        logger.info(f"Deleting detector status for DOM {dom_id}")
        response = self._make_request(
            "DELETE", f"/detector-status/{dom_id}", token=token
        )
        return response.get("success", True)

    # =========================
    # Configuration Endpoints
    # =========================

    def get_configurations(self, token: str) -> List[Configuration]:
        """
        Get all configurations.
        
        Args:
            token: Bearer token for authentication
            
        Returns:
            List of Configuration objects
        """
        logger.info("Fetching all configurations")
        response = self._make_request("GET", "/config", token=token)
        configs = response.get("data", [])
        return [Configuration(**config) for config in configs]

    def get_configuration(self, token: str, key: str) -> Optional[Configuration]:
        """
        Get a specific configuration by key.
        
        Args:
            token: Bearer token for authentication
            key: Configuration key
            
        Returns:
            Configuration object or None if not found
        """
        logger.info(f"Fetching configuration with key: {key}")
        response = self._make_request("GET", f"/config/{key}", token=token)
        data = response.get("data")
        return Configuration(**data) if data else None

    def create_configuration(
        self, token: str, key: str, value: Dict[str, Any]
    ) -> Configuration:
        """
        Create a new configuration.
        
        Args:
            token: Bearer token for authentication
            key: Configuration key
            value: Configuration value (any JSON-serializable object)
            
        Returns:
            Created Configuration object
        """
        logger.info(f"Creating configuration with key: {key}")
        data = {
            "key": key,
            "value": value,
        }
        response = self._make_request("POST", "/config", token=token, data=data)
        return Configuration(**response.get("data"))

    def update_configuration(
        self, token: str, key: str, value: Dict[str, Any]
    ) -> Configuration:
        """
        Update an existing configuration.
        
        Args:
            token: Bearer token for authentication
            key: Configuration key
            value: Updated configuration value
            
        Returns:
            Updated Configuration object
        """
        logger.info(f"Updating configuration with key: {key}")
        data = {
            "key": key,
            "value": value,
        }
        response = self._make_request("PUT", f"/config/{key}", token=token, data=data)
        return Configuration(**response.get("data"))

    def delete_configuration(self, token: str, key: str) -> bool:
        """
        Delete a configuration.
        
        Args:
            token: Bearer token for authentication
            key: Configuration key
            
        Returns:
            True if deletion was successful
        """
        logger.info(f"Deleting configuration with key: {key}")
        response = self._make_request("DELETE", f"/config/{key}", token=token)
        return response.get("success", True)

    # =========================
    # Health Check
    # =========================

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is healthy.
        
        Returns:
            Health check response
        """
        logger.info("Checking API health")
        response = self._make_request("GET", "/health")
        return response.get("data", response)


if __name__ == "__main__":
    # Example usage
    client = GCDServerClient(base_url="http://localhost:8080")
    
    # Health check
    try:
        health = client.health_check()
        print("Health check:", health)
    except GCDServerAPIError as e:
        print(f"Error: {e}")
