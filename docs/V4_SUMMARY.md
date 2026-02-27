# V4 Level Finder - Summary & Comparison

## Key Differences: Scalp Code vs V3

### 1. Total Move Threshold
- **Scalp Code (V4):** 3.5% minimum rally move
- **V3:** 10% minimum rally move
- **Why:** Smaller timeframes have smaller percentage moves

### 2. Small Red Body Condition
- **Scalp Code (V4):** Body < 30% of open price
- **V3:** Body < 3% of open price  
- **Why:** The scalp code uses 0.3 (30%) not 0.03 (3%) - this is more realistic for small timeframes

### 3. Timeframe Focus
- **V4:** Designed for 4h, 1h, 15min timeframes
- **V3:** Designed for weekly/monthly timeframes

## V4 Test Results

### XAU/USD @ 4h Timeframe
✅ **Successfully found 4 zones:**

1. At=2026-02-04 15:00 | TOP=4932.80 BOTTOM=4926.48 | Rally=3 Move=3.69%
2. At=2026-01-28 15:00 | TOP=5088.05 BOTTOM=5077.44 | Rally=5 Move=4.74%
3. At=2026-01-21 19:00 | TOP=4670.79 BOTTOM=4666.00 | Rally=9 Move=4.39%
4. At=2025-05-16 03:00 | TOP=3188.25 BOTTOM=3181.20 | Rally=4 Move=3.96%

**Analysis:**
- V4 works well for 4h timeframe on XAU/USD
- Found recent zones with 3.5-4.7% moves
- Rally lengths: 3-9 candles (reasonable for 4h)

## V3 Issue with EUR/USD

### Problem
V3 is not finding levels for EUR/USD on weekly timeframe because:

1. **10% threshold too high:** Forex pairs like EUR/USD rarely move 10% in a weekly rally
2. **3% body condition too strict:** The small red candle body must be < 3% of open, which is very rare

### Solution Options

#### Option 1: Use V4 for EUR/USD on Daily/4h
```python
python v4.py
# Enter: EUR/USD
# Enter: 1day or 4h
```

#### Option 2: Create V3_Forex variant with adjusted thresholds
- Total move: 5% instead of 10%
- Small red body: 1% instead of 0.3%
- This would work better for forex pairs

## Recommendations

### For Crypto (BTC, ETH, etc.)
- **Use V3** with weekly/monthly timeframes
- 10% moves are common in crypto

### For Forex (EUR/USD, GBP/USD, etc.)
- **Use V4** with daily or 4h timeframes
- Or create V3_Forex with 5% threshold

### For Gold (XAU/USD)
- **V3** for weekly/monthly (10% moves happen)
- **V4** for 4h/1h (tested and working)

## Code Comparison

### V3 (Weekly/Monthly - Crypto)
```python
total_move_threshold = 10%  # Large moves
small_body = < 0.03 * open  # 3% of open
rally_min = 3 candles
```

### V4 (4h/1h - Small Timeframes)
```python
total_move_threshold = 3.5%  # Smaller moves
small_body = < 0.30 * open   # 30% of open (from scalp code)
rally_min = 3 candles
```

### Scalp Code (Original TradingView)
```pinescript
totalMove >= 3.5%           // 3.5% threshold
bodySize < 0.3 * open       // 30% of open (0.3 not 0.03!)
rallyLength >= 3
```

## Files Created

1. **v4.py** - Small timeframe level finder (4h, 1h, 15min)
2. **test_v4_xauusd.py** - Test script for XAU/USD @ 4h
3. **test_v3_eurusd.py** - Test script for EUR/USD @ 1week (shows the issue)

## Next Steps

1. ✅ V4 works for XAU/USD @ 4h
2. ❌ V3 doesn't work for EUR/USD @ weekly (threshold too high)
3. 💡 Consider creating V3_Forex with 5% threshold for forex pairs
4. 💡 Or use V4 with daily/4h timeframes for forex

## Usage

### V4 for Small Timeframes
```bash
python v4.py
# Enter symbol: XAU/USD
# Enter interval: 4h
```

### V3 for Weekly/Monthly
```bash
python v3.py
# Enter symbol: BTCUSDT
# Works best for crypto with large moves
```

## TwelveData Interval Names
- `1min`, `5min`, `15min`, `30min`, `45min`
- `1h`, `2h`, `4h`, `8h`
- `1day`, `1week`, `1month`

Note: Use `1week` not `1w`, `1day` not `1d`
