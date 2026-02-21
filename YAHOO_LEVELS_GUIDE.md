# Yahoo Finance Support Levels Finder

Find support levels for Forex, Gold, Silver, and other instruments using Yahoo Finance data.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_yahoo.txt
```

### 2. Run the Script
```bash
python yahoo_levels_finder.py
```

### 3. Enter Symbol and Timeframe
```
Enter symbol: GC=F
Enter timeframe: 1w
```

## 📊 Available Symbols

### Forex Pairs
- `EURUSD=X` - Euro/US Dollar
- `GBPUSD=X` - British Pound/US Dollar  
- `USDJPY=X` - US Dollar/Japanese Yen
- `AUDUSD=X` - Australian Dollar/US Dollar
- `NZDUSD=X` - New Zealand Dollar/US Dollar
- `USDCAD=X` - US Dollar/Canadian Dollar
- `USDCHF=X` - US Dollar/Swiss Franc
- `USDINR=X` - US Dollar/Indian Rupee
- `EURINR=X` - Euro/Indian Rupee
- `GBPINR=X` - British Pound/Indian Rupee

### Precious Metals
- `GC=F` - Gold Futures (XAU/USD)
- `SI=F` - Silver Futures (XAG/USD)
- `PL=F` - Platinum Futures
- `PA=F` - Palladium Futures
- `HG=F` - Copper Futures

### Indices
- `^GSPC` - S&P 500
- `^DJI` - Dow Jones Industrial Average
- `^IXIC` - NASDAQ Composite
- `^NSEI` - Nifty 50 (India)
- `^BSESN` - BSE Sensex (India)

### Commodities
- `CL=F` - Crude Oil
- `NG=F` - Natural Gas
- `ZC=F` - Corn
- `ZW=F` - Wheat

## ⏰ Timeframes

- `1M` - Monthly (10 years of data)
- `1w` - Weekly (5 years of data)
- `1d` - Daily (2 years of data)
- `4h` - 4 Hour (60 days of data)
- `1h` - 1 Hour (60 days of data)

## 📝 Example Output

```
==============================================================
RESULTS: GC=F - 1W
==============================================================
Total zones found: 8

#    Date         TOP          BOTTOM       Rally    Move %  
------------------------------------------------------------
1    2023-10-15   $1950.00     $1945.00     5        12.5%
2    2023-08-20   $1920.00     $1915.00     4        10.8%
3    2023-06-10   $1880.00     $1875.00     6        15.2%
...
```

## 🔧 How It Works

1. **Fetches Data:** Downloads historical price data from Yahoo Finance
2. **Resamples:** Converts to requested timeframe (weekly, monthly, etc.)
3. **Analyzes:** Looks for support zones using rally patterns
4. **Filters:** Finds small red candles after strong rallies
5. **Returns:** List of support levels with prices and dates

## 💡 Tips

### For Gold (GC=F):
- Use Weekly (1w) for long-term support
- Use Daily (1d) for swing trading
- Use 4H for day trading

### For Forex:
- Weekly works best for major pairs
- Daily for short-term trading
- 1H for scalping

### For Indian Markets:
- `^NSEI` (Nifty 50) - Use Weekly/Daily
- `USDINR=X` - Use Daily/4H
- `EURINR=X` - Use Daily

## ⚠️ Limitations

- **Data Availability:** Yahoo Finance may have limited intraday data
- **Delays:** Data may be delayed 15-20 minutes
- **No Volume:** Forex pairs don't have volume data
- **Rate Limits:** No official limits, but don't abuse

## 🆚 vs Delta Exchange

| Feature | Yahoo Finance | Delta Exchange |
|---------|---------------|----------------|
| **Cost** | Free | Free |
| **Forex** | ✅ Yes | ❌ No |
| **Crypto** | ✅ Limited | ✅ Full |
| **Gold/Silver** | ✅ Yes | ❌ No |
| **Indian Markets** | ✅ Yes | ❌ No |
| **Real-time** | ❌ Delayed | ✅ Real-time |
| **API Key** | ❌ Not needed | ❌ Not needed |

## 🚀 Next Steps

1. **Test with different symbols**
2. **Try different timeframes**
3. **Compare with your current levels**
4. **Integrate into your monitoring system**

## 📞 Support

If you get errors:
- Check symbol is correct (use Yahoo Finance website to verify)
- Try different timeframe
- Check internet connection
- Update yfinance: `pip install --upgrade yfinance`

---

**Created:** January 2026
**Works in:** India and worldwide
**No API Key Required**
