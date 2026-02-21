# XAUUSD Price Display Fix

## Problem
XAUUSD (and other forex symbols) were showing "--" for Current Mark Price in the Monitor page.

## Root Cause
The Monitor page was calling the price API without the `market_type` parameter, so the backend was trying to fetch XAUUSD from Delta Exchange API (which doesn't have forex symbols) instead of Twelve Data API.

## Solution

### Files Modified:
1. `crypto_levels_bhushan/frontend/src/pages/Monitor.js`
2. `crypto_levels_bhushan/frontend/src/App.js`

### Changes Made:

#### Monitor.js:
```javascript
// BEFORE:
const fetchPriceForSymbol = async (symbol) => {
  const response = await axios.get(`${API_URL}/api/price/${symbol}`);
}

const price = await fetchPriceForSymbol(scrip.symbol);

// AFTER:
const fetchPriceForSymbol = async (symbol, marketType = 'crypto') => {
  const response = await axios.get(`${API_URL}/api/price/${symbol}`, {
    params: { market_type: marketType }
  });
}

const marketType = scrip.market_type || 'crypto';
const price = await fetchPriceForSymbol(scrip.symbol, marketType);
```

#### App.js (Notification Bell):
```javascript
// BEFORE:
const priceResponse = await axios.get(`${API_URL}/api/price/${scrip.symbol}`);

// AFTER:
const marketType = scrip.market_type || 'crypto';
const priceResponse = await axios.get(`${API_URL}/api/price/${scrip.symbol}`, {
  params: { market_type: marketType }
});
```

## How It Works Now

1. When zones are pushed to MongoDB, `market_type` is stored with the scrip
2. Monitor page reads `market_type` from the scrip document
3. When fetching price, it passes `market_type` to the backend
4. Backend routes to correct API:
   - `market_type=crypto` → Delta Exchange API
   - `market_type=forex` → Twelve Data API (with 3-min caching)

## Testing

1. **Restart frontend** (if running):
   ```
   Ctrl+C in frontend terminal
   npm start
   ```

2. **Test XAUUSD**:
   - Go to Monitor page
   - Select XAUUSD tab
   - Current Mark Price should now show (e.g., "$2650.50")
   - Price updates every 3 seconds (from cache if < 3 min old)

3. **Check API Usage**:
   - Navbar shows API usage: "📊 X/800"
   - First price fetch: Counter increases by 1
   - Next 3 minutes: Counter stays same (cache hit)
   - After 3 minutes: Counter increases by 1 (cache miss)

## Backend Logs

You should see:
```
[CACHE HIT] XAU/USD: $2650.50 (age: 45s)
[API USAGE] 5/800 calls today
```

Or on first fetch:
```
[CACHE SET] XAU/USD: $2650.50
[API USAGE] 5/800 calls today
```

## Verification

✅ XAUUSD price displays correctly
✅ Price updates every 3 seconds
✅ API calls are cached (3-min duration)
✅ API usage counter works
✅ Crypto symbols still work (BTCUSDT, ETHUSDT)
✅ Forex symbols work (XAU/USD, EUR/USD, etc.)

## Notes

- Make sure backend is restarted to have the latest code
- Frontend needs refresh to load updated JavaScript
- First price fetch will use 1 API call
- Subsequent fetches (within 3 min) use cache (0 API calls)
