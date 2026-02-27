# MongoDB Storage Format for Indian Stock Levels

## Source Data (TradingView OCR - Weekly Timeframe)

From `tradingview_levels_20260225_120752.json`:

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "market_type": "indian_stock",
  "support_levels": [1483.0, 1291.0, 1216.55, 1166.15, 1107.2, 1086.75, 975.65, 880.15, 880.1, 805.0],
  "resistance_levels": [],
  "timestamp": "2026-02-25 12:07:52",
  "source": "TradingView Simple OCR"
}
```

## MongoDB Document Structure

When pushed to MongoDB `delta_tracker.monitored_scrips` collection:

```json
{
  "_id": ObjectId("..."),
  "symbol": "RELIANCE",
  "timeframe": "1W",
  "interval": "60",
  "device_id": "web_app",
  "active": true,
  "last_updated": "2026-02-25T12:07:52",
  "source": "tradingview_weekly_ocr",
  "monitoring_type": "multi_level",
  "market_type": "indian_stock",
  "trigger_levels": [
    {
      "trigger_price": 1483.0,
      "bottom": 1483.0,
      "rally_end_high": 1483.0,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 0,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 1291.0,
      "bottom": 1291.0,
      "rally_end_high": 1291.0,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 1,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 1216.55,
      "bottom": 1216.55,
      "rally_end_high": 1216.55,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 2,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 1166.15,
      "bottom": 1166.15,
      "rally_end_high": 1166.15,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 3,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 1107.2,
      "bottom": 1107.2,
      "rally_end_high": 1107.2,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 4,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 1086.75,
      "bottom": 1086.75,
      "rally_end_high": 1086.75,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 5,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 975.65,
      "bottom": 975.65,
      "rally_end_high": 975.65,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 6,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 880.15,
      "bottom": 880.15,
      "rally_end_high": 880.15,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 7,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 880.1,
      "bottom": 880.1,
      "rally_end_high": 880.1,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 8,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    },
    {
      "trigger_price": 805.0,
      "bottom": 805.0,
      "rally_end_high": 805.0,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 9,
      "triggered": false,
      "alert_disabled": false,
      "last_checked": null,
      "timeframe": "1W"
    }
  ]
}
```

## Key Differences from Crypto/Forex

### Crypto/Forex Documents:
```json
{
  "symbol": "BTCUSDT",
  "market_type": "crypto",
  "timeframe": "1h",
  "trigger_levels": [
    {
      "trigger_price": 50000.0,
      "bottom": 49800.0,
      "rally_end_high": 52000.0,
      "small_red_time": "2026-02-20T10:00:00",
      "rally_length": 120,
      "total_move_pct": 4.2,
      "zone_index": 0,
      "triggered": false,
      "timeframe": "1h"
    }
  ]
}
```

### Indian Stock Documents:
```json
{
  "symbol": "RELIANCE",
  "market_type": "indian_stock",
  "timeframe": "1W",
  "trigger_levels": [
    {
      "trigger_price": 1483.0,
      "bottom": 1483.0,
      "rally_end_high": 1483.0,
      "small_red_time": null,
      "rally_length": 0,
      "total_move_pct": 0,
      "zone_index": 0,
      "triggered": false,
      "timeframe": "1W"
    }
  ]
}
```

## Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `symbol` | string | Stock symbol | "RELIANCE" |
| `exchange` | string | Stock exchange | "NSE" |
| `market_type` | string | Market classification | "indian_stock" (vs "crypto" or "forex") |
| `timeframe` | string | Chart timeframe | "1W" (weekly), "1D" (daily), "1h" (hourly) |
| `interval` | string | Monitoring interval in minutes | "60" |
| `device_id` | string | Source device/app | "web_app" |
| `active` | boolean | Whether monitoring is active | true |
| `last_updated` | string (ISO) | Last update timestamp | "2026-02-25T12:07:52" |
| `source` | string | Data source | "tradingview_weekly_ocr" |
| `monitoring_type` | string | Type of monitoring | "multi_level" |
| `trigger_levels` | array | Array of support/resistance levels | See below |

### Trigger Level Fields

| Field | Type | Description | Stock Value | Crypto/Forex Value |
|-------|------|-------------|-------------|-------------------|
| `trigger_price` | float | Price level to monitor | 1483.0 | 50000.0 |
| `bottom` | float | Bottom of support zone | 1483.0 (same) | 49800.0 (calculated) |
| `rally_end_high` | float | High after rally | 1483.0 (same) | 52000.0 (calculated) |
| `small_red_time` | string/null | Time of small red candle | null (not calculated) | "2026-02-20T10:00:00" |
| `rally_length` | int | Length of rally in candles | 0 (not calculated) | 120 |
| `total_move_pct` | float | Total move percentage | 0 (not calculated) | 4.2 |
| `zone_index` | int | Index in array | 0, 1, 2... | 0, 1, 2... |
| `triggered` | boolean | Whether level was hit | false | false |
| `alert_disabled` | boolean | Whether alerts are disabled | false | false |
| `last_checked` | string/null | Last price check time | null | "2026-02-25T12:00:00" |
| `timeframe` | string | Timeframe for this level | "1W" | "1h" |

## Summary

For Indian stocks from TradingView OCR:
- `market_type` = "indian_stock" (NOT "crypto" or "forex")
- `timeframe` = "1W" (weekly analysis)
- `trigger_price` = `bottom` = `rally_end_high` (simple support levels, no zone calculation)
- `small_red_time`, `rally_length`, `total_move_pct` = null/0 (not calculated from OCR)
- All levels are support levels (no resistance levels in current implementation)
