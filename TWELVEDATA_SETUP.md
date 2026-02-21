# Twelve Data Setup Guide

## ✅ Works in India | 800 Free API Calls/Day

### Step 1: Get Free API Key

1. Go to: **https://twelvedata.com/**
2. Click "Get Free API Key" or "Sign Up"
3. Enter your email and create password
4. Verify your email
5. Copy your API key from dashboard

**No credit card required!**

### Step 2: Install Dependencies

```bash
pip install requests
```

### Step 3: Add API Key to Script

Open `twelvedata_levels_finder.py` and replace:

```python
TWELVE_DATA_API_KEY = "YOUR_API_KEY_HERE"
```

With your actual key:

```python
TWELVE_DATA_API_KEY = "abc123xyz456..."  # Your key here
```

### Step 4: Run the Script

```bash
python twelvedata_levels_finder.py
```

### Step 5: Enter Symbol

```
Enter symbol: XAU/USD
Enter timeframe: 1w
```

## 📊 Available Symbols

### Forex (120+ pairs)
- `EUR/USD` - Euro/US Dollar
- `GBP/USD` - British Pound/US Dollar
- `USD/JPY` - US Dollar/Japanese Yen
- `AUD/USD` - Australian Dollar/US Dollar
- `USD/CAD` - US Dollar/Canadian Dollar
- `USD/CHF` - US Dollar/Swiss Franc
- `NZD/USD` - New Zealand Dollar/US Dollar
- `USD/INR` - US Dollar/Indian Rupee ✅
- `EUR/INR` - Euro/Indian Rupee ✅
- `GBP/INR` - British Pound/Indian Rupee ✅

### Precious Metals
- `XAU/USD` - Gold ✅
- `XAG/USD` - Silver ✅
- `XPT/USD` - Platinum
- `XPD/USD` - Palladium

### Crypto
- `BTC/USD` - Bitcoin
- `ETH/USD` - Ethereum
- `BNB/USD` - Binance Coin
- `XRP/USD` - Ripple
- `ADA/USD` - Cardano

### Indices
- `SPX` - S&P 500
- `DJI` - Dow Jones
- `IXIC` - NASDAQ
- `NIFTY` - Nifty 50 (India) ✅
- `SENSEX` - BSE Sensex (India) ✅

### Commodities
- `WTI/USD` - Crude Oil
- `BRENT/USD` - Brent Oil
- `NG/USD` - Natural Gas

## ⏰ Timeframes

- `1M` - Monthly
- `1w` - Weekly  
- `1d` - Daily
- `4h` - 4 Hour
- `1h` - 1 Hour
- `30min` - 30 Minutes
- `15min` - 15 Minutes
- `5min` - 5 Minutes
- `1min` - 1 Minute

## 📈 Example Output

```
==============================================================
RESULTS: XAU/USD - 1W
==============================================================
Total zones found: 12

#    Date         TOP          BOTTOM       Rally High   Rally    Move %  
--------------------------------------------------------------------------------
1    2024-11-18   $3344.14     $3331.75     $4530.00     9        32.9%
2    2024-05-20   $2611.38     $2607.18     $2911.44     6        11.6%
3    2020-07-27   $1733.37     $1729.57     $2072.90     9        19.9%
...

==============================================================
API calls used: 1-2 (800 daily limit)
==============================================================
```

### Understanding the Output

- **TOP**: Support zone top (trigger price for alerts)
- **BOTTOM**: Support zone bottom
- **Rally High**: Resistance level (top of the rally) - NEW!
- **Date**: When the support zone was formed
- **Rally**: Number of consecutive green candles
- **Move %**: Total rally percentage move

## 💡 Tips

### API Call Management
- Each symbol search = 1-2 API calls
- 800 calls/day = ~400 symbol searches
- Resets every 24 hours
- Check usage at: https://twelvedata.com/account

### Best Symbols for India
- **USD/INR** - Most liquid INR pair
- **XAU/USD** - Gold (very popular)
- **NIFTY** - Indian stock index
- **EUR/USD** - Most liquid forex pair

### Recommended Timeframes
- **Gold (XAU/USD):** Weekly (1w) or Daily (1d)
- **Forex:** Daily (1d) or 4H
- **Indices:** Weekly (1w) or Daily (1d)

## ⚠️ Troubleshooting

### Error: "Please set your API key"
- Edit `twelvedata_levels_finder.py`
- Replace `YOUR_API_KEY_HERE` with your actual key

### Error: "Rate limit exceeded"
- You've used 800 calls today
- Wait 24 hours for reset
- Or upgrade plan (paid)

### Error: "No data found"
- Check symbol format (use `/` for forex: `EUR/USD`)
- Try different symbol
- Verify symbol exists on Twelve Data website

### Error: "Network error"
- Check internet connection
- Try again in a few seconds
- Check if Twelve Data is down

## 🆚 Comparison

| Feature | Twelve Data | Yahoo Finance |
|---------|-------------|---------------|
| **Free Calls** | 800/day | Unlimited |
| **Forex** | ✅ 120+ pairs | ✅ Limited |
| **Gold** | ✅ XAU/USD | ✅ GC=F |
| **Indian Markets** | ✅ Yes | ✅ Yes |
| **API Key** | ✅ Required | ❌ Not needed |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Data Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Works in India** | ✅ Yes | ⚠️ Sometimes |

## 🚀 Why Twelve Data?

1. ✅ **Works in India** - No restrictions
2. ✅ **800 free calls/day** - Plenty for testing
3. ✅ **High quality data** - Professional grade
4. ✅ **All timeframes** - 1min to 1month
5. ✅ **Forex + Gold + Crypto** - Everything you need
6. ✅ **Easy API** - Simple to use
7. ✅ **No credit card** - Free tier forever

## 📞 Support

**Twelve Data:**
- Website: https://twelvedata.com/
- Docs: https://twelvedata.com/docs
- Support: support@twelvedata.com

**This Script:**
- Check symbol format
- Verify API key is correct
- Ensure internet connection
- Try different timeframe

---

**Status:** ✅ Working in India
**Cost:** Free (800 calls/day)
**Setup Time:** 2 minutes
