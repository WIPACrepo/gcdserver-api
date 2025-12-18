#!/usr/bin/env python3
"""
GCDServer API Client - Usage Examples

This script demonstrates how to use the GCDServerClient to perform
the same operations that were previously done with direct database calls.

Make sure the API server is running before executing this script.
"""

import os
import json
import sys
from typing import Optional

# Add the resources directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gcdserver_api_client import (
    GCDServerClient,
    DOMCal,
    GeoLocation,
    Calibration,
    Geometry,
    DetectorStatus,
    Configuration,
    GCDServerAPIError,
)


def example_health_check(client: GCDServerClient):
    """Example: Check API health"""
    print("\n" + "="*60)
    print("EXAMPLE: Health Check")
    print("="*60)
    
    try:
        health = client.health_check()
        print(f"✓ API Health: {json.dumps(health, indent=2)}")
    except GCDServerAPIError as e:
        print(f"✗ Health check failed: {e}")


def example_login(client: GCDServerClient):
    """Example: OAuth2 login flow"""
    print("\n" + "="*60)
    print("EXAMPLE: OAuth2 Login Flow")
    print("="*60)
    
    try:
        login_response = client.login()
        print(f"✓ OAuth2 login initiated:")
        print(f"  - Authorization URL: {login_response.get('authorization_url')}")
        print(f"  - State: {login_response.get('state')}")
        print(f"  - Nonce: {login_response.get('nonce')}")
        print("\nNote: In a real scenario, you would:")
        print("  1. Redirect user to the authorization URL")
        print("  2. User logs in and authorizes")
        print("  3. Provider redirects to callback with authorization code")
        print("  4. Exchange code for access token via callback endpoint")
    except GCDServerAPIError as e:
        print(f"✗ Login failed: {e}")


def example_calibrations(client: GCDServerClient, token: str):
    """Example: Calibration CRUD operations"""
    print("\n" + "="*60)
    print("EXAMPLE: Calibration Operations")
    print("="*60)
    
    try:
        # Get all calibrations
        print("\n1. Fetching all calibrations...")
        calibrations = client.get_calibrations(token)
        print(f"✓ Found {len(calibrations)} calibration(s)")
        if calibrations:
            print(f"  First calibration: DOM {calibrations[0].dom_id}")
        
        # Create new calibration
        print("\n2. Creating new calibration...")
        domcal = DOMCal(
            atwd_gain=[1.0, 1.1, 1.2, 1.3],
            atwd_freq=[50.0, 50.1, 50.2, 50.3],
            fadc_gain=1.0,
            fadc_freq=50.0,
            pmt_gain=1.0,
            transit_time=1.0,
            relative_pmt_gain=1.0
        )
        new_cal = client.create_calibration(token, dom_id=12345, domcal=domcal)
        print(f"✓ Created calibration for DOM {new_cal.dom_id}")
        
        # Get specific calibration
        print("\n3. Fetching specific calibration...")
        cal = client.get_calibration(token, dom_id=12345)
        if cal:
            print(f"✓ Retrieved calibration for DOM {cal.dom_id}")
        else:
            print("✗ Calibration not found")
        
        # Get latest calibration
        print("\n4. Fetching latest calibration...")
        latest_cal = client.get_latest_calibration(token, dom_id=12345)
        if latest_cal:
            print(f"✓ Retrieved latest calibration for DOM {latest_cal.dom_id}")
        
        # Update calibration
        print("\n5. Updating calibration...")
        updated_domcal = DOMCal(
            atwd_gain=[1.05, 1.15, 1.25, 1.35],
            atwd_freq=[50.5, 50.6, 50.7, 50.8],
            fadc_gain=1.05,
            fadc_freq=50.5,
            pmt_gain=1.05,
            transit_time=1.05,
            relative_pmt_gain=1.05
        )
        updated_cal = client.update_calibration(token, dom_id=12345, domcal=updated_domcal)
        print(f"✓ Updated calibration for DOM {updated_cal.dom_id}")
        
        # Delete calibration
        print("\n6. Deleting calibration...")
        success = client.delete_calibration(token, dom_id=12345)
        if success:
            print("✓ Deleted calibration successfully")
        
    except GCDServerAPIError as e:
        print(f"✗ Calibration operation failed: {e}")


def example_geometries(client: GCDServerClient, token: str):
    """Example: Geometry CRUD operations"""
    print("\n" + "="*60)
    print("EXAMPLE: Geometry Operations")
    print("="*60)
    
    try:
        # Get all geometries
        print("\n1. Fetching all geometries...")
        geometries = client.get_geometries(token)
        print(f"✓ Found {len(geometries)} geometry record(s)")
        
        # Create new geometry
        print("\n2. Creating new geometry...")
        location = GeoLocation(x=100.0, y=200.0, z=300.0)
        new_geom = client.create_geometry(
            token, string=34, position=50, location=location
        )
        print(f"✓ Created geometry for string {new_geom.string}, position {new_geom.position}")
        
        # Get specific geometry
        print("\n3. Fetching specific geometry...")
        geom = client.get_geometry(token, string=34, position=50)
        if geom:
            print(f"✓ Retrieved geometry for string {geom.string}, position {geom.position}")
            print(f"  Location: x={geom.location.x}, y={geom.location.y}, z={geom.location.z}")
        
        # Get all geometry for a string
        print("\n4. Fetching all geometry for string 34...")
        string_geoms = client.get_string_geometry(token, string=34)
        print(f"✓ Found {len(string_geoms)} geometry record(s) for string 34")
        
        # Update geometry
        print("\n5. Updating geometry...")
        updated_location = GeoLocation(x=110.0, y=210.0, z=310.0)
        updated_geom = client.update_geometry(
            token, string=34, position=50, location=updated_location
        )
        print(f"✓ Updated geometry for string {updated_geom.string}, position {updated_geom.position}")
        
        # Delete geometry
        print("\n6. Deleting geometry...")
        success = client.delete_geometry(token, string=34, position=50)
        if success:
            print("✓ Deleted geometry successfully")
        
    except GCDServerAPIError as e:
        print(f"✗ Geometry operation failed: {e}")


def example_detector_status(client: GCDServerClient, token: str):
    """Example: Detector Status CRUD operations"""
    print("\n" + "="*60)
    print("EXAMPLE: Detector Status Operations")
    print("="*60)
    
    try:
        # Get all detector statuses
        print("\n1. Fetching all detector statuses...")
        statuses = client.get_detector_statuses(token)
        print(f"✓ Found {len(statuses)} detector status record(s)")
        
        # Create new detector status
        print("\n2. Creating new detector status...")
        new_status = client.create_detector_status(
            token, dom_id=67890, status="operational", is_bad=False
        )
        print(f"✓ Created status for DOM {new_status.dom_id}: {new_status.status}")
        
        # Get specific detector status
        print("\n3. Fetching specific detector status...")
        status = client.get_detector_status(token, dom_id=67890)
        if status:
            print(f"✓ Retrieved status for DOM {status.dom_id}: {status.status}")
            print(f"  Is bad: {status.is_bad}")
        
        # Get all bad DOMs
        print("\n4. Fetching all bad DOMs...")
        bad_doms = client.get_bad_doms(token)
        print(f"✓ Found {len(bad_doms)} bad DOM(s)")
        
        # Update detector status
        print("\n5. Updating detector status...")
        updated_status = client.update_detector_status(
            token, dom_id=67890, status="maintenance", is_bad=True
        )
        print(f"✓ Updated status for DOM {updated_status.dom_id}: {updated_status.status}")
        
        # Delete detector status
        print("\n6. Deleting detector status...")
        success = client.delete_detector_status(token, dom_id=67890)
        if success:
            print("✓ Deleted detector status successfully")
        
    except GCDServerAPIError as e:
        print(f"✗ Detector status operation failed: {e}")


def example_configurations(client: GCDServerClient, token: str):
    """Example: Configuration CRUD operations"""
    print("\n" + "="*60)
    print("EXAMPLE: Configuration Operations")
    print("="*60)
    
    try:
        # Get all configurations
        print("\n1. Fetching all configurations...")
        configs = client.get_configurations(token)
        print(f"✓ Found {len(configs)} configuration(s)")
        
        # Create new configuration
        print("\n2. Creating new configuration...")
        config_value = {
            "detector_name": "IceCube",
            "version": "1.0",
            "parameters": {
                "num_strings": 86,
                "doms_per_string": 60
            }
        }
        new_config = client.create_configuration(
            token, key="detector_config", value=config_value
        )
        print(f"✓ Created configuration: {new_config.key}")
        
        # Get specific configuration
        print("\n3. Fetching specific configuration...")
        config = client.get_configuration(token, key="detector_config")
        if config:
            print(f"✓ Retrieved configuration: {config.key}")
            print(f"  Value: {json.dumps(config.value, indent=2)}")
        
        # Update configuration
        print("\n4. Updating configuration...")
        updated_value = {
            "detector_name": "IceCube",
            "version": "1.1",
            "parameters": {
                "num_strings": 86,
                "doms_per_string": 60,
                "updated": True
            }
        }
        updated_config = client.update_configuration(
            token, key="detector_config", value=updated_value
        )
        print(f"✓ Updated configuration: {updated_config.key}")
        
        # Delete configuration
        print("\n5. Deleting configuration...")
        success = client.delete_configuration(token, key="detector_config")
        if success:
            print("✓ Deleted configuration successfully")
        
    except GCDServerAPIError as e:
        print(f"✗ Configuration operation failed: {e}")


def example_token_operations(client: GCDServerClient, token: str):
    """Example: Token verification and refresh"""
    print("\n" + "="*60)
    print("EXAMPLE: Token Operations")
    print("="*60)
    
    try:
        # Verify token
        print("\n1. Verifying token...")
        verification = client.verify_token(token)
        print(f"✓ Token verified:")
        print(f"  - Valid: {verification.get('valid', True)}")
        print(f"  - User ID: {verification.get('user_id')}")
        print(f"  - Email: {verification.get('email')}")
        if 'scopes' in verification:
            print(f"  - Scopes: {verification.get('scopes')}")
        
        # Refresh token (optional - only if API supports it)
        print("\n2. Refreshing token...")
        try:
            new_token = client.refresh_token(token)
            print(f"✓ Token refreshed successfully")
            print(f"  - New token: {new_token[:20]}...")
        except GCDServerAPIError:
            print("⚠ Token refresh not supported or failed")
        
    except GCDServerAPIError as e:
        print(f"✗ Token operation failed: {e}")


def main():
    """Main example runner"""
    print("\n" + "="*60)
    print("GCDServer API Client - Examples")
    print("="*60)
    
    # Initialize client
    base_url = os.getenv("GCDSERVER_API_URL", "http://localhost:8080")
    print(f"\nConnecting to: {base_url}")
    
    client = GCDServerClient(base_url=base_url)
    
    # Health check
    example_health_check(client)
    
    # Login
    example_login(client)
    
    # Get token from environment or demonstrate usage
    token = os.getenv("GCDSERVER_TOKEN")
    
    if not token:
        print("\n" + "="*60)
        print("NOTE: To run authenticated examples, set GCDSERVER_TOKEN")
        print("="*60)
        print("\nExample setup:")
        print("  1. Get authorization URL via /auth/login endpoint")
        print("  2. User authorizes in OAuth2 provider")
        print("  3. Provider redirects to /auth/callback")
        print("  4. Extract access_token from response")
        print("  5. Set GCDSERVER_TOKEN=<token>")
        print("  6. Run this script again")
        return
    
    print(f"\n✓ Using token from environment variable")
    
    # Run examples with token
    example_calibrations(client, token)
    example_geometries(client, token)
    example_detector_status(client, token)
    example_configurations(client, token)
    example_token_operations(client, token)
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
