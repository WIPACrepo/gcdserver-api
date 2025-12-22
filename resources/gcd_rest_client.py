"""
GCD REST API Client Module

This module provides utilities for interacting with the GCD REST API,
including building GCD files, managing calibrations, geometry, and detector status.
"""

import requests
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class GCDAPIConfig:
    """Configuration for GCD REST API access"""
    api_url: str
    bearer_token: str
    timeout: int = 30
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }


class APIError(Exception):
    """API request error"""
    pass


class GCDRestClient:
    """Client for GCD REST API"""
    
    def __init__(self, config: GCDAPIConfig):
        self.config = config
        self.api_url = config.api_url.rstrip('/')
        self.session = requests.Session()
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a request to the API"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(
                    url, 
                    headers=self.config.headers,
                    params=params,
                    timeout=self.config.timeout
                )
            elif method == "POST":
                response = self.session.post(
                    url,
                    headers=self.config.headers,
                    json=data,
                    timeout=self.config.timeout
                )
            elif method == "PUT":
                response = self.session.put(
                    url,
                    headers=self.config.headers,
                    json=data,
                    timeout=self.config.timeout
                )
            elif method == "DELETE":
                response = self.session.delete(
                    url,
                    headers=self.config.headers,
                    timeout=self.config.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"API request failed: {error_msg}")
            raise APIError(error_msg) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"API request failed: {e}") from e
    
    def health_check(self) -> bool:
        """Check API health"""
        try:
            result = self._make_request("GET", "/health")
            return result.get("status") == "healthy"
        except:
            return False
    
    def verify_token(self) -> bool:
        """Verify that the current token is valid"""
        try:
            result = self._make_request("GET", "/auth/verify")
            return result.get("success", False)
        except:
            return False
    
    # Calibration operations
    def get_calibrations(self) -> List[Dict]:
        """Get all calibrations"""
        result = self._make_request("GET", "/calibration")
        return result.get("data", [])
    
    def get_calibration(self, dom_id: int) -> Optional[Dict]:
        """Get calibration by DOM ID"""
        result = self._make_request("GET", f"/calibration/{dom_id}")
        return result.get("data")
    
    def create_calibration(self, dom_id: int, domcal: Dict) -> Dict:
        """Create new calibration"""
        data = {"dom_id": dom_id, "domcal": domcal}
        result = self._make_request("POST", "/calibration", data=data)
        return result.get("data", {})
    
    def update_calibration(self, dom_id: int, domcal: Dict) -> Dict:
        """Update calibration"""
        data = {"dom_id": dom_id, "domcal": domcal}
        result = self._make_request("PUT", f"/calibration/{dom_id}", data=data)
        return result.get("data", {})
    
    def delete_calibration(self, dom_id: int) -> bool:
        """Delete calibration"""
        try:
            self._make_request("DELETE", f"/calibration/{dom_id}")
            return True
        except:
            return False
    
    # Geometry operations
    def get_geometry(self) -> List[Dict]:
        """Get all geometry entries"""
        result = self._make_request("GET", "/geometry")
        return result.get("data", [])
    
    def get_geometry_entry(self, string: int, position: int) -> Optional[Dict]:
        """Get geometry by string and position"""
        result = self._make_request("GET", f"/geometry/{string}/{position}")
        return result.get("data")
    
    def create_geometry(self, string: int, position: int, location: Dict) -> Dict:
        """Create new geometry entry"""
        data = {"string": string, "position": position, "location": location}
        result = self._make_request("POST", "/geometry", data=data)
        return result.get("data", {})
    
    def update_geometry(self, string: int, position: int, location: Dict) -> Dict:
        """Update geometry entry"""
        data = {"string": string, "position": position, "location": location}
        result = self._make_request("PUT", f"/geometry/{string}/{position}", data=data)
        return result.get("data", {})
    
    # Detector Status operations
    def get_detector_statuses(self) -> List[Dict]:
        """Get all detector statuses"""
        result = self._make_request("GET", "/detector-status")
        return result.get("data", [])
    
    def get_detector_status(self, dom_id: int) -> Optional[Dict]:
        """Get detector status by DOM ID"""
        result = self._make_request("GET", f"/detector-status/{dom_id}")
        return result.get("data")
    
    def create_detector_status(self, dom_id: int, status: str, is_bad: bool) -> Dict:
        """Create detector status"""
        data = {"dom_id": dom_id, "status": status, "is_bad": is_bad}
        result = self._make_request("POST", "/detector-status", data=data)
        return result.get("data", {})
    
    def update_detector_status(self, dom_id: int, status: str, is_bad: bool) -> Dict:
        """Update detector status"""
        data = {"dom_id": dom_id, "status": status, "is_bad": is_bad}
        result = self._make_request("PUT", f"/detector-status/{dom_id}", data=data)
        return result.get("data", {})
    
    # Snow Height operations
    def get_snow_heights(self) -> List[Dict]:
        """Get all snow height records"""
        result = self._make_request("GET", "/snow-height")
        return result.get("data", [])
    
    def get_snow_height(self, run_number: int) -> Optional[Dict]:
        """Get snow height for a specific run"""
        result = self._make_request("GET", f"/snow-height/{run_number}")
        return result.get("data")
    
    def create_snow_height(self, run_number: int, height: float) -> Dict:
        """Create snow height record"""
        data = {"run_number": run_number, "height": height}
        result = self._make_request("POST", "/snow-height", data=data)
        return result.get("data", {})
    
    def update_snow_height(self, run_number: int, height: float) -> Dict:
        """Update snow height for run"""
        data = {"run_number": run_number, "height": height}
        result = self._make_request("PUT", f"/snow-height/{run_number}", data=data)
        return result.get("data", {})
    
    # Configuration operations
    def get_configurations(self) -> List[Dict]:
        """Get all configurations"""
        result = self._make_request("GET", "/config")
        return result.get("data", [])
    
    def get_configuration(self, key: str) -> Optional[Dict]:
        """Get configuration by key"""
        result = self._make_request("GET", f"/config/{key}")
        return result.get("data")
    
    def create_configuration(self, key: str, value: Any) -> Dict:
        """Create configuration"""
        data = {"key": key, "value": value}
        result = self._make_request("POST", "/config", data=data)
        return result.get("data", {})
    
    def update_configuration(self, key: str, value: Any) -> Dict:
        """Update configuration"""
        data = {"key": key, "value": value}
        result = self._make_request("PUT", f"/config/{key}", data=data)
        return result.get("data", {})
    
    # GCD Collection operations
    def generate_gcd_collection(self, run_number: int) -> Dict[str, Any]:
        """Generate complete GCD collection for a run"""
        result = self._make_request("POST", f"/gcd/generate/{run_number}")
        return result.get("data", {})
    
    def get_gcd_collection(self, collection_id: str) -> Optional[Dict]:
        """Retrieve previously generated GCD collection"""
        result = self._make_request("GET", f"/gcd/collection/{collection_id}")
        return result.get("data")


class GCDBuilder:
    """High-level GCD builder using REST API"""
    
    def __init__(self, client: GCDRestClient):
        self.client = client
    
    def build_and_save(self, run_number: int, output_file: str) -> bool:
        """
        Build GCD and save to file.
        
        Args:
            run_number: Run number to build GCD for
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Building GCD for run {run_number}...")
            
            # Verify authentication
            if not self.client.verify_token():
                logger.error("Authentication token is invalid")
                return False
            
            # Generate GCD collection
            gcd_data = self.client.generate_gcd_collection(run_number)
            if not gcd_data or not gcd_data.get("collection_id"):
                logger.error(f"Failed to generate GCD for run {run_number}")
                return False
            
            # Log statistics
            collection_id = gcd_data.get("collection_id")
            num_calibrations = len(gcd_data.get("calibrations", []))
            num_geometry = len(gcd_data.get("geometry", []))
            num_detector_status = len(gcd_data.get("detector_status", []))
            
            logger.info(f"Generated GCD collection {collection_id}")
            logger.info(f"  Calibrations: {num_calibrations}")
            logger.info(f"  Geometry entries: {num_geometry}")
            logger.info(f"  Detector status: {num_detector_status}")
            
            # Get snow height if available
            snow_data = self.client.get_snow_height(run_number)
            if snow_data:
                logger.info(f"  Snow height: {snow_data.get('height')} m")
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(gcd_data, f, indent=2, default=str)
            
            logger.info(f"GCD saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build GCD: {e}", exc_info=True)
            return False
    
    def get_summary(self, run_number: int) -> Optional[Dict]:
        """Get summary of GCD data for a run"""
        try:
            gcd_data = self.client.generate_gcd_collection(run_number)
            return {
                "run_number": run_number,
                "collection_id": gcd_data.get("collection_id"),
                "generated_at": gcd_data.get("generated_at"),
                "generated_by": gcd_data.get("generated_by"),
                "num_calibrations": len(gcd_data.get("calibrations", [])),
                "num_geometry": len(gcd_data.get("geometry", [])),
                "num_detector_status": len(gcd_data.get("detector_status", [])),
            }
        except Exception as e:
            logger.error(f"Failed to get GCD summary: {e}")
            return None
