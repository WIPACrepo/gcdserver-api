#!/usr/bin/env python3
"""
Migration Guide: From Direct MongoDB Access to GCDServer REST API

This file shows side-by-side comparisons of how to migrate from
direct database calls to API-based calls.
"""

# ==============================================================================
# BEFORE: Direct MongoDB Access (Old Way)
# ==============================================================================

"""
import pymongo
from datetime import datetime

# Connect directly to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["gcdserver"]
calibrations_col = db["calibrations"]
geometries_col = db["geometries"]
statuses_col = db["detector_statuses"]
configs_col = db["configurations"]

# === CALIBRATIONS ===

# GET: Fetch all calibrations
all_cals = list(calibrations_col.find())

# GET: Fetch specific calibration
cal = calibrations_col.find_one({"dom_id": 12345})

# GET: Fetch latest calibration for DOM
latest_cal = calibrations_col.find_one(
    {"dom_id": 12345},
    sort=[("timestamp", -1)]
)

# CREATE: Add new calibration
calibrations_col.insert_one({
    "dom_id": 12345,
    "domcal": {
        "atwd_gain": [1.0, 1.1, 1.2, 1.3],
        "atwd_freq": [50.0, 50.1, 50.2, 50.3],
        "fadc_gain": 1.0,
        "fadc_freq": 50.0,
        "pmt_gain": 1.0,
        "transit_time": 1.0,
        "relative_pmt_gain": 1.0
    },
    "timestamp": datetime.utcnow()
})

# UPDATE: Modify calibration
calibrations_col.update_one(
    {"dom_id": 12345},
    {"$set": {"domcal.fadc_gain": 1.05}}
)

# DELETE: Remove calibration
calibrations_col.delete_one({"dom_id": 12345})

# === GEOMETRIES ===

# GET: All geometries
all_geoms = list(geometries_col.find())

# GET: Specific geometry
geom = geometries_col.find_one({
    "string": 34,
    "position": 50
})

# GET: All for a string
string_geoms = list(geometries_col.find({"string": 34}))

# CREATE: New geometry
geometries_col.insert_one({
    "string": 34,
    "position": 50,
    "location": {"x": 100.0, "y": 200.0, "z": 300.0},
    "timestamp": datetime.utcnow()
})

# UPDATE: Modify geometry
geometries_col.update_one(
    {"string": 34, "position": 50},
    {"$set": {"location.x": 110.0}}
)

# DELETE: Remove geometry
geometries_col.delete_one({"string": 34, "position": 50})

# === DETECTOR STATUS ===

# GET: All statuses
all_statuses = list(statuses_col.find())

# GET: Specific status
status = statuses_col.find_one({"dom_id": 67890})

# GET: All bad DOMs
bad_doms = list(statuses_col.find({"is_bad": True}))

# CREATE: New status
statuses_col.insert_one({
    "dom_id": 67890,
    "status": "operational",
    "is_bad": False,
    "timestamp": datetime.utcnow()
})

# UPDATE: Change status
statuses_col.update_one(
    {"dom_id": 67890},
    {"$set": {"status": "maintenance", "is_bad": True}}
)

# DELETE: Remove status
statuses_col.delete_one({"dom_id": 67890})

# === CONFIGURATION ===

# GET: All configs
all_configs = list(configs_col.find())

# GET: Specific config
config = configs_col.find_one({"key": "detector_config"})

# CREATE: New config
configs_col.insert_one({
    "key": "detector_config",
    "value": {"name": "IceCube", "version": 1},
    "timestamp": datetime.utcnow()
})

# UPDATE: Modify config
configs_col.update_one(
    {"key": "detector_config"},
    {"$set": {"value.version": 2}}
)

# DELETE: Remove config
configs_col.delete_one({"key": "detector_config"})
"""

# ==============================================================================
# AFTER: GCDServer REST API (New Way)
# ==============================================================================

from gcdserver_api_client import (
    GCDServerClient,
    DOMCal,
    GeoLocation,
)

# Connect via API
client = GCDServerClient(base_url="http://localhost:8080")
token = "your-oauth2-token"  # Get from OAuth2 flow

# === CALIBRATIONS ===

# GET: Fetch all calibrations
all_cals = client.get_calibrations(token)

# GET: Fetch specific calibration
cal = client.get_calibration(token, dom_id=12345)

# GET: Fetch latest calibration for DOM
latest_cal = client.get_latest_calibration(token, dom_id=12345)

# CREATE: Add new calibration
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

# UPDATE: Modify calibration
domcal.fadc_gain = 1.05
updated_cal = client.update_calibration(token, dom_id=12345, domcal=domcal)

# DELETE: Remove calibration
success = client.delete_calibration(token, dom_id=12345)

# === GEOMETRIES ===

# GET: All geometries
all_geoms = client.get_geometries(token)

# GET: Specific geometry
geom = client.get_geometry(token, string=34, position=50)

# GET: All for a string
string_geoms = client.get_string_geometry(token, string=34)

# CREATE: New geometry
location = GeoLocation(x=100.0, y=200.0, z=300.0)
new_geom = client.create_geometry(token, string=34, position=50, location=location)

# UPDATE: Modify geometry
location.x = 110.0
updated_geom = client.update_geometry(token, string=34, position=50, location=location)

# DELETE: Remove geometry
success = client.delete_geometry(token, string=34, position=50)

# === DETECTOR STATUS ===

# GET: All statuses
all_statuses = client.get_detector_statuses(token)

# GET: Specific status
status = client.get_detector_status(token, dom_id=67890)

# GET: All bad DOMs
bad_doms = client.get_bad_doms(token)

# CREATE: New status
new_status = client.create_detector_status(
    token, dom_id=67890, status="operational", is_bad=False
)

# UPDATE: Change status
updated_status = client.update_detector_status(
    token, dom_id=67890, status="maintenance", is_bad=True
)

# DELETE: Remove status
success = client.delete_detector_status(token, dom_id=67890)

# === CONFIGURATION ===

# GET: All configs
all_configs = client.get_configurations(token)

# GET: Specific config
config = client.get_configuration(token, key="detector_config")

# CREATE: New config
new_config = client.create_configuration(
    token, key="detector_config", value={"name": "IceCube", "version": 1}
)

# UPDATE: Modify config
updated_config = client.update_configuration(
    token, key="detector_config", value={"name": "IceCube", "version": 2}
)

# DELETE: Remove config
success = client.delete_configuration(token, key="detector_config")


# ==============================================================================
# KEY DIFFERENCES & BENEFITS
# ==============================================================================

"""
COMPARISON TABLE:

┌─────────────────────┬──────────────────────┬─────────────────────────┐
│ Aspect              │ Direct DB            │ REST API                │
├─────────────────────┼──────────────────────┼─────────────────────────┤
│ Security            │ No auth, exposed DB  │ OAuth2 + JWT tokens     │
│ Network Isolation   │ Direct DB connection │ Only API accessible     │
│ Scalability         │ Single DB instance   │ Multiple API servers    │
│ Auditability        │ Limited logging      │ Full API audit trail    │
│ Error Handling      │ Driver-specific      │ Consistent HTTP codes   │
│ Version Control     │ Schema migration     │ API versioning          │
│ Backend Change      │ Code changes         │ Transparent to clients  │
│ Monitoring          │ DB metrics only      │ API metrics available   │
│ Load Balancing      │ Not applicable       │ Multiple endpoints      │
│ Firewall Rules      │ Open DB port         │ Single API port         │
└─────────────────────┴──────────────────────┴─────────────────────────┘

MIGRATION CHECKLIST:

1. Authentication
   ✓ Migrate from no auth to OAuth2 flow
   ✓ Store tokens securely
   ✓ Handle token refresh

2. Error Handling
   ✓ Change from pymongo exceptions to GCDServerAPIError
   ✓ Update error messages to use HTTP status codes
   ✓ Add retry logic for transient failures

3. Data Access Patterns
   ✓ Replace find() with get_*() methods
   ✓ Replace find_one() with single get methods
   ✓ Update sorting/filtering logic if needed

4. Performance
   ✓ Add client-side caching where appropriate
   ✓ Batch operations if supported
   ✓ Monitor API response times

5. Testing
   ✓ Update mocks to use API client
   ✓ Add tests for token handling
   ✓ Test error scenarios

6. Deployment
   ✓ Remove direct DB connection strings
   ✓ Update environment variables
   ✓ Configure API endpoints
   ✓ Set up OAuth2 provider

MIGRATION SCRIPT TEMPLATE:

import pymongo
from gcdserver_api_client import GCDServerClient

# Old DB connection
old_db = pymongo.MongoClient("mongodb://old-server:27017")["gcdserver"]

# New API client
new_client = GCDServerClient(base_url="http://api-server:8080")
token = "oauth2-token"

# Migrate calibrations
for old_cal in old_db["calibrations"].find():
    try:
        new_client.create_calibration(
            token,
            dom_id=old_cal["dom_id"],
            domcal=DOMCal(**old_cal["domcal"])
        )
        print(f"Migrated calibration for DOM {old_cal['dom_id']}")
    except Exception as e:
        print(f"Failed to migrate: {e}")

# Repeat for other collections...
"""

if __name__ == "__main__":
    print("See comments in this file for migration patterns")
    print("\nKey migration steps:")
    print("1. Replace pymongo.MongoClient with GCDServerClient")
    print("2. Replace find() with get_*() methods")
    print("3. Handle OAuth2 authentication")
    print("4. Update error handling to use GCDServerAPIError")
    print("5. Test thoroughly with the new API")
