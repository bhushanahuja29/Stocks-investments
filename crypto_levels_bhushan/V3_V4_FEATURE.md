# V3 vs V4 Algorithm Selection Feature

## Overview
The Zone Finder now supports two algorithm versions: V3 (Standard) and V4 (Scalping). Users can toggle between them when searching for support zones.

## Key Differences

### V3 - Standard Algorithm (Original)
**Best for:** Weekly, Monthly timeframes and large moves

| Timeframe | Min Rally | Min Move % | Use Case |
|-----------|-----------|------------|----------|
| 1M (Monthly) | 2 candles | 15% | Long-term crypto trends |
| 1w (Weekly) | 3 candles | 10% | Standard crypto analysis |
| 1d (Daily) | 3 candles | 8% | Swing trading |
| 4h | 4 candles | 6% | Intraday positions |
| 1h | 5 candles | 5% | Short-term trades |

**Characteristics:**
- Higher move thresholds
- More conservative zone detection
- Fewer but stronger zones
- Best for crypto with high volatility

### V4 - Scalping Algorithm (New)
**Best for:** Forex pairs with small moves, all timeframes

| Timeframe | Min Rally | Min Move % | Use Case |
|-----------|-----------|------------|----------|
| 1M (Monthly) | 2 candles | 5% | Forex monthly analysis |
| 1w (Weekly) | 3 candles | 2% | Forex weekly trends |
| 1d (Daily) | 3 candles | 1.5% | Forex daily trading |
| 4h | 3 candles | 0.8% | Forex intraday & scalping |
| 1h | 3 candles | 0.5% | High-frequency forex scalping |

**Characteristics:**
- Very low move thresholds (optimized for forex)
- More sensitive zone detection
- Many more zones found
- Perfect for EUR/USD, GBP/USD and other forex pairs
- Small red body: 30% of open (same as Pine Script)

## Common Parameters (Both Versions)
- Small red body: < 30% of open price (0.3 * open)
- Average body condition: < 50% of 10-candle average
- Adjacent green candles required
- Start year filter: 2020+

## When to Use Each Version

### Use V3 When:
- ✅ Trading crypto (BTC, ETH, etc.)
- ✅ Using weekly or monthly timeframes
- ✅ Looking for major support zones
- ✅ Want fewer, stronger signals
- ✅ Swing trading or position trading

### Use V4 When:
- ✅ Trading forex pairs (EUR/USD, GBP/USD)
- ✅ Trading gold (XAU/USD) on small timeframes
- ✅ Using 4h or 1h timeframes
- ✅ Scalping or day trading
- ✅ Want more zone options
- ✅ Markets with smaller percentage moves

## UI Changes

### Frontend (ZoneFinder.js)
Added version selector with two buttons:
```
┌─────────────────────────┐
│ Algorithm Version       │
│ ┌────┐ ┌────┐          │
│ │ V3 │ │ V4 │          │
│ └────┘ └────┘          │
│ 📊 Standard (10% move) │
└─────────────────────────┘
```

### Visual Design
- V3 button: Standard blue theme
- V4 button: Purple gradient (active state)
- Tooltip hints on hover
- Dynamic hint text below buttons

## Backend Changes

### API Request
```json
{
  "symbol": "XAU/USD",
  "timeframe": "4h",
  "market_type": "forex",
  "version": "v4"  // NEW PARAMETER
}
```

### compute_zones_forex() Function
Now accepts `version` parameter and adjusts thresholds accordingly:
```python
def compute_zones_forex(symbol, timeframe="1w", version="v3"):
    if version == "v3":
        # Original thresholds
    else:  # v4
        # Lower thresholds for scalping
```

## Example Use Cases

### Example 1: BTC Weekly Analysis
- Symbol: BTCUSDT
- Timeframe: 1w
- Market: Crypto
- **Version: V3** ✅
- Result: Strong weekly support zones with 10%+ moves

### Example 2: Gold 4H Scalping
- Symbol: XAU/USD
- Timeframe: 4h
- Market: Forex
- **Version: V4** ✅
- Result: More frequent zones with 3.5%+ moves

### Example 3: EUR/USD Daily
- Symbol: EUR/USD
- Timeframe: 1d
- Market: Forex
- **Version: V4** ✅
- Result: Daily support zones with 4%+ moves (V3 would find very few)

## Testing Results

### XAU/USD @ 4h with V4
✅ Found 4 zones with moves: 3.69%, 4.74%, 4.39%, 3.96%

### EUR/USD with V4 (Updated Thresholds)
✅ 1h: 1 zone (0.52% move)
✅ 4h: 3 zones (0.85-1.43% moves)
✅ 1d: 1 zone (2.63% move)
✅ 1w: 3 zones (2.49-4.65% moves)
✅ 1M: 1 zone (10.88% move)

### EUR/USD @ 1w with V3
❌ Found 0 zones (10% threshold too high for forex)

## Files Modified

1. **frontend/src/pages/ZoneFinder.js**
   - Added `version` state
   - Added version toggle UI
   - Pass version to API

2. **frontend/src/pages/ZoneFinder.css**
   - Added `.version-toggle` styles
   - Added `.version-btn` styles
   - Added `.version-hint` styles
   - Updated grid layout

3. **backend/main.py**
   - Updated `ZoneSearchRequest` model
   - Updated `search_zones()` endpoint
   - Updated `compute_zones_forex()` function
   - Added V4 threshold logic

## Recommendations

### For Crypto Traders
- Use **V3** for weekly/monthly analysis
- Use **V4** for 4h/1h scalping

### For Forex Traders
- Use **V4** for most timeframes
- V3 may be too strict for forex pairs

### For Gold Traders
- Use **V3** for weekly/monthly
- Use **V4** for 4h/1h intraday

## Future Enhancements

1. Auto-suggest version based on:
   - Market type (crypto → V3, forex → V4)
   - Timeframe (weekly → V3, 4h → V4)

2. Custom threshold editor for advanced users

3. Backtest results showing V3 vs V4 performance

4. Version-specific zone coloring in Monitor

## Migration Notes

- Existing zones in database are V3-based
- New searches can use either version
- No breaking changes to existing functionality
- Default version is V3 (backward compatible)
