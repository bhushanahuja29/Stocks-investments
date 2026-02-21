# Delta Exchange Monitor

Real-time cryptocurrency price monitoring with alerts for Delta Exchange India.

## 📁 Projects

### Desktop App (Python)
**File:** `delta_monitor_modern.py`

Modern minimalistic desktop app with multi-tab monitoring.

**Run:**
```bash
pip install -r requirements.txt
python delta_monitor_modern.py
```

**Features:**
- Multi-tab Chrome-style interface
- Real-time price monitoring with visual progress bar
- Audio alerts when trigger price is reached
- **Direct link to Delta Exchange** - Click to open trading page
- MongoDB sync across devices
- Timeframe tracking (5M, 15M, 30M, 1H, 4H, 1D, 1W)
- API usage tracking
- Clean Material Design UI
- Scrollable and resizable interface

---

### Mobile App (React Native + Expo)
**Folder:** `delta-monitor/`

Cross-platform mobile app for Android/iOS.

**Setup:**
```bash
cd delta-monitor
npm install
```

**Run on Phone:**
```bash
npx expo start
# Scan QR code with Expo Go app
```

**Build APK:**
```bash
npm install -g eas-cli
eas login
eas build --platform android --profile preview
```

**Features:**
- Multi-tab monitoring
- Vibration alerts
- Background monitoring
- Activity log
- Modern mobile UI

---

## 🚀 Quick Start

### Desktop (Windows)
```bash
python delta_monitor_modern.py
```

### Mobile (Android/iOS)
```bash
cd delta-monitor
npx expo start
```

---

## 📱 Features

- **Multi-Symbol Monitoring**: Track multiple cryptocurrencies simultaneously
- **Price Alerts**: Get notified when price drops below trigger
- **Real-time Updates**: Configurable refresh intervals (1-60 seconds)
- **API Rate Limiting**: Tracks and displays API usage
- **Chrome-style Tabs**: Easy navigation between monitors
- **Clean UI**: Modern minimalistic design

---

## 🔧 Requirements

### Desktop
- Python 3.10+
- tkinter (included with Python)
- requests library

### Mobile
- Node.js 16+
- Expo Go app (for testing)
- Expo account (for building APK)

---

## 📖 API

Uses Delta Exchange India API:
- Endpoint: `https://api.india.delta.exchange/v2/tickers`
- Rate Limit: 10,000 units per 5 minutes
- Cost: 3 units per call

---

## 🎨 Design

- Material Design principles
- Color-coded status indicators
- Card-based layouts
- Responsive and touch-friendly

---

## 📄 License

MIT
