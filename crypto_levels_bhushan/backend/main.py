"""
FastAPI Backend for Crypto Levels Bhushan
Provides APIs for support zone finding and monitoring
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import requests
from pathlib import Path

# Add parent directory to path to import v3
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import v3 functions
from v3 import compute_zones_for_symbol, ts_str, fnum, is_green, is_red, body_size, START_YEAR_TS

# Twelve Data API Configuration
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "b455fff947db40efb714b37b4873b135")

# API call tracking
api_call_count = 0
last_api_reset = datetime.now(timezone.utc).date()
forex_price_cache = {}  # Cache forex prices: {symbol: {"price": float, "timestamp": datetime}}
FOREX_PRICE_CACHE_DURATION = 180  # 3 minutes in seconds

app = FastAPI(title="Crypto Levels API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://Bhushan:BhushanDelta@deltapricetracker.y0ipzbf.mongodb.net/?appName=DeltaPriceTracker")
DB_NAME = os.getenv("DB_NAME", "delta_tracker")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "monitored_scrips")

# MongoDB client
mongo_client = None
db = None
collection = None

def get_mongo_connection():
    global mongo_client, db, collection
    if mongo_client is None:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[DB_NAME]
        collection = db[COLLECTION_NAME]
    return collection

# ====== API CALL TRACKING ======

def increment_api_calls(count=1):
    """Increment API call counter and reset daily"""
    global api_call_count, last_api_reset
    
    today = datetime.now(timezone.utc).date()
    if today > last_api_reset:
        # Reset counter for new day
        api_call_count = 0
        last_api_reset = today
    
    api_call_count += count
    print(f"[API USAGE] {api_call_count}/800 calls today")
    return api_call_count

def get_api_usage():
    """Get current API usage"""
    global api_call_count, last_api_reset
    
    today = datetime.now(timezone.utc).date()
    if today > last_api_reset:
        api_call_count = 0
        last_api_reset = today
    
    return {
        "used": api_call_count,
        "limit": 800,
        "remaining": 800 - api_call_count,
        "reset_date": last_api_reset.isoformat()
    }

def get_cached_forex_price(symbol: str):
    """Get cached forex price if available and fresh"""
    if symbol in forex_price_cache:
        cached = forex_price_cache[symbol]
        age = (datetime.now(timezone.utc) - cached["timestamp"]).total_seconds()
        if age < FOREX_PRICE_CACHE_DURATION:
            print(f"[CACHE HIT] {symbol}: ${cached['price']:.2f} (age: {age:.0f}s)")
            return cached["price"]
    return None

def cache_forex_price(symbol: str, price: float):
    """Cache forex price"""
    forex_price_cache[symbol] = {
        "price": price,
        "timestamp": datetime.now(timezone.utc)
    }
    print(f"[CACHE SET] {symbol}: ${price:.2f}")

# ====== END API CALL TRACKING ======

# ====== TWELVE DATA FUNCTIONS ======

def fetch_twelve_data(symbol: str, interval: str = "1day", outputsize: int = 5000):
    """Fetch data from Twelve Data API for forex/gold"""
    increment_api_calls(1)  # Track API call
    
    url = "https://api.twelvedata.com/time_series"
    params = {
        'symbol': symbol,
        'interval': interval,
        'outputsize': outputsize,
        'apikey': TWELVE_DATA_API_KEY,
        'format': 'JSON'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'code' in data and data['code'] == 429:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Wait 24 hours or upgrade plan.")
        
        if 'status' in data and data['status'] == 'error':
            raise HTTPException(status_code=400, detail=f"API Error: {data.get('message', 'Unknown error')}")
        
        if 'values' not in data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        values = data['values']
        
        # Convert to our format
        candles = []
        for item in values:
            datetime_str = item['datetime']
            try:
                if ' ' in datetime_str:
                    dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.strptime(datetime_str, '%Y-%m-%d')
            except ValueError:
                continue
            
            candles.append({
                "time": int(dt.timestamp()),
                "open": fnum(item['open']),
                "high": fnum(item['high']),
                "low": fnum(item['low']),
                "close": fnum(item['close']),
                "volume": fnum(item.get('volume'), 0.0),
            })
        
        candles.sort(key=lambda x: x["time"])
        return candles
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Network error: {e}")


def week_start_ts(day_ts: int, week_start_day: int = 0) -> int:
    dt = datetime.fromtimestamp(day_ts, tz=timezone.utc)
    dt0 = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    delta_days = (dt0.weekday() - week_start_day) % 7
    ws = dt0 - timedelta(days=delta_days)
    return int(ws.timestamp())


def resample_daily_to_weekly_monday(daily):
    buckets = {}
    order = []
    for d in daily:
        ws = week_start_ts(d["time"], week_start_day=0)
        if ws not in buckets:
            buckets[ws] = {
                "time": ws,
                "open": d["open"],
                "high": d["high"],
                "low": d["low"],
                "close": d["close"],
                "volume": d["volume"],
            }
            order.append(ws)
        else:
            b = buckets[ws]
            b["high"] = max(b["high"], d["high"])
            b["low"] = min(b["low"], d["low"])
            b["close"] = d["close"]
            b["volume"] += d["volume"]

    weekly = [buckets[k] for k in order]
    weekly.sort(key=lambda x: x["time"], reverse=True)
    return weekly


def resample_daily_to_monthly(daily):
    buckets = {}
    order = []
    
    for d in daily:
        dt = datetime.fromtimestamp(d["time"], tz=timezone.utc)
        month_start = datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)
        ms = int(month_start.timestamp())
        
        if ms not in buckets:
            buckets[ms] = {
                "time": ms,
                "open": d["open"],
                "high": d["high"],
                "low": d["low"],
                "close": d["close"],
                "volume": d["volume"],
            }
            order.append(ms)
        else:
            b = buckets[ms]
            b["high"] = max(b["high"], d["high"])
            b["low"] = min(b["low"], d["low"])
            b["close"] = d["close"]
            b["volume"] += d["volume"]
    
    monthly = [buckets[k] for k in order]
    monthly.sort(key=lambda x: x["time"], reverse=True)
    return monthly


def compute_zone_for_bar_flexible(candles_most_recent_first, base_offset, rally_min=3, move_min=10):
    if base_offset + 30 >= len(candles_most_recent_first):
        return None

    view = candles_most_recent_first[base_offset:]
    bodies = [body_size(view[i]) for i in range(0, min(10, len(view)))]
    avg_body = sum(bodies) / len(bodies) if bodies else 0

    rally_len = 0
    for i in range(0, min(11, len(view))):
        if is_green(view[i]):
            rally_len += 1
        else:
            break

    if rally_len < rally_min:
        return None

    rally_start_low = view[rally_len - 1]["low"]
    rally_end_close = view[0]["close"]
    total_move = ((rally_end_close - rally_start_low) / rally_start_low) * 100.0
    if total_move < move_min:
        return None

    for i in range(rally_len, min(rally_len + 3, len(view))):
        c = view[i]
        small_body_condition = body_size(c) < 0.3 * c["open"]
        avg_body_condition   = body_size(c) < 0.5 * avg_body if avg_body > 0 else True

        adjacent_green = (is_green(view[i - 1]) if i - 1 >= 0 else False) or \
                         (is_green(view[i + 1]) if i + 1 < len(view) else False)

        if is_red(c) and small_body_condition and avg_body_condition and adjacent_green:
            if c["time"] >= START_YEAR_TS:
                top = float(c["open"])
                bottom = float(c["close"])
                if bottom > top:
                    top, bottom = bottom, top

                rally_end_high = view[0]["high"]

                return {
                    "current_week_time": view[0]["time"],
                    "small_red_time": c["time"],
                    "top": top,
                    "bottom": bottom,
                    "rally_end_high": rally_end_high,
                    "rally_length": rally_len,
                    "total_move_pct": float(total_move),
                    "small_red_offset": i,
                }

    return None


def compute_zones_forex(symbol: str, timeframe: str = "1w"):
    """Compute zones for forex/gold using Twelve Data"""
    print(f"[compute_zones_forex] symbol={symbol}, timeframe={timeframe}")
    
    if timeframe == "1M":
        daily = fetch_twelve_data(symbol, interval="1day", outputsize=5000)
        candles = resample_daily_to_monthly(daily)
        min_candles = 40
        rally_min = 2
        move_min = 15
    elif timeframe == "1w":
        daily = fetch_twelve_data(symbol, interval="1day", outputsize=5000)
        candles = resample_daily_to_weekly_monday(daily)
        min_candles = 60
        rally_min = 3
        move_min = 10
    elif timeframe == "1d":
        candles = fetch_twelve_data(symbol, interval="1day", outputsize=5000)
        candles.sort(key=lambda x: x["time"], reverse=True)
        min_candles = 100
        rally_min = 3
        move_min = 8
    elif timeframe == "4h":
        candles = fetch_twelve_data(symbol, interval="4h", outputsize=5000)
        candles.sort(key=lambda x: x["time"], reverse=True)
        min_candles = 150
        rally_min = 4
        move_min = 6
    elif timeframe == "1h":
        candles = fetch_twelve_data(symbol, interval="1h", outputsize=5000)
        candles.sort(key=lambda x: x["time"], reverse=True)
        min_candles = 200
        rally_min = 5
        move_min = 5
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    print(f"[compute_zones_forex] Got {len(candles)} candles, min_candles={min_candles}")
    
    if len(candles) < min_candles:
        print(f"[compute_zones_forex] Not enough candles, returning empty")
        return []

    start_offset = 1
    max_scan = len(candles) - 35
    scan_depth = 400 if timeframe in ["1w", "1M"] else min(400, max_scan - start_offset)
    end_offset = min(start_offset + scan_depth, max_scan)

    print(f"[compute_zones_forex] Scanning from {start_offset} to {end_offset}, rally_min={rally_min}, move_min={move_min}")

    zones = []
    for base_offset in range(start_offset, end_offset):
        z = compute_zone_for_bar_flexible(candles, base_offset, rally_min, move_min)
        if z:
            z["symbol"] = symbol
            z["timeframe"] = timeframe
            z["zone_key"] = f"{z['top']:.8f}|{z['bottom']:.8f}"
            zones.append(z)

    # Dedupe
    seen = set()
    unique_zones = []
    for z in zones:
        key = z["zone_key"]
        if key not in seen:
            seen.add(key)
            unique_zones.append(z)

    return unique_zones

# ====== END TWELVE DATA FUNCTIONS ======

# Pydantic models
class ZoneSearchRequest(BaseModel):
    symbol: str
    timeframe: Optional[str] = "1w"  # Default to weekly
    market_type: Optional[str] = "crypto"  # "crypto" or "forex"

class TriggerLevel(BaseModel):
    trigger_price: float
    bottom: float
    small_red_time: int
    rally_length: int
    total_move_pct: float
    zone_index: int
    triggered: bool = False
    alert_disabled: bool = False
    last_checked: Optional[str] = None

class PushZonesRequest(BaseModel):
    symbol: str
    timeframe: str
    selected_indices: List[int]
    zones: List[dict]
    market_type: Optional[str] = "crypto"  # "crypto" or "forex"

class UpdateAlertRequest(BaseModel):
    symbol: str
    level_index: int
    disabled: bool

@app.get("/")
def read_root():
    return {"message": "Crypto Levels API", "version": "1.0.0"}

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        coll = get_mongo_connection()
        coll.find_one()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/usage")
def get_usage():
    """Get Twelve Data API usage"""
    usage = get_api_usage()
    return {
        "success": True,
        "usage": usage
    }

@app.post("/api/zones/search")
def search_zones(request: ZoneSearchRequest):
    """Search for support zones for a symbol in specified timeframe"""
    try:
        symbol = request.symbol.strip().upper()
        timeframe = request.timeframe or "1w"
        market_type = request.market_type or "crypto"
        
        print(f"[SEARCH] Received: symbol={symbol}, timeframe={timeframe}, market_type={market_type}")
        
        # Validate timeframe
        valid_timeframes = ["1M", "1w", "1d", "4h", "1h"]
        if timeframe not in valid_timeframes:
            raise HTTPException(status_code=400, detail=f"Invalid timeframe. Must be one of: {valid_timeframes}")
        
        # Choose API based on market type
        if market_type == "forex":
            # Auto-format forex symbols (XAUUSD -> XAU/USD)
            original_symbol = symbol
            if '/' not in symbol:
                if symbol.startswith('XAU'):
                    symbol = 'XAU/' + symbol[3:]
                elif symbol.startswith('XAG'):
                    symbol = 'XAG/' + symbol[3:]
                elif len(symbol) == 6:  # EURUSD -> EUR/USD
                    symbol = symbol[:3] + '/' + symbol[3:]
            
            print(f"[FOREX] Formatted symbol: {original_symbol} -> {symbol}")
            zones = compute_zones_forex(symbol, timeframe)
            print(f"[FOREX] Found {len(zones)} zones")
        else:
            # Use Delta API for crypto
            print(f"[CRYPTO] Using Delta API for {symbol}")
            zones = compute_zones_for_symbol(symbol, timeframe)
            print(f"[CRYPTO] Found {len(zones)} zones")
        
        # Format zones for frontend
        formatted_zones = []
        for i, zone in enumerate(zones):
            formatted_zones.append({
                "index": i,
                "top": zone["top"],
                "bottom": zone["bottom"],
                "rally_end_high": zone.get("rally_end_high", zone["top"]),
                "date": ts_str(zone["small_red_time"]),
                "rally_length": zone["rally_length"],
                "total_move_pct": zone["total_move_pct"],
                "small_red_time": zone["small_red_time"]
            })
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "market_type": market_type,
            "zones": formatted_zones,
            "count": len(formatted_zones)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zones/push")
def push_zones(request: PushZonesRequest):
    """Push selected zones to MongoDB"""
    try:
        coll = get_mongo_connection()
        
        # Build trigger_levels array
        trigger_levels = []
        for idx in request.selected_indices:
            zone = request.zones[idx]
            trigger_levels.append({
                "trigger_price": zone["top"],
                "bottom": zone["bottom"],
                "rally_end_high": zone.get("rally_end_high", zone["top"]),
                "small_red_time": zone["small_red_time"],
                "rally_length": zone["rally_length"],
                "total_move_pct": zone["total_move_pct"],
                "zone_index": idx,
                "triggered": False,
                "alert_disabled": False,
                "last_checked": None,
                "timeframe": request.timeframe
            })
        
        # Check if document exists
        existing = coll.find_one({"symbol": request.symbol})
        
        if existing and "trigger_levels" in existing:
            # Append to existing levels
            existing_levels = existing["trigger_levels"]
            existing_levels.extend(trigger_levels)
            
            # Preserve or update market_type
            existing_market_type = existing.get("market_type", "crypto")
            new_market_type = request.market_type or "crypto"
            
            scrip_data = {
                "symbol": request.symbol,
                "timeframe": "multi",  # Multiple timeframes
                "interval": "60",
                "device_id": "web_app",
                "active": True,
                "last_updated": datetime.now().isoformat(),
                "source": "v3_multi_timeframe",
                "trigger_levels": existing_levels,
                "monitoring_type": "multi_level",
                "market_type": new_market_type  # Store market type
            }
        else:
            # Create new document
            scrip_data = {
                "symbol": request.symbol,
                "timeframe": request.timeframe,
                "interval": "60",
                "device_id": "web_app",
                "active": True,
                "last_updated": datetime.now().isoformat(),
                "source": "v3_multi_timeframe",
                "trigger_levels": trigger_levels,
                "monitoring_type": "multi_level",
                "market_type": request.market_type or "crypto"  # Store market type
            }
        
        # Upsert by symbol only
        result = coll.update_one(
            {"symbol": request.symbol},
            {"$set": scrip_data},
            upsert=True
        )
        
        return {
            "success": True,
            "message": f"Pushed {len(trigger_levels)} levels ({request.timeframe}) for {request.symbol}",
            "upserted": result.upserted_id is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scrips")
def get_all_scrips():
    """Get all active scrips from MongoDB"""
    try:
        coll = get_mongo_connection()
        scrips = list(coll.find({"active": True, "monitoring_type": "multi_level"}))
        
        # Convert ObjectId to string
        for scrip in scrips:
            scrip["_id"] = str(scrip["_id"])
        
        return {
            "success": True,
            "scrips": scrips,
            "count": len(scrips)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/price/{symbol}")
def get_mark_price(symbol: str, market_type: Optional[str] = "crypto"):
    """Get current mark price for a symbol"""
    try:
        if market_type == "forex":
            # Format symbol for Twelve Data (XAUUSD -> XAU/USD)
            formatted_symbol = symbol
            if '/' not in symbol:
                if symbol.startswith('XAU'):
                    formatted_symbol = 'XAU/' + symbol[3:]
                elif symbol.startswith('XAG'):
                    formatted_symbol = 'XAG/' + symbol[3:]
                elif len(symbol) == 6:  # EURUSD -> EUR/USD
                    formatted_symbol = symbol[:3] + '/' + symbol[3:]
            
            print(f"[PRICE] Forex: {symbol} -> {formatted_symbol}")
            
            # Check cache first (use formatted symbol for cache key)
            cached_price = get_cached_forex_price(formatted_symbol)
            if cached_price is not None:
                return {
                    "success": True,
                    "symbol": symbol,
                    "mark_price": cached_price,
                    "cached": True
                }
            
            # Use Twelve Data for forex/gold
            increment_api_calls(1)  # Track API call
            
            url = "https://api.twelvedata.com/quote"
            params = {
                'symbol': formatted_symbol,
                'apikey': TWELVE_DATA_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            print(f"[TWELVE DATA] Response for {formatted_symbol}: {data}")
            
            if 'close' in data:
                price = float(data['close'])
                cache_forex_price(formatted_symbol, price)  # Cache the price
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "mark_price": price,
                    "cached": False
                }
            else:
                error_msg = data.get('message', f"No price data for {formatted_symbol}")
                print(f"[TWELVE DATA ERROR] {error_msg}")
                raise HTTPException(status_code=404, detail=error_msg)
        else:
            # Use Delta Exchange for crypto (no caching needed - free API)
            url = "https://api.delta.exchange/v2/tickers"
            response = requests.get(url, timeout=10, headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    tickers = data.get('result', [])
                    for ticker in tickers:
                        if ticker.get('symbol') == symbol.upper():
                            mark_price = ticker.get('mark_price')
                            if mark_price:
                                return {
                                    "success": True,
                                    "symbol": symbol,
                                    "mark_price": float(mark_price)
                                }
            
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"API error: {str(e)}")

@app.put("/api/scrips/{symbol}/alert")
def update_alert_status(symbol: str, request: UpdateAlertRequest):
    """Update alert status for a specific level"""
    try:
        coll = get_mongo_connection()
        
        print(f"Updating alert for {symbol}, level {request.level_index}, disabled={request.disabled}")
        
        result = coll.update_one(
            {"symbol": symbol},
            {"$set": {f"trigger_levels.{request.level_index}.alert_disabled": request.disabled}}
        )
        
        print(f"MongoDB update result: matched={result.matched_count}, modified={result.modified_count}")
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        # Verify the update
        updated_doc = coll.find_one({"symbol": symbol})
        if updated_doc and "trigger_levels" in updated_doc:
            level_status = updated_doc["trigger_levels"][request.level_index].get("alert_disabled", False)
            print(f"Verified: alert_disabled is now {level_status}")
        
        return {
            "success": True,
            "message": f"Alert {'disabled' if request.disabled else 'enabled'} for level {request.level_index}",
            "updated": True
        }
    except Exception as e:
        print(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/scrips/{symbol}")
def delete_scrip(symbol: str):
    """Mark a scrip as inactive"""
    try:
        coll = get_mongo_connection()
        
        result = coll.update_one(
            {"symbol": symbol},
            {"$set": {"active": False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        return {
            "success": True,
            "message": f"Scrip {symbol} marked as inactive"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
