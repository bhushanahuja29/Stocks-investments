# Upstox API for Indian Stocks - Complete Guide

## Overview
Upstox offers a FREE API for historical candle data that provides direct NSE/BSE data with excellent accuracy matching TradingView.

## Key Features ✅

### 1. Historical Candle Data
- **Daily candles:** Past 1 year
- **Weekly candles:** Past 10 years
- **Monthly candles:** Past 10 years
- **Intraday (1min):** Past 1 month
- **Intraday (30min):** Past 1 year

### 2. Data Quality
- ⭐⭐⭐⭐⭐ Direct from NSE/BSE
- ✅ Matches TradingView perfectly
- ✅ Clean OHLCV format
- ✅ No adjustments issues

### 3. Pricing
- **API Access:** FREE ✅
- **Requirements:** Upstox trading account (free to open)
- **Brokerage:** ₹10/order (only if you trade via API)
- **Data API:** Completely FREE (no charges for fetching data)

### 4. Supported Exchanges
- NSE Equity (NSE_EQ)
- BSE Equity (BSE_EQ)
- NSE F&O (NSE_FNO)
- NSE Currency (NSE_CURRENCY)
- MCX Commodity (MCX_COMM)

## Requirements

### 1. Upstox Account
- Open free trading account at https://upstox.com/
- Complete KYC (Aadhaar + PAN)
- No minimum balance required

### 2. Create API App
1. Login to Upstox
2. Go to https://upstox.com/developer/apps
3. Create new app
4. Get API Key and Secret
5. Generate Access Token

### 3. Python SDK
```bash
pip install upstox-python-sdk
```

## API Documentation

### Endpoint
```
GET https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
```

### Parameters
- **instrument_key:** `NSE_EQ|INE002A01018` (format: EXCHANGE|ISIN)
- **interval:** `1minute`, `30minute`, `day`, `week`, `month`
- **to_date:** `2024-01-31` (inclusive)
- **from_date:** `2024-01-01` (optional)

### Response Format
```json
{
  "status": "success",
  "data": {
    "candles": [
      [
        "2023-10-01T00:00:00+05:30",  // timestamp
        53.1,                          // open
        53.95,                         // high
        51.6,                          // low
        52.05,                         // close
        235519861,                     // volume
        0                              // open interest
      ]
    ]
  }
}
```

## Implementation

### Step 1: Get Instrument Key

Upstox uses ISIN codes. You need to map symbols to ISINs:

**Popular Indian Stocks:**
| Symbol | ISIN | Instrument Key |
|--------|------|----------------|
| RELIANCE | INE002A01018 | NSE_EQ\|INE002A01018 |
| TCS | INE467B01029 | NSE_EQ\|INE467B01029 |
| INFY | INE009A01021 | NSE_EQ\|INE009A01021 |
| HDFCBANK | INE040A01034 | NSE_EQ\|INE040A01034 |
| ITC | INE154A01025 | NSE_EQ\|INE154A01025 |

**Get full list:**
```python
import requests

# Download instruments file
url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv"
response = requests.get(url)

# Parse and find ISIN
import pandas as pd
df = pd.read_csv(url)
reliance = df[df['tradingsymbol'] == 'RELIANCE']
print(reliance['instrument_key'].values[0])  # NSE_EQ|INE002A01018
```

### Step 2: Fetch Historical Data

```python
import requests
from datetime import datetime, timedelta

def fetch_upstox_data(instrument_key, interval="day", days_back=365):
    """
    Fetch historical data from Upstox
    
    instrument_key: e.g., "NSE_EQ|INE002A01018" for RELIANCE
    interval: "1minute", "30minute", "day", "week", "month"
    days_back: number of days to fetch
    """
    
    # Calculate dates
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    # Build URL
    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
    
    # Make request (no auth needed for historical data!)
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        if data['status'] == 'success':
            candles = []
            for candle in data['data']['candles']:
                candles.append({
                    'time': int(datetime.fromisoformat(candle[0]).timestamp()),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            # Sort by time ascending
            candles.sort(key=lambda x: x['time'])
            return candles
    
    raise Exception(f"Failed to fetch data: {response.text}")


# Example usage
reliance_data = fetch_upstox_data("NSE_EQ|INE002A01018", "day", 365)
print(f"Fetched {len(reliance_data)} candles for RELIANCE")
```

### Step 3: Symbol to ISIN Mapping

```python
# Create a mapping dictionary
INDIAN_STOCKS_ISIN = {
    "RELIANCE": "INE002A01018",
    "TCS": "INE467B01029",
    "INFY": "INE009A01021",
    "HDFCBANK": "INE040A01034",
    "ITC": "INE154A01025",
    "HINDUNILVR": "INE030A01027",
    "ICICIBANK": "INE090A01021",
    "SBIN": "INE062A01020",
    "BHARTIARTL": "INE397D01024",
    "KOTAKBANK": "INE237A01028",
}

def get_instrument_key(symbol, exchange="NSE_EQ"):
    """Convert symbol to Upstox instrument key"""
    isin = INDIAN_STOCKS_ISIN.get(symbol.upper())
    if not isin:
        raise ValueError(f"ISIN not found for {symbol}")
    return f"{exchange}|{isin}"

# Usage
instrument_key = get_instrument_key("RELIANCE")
print(instrument_key)  # NSE_EQ|INE002A01018
```

### Step 4: Update Backend

Replace `fetch_yahoo_data_indian()` with `fetch_upstox_data()`:

```python
def compute_zones_indian_stocks(symbol: str, timeframe: str = "1w", version: str = "v3"):
    """Compute zones for Indian stocks using Upstox"""
    
    # Get instrument key
    instrument_key = get_instrument_key(symbol)
    
    # Map timeframe to Upstox interval
    if timeframe == "1M":
        interval = "month"
        days_back = 3650  # 10 years
        candles = fetch_upstox_data(instrument_key, interval, days_back)
        min_candles = 40
        rally_min = 2
        move_min = 15 if version == "v3" else 5
        
    elif timeframe == "1w":
        interval = "week"
        days_back = 3650  # 10 years
        candles = fetch_upstox_data(instrument_key, interval, days_back)
        min_candles = 60
        rally_min = 3
        move_min = 10 if version == "v3" else 3
        
    elif timeframe == "1d":
        interval = "day"
        days_back = 730  # 2 years
        candles = fetch_upstox_data(instrument_key, interval, days_back)
        candles.sort(key=lambda x: x["time"], reverse=True)
        min_candles = 100
        rally_min = 3
        move_min = 8 if version == "v3" else 2
    
    # ... rest of the logic remains same
```

## Advantages Over Yahoo Finance

| Feature | Yahoo Finance | Upstox API |
|---------|---------------|------------|
| Data Source | Aggregated | Direct NSE/BSE |
| Accuracy | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Matches TradingView | ❌ No | ✅ Yes |
| Adjustments Issues | ⚠️ Yes | ✅ No |
| Historical Data | 10+ years | 10 years |
| Cost | FREE | FREE |
| API Key Required | ❌ No | ✅ Yes (free) |
| Account Required | ❌ No | ✅ Yes (free) |

## Comparison: Upstox vs DhanHQ vs Yahoo

| Feature | Upstox | DhanHQ | Yahoo Finance |
|---------|--------|--------|---------------|
| **Cost** | FREE | FREE | FREE |
| **Account Required** | ✅ Yes | ✅ Yes | ❌ No |
| **Data Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Matches TradingView** | ✅ Yes | ✅ Yes | ❌ No |
| **Historical Daily** | 1 year | Inception | 10+ years |
| **Historical Weekly** | 10 years | Inception | 10+ years |
| **Historical Monthly** | 10 years | Inception | 10+ years |
| **Setup Difficulty** | Easy | Easy | Very Easy |
| **Python SDK** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Documentation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Recommendation

### Use Upstox if:
- ✅ You have or can open an Upstox account
- ✅ You want data that matches TradingView
- ✅ You need accurate NSE/BSE data
- ✅ You're okay with ISIN-based symbol format

### Use DhanHQ if:
- ✅ You have or can open a DhanHQ account
- ✅ You need data back to stock inception
- ✅ You prefer symbol-based format (easier)

### Use Yahoo Finance if:
- ✅ You don't want to create any account
- ✅ You're okay with data discrepancies
- ✅ You want quickest setup

## Next Steps

1. **Open Upstox Account** (if you don't have one)
   - Visit https://upstox.com/
   - Complete KYC (takes 1-2 days)
   - Free to open, no charges

2. **Create API App**
   - Login to Upstox
   - Go to Developer Console
   - Create app and get credentials

3. **Download Instruments File**
   - Get ISIN codes for stocks
   - Create symbol-to-ISIN mapping

4. **Update Backend Code**
   - Replace Yahoo Finance with Upstox
   - Test with RELIANCE, TCS, INFY

5. **Test Data Quality**
   - Compare with TradingView
   - Verify levels match

## Support

- **Upstox API Docs:** https://upstox.com/developer/api-documentation/
- **Community Forum:** https://community.upstox.com/
- **Support:** support@upstox.com

## Conclusion

Upstox API is an excellent choice for Indian stocks if you have or can open an Upstox account. The data quality is superior to Yahoo Finance and matches TradingView perfectly. The only downside is the need for an account and ISIN-based symbol format, but the improved accuracy makes it worth it.

**Recommended:** If you're serious about accurate Indian stock data, use Upstox or DhanHQ instead of Yahoo Finance.

