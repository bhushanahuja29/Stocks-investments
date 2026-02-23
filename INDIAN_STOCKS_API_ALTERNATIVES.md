# Indian Stocks API Alternatives - Data Quality Comparison

## Issue
Yahoo Finance data for Indian stocks differs from TradingView, causing discrepancies in support/resistance levels.

## Root Cause
Different data providers may have:
- Different data sources (NSE direct vs aggregators)
- Different adjustment methods (splits, dividends, bonuses)
- Different time zones (IST vs UTC)
- Different data cleaning processes
- Delayed vs real-time data

## Alternative APIs for Indian Stocks

### 1. DhanHQ API ⭐ RECOMMENDED
**Website:** https://dhanhq.co/docs/v1/historical-data/

**Pros:**
- ✅ FREE for personal use
- ✅ Direct NSE/BSE data (better accuracy)
- ✅ Historical daily data back to inception
- ✅ Intraday 1-minute candles
- ✅ Supports NSE_EQ, BSE_EQ, NSE_FNO, MCX
- ✅ Clean OHLCV format
- ✅ Python SDK available
- ✅ Good documentation

**Cons:**
- ⚠️ Requires DhanHQ account (free to create)
- ⚠️ Need API key (free)
- ⚠️ Rate limits (not specified, likely generous)

**Data Quality:** HIGH - Direct from exchange

**Symbol Format:** `RELIANCE` with `exchange_segment="NSE_EQ"`

**Example:**
```python
from dhanhq import dhanhq

dhan = dhanhq("client_id", "access_token")
data = dhan.historical_daily_data(
    symbol="RELIANCE",
    exchange_segment="NSE_EQ",
    instrument_type="EQUITY",
    from_date="2020-01-01",
    to_date="2024-01-01"
)
```

### 2. NSE India Official (Web Scraping)
**Website:** https://www.nseindia.com/

**Pros:**
- ✅ FREE
- ✅ Most accurate (direct from source)
- ✅ Real-time data
- ✅ No API key needed

**Cons:**
- ❌ No official API
- ❌ Requires web scraping
- ❌ Needs headers to bypass bot detection
- ❌ May break if website changes
- ❌ Rate limiting / IP blocking risk
- ❌ More complex implementation

**Data Quality:** HIGHEST - Direct from exchange

**Implementation:** Use libraries like `nse-python` or custom scraping

### 3. Alpha Vantage
**Website:** https://www.alphavantage.co/

**Pros:**
- ✅ FREE tier (500 calls/day)
- ✅ Official API with documentation
- ✅ Reliable service

**Cons:**
- ❌ Only BSE stocks (no NSE)
- ❌ Limited quota (500 calls/day)
- ❌ Requires API key
- ❌ BSE has lower liquidity than NSE

**Data Quality:** MEDIUM - BSE only

**Symbol Format:** `RELIANCE.BSE`

### 4. TwelveData (Paid)
**Website:** https://twelvedata.com/

**Pros:**
- ✅ High quality data
- ✅ Good documentation
- ✅ Already integrated for forex

**Cons:**
- ❌ Requires paid "Grow" plan ($79/month)
- ❌ 800 calls/day on Grow plan
- ❌ Expensive for personal use

**Data Quality:** HIGH

### 5. Upstox API
**Website:** https://upstox.com/developer/

**Pros:**
- ✅ FREE for Upstox users
- ✅ Direct NSE/BSE data
- ✅ Historical candle data
- ✅ Good documentation

**Cons:**
- ⚠️ Requires Upstox trading account
- ⚠️ Need to be a customer

**Data Quality:** HIGH - Direct from exchange

### 6. Zerodha Kite Connect (Paid)
**Website:** https://kite.trade/

**Pros:**
- ✅ Excellent data quality
- ✅ Real-time data
- ✅ Comprehensive API

**Cons:**
- ❌ Costs ₹2000/month
- ❌ Requires Zerodha account
- ❌ Expensive

**Data Quality:** HIGHEST

### 7. Yahoo Finance (Current)
**Website:** yfinance library

**Pros:**
- ✅ FREE, unlimited
- ✅ No API key needed
- ✅ Easy to use
- ✅ Already implemented

**Cons:**
- ⚠️ Data quality issues (adjustments differ from TradingView)
- ⚠️ Occasional data gaps
- ⚠️ Not official source

**Data Quality:** MEDIUM - Data discrepancies with TradingView

## Recommended Solution: DhanHQ API

### Why DhanHQ?
1. **Free** - No cost for personal use
2. **Accurate** - Direct NSE/BSE data
3. **Easy** - Good documentation and Python SDK
4. **Reliable** - Backed by a regulated broker
5. **Complete** - Historical data back to inception

### Implementation Steps

#### 1. Create DhanHQ Account
- Visit https://dhanhq.co/
- Sign up for free account
- Get API credentials (client_id and access_token)

#### 2. Install DhanHQ Python SDK
```bash
pip install dhanhq
```

#### 3. Update Backend Code
Replace `fetch_yahoo_data_indian()` with `fetch_dhanhq_data()`:

```python
from dhanhq import dhanhq

def fetch_dhanhq_data(symbol: str, period: str = "2y", interval: str = "1d"):
    """Fetch Indian stock data from DhanHQ"""
    
    # Initialize DhanHQ client
    dhan = dhanhq(
        client_id=os.getenv("DHANHQ_CLIENT_ID"),
        access_token=os.getenv("DHANHQ_ACCESS_TOKEN")
    )
    
    # Calculate date range
    end_date = datetime.now()
    if period == "2y":
        start_date = end_date - timedelta(days=730)
    elif period == "5y":
        start_date = end_date - timedelta(days=1825)
    elif period == "10y":
        start_date = end_date - timedelta(days=3650)
    
    # Fetch data
    response = dhan.historical_daily_data(
        symbol=symbol,
        exchange_segment="NSE_EQ",
        instrument_type="EQUITY",
        from_date=start_date.strftime("%Y-%m-%d"),
        to_date=end_date.strftime("%Y-%m-%d")
    )
    
    # Convert to our format
    candles = []
    for i in range(len(response['start_Time'])):
        candles.append({
            "time": convert_dhanhq_timestamp(response['start_Time'][i]),
            "open": response['open'][i],
            "high": response['high'][i],
            "low": response['low'][i],
            "close": response['close'][i],
            "volume": response['volume'][i]
        })
    
    return candles

def convert_dhanhq_timestamp(dhan_ts):
    """Convert DhanHQ custom epoch to Unix timestamp"""
    # DhanHQ epoch starts from 1 Jan 1980 IST
    base_time = datetime(1980, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    return int((base_time + timedelta(seconds=dhan_ts)).timestamp())
```

#### 4. Add Environment Variables
```bash
# .env file
DHANHQ_CLIENT_ID=your_client_id
DHANHQ_ACCESS_TOKEN=your_access_token
```

#### 5. Test
```bash
python test_indian_stocks_dhanhq.py
```

### Data Quality Comparison

| API | Accuracy | Matches TradingView | Cost | Setup Difficulty |
|-----|----------|---------------------|------|------------------|
| DhanHQ | ⭐⭐⭐⭐⭐ | ✅ Yes | FREE | Easy |
| NSE Official | ⭐⭐⭐⭐⭐ | ✅ Yes | FREE | Hard |
| Upstox | ⭐⭐⭐⭐⭐ | ✅ Yes | FREE* | Easy |
| Zerodha | ⭐⭐⭐⭐⭐ | ✅ Yes | ₹2000/mo | Easy |
| TwelveData | ⭐⭐⭐⭐ | ✅ Yes | $79/mo | Easy |
| Alpha Vantage | ⭐⭐⭐ | ⚠️ BSE only | FREE | Easy |
| Yahoo Finance | ⭐⭐⭐ | ❌ No | FREE | Easy |

*Requires trading account

## Quick Fix: Adjust Yahoo Finance Data

If you want to stick with Yahoo Finance but improve accuracy:

### Option A: Use Adjusted Close
```python
# Use adjusted close instead of close
candles.append({
    "close": fnum(row['Close']),  # Use adjusted close
    # ... other fields
})
```

### Option B: Disable Adjustments
```python
ticker = yf.Ticker(symbol)
df = ticker.history(period=period, interval=interval, auto_adjust=False)
```

### Option C: Manual Adjustment
Compare with TradingView and apply correction factor:
```python
# If Yahoo shows 1500 but TradingView shows 1485
correction_factor = 1485 / 1500  # 0.99
adjusted_price = yahoo_price * correction_factor
```

## Recommendation

**For Best Data Quality:**
1. Use DhanHQ API (free, accurate, easy)
2. Create free account at https://dhanhq.co/
3. Get API credentials
4. Update backend to use DhanHQ
5. Test and compare with TradingView

**For Quick Fix:**
1. Try `auto_adjust=False` in yfinance
2. Compare results with TradingView
3. If still different, switch to DhanHQ

## Next Steps

1. ✅ Document alternatives (this file)
2. ⏳ Create DhanHQ account
3. ⏳ Get API credentials
4. ⏳ Implement DhanHQ integration
5. ⏳ Test data quality vs TradingView
6. ⏳ Update documentation

## Support

If you need help:
- DhanHQ Docs: https://dhanhq.co/docs/
- DhanHQ Support: support@dhanhq.co
- NSE Data: https://www.nseindia.com/market-data

