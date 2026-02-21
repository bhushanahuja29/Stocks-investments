# Crypto Levels Bhushan

Full-stack web application for finding and monitoring cryptocurrency support levels with a **premium, institutional-grade trading dashboard**.

## 🎨 NEW: Premium Dashboard

**A Bloomberg Terminal-inspired trading interface with dark mode, mobile optimization, and smooth animations!**

✨ **Key Features:**
- 🌓 Dark mode support
- 📱 Mobile-first responsive design
- 🎨 Premium UI with smooth animations
- 📊 Market filtering (Crypto/Forex/Stocks)
- 🔔 Enhanced alert management
- ⚡ 60fps micro-interactions

👉 **[See Premium Dashboard Documentation](./PREMIUM_DASHBOARD_SUMMARY.md)**

## Features

### Core Features
- **Zone Finder**: Search for weekly support zones for any crypto symbol
- **Multi-Level Monitor**: Monitor multiple support levels simultaneously with real-time price updates
- **Alert Management**: Enable/disable alerts for individual levels
- **MongoDB Integration**: Store and retrieve support levels

### Premium Dashboard Features ✨
- **Dark Mode**: Light and dark themes with persistent preferences
- **Market Filtering**: Quick switch between Crypto, Forex, and Stocks
- **Symbol Pills**: Modern segmented control for symbol selection
- **Hero Price Display**: Large, animated price display with live updates
- **Premium Cards**: Beautifully designed level cards with shadows and depth
- **Animated Progress Bars**: Smooth animations showing distance to levels
- **iOS-Style Switches**: Modern alert toggles with smooth animations
- **Color-Coded Indicators**: Green (safe), Amber (caution), Red (alert)
- **Mobile Optimized**: Touch-friendly interface for phones and tablets
- **Smooth Animations**: 60fps micro-interactions throughout

## Tech Stack

### Backend
- FastAPI (Python)
- MongoDB
- Deployed on Render

### Frontend
- React
- Axios for API calls
- Deployed on Vercel

## Project Structure

```
crypto_levels_bhushan/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── v3.py             # Support zone calculation logic
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ZoneFinder.js         # Zone search page
│   │   │   ├── Monitor.js            # Classic monitoring page
│   │   │   ├── Monitor_Premium.js    # ✨ Premium dashboard
│   │   │   └── Monitor_Premium.css   # ✨ Premium styles
│   │   ├── App.js                    # Routes (premium as default)
│   │   ├── App_Premium.css           # ✨ Premium navigation
│   │   └── index.js
│   ├── README_PREMIUM.md             # ✨ Premium documentation
│   ├── INTEGRATION_GUIDE.md          # ✨ Setup guide
│   ├── CUSTOMIZATION_EXAMPLES.md     # ✨ Code examples
│   ├── package.json
│   └── .env             # Environment variables
├── PREMIUM_DASHBOARD_SUMMARY.md      # ✨ Complete overview
├── DELIVERABLES.md                   # ✨ What's included
└── README.md                         # This file
```

## Local Development

### Backend Setup

1. Navigate to backend directory:
```bash
cd crypto_levels_bhushan/backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with your MongoDB credentials (see `.env.example`)

4. Run the server:
```bash
python main.py
```

Backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd crypto_levels_bhushan/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```
REACT_APP_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm start
```

Frontend will run on `http://localhost:3000`

**Premium Dashboard:** Navigate to `http://localhost:3000/monitor` to see the new premium interface!

## 🎨 Premium Dashboard Quick Start

The premium dashboard is **already configured as default**!

1. Start the app (see Frontend Setup above)
2. Navigate to: `http://localhost:3000/monitor`
3. Click the moon icon (top right) to toggle dark mode
4. Use market tabs to filter Crypto/Forex/Stocks
5. Click symbol pills to switch between assets

**Documentation:**
- **Overview:** `PREMIUM_DASHBOARD_SUMMARY.md`
- **Setup Guide:** `frontend/INTEGRATION_GUIDE.md`
- **Customization:** `frontend/CUSTOMIZATION_EXAMPLES.md`
- **Quick Reference:** `frontend/QUICK_REFERENCE.md`

## Deployment

### Backend (Render)

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables from `.env`
7. Deploy

### Frontend (Vercel)

1. Push code to GitHub
2. Import project on Vercel
3. Set root directory to `crypto_levels_bhushan/frontend`
4. Add environment variable: `REACT_APP_API_URL=<your-render-backend-url>`
5. Deploy

## API Endpoints

- `GET /` - Health check
- `POST /api/zones/search` - Search for support zones
- `POST /api/zones/push` - Push zones to MongoDB
- `GET /api/scrips` - Get all monitored scrips
- `GET /api/price/{symbol}` - Get current price for symbol
- `PUT /api/scrips/{symbol}/alert` - Update alert status
- `DELETE /api/scrips/{symbol}` - Delete scrip

## Environment Variables

### Backend (.env)
```
MONGODB_URI=mongodb+srv://...
DB_NAME=delta_tracker
COLLECTION_NAME=monitored_scrips
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
```

## License

Private - Bhushan
