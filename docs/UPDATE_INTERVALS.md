# Price Update Intervals

## Changes Made

### Update Frequencies:
- **Crypto (Delta API)**: Every 20 seconds
- **Forex (Twelve Data)**: Every 20 seconds (but cached for 3 minutes)

### Why These Intervals?

#### Crypto - 20 seconds:
- Delta API is free and unlimited
- 20 seconds is frequent enough for monitoring
- Reduces unnecessary API calls
- Still responsive for price alerts

#### Forex - 3 minutes (cached):
- Twelve Data has 800 calls/day limit
- Backend caches prices for 3 minutes
- Frontend requests every 20 seconds, but gets cached response
- Actual API calls: ~480/day (well under 800 limit)

## Display Updates

### Price Display:
```
Current Mark Price
$2650.5000

💱 Twelve Data  (or 🪙 Delta Exchange)
```

### Status Row:
```
● Monitoring all levels    Last updated: 10:30:45 AM
```

### Auto-Monitoring Badge:
```
● Auto-Monitoring 4 Scrip(s)
Updates every 20 seconds (Crypto) / 3 minutes (Forex cached)
```

## API Call Optimization

### Before:
- Update interval: 3 seconds
- Forex API calls: ~28,800/day (way over limit!)
- Crypto API calls: ~28,800/day (unnecessary)

### After:
- Update interval: 20 seconds
- Forex API calls: ~480/day (cached to ~160/day)
- Crypto API calls: ~4,320/day (free, no limit)

### Savings:
- Forex: 98% reduction in API calls
- Crypto: 85% reduction in requests
- Still responsive for monitoring

## Cache Behavior

### First Request (Forex):
```
Frontend → Backend → Twelve Data API → Cache → Frontend
API Call: 1
```

### Subsequent Requests (< 3 min):
```
Frontend → Backend → Cache → Frontend
API Call: 0
```

### After 3 Minutes:
```
Frontend → Backend → Twelve Data API → Cache → Frontend
API Call: 1
```

## User Experience

### What Users See:
1. **Price updates every 20 seconds**
2. **Last updated time** shows when price was fetched
3. **Data source indicator** (Twelve Data or Delta Exchange)
4. **Smooth monitoring** without delays

### What Happens Behind the Scenes:
1. **Crypto**: Fresh data every 20 seconds from Delta
2. **Forex**: Cached data (< 3 min old) or fresh from Twelve Data
3. **API usage tracked** and displayed in navbar

## Testing

### Verify Update Interval:
1. Open Monitor page
2. Watch "Last updated" time
3. Should update every 20 seconds

### Verify Caching (Forex):
1. Select XAUUSD
2. Watch backend logs
3. First request: `[API USAGE] X/800`
4. Next 20 seconds: No API call (cache hit)
5. After 3 minutes: `[API USAGE] X+1/800`

### Verify API Usage:
1. Check navbar: 📊 X/800
2. Should increase slowly (not rapidly)
3. Estimate: ~20 calls/hour for forex monitoring

## Configuration

To change intervals, edit `Monitor.js`:

```javascript
// Line ~209
const interval = setInterval(fetchAllPrices, 20000); // 20 seconds
```

To change cache duration, edit `backend/main.py`:

```python
# Line ~27
FOREX_PRICE_CACHE_DURATION = 180  # 3 minutes in seconds
```

## Benefits

✅ Reduced API calls by 98%
✅ Stay within 800/day limit
✅ Responsive monitoring (20s updates)
✅ Clear last updated time
✅ Data source transparency
✅ Better user experience
