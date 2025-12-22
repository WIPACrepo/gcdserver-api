# Migration Guide: BuildGCD.py to REST API

This guide helps migrate from the original `BuildGCD.py` (direct MongoDB access) to the new REST API-based tools.

## Quick Comparison

| Task | Old Way | New Way |
|------|---------|---------|
| Build GCD | `python BuildGCD.py -r 137292 -o gcd.i3` | `python resources/build_gcd_rest.py -r 137292 -o gcd.json` |
| Get database | `getDB(host, user, password)` | `GCDAPIConfig(api_url=url, bearer_token=token)` |
| Create client | `MongoClient(uri)` | `GCDRestClient(config)` |
| Generate GCD | `buildGCD(db, ...)` | `builder.build_and_save(run_num, file)` |

## Step-by-Step Migration

### Step 1: Update Dependencies

**Before:**
```python
from icecube.gcdserver.MongoDB import getDB
from icecube.gcdserver.I3GeometryBuilder import buildI3Geometry
# ... other IceTray imports
```

**After:**
```python
from resources.gcd_rest_client import GCDRestClient, GCDBuilder, GCDAPIConfig
import requests
```

### Step 2: Update Configuration

**Before:**
```python
db = getDB(dbhost="localhost", dbuser="user", dbpass="password")
i3livehost = "i3live.example.com"
```

**After:**
```python
config = GCDAPIConfig(
    api_url="http://localhost:8080",
    bearer_token="your-keycloak-token"
)
client = GCDRestClient(config)
# No need for I3Live - data comes from API
```

### Step 3: Update GCD Building

**Before:**
```python
from icecube.gcdserver.I3GeometryBuilder import buildI3Geometry
from icecube.gcdserver.I3CalibrationBuilder import buildI3Calibration
from icecube.gcdserver.I3DetectorStatusBuilder import buildI3DetectorStatus

def buildGCD(db, i3LiveHost, runNumber, outFilePath):
    runData = getLiveRunData(runNumber, i3LiveHost)
    blobDB = fillBlobDB(db, run=int(runNumber), configuration=runData.configName)
    
    g = buildI3Geometry(blobDB)
    c = buildI3Calibration(blobDB)
    d = buildI3DetectorStatus(blobDB, runData)
    
    # ... write I3 file format
    f = dataio.I3File(outFilePath, 'w')
    # ... push frames
```

**After:**
```python
def build_gcd(run_number, output_file):
    config = GCDAPIConfig(
        api_url="http://localhost:8080",
        bearer_token="token"
    )
    client = GCDRestClient(config)
    builder = GCDBuilder(client)
    
    if builder.build_and_save(run_number, output_file):
        print(f"GCD built for run {run_number}")
    else:
        print("Failed to build GCD")
```

### Step 4: Update Output Format

**Before (I3 File Format):**
```python
f = dataio.I3File(outFilePath, 'w')
fr = icetray.I3Frame(icetray.I3Frame.Geometry)
fr['I3Geometry'] = g
f.push(fr)
# ... more frames
```

**After (JSON Format):**
```python
# Automatically handled by build_and_save()
# Output is standard JSON containing all GCD data
import json
with open("gcd.json") as f:
    gcd_data = json.load(f)
    print(f"Calibrations: {len(gcd_data['calibrations'])}")
    print(f"Geometry: {len(gcd_data['geometry'])}")
```

## Integration Examples

### Command-Line Tool

**Old approach:**
```bash
python resources/BuildGCD.py -r 137292 -o gcd.i3 \
    --dbhost localhost --dbuser user --dbpass password
```

**New approach:**
```bash
export GCD_API_TOKEN="keycloak-token"
python resources/build_gcd_rest.py -r 137292 -o gcd.json
```

### Python Script

**Old:**
```python
#!/usr/bin/env python3
import sys
from icecube.gcdserver.MongoDB import getDB
from resources.BuildGCD import buildGCD

db = getDB("localhost", "user", "password")
buildGCD(db, "i3live.example.com", 137292, "gcd.i3")
```

**New:**
```python
#!/usr/bin/env python3
from resources.gcd_rest_client import GCDBuilder, GCDRestClient, GCDAPIConfig

config = GCDAPIConfig(
    api_url="http://localhost:8080",
    bearer_token="token"
)
client = GCDRestClient(config)
builder = GCDBuilder(client)
builder.build_and_save(137292, "gcd.json")
```

### CI/CD Pipeline

**Old (GitLab CI):**
```yaml
build_gcd:
  image: icecube/icetray:latest
  script:
    - python resources/BuildGCD.py -r $RUN_NUMBER -o gcd.i3 \
        --dbhost $DB_HOST --dbuser $DB_USER --dbpass $DB_PASS
  artifacts:
    paths:
      - gcd.i3
```

**New:**
```yaml
build_gcd:
  image: python:3.9
  before_script:
    - pip install requests
  script:
    - python resources/build_gcd_rest.py -r $RUN_NUMBER -o gcd.json
  artifacts:
    paths:
      - gcd.json
  env:
    - GCD_API_TOKEN: $KEYCLOAK_TOKEN
    - GCD_API_URL: $GCD_SERVER_URL
```

### Docker Integration

**Old Dockerfile:**
```dockerfile
FROM icecube/icetray:latest
COPY resources/BuildGCD.py .
ENTRYPOINT ["python", "BuildGCD.py"]
```

**New Dockerfile:**
```dockerfile
FROM python:3.9
RUN pip install requests
COPY resources/ /app/resources/
WORKDIR /app
ENTRYPOINT ["python", "resources/build_gcd_rest.py"]
```

## Data Format Changes

### Input/Output

**Old:** Binary I3 file format with frames
- I3Geometry frame
- I3Calibration frame
- I3DetectorStatus frame
- I3FlasherSubrunMap frame

**New:** JSON format
- All data in single JSON document
- Human-readable
- Easy to parse and process
- Includes metadata (collection ID, timestamp, etc.)

### Accessing Data

**Old:**
```python
from icecube import dataio, icetray
f = dataio.I3File("gcd.i3", 'r')
for frame in f:
    if frame.type == icetray.I3Frame.Geometry:
        geom = frame['I3Geometry']
    elif frame.type == icetray.I3Frame.Calibration:
        calib = frame['I3Calibration']
```

**New:**
```python
import json
with open("gcd.json") as f:
    gcd = json.load(f)
    geometry = gcd['geometry']
    calibrations = gcd['calibrations']
```

## Snow Height Handling

**Old (via MongoDB/I3Live):**
```python
# Snow height was queried from I3Live or DB
snow_height = getLiveSnowHeight(run_number)
```

**New (via REST API):**
```python
# Direct API call
snow = client.get_snow_height(137292)
if snow:
    print(f"Height: {snow['height']} m")

# Or included in GCD collection
gcd = client.generate_gcd_collection(137292)
# Snow height data available if set for the run
```

## Troubleshooting

### Issue: Authentication Token Invalid
```
ERROR: Authentication token is invalid
```

**Solution:**
```bash
# Get fresh token from Keycloak
# Then set it
export GCD_API_TOKEN="new-token"
```

### Issue: API Server Not Responding
```
APIError: API request failed
```

**Solution:**
```bash
# Check API is running
curl http://localhost:8080/health

# Or specify correct URL
python build_gcd_rest.py -r 137292 -o gcd.json \
    --api-url http://gcdserver.example.com:8080
```

### Issue: File Format Not Recognized
```
ImportError: cannot import I3File
```

**Solution:** The new tools output JSON, not I3 files. Update downstream code:
```python
# Old: gcd = dataio.I3File("gcd.i3").read()
# New:
import json
gcd = json.load(open("gcd.json"))
```

## Rollback Plan

If you need to revert to the old system:

```bash
# Keep both available
python resources/BuildGCD.py -r 137292 -o gcd.i3       # Old way
python resources/build_gcd_rest.py -r 137292 -o gcd.json  # New way

# Compare outputs
diff <(gzip -dc gcd.i3 | strings) <(cat gcd.json)
```

## Testing Migration

### 1. Test with Sample Run

```bash
# Build with new tool
python resources/build_gcd_rest.py -r 137292 -o gcd_new.json

# Verify contents
python -c "
import json
with open('gcd_new.json') as f:
    gcd = json.load(f)
    print(f'Calibrations: {len(gcd[\"calibrations\"])}')
    print(f'Geometry: {len(gcd[\"geometry\"])}')
    print(f'Detector Status: {len(gcd[\"detector_status\"])}')
"
```

### 2. Test Data Integrity

```python
from resources.gcd_rest_client import GCDRestClient, GCDAPIConfig

config = GCDAPIConfig(
    api_url="http://localhost:8080",
    bearer_token="token"
)
client = GCDRestClient(config)

# Verify we can access individual components
cals = client.get_calibrations()
geom = client.get_geometry()
status = client.get_detector_statuses()

assert len(cals) > 0, "No calibrations found"
assert len(geom) > 0, "No geometry found"
assert len(status) > 0, "No detector status found"
```

### 3. Test in CI/CD

Update one job at a time, verify results before rolling out.

## Support

For issues or questions:
1. Check [BUILD_TOOLS_SUMMARY.md](BUILD_TOOLS_SUMMARY.md)
2. Review [gcd_build_examples.py](resources/gcd_build_examples.py)
3. Check API logs: Set `RUST_LOG=debug` on API server
