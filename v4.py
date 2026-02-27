import os
import time
import requests
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, UpdateOne


# ====== CONFIG ======
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY", "b455fff947db40efb714b37b4873b135")
START_YEAR_TS = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())

# For smaller timeframes (4h, 1h, etc.)
FETCH_CANDLES = 2000  # Number of candles to fetch
SCAN_LAST_CANDLES = 1500  # How many candles to scan for patterns

# ====== MONGO ======
MONGO_DB = os.getenv("MONGO_DB", "sr_levels")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "zones")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Bhushan:BhushanDelta@deltapricetracker.y0ipzbf.mongodb.net/?appName=DeltaPriceTracker")

try:
    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo.admin.command('ping')
    print(f"✓ Connected to MongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
except Exception as e:
    raise RuntimeError(f"Failed to connect to MongoDB: {e}")

db = mongo[MONGO_DB]
zones_col = db[MONGO_COLLECTION]


def twelve_get_candles(symbol: str, interval: str, outputsize: int = 2000):
    """
    Fetch candles from TwelveData API
    interval: 4h, 1h, 15min, etc.
    """
    if not TWELVE_API_KEY:
        raise RuntimeError("TWELVE_API_KEY not set")
    
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": TWELVE_API_KEY,
        "format": "JSON"
    }
    
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    
    if j.get("status") == "error":
        raise RuntimeError(f"TwelveData API error: {j.get('message')}")
    
    values = j.get("values", [])
    candles = []
    
    for v in values:
        try:
            dt = datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
            ts = int(dt.timestamp())
            
            candles.append({
                "time": ts,
                "open": float(v["open"]),
                "high": float(v["high"]),
                "low": float(v["low"]),
                "close": float(v["close"]),
                "volume": float(v.get("volume", 0)),
            })
        except (ValueError, KeyError) as e:
            print(f"Skipping invalid candle: {e}")
            continue
    
    # Sort ascending by time
    candles.sort(key=lambda x: x["time"])
    return candles


def is_green(c): return c["close"] > c["open"]
def is_red(c):   return c["close"] < c["open"]
def body_size(c): return abs(c["close"] - c["open"])


def compute_zone_for_bar_v4(candles_most_recent_first, base_offset):
    """
    V4 logic for smaller timeframes based on scalp code:
    - Rally: 3+ consecutive green candles
    - Total move: >= 3.5% (instead of 10%)
    - Small red body: < 30% of open price (instead of 3%)
    - Avg body condition: < 50% of avg body
    """
    if base_offset + 30 >= len(candles_most_recent_first):
        return None

    view = candles_most_recent_first[base_offset:]

    # avgBody = sma(bodySize(0), 10)
    bodies = [body_size(view[i]) for i in range(0, min(10, len(view)))]
    avg_body = sum(bodies) / len(bodies) if bodies else 0.0

    # Identify rally (3+ consecutive green candles)
    rally_len = 0
    for i in range(0, min(11, len(view))):
        if is_green(view[i]):
            rally_len += 1
        else:
            break

    if rally_len < 3:
        return None

    rally_start_low = view[rally_len - 1]["low"]
    rally_end_close = view[0]["close"]
    total_move = ((rally_end_close - rally_start_low) / rally_start_low) * 100.0
    
    # V4: Lower threshold for smaller timeframes
    if total_move < 3.5:
        return None

    # Find small red candle i in [rally_len .. rally_len+2]
    for i in range(rally_len, min(rally_len + 3, len(view))):
        c = view[i]
        
        # V4: Adjusted thresholds for smaller timeframes
        small_body_condition = body_size(c) < 0.30 * c["open"]  # 30% instead of 3%
        avg_body_condition   = body_size(c) < 0.5 * avg_body

        adjacent_green = (is_green(view[i - 1]) if i - 1 >= 0 else False) or \
                         (is_green(view[i + 1]) if i + 1 < len(view) else False)

        if is_red(c) and small_body_condition and avg_body_condition and adjacent_green:
            if c["time"] >= START_YEAR_TS:
                top = float(c["open"])
                bottom = float(c["close"])
                if bottom > top:
                    top, bottom = bottom, top

                return {
                    "current_candle_time": view[0]["time"],
                    "small_red_time": c["time"],
                    "top": top,
                    "bottom": bottom,
                    "rally_length": rally_len,
                    "total_move_pct": float(total_move),
                    "small_red_offset": i,
                }

    return None


def dedupe_zones_keep_most_recent(zones):
    """
    Dedup by (top,bottom). Keep most recent occurrence.
    """
    seen = set()
    out = []
    for z in zones:
        key = z["zone_key"]
        if key in seen:
            continue
        seen.add(key)
        out.append(z)
    return out


def ts_str(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def compute_zones_for_symbol_v4(symbol: str, interval: str):
    """
    Compute zones for smaller timeframes (4h, 1h, etc.)
    """
    candles = twelve_get_candles(symbol, interval, outputsize=FETCH_CANDLES)
    
    if len(candles) < 60:
        print(f"Not enough candles: {len(candles)}")
        return []
    
    # Reverse to most recent first
    candles_desc = list(reversed(candles))
    
    start_offset = 1  # Skip current incomplete candle
    max_scan = len(candles_desc) - 35
    end_offset = min(start_offset + SCAN_LAST_CANDLES, max_scan)
    
    zones = []
    for base_offset in range(start_offset, end_offset):
        z = compute_zone_for_bar_v4(candles_desc, base_offset)
        if z:
            z["symbol"] = symbol
            z["timeframe"] = interval
            z["zone_key"] = f"{z['top']:.8f}|{z['bottom']:.8f}"
            zones.append(z)
    
    zones = dedupe_zones_keep_most_recent(zones)
    return zones


def upsert_zones(symbol: str, zones: list):
    now = datetime.now(timezone.utc)

    ops = []
    for z in zones:
        doc = {
            "symbol": z["symbol"],
            "timeframe": z["timeframe"],
            "zone_key": z["zone_key"],
            "top": z["top"],
            "bottom": z["bottom"],
            "small_red_time": z["small_red_time"],
            "current_candle_time": z["current_candle_time"],
            "pattern_metadata": {
                "rally_length": z["rally_length"],
                "total_move_pct": z["total_move_pct"],
                "small_red_offset": z["small_red_offset"],
                "source": "twelvedata_v4_small_timeframes"
            },
            "updated_at": now,
            "status": "active",
        }

        ops.append(UpdateOne(
            {"symbol": doc["symbol"], "timeframe": doc["timeframe"], "zone_key": doc["zone_key"]},
            {"$set": doc},
            upsert=True
        ))

    if ops:
        res = zones_col.bulk_write(ops, ordered=False)
        return {"upserted": res.upserted_count, "modified": res.modified_count, "matched": res.matched_count}
    return {"upserted": 0, "modified": 0, "matched": 0}


def main():
    print("=== V4 Level Finder (Small Timeframes) ===")
    print("Key differences from V3:")
    print("- Total move threshold: 3.5% (vs 10%)")
    print("- Small red body: < 30% of open (vs 3%)")
    print("- Works with 4h, 1h, 15min timeframes\n")
    
    symbol = input("Enter symbol (e.g., XAU/USD, EUR/USD): ").strip().upper()
    if not symbol:
        print("No symbol provided.")
        return
    
    interval = input("Enter interval (4h, 1h, 15min, etc.): ").strip().lower()
    if not interval:
        print("No interval provided.")
        return
    
    print(f"\nFetching {FETCH_CANDLES} candles for {symbol} @ {interval}...")
    zones = compute_zones_for_symbol_v4(symbol, interval)
    
    print(f"\nSymbol: {symbol}")
    print(f"Timeframe: {interval}")
    print(f"Unique zones computed: {len(zones)}")
    
    for z in zones[:15]:
        print(
            f"At={ts_str(z['current_candle_time'])} | "
            f"TOP={z['top']:.4f} BOTTOM={z['bottom']:.4f} | "
            f"SmallRed={ts_str(z['small_red_time'])} | "
            f"Rally={z['rally_length']} Move={z['total_move_pct']:.2f}%"
        )
    
    if zones:
        save = input("\nSave to MongoDB? (y/n): ").strip().lower()
        if save == 'y':
            result = upsert_zones(symbol, zones)
            print(f"\nMongo upsert result: {result}")
            print(f"DB: {MONGO_DB}, Collection: {MONGO_COLLECTION}")
    else:
        print("\nNo zones found. Try adjusting parameters or checking data availability.")


if __name__ == "__main__":
    main()
