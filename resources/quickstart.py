#!/usr/bin/env python3
"""
Quick Start Guide - GCDServer API Client

This file demonstrates the most common operations you'll need.
Run this after setting up your authentication token.
"""

import os
from gcdserver_api_client import (
    GCDServerClient,
    DOMCal,
    GeoLocation,
)


def quick_start():
    """Quick start with basic operations"""
    
    # 1. Initialize the client
    client = GCDServerClient(base_url="http://localhost:8080")
    print("✓ Client initialized")
    
    # 2. Get your authentication token
    # This should come from OAuth2 flow or environment variable
    token = os.getenv("GCDSERVER_TOKEN")
    if not token:
        print("\n⚠️  No GCDSERVER_TOKEN found. Please:")
        print("   1. Get authorization URL: POST /auth/login")
        print("   2. User logs in and authorizes")
        print("   3. Provider redirects to /auth/callback with token")
        print("   4. Set: export GCDSERVER_TOKEN='your-token'")
        return
    
    print("✓ Token loaded")
    
    # 3. Verify the token works
    try:
        verification = client.verify_token(token)
        print(f"✓ Token verified for user: {verification.get('email')}")
    except Exception as e:
        print(f"✗ Token verification failed: {e}")
        return
    
    # === CALIBRATIONS ===
    print("\n--- Calibrations ---")
    
    # Read: Get all calibrations
    cals = client.get_calibrations(token)
    print(f"Found {len(cals)} calibration(s)")
    
    # Create: Add a new calibration
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
    print(f"Created calibration for DOM {new_cal.dom_id}")
    
    # Read: Get specific calibration
    cal = client.get_calibration(token, dom_id=12345)
    if cal:
        print(f"Retrieved calibration for DOM {cal.dom_id}")
    
    # Update: Modify existing calibration
    domcal.fadc_gain = 1.05
    updated = client.update_calibration(token, dom_id=12345, domcal=domcal)
    print(f"Updated calibration for DOM {updated.dom_id}")
    
    # Delete: Remove calibration
    client.delete_calibration(token, dom_id=12345)
    print("Deleted calibration")
    
    # === GEOMETRIES ===
    print("\n--- Geometries ---")
    
    # Read: Get all geometries
    geoms = client.get_geometries(token)
    print(f"Found {len(geoms)} geometry record(s)")
    
    # Create: Add new geometry
    loc = GeoLocation(x=100.0, y=200.0, z=300.0)
    new_geom = client.create_geometry(
        token, string=34, position=50, location=loc
    )
    print(f"Created geometry for string {new_geom.string}")
    
    # Read: Get specific geometry
    geom = client.get_geometry(token, string=34, position=50)
    if geom:
        print(f"Retrieved geometry at string {geom.string}, position {geom.position}")
    
    # Update: Modify geometry
    loc.x = 110.0
    updated = client.update_geometry(token, string=34, position=50, location=loc)
    print(f"Updated geometry")
    
    # Delete: Remove geometry
    client.delete_geometry(token, string=34, position=50)
    print("Deleted geometry")
    
    # === DETECTOR STATUS ===
    print("\n--- Detector Status ---")
    
    # Read: Get all statuses
    statuses = client.get_detector_statuses(token)
    print(f"Found {len(statuses)} detector status record(s)")
    
    # Read: Get all bad DOMs
    bad_doms = client.get_bad_doms(token)
    print(f"Found {len(bad_doms)} bad DOM(s)")
    
    # Create: Add status
    new_status = client.create_detector_status(
        token, dom_id=67890, status="operational", is_bad=False
    )
    print(f"Created status for DOM {new_status.dom_id}")
    
    # Update: Change status
    updated = client.update_detector_status(
        token, dom_id=67890, status="maintenance", is_bad=True
    )
    print(f"Updated status for DOM {updated.dom_id}")
    
    # Delete: Remove status
    client.delete_detector_status(token, dom_id=67890)
    print("Deleted status")
    
    # === CONFIGURATION ===
    print("\n--- Configuration ---")
    
    # Read: Get all configs
    configs = client.get_configurations(token)
    print(f"Found {len(configs)} configuration(s)")
    
    # Create: Add config
    config_val = {"name": "test", "version": 1}
    new_cfg = client.create_configuration(token, key="test_config", value=config_val)
    print(f"Created configuration: {new_cfg.key}")
    
    # Read: Get specific config
    cfg = client.get_configuration(token, key="test_config")
    if cfg:
        print(f"Retrieved config: {cfg.key}")
    
    # Update: Modify config
    config_val["version"] = 2
    updated = client.update_configuration(token, key="test_config", value=config_val)
    print(f"Updated configuration: {updated.key}")
    
    # Delete: Remove config
    client.delete_configuration(token, key="test_config")
    print("Deleted configuration")
    
    print("\n✓ Quick start complete!")


if __name__ == "__main__":
    quick_start()
