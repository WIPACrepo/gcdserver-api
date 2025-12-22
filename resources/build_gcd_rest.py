#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 The IceTray Contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""
BuildGCD for Rust REST API

This module builds I3Geometry, I3Calibration, and I3DetectorStatus instances
by querying the Rust REST API instead of direct MongoDB access.

Usage:
    python build_gcd_rest.py -r <run_number> -o <output_file> \
        --api-url <gcdserver_api_url> \
        --token <bearer_token>
"""

import sys
import requests
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GCDAPIConfig:
    """Configuration for GCD REST API access"""
    api_url: str
    bearer_token: str
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }


class GCDRestClient:
    """Client for GCD REST API"""
    
    def __init__(self, config: GCDAPIConfig):
        self.config = config
        self.api_url = config.api_url.rstrip('/')
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the API"""
        url = f"{self.api_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.config.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.config.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.config.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            sys.exit(1)
    
    def get_calibrations(self) -> list:
        """Get all calibrations"""
        result = self._make_request("GET", "/calibration")
        return result.get("data", [])
    
    def get_geometry(self) -> list:
        """Get all geometry entries"""
        result = self._make_request("GET", "/geometry")
        return result.get("data", [])
    
    def get_detector_status(self) -> list:
        """Get all detector status entries"""
        result = self._make_request("GET", "/detector-status")
        return result.get("data", [])
    
    def get_snow_height(self, run_number: int) -> Optional[Dict]:
        """Get snow height for a specific run"""
        result = self._make_request("GET", f"/snow-height/{run_number}")
        return result.get("data")
    
    def get_configuration(self, key: str) -> Optional[Dict]:
        """Get configuration by key"""
        result = self._make_request("GET", f"/config/{key}")
        return result.get("data")
    
    def generate_gcd_collection(self, run_number: int) -> Dict[str, Any]:
        """Generate complete GCD collection for a run"""
        result = self._make_request("POST", f"/gcd/generate/{run_number}")
        return result.get("data", {})
    
    def verify_token(self) -> bool:
        """Verify that the current token is valid"""
        try:
            result = self._make_request("GET", "/auth/verify")
            return result.get("success", False)
        except:
            return False


class GCDBuilder:
    """Build GCD from REST API data"""
    
    def __init__(self, client: GCDRestClient):
        self.client = client
    
    def build_gcd(self, run_number: int, output_file_path: str) -> bool:
        """
        Build GCD file using REST API data.
        
        Args:
            run_number: The run number to build GCD for
            output_file_path: Path to write GCD output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify token is valid
            if not self.client.verify_token():
                print("ERROR: Authentication token is invalid")
                return False
            
            print(f"Generating GCD collection for run {run_number}...")
            
            # Generate GCD collection
            gcd_collection = self.client.generate_gcd_collection(run_number)
            
            if not gcd_collection:
                print(f"ERROR: No GCD collection generated for run {run_number}")
                return False
            
            collection_id = gcd_collection.get("collection_id")
            num_calibrations = len(gcd_collection.get("calibrations", []))
            num_geometry = len(gcd_collection.get("geometry", []))
            num_detector_status = len(gcd_collection.get("detector_status", []))
            
            print(f"Successfully generated GCD collection {collection_id}")
            print(f"  - Calibrations: {num_calibrations}")
            print(f"  - Geometry entries: {num_geometry}")
            print(f"  - Detector status entries: {num_detector_status}")
            
            # Get snow height for this run (if available)
            snow_height = self.client.get_snow_height(run_number)
            if snow_height:
                print(f"  - Snow height: {snow_height.get('height', 'N/A')} m")
            
            # Write to output file
            with open(output_file_path, 'w') as f:
                json.dump(gcd_collection, f, indent=2, default=str)
            
            print(f"GCD data written to {output_file_path}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to build GCD: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build GCD using Rust REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variable for token
  export GCD_API_TOKEN="your-keycloak-token"
  python build_gcd_rest.py -r 137292 -o gcd.json --api-url http://localhost:8080
  
  # Using command-line token
  python build_gcd_rest.py -r 137292 -o gcd.json \\
    --api-url http://localhost:8080 \\
    --token "your-keycloak-token"
        """
    )
    
    parser.add_argument(
        "-r", "--run",
        type=int,
        required=True,
        help="Run number to build GCD for"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output file path for GCD data"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="GCD Server REST API URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--token",
        help="Bearer token for authentication (or set GCD_API_TOKEN env var)"
    )
    
    args = parser.parse_args()
    
    # Get token from argument or environment
    token = args.token or os.environ.get("GCD_API_TOKEN")
    if not token:
        print("ERROR: Bearer token not provided")
        print("Provide via --token argument or GCD_API_TOKEN environment variable")
        parser.print_help()
        sys.exit(1)
    
    # Create API client
    config = GCDAPIConfig(api_url=args.api_url, bearer_token=token)
    client = GCDRestClient(config)
    
    # Build GCD
    builder = GCDBuilder(client)
    success = builder.build_gcd(args.run, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import os
    main()
