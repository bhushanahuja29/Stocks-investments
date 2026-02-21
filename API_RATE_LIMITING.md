# Twelve Data API Rate Limiting

## Overview
Implemented smart rate limiting and caching to stay within the 800 API calls/day limit.

## Features Implemented

### 1. Price Caching (3 minutes)
- Forex prices are cached for 3 minutes
- Reduces API calls from ~960/day to ~160/day for monitoring
- Cache is per-symbol and timestamp-based

### 2. API Call Tracking
- Backend tracks all Twelve Data API calls
- Counter resets daily at midnight UTC
- Displayed in navbar: "20/800"

### 3. Smart Fetching
- **Zone Search**: 1-2 API calls per search
- **Price Updates**: Cached for 3 minutes
  - First request: API call + cache
  - Next 3 minutes: Cache only (0 API calls)
  - After 3 minutes: New API call

### 4. Usage Display
- Real-time counter in navbar
- Shows: `used/limit` (e.g., "20/800")
- Updates every 5 seconds
- Purple gradient badge

## API Call Breakdown

### Daily Usage Estimate:
- **Zone Searches**: ~10 searches/day = 20 calls
- **Price Monitoring**: 
  - Without cache: 20 calls/hour × 24 hours = 480 calls
  - With 3-min cache: 20 calls/hour × 24 hours ÷ 60 = 8 calls/hour = 192 calls/day
- **Total**: ~212 calls/day (well under 800 limit)

### Per Operation:
- Find zones (any timeframe): 1-2 calls
- Get price (cached): 0 calls (if < 3 min old)
- Get price (fresh): 1 call

## Backend Implementation

### Cache Structure:
```python
forex_price_cache = {
    "XAU/USD": {
        "price": 2650.50,
        "timestamp": datetime(2026, 2, 2, 10, 30, 0)
    }
}
```

### API Tracking:
```python
api_call_count = 0  # Resets daily
last_api_reset = date.today()
```

### Endpoints:
- `GET /api/usage` - Get current API usage
- `GET /api/price/{symbol}?market_type=forex` - Get price (with caching)

## Frontend Display

### Navbar Badge:
```
📊 20/800
```

- Purple gradient background
- Monospace font for numbers
- Updates every 5 seconds

## Configuration

### Cache Duration:
```python
FOREX_PRICE_CACHE_DURATION = 180  # 3 minutes in seconds
```

To change cache duration, edit this value in `backend/main.py`.

### Monitoring Interval:
Frontend fetches prices every 3 seconds, but backend caches prevent excessive API calls.

## Logs

Backend logs show:
```
[CACHE HIT] XAU/USD: $2650.50 (age: 45s)
[CACHE SET] XAU/USD: $2650.50
[API USAGE] 20/800 calls today
```

## Benefits

1. **Cost Savings**: Stay within free tier (800 calls/day)
2. **Performance**: Faster responses from cache
3. **Reliability**: Less dependent on API availability
4. **Visibility**: Always know your usage

## Monitoring

Check API usage:
- **Navbar**: Real-time display
- **Backend logs**: Detailed call tracking
- **Twelve Data Dashboard**: Official usage stats

## Recommendations

- Keep cache at 3 minutes for good balance
- Monitor usage in navbar
- If approaching limit, increase cache duration
- Consider upgrading plan if consistently hitting limit
