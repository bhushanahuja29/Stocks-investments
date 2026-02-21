# MongoDB SSL Connection Fix

## Problem

Getting SSL/TLS handshake errors when connecting to MongoDB Atlas:
```
pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed
[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

## Solution Applied

Updated `backend/v3.py` to handle SSL connections properly on Windows.

### Changes Made

1. **Added SSL/TLS parameters to MongoDB connection:**
```python
mongo = MongoClient(
    MONGO_URI, 
    serverSelectionTimeoutMS=5000,
    tls=True,
    tlsAllowInvalidCertificates=True  # For development
)
```

2. **Made MongoDB optional (graceful degradation):**
```python
except Exception as e:
    print(f"⚠️ MongoDB connection failed: {e}")
    print("⚠️ Continuing without MongoDB - some features may not work")
    mongo = None
```

3. **Added safety checks in functions:**
```python
def upsert_zones(symbol: str, zones: list):
    if not zones_col:
        print("⚠️ MongoDB not connected - skipping zone upsert")
        return {"error": "MongoDB not connected"}
```

## Alternative Solutions

### Option 1: Update Python SSL Libraries (Recommended for Production)

```bash
# In your backend virtual environment
pip install --upgrade certifi
pip install --upgrade pymongo
```

### Option 2: Use Different Connection String

Try adding SSL parameters directly in the connection string:

```
mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true
```

### Option 3: Update Python Version

If using Python 3.8 or older, upgrade to Python 3.10+:
```bash
python --version  # Check current version
# Download Python 3.11+ from python.org
```

### Option 4: Use Environment Variable

Set in `.env`:
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?tls=true&tlsAllowInvalidCertificates=true
```

## Testing the Fix

1. **Start the backend:**
```bash
cd crypto_levels_bhushan/backend
python main.py
```

2. **Look for success message:**
```
✓ Connected to MongoDB: sr_levels.zones
```

3. **If you see warning:**
```
⚠️ MongoDB connection failed: ...
⚠️ Continuing without MongoDB - some features may not work
```

The app will still work, but won't save zones to MongoDB.

## Features Affected Without MongoDB

- ❌ Saving zones to database
- ❌ Retrieving saved zones
- ✅ Finding zones (still works)
- ✅ Price monitoring (still works)
- ✅ Premium dashboard (still works)

## Production Fix

For production deployment, use proper SSL certificates:

```python
mongo = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile='/path/to/ca-certificate.crt'  # Proper cert
)
```

## Windows-Specific Issues

### Issue: OpenSSL Version

Windows Python may use an older OpenSSL version.

**Check:**
```python
import ssl
print(ssl.OPENSSL_VERSION)
```

**Fix:** Reinstall Python with latest OpenSSL or use conda:
```bash
conda install openssl
```

### Issue: Firewall/Antivirus

Some antivirus software blocks SSL connections.

**Fix:** Temporarily disable antivirus and test.

### Issue: Corporate Proxy

If behind a corporate proxy, SSL may be intercepted.

**Fix:** Add proxy settings or use VPN.

## Verification

After applying the fix, verify:

1. **Backend starts without errors**
2. **Can search for zones**
3. **Can monitor prices**
4. **Premium dashboard loads**

## Need More Help?

1. Check Python version: `python --version`
2. Check pymongo version: `pip show pymongo`
3. Check OpenSSL: `python -c "import ssl; print(ssl.OPENSSL_VERSION)"`
4. Try connecting from MongoDB Compass (GUI tool)
5. Check MongoDB Atlas network access settings

## Summary

The fix allows the app to run even if MongoDB connection fails. This is useful for:
- Development without MongoDB
- Testing the premium dashboard
- Running on systems with SSL issues

For production, properly configure SSL certificates.
