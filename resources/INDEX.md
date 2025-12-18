<!-- GCDServer API Python Client - Index & Navigation -->

# GCDServer API Python Client Resources

This folder contains a complete, production-ready Python client library for interacting with the GCDServer REST API. All operations that were previously done with direct MongoDB access are now available through a secure, authenticated REST API.

## 📚 Quick Navigation

| File | Purpose | Lines | Start Here? |
|------|---------|-------|------------|
| **SETUP.md** | Quick start & setup guide | 280 | ✅ YES - Start here! |
| **README.md** | Full documentation & API reference | 550 | 📖 After SETUP.md |
| **quickstart.py** | Basic usage examples | 164 | 🏃 Run this first |
| **gcdserver_api_client.py** | Main client library | 796 | 🔧 Core implementation |
| **examples.py** | Comprehensive examples | 368 | 📚 Learn by example |
| **migration_guide.py** | From DB to API migration | 348 | 🔄 If migrating from DB |
| **__init__.py** | Python package init | 45 | 📦 For imports |
| **requirements.txt** | Python dependencies | 1 | 🛠️ Just `requests` |

## 🎯 Getting Started (Choose Your Path)

### Path 1: I'm New (5 minutes)
1. Read [SETUP.md](SETUP.md) - Quick start section
2. Install: `pip install -r requirements.txt`
3. Run: `python quickstart.py` (with token)
4. Try modifying an example

### Path 2: I'm Migrating from Direct DB (15 minutes)
1. Read [migration_guide.py](migration_guide.py) - Side-by-side comparison
2. Read [SETUP.md](SETUP.md) - Authentication section
3. Update your code following the migration guide
4. Run tests with new client

### Path 3: I Need Complete Reference (30 minutes)
1. Read [SETUP.md](SETUP.md) - Overview
2. Read [README.md](README.md) - Complete documentation
3. Study [examples.py](examples.py) - All operations
4. Reference [gcdserver_api_client.py](gcdserver_api_client.py) - Code details

## 📁 File Descriptions

### SETUP.md
**What**: Quick start guide (YOU ARE HERE on first visit)
**Contains**:
- What's in this folder (overview)
- 5-minute quick start
- Common tasks with code examples
- Authentication guide
- Troubleshooting basics
- Key features summary

**When to read**: First! Before anything else.

### README.md
**What**: Complete API reference and documentation
**Contains**:
- Detailed installation instructions
- Complete API operations reference
- All configuration options
- Data model definitions
- Error handling guide
- Performance tips
- Migration from direct DB guide
- Logging configuration

**When to read**: After SETUP.md, for comprehensive reference.

### quickstart.py
**What**: Executable Python script with basic examples
**Contains**:
- Health check
- Token verification
- Basic CRUD for: Calibrations, Geometries, Detector Status, Configurations
- One operation per data type

**When to run**: 
```bash
export GCDSERVER_TOKEN="your-token"
python quickstart.py
```

### gcdserver_api_client.py
**What**: Main client library (the actual code you'll import)
**Contains**:
- `GCDServerClient` class - Main client
- `GCDServerAPIError` - Exception class
- Data model classes: `DOMCal`, `GeoLocation`, `Calibration`, `Geometry`, `DetectorStatus`, `Configuration`
- Full documentation for every method
- Type hints throughout
- Internal HTTP handling

**When to use**:
```python
from gcdserver_api_client import GCDServerClient, DOMCal

client = GCDServerClient()
# ... use client ...
```

### examples.py
**What**: Comprehensive examples for all operations
**Contains**:
- Health check example
- OAuth2 login flow example
- CRUD examples for each data type (Calibrations, Geometries, Detector Status, Configuration)
- Token operations (verify, refresh, logout)
- Organized into example functions

**When to run**:
```bash
# Without token (limited examples)
python examples.py

# With token (all examples)
export GCDSERVER_TOKEN="your-token"
python examples.py
```

### migration_guide.py
**What**: Side-by-side migration guide from direct MongoDB to REST API
**Contains**:
- Old code (direct MongoDB) - commented out
- New code (REST API) - active examples
- Comparison table
- Migration checklist
- Batch migration script template
- Key benefits of migration

**When to read**: If migrating from direct database access.

### __init__.py
**What**: Python package initialization file
**Contains**:
- Module docstring
- Public exports
- Version info

**When used**: When importing the package:
```python
from resources import GCDServerClient
```

### requirements.txt
**What**: Python dependencies specification
**Contains**:
- `requests>=2.28.0`

**When to use**:
```bash
pip install -r requirements.txt
```

## 🔄 Typical Usage Workflow

### Step 1: Setup
```bash
# Clone or navigate to this folder
cd resources

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Learn
```bash
# Read quick start
cat SETUP.md

# Or read full documentation
cat README.md
```

### Step 3: Authenticate
```bash
# Option A: Get token via browser (see SETUP.md)
export GCDSERVER_TOKEN="your-oauth2-token"

# Option B: Use Keycloak to get token
# Option C: Run OAuth2 login flow in your code
```

### Step 4: Try Examples
```bash
# Run quick start
python quickstart.py

# Or run comprehensive examples
python examples.py

# Or run specific migration examples
python migration_guide.py
```

### Step 5: Use in Your Code
```python
from gcdserver_api_client import GCDServerClient, DOMCal

client = GCDServerClient(base_url="http://localhost:8080")
token = "your-oauth2-token"

# Get data
cals = client.get_calibrations(token)

# Create data
new_cal = client.create_calibration(token, dom_id=12345, domcal=domcal)

# Update data
updated = client.update_calibration(token, dom_id=12345, domcal=updated_domcal)

# Delete data
client.delete_calibration(token, dom_id=12345)
```

## 📊 API Operations Summary

### Calibrations (Detector Calibration Data)
```
GET    /calibration                    - Get all
GET    /calibration/{dom_id}           - Get specific
GET    /calibration/latest/{dom_id}    - Get latest
POST   /calibration                    - Create new
PUT    /calibration/{dom_id}           - Update
DELETE /calibration/{dom_id}           - Delete
```

### Geometry (DOM Positions)
```
GET    /geometry                       - Get all
GET    /geometry/{string}/{position}   - Get specific
GET    /geometry/string/{string}       - Get all for string
POST   /geometry                       - Create new
PUT    /geometry/{string}/{position}   - Update
DELETE /geometry/{string}/{position}   - Delete
```

### Detector Status (DOM Health)
```
GET    /detector-status                - Get all
GET    /detector-status/{dom_id}       - Get specific
GET    /detector-status/bad-doms       - Get all bad DOMs
POST   /detector-status                - Create new
PUT    /detector-status/{dom_id}       - Update
DELETE /detector-status/{dom_id}       - Delete
```

### Configuration (Settings)
```
GET    /config                         - Get all
GET    /config/{key}                   - Get specific
POST   /config                         - Create new
PUT    /config/{key}                   - Update
DELETE /config/{key}                   - Delete
```

### Authentication
```
POST   /auth/login                     - Initiate OAuth2 flow
GET    /auth/callback                  - OAuth2 callback (gets token)
GET    /auth/verify                    - Verify token validity
POST   /auth/refresh                   - Refresh token
POST   /auth/logout                    - Logout
```

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: requests` | Run `pip install -r requirements.txt` |
| `Connection refused` | Start API: `cd ../gcdserver_rust_api && cargo run` |
| `401 Unauthorized` | Set valid token: `export GCDSERVER_TOKEN="token"` |
| `404 Not found` | Resource doesn't exist, check ID/key |
| `500 Server error` | Check API server logs, might be DB issue |

For more help, see [Troubleshooting in README.md](README.md#troubleshooting)

## 🎓 Learning Resources in This Folder

### For Beginners
1. **SETUP.md** - Quick overview
2. **quickstart.py** - Run and modify
3. **examples.py** - Study each section

### For Migrating from DB
1. **migration_guide.py** - See old vs new code
2. **README.md** - Migration section
3. **examples.py** - Study equivalents

### For Advanced Users
1. **gcdserver_api_client.py** - Source code
2. **README.md** - Full API reference
3. **Rust API docs** - See ../gcdserver_rust_api/README.md

## 📈 Project Statistics

| Metric | Value |
|--------|-------|
| Total files | 8 |
| Total size | ~92 KB |
| Lines of code | ~2,100+ |
| Documentation | ~2,000+ lines |
| Example coverage | All operations |
| Python version | 3.7+ |
| Dependencies | Just `requests` |

## ✨ What Makes This Great

✅ **Complete** - Every API operation is covered
✅ **Well Documented** - 2,000+ lines of documentation
✅ **Production Ready** - Error handling, logging, type hints
✅ **Easy to Use** - Simple, Pythonic interface
✅ **Migration Friendly** - Guides for transitioning from direct DB
✅ **Examples Galore** - Multiple ways to see how to use it
✅ **Type Safe** - Full type hints for IDE support
✅ **OAuth2 Ready** - Built-in authentication support

## 🚀 Next Steps

1. **Right now**: Read [SETUP.md](SETUP.md)
2. **In 5 minutes**: Run `python quickstart.py`
3. **In 15 minutes**: Study [examples.py](examples.py)
4. **In 30 minutes**: Read full [README.md](README.md)
5. **In 1 hour**: Build your own script!

---

**Need help?** Start with [SETUP.md](SETUP.md) → then [README.md](README.md) → then [examples.py](examples.py)

**Happy coding!** 🎉
