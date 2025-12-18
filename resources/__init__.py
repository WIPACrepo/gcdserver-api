"""
GCDServer API Python Client Package

A comprehensive Python client library for interacting with the GCDServer REST API.
Provides a Pythonic interface for all CRUD operations on GCDServer data.

Usage:
    from gcdserver_api_client import GCDServerClient, DOMCal, GeoLocation
    
    client = GCDServerClient()
    token = "your-oauth2-token"
    
    # Calibrations
    calibrations = client.get_calibrations(token)
    
    # Geometry
    geometries = client.get_geometries(token)
    
    # Detector Status
    statuses = client.get_detector_statuses(token)
    
    # Configuration
    configs = client.get_configurations(token)
"""

from gcdserver_api_client import (
    GCDServerClient,
    GCDServerAPIError,
    DOMCal,
    GeoLocation,
    Calibration,
    Geometry,
    DetectorStatus,
    Configuration,
)

__version__ = "1.0.0"
__author__ = "IceCube Collaboration"
__all__ = [
    "GCDServerClient",
    "GCDServerAPIError",
    "DOMCal",
    "GeoLocation",
    "Calibration",
    "Geometry",
    "DetectorStatus",
    "Configuration",
]
