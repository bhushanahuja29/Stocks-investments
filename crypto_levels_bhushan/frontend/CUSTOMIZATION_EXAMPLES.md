# Customization Examples

## 🎨 Quick Customizations

### 1. Change Brand Colors

**Location:** `src/pages/Monitor_Premium.css`

```css
:root {
  /* Your brand colors */
  --color-bullish: #00D084;    /* Mint green */
  --color-bearish: #FF4757;    /* Coral red */
  --color-warning: #FFA502;    /* Orange */
  --color-info: #5F27CD;       /* Purple */
  --color-neutral: #747D8C;    /* Gray */
}
```

**Result:** All buttons, badges, and indicators use your colors.

---

### 2. Adjust Border Radius (Roundness)

```css
:root {
  /* More rounded (Apple style) */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  
  /* Less rounded (Material style) */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* Square (Bloomberg style) */
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 6px;
  --radius-xl: 8px;
}
```

---

### 3. Modify Spacing Scale

```css
:root {
  /* Compact layout */
  --spacing-xs: 0.125rem;
  --spacing-sm: 0.25rem;
  --spacing-md: 0.5rem;
  --spacing-lg: 1rem;
  --spacing-xl: 1.5rem;
  
  /* Spacious layout */
  --spacing-xs: 0.5rem;
  --spacing-sm: 1rem;
  --spacing-md: 1.5rem;
  --spacing-lg: 2rem;
  --spacing-xl: 3rem;
}
```

---

### 4. Custom Dark Theme Colors

```css
[data-theme="dark"] {
  /* Deep blue theme */
  --bg-primary: #0A1929;
  --bg-secondary: #132F4C;
  --bg-card: #1A2027;
  --bg-hover: #1E2A35;
  
  /* Warm dark theme */
  --bg-primary: #1A1614;
  --bg-secondary: #2D2420;
  --bg-card: #3A2F28;
  --bg-hover: #4A3D34;
  
  /* Pure black (OLED) */
  --bg-primary: #000000;
  --bg-secondary: #0A0A0A;
  --bg-card: #121212;
  --bg-hover: #1E1E1E;
}
```

---

### 5. Change Typography

```css
:root {
  /* Roboto (Google) */
  --font-sans: 'Roboto', -apple-system, sans-serif;
  
  /* Poppins (Modern) */
  --font-sans: 'Poppins', -apple-system, sans-serif;
  
  /* IBM Plex (Professional) */
  --font-sans: 'IBM Plex Sans', -apple-system, sans-serif;
  
  /* Monospace for prices */
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}
```

Don't forget to import fonts in `public/index.html`:

```html
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
```

---

## 🎯 Advanced Customizations

### 6. Add Gradient Backgrounds

```css
.price-hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.price-hero .price-label,
.price-hero .current-price,
.price-hero .price-meta {
  color: white;
}
```

---

### 7. Glassmorphism Effect

```css
.market-selector {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

[data-theme="dark"] .market-selector {
  background: rgba(28, 31, 38, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

### 8. Neon Glow Effect (Cyberpunk Style)

```css
.level-card.triggered {
  box-shadow: 
    0 0 20px rgba(239, 68, 68, 0.5),
    0 0 40px rgba(239, 68, 68, 0.3),
    0 0 60px rgba(239, 68, 68, 0.1);
  border-color: #EF4444;
  animation: neon-pulse 2s infinite;
}

@keyframes neon-pulse {
  0%, 100% { 
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
  }
  50% { 
    box-shadow: 0 0 40px rgba(239, 68, 68, 0.8);
  }
}
```

---

### 9. Add Sound Effects

**Location:** `src/pages/Monitor_Premium.js`

```javascript
// Add at top of component
const playAlertSound = () => {
  const audio = new Audio('/sounds/alert.mp3');
  audio.volume = 0.5;
  audio.play().catch(e => console.log('Audio play failed:', e));
};

// In sendNotification function
const sendNotification = useCallback((title, body) => {
  if (notificationPermission === 'granted') {
    try {
      new Notification(title, { body });
      playAlertSound(); // Add this line
    } catch (error) {
      console.error('Notification error:', error);
    }
  }
}, [notificationPermission]);
```

---

### 10. Add Price Change Indicator

```javascript
// Add state
const [priceChange, setPriceChange] = useState({});

// In fetchAllPrices
if (price !== null) {
  const oldPrice = prices[scrip.symbol];
  if (oldPrice) {
    const change = ((price - oldPrice) / oldPrice) * 100;
    setPriceChange(prev => ({
      ...prev,
      [scrip.symbol]: {
        value: change,
        direction: change > 0 ? 'up' : 'down'
      }
    }));
  }
  newPrices[scrip.symbol] = price;
}

// In JSX
<div className="price-display-main">
  <div className="current-price">
    ${currentPrice.toFixed(4)}
    {priceChange[selectedScrip.symbol] && (
      <span className={`price-change ${priceChange[selectedScrip.symbol].direction}`}>
        {priceChange[selectedScrip.symbol].direction === 'up' ? '↑' : '↓'}
        {Math.abs(priceChange[selectedScrip.symbol].value).toFixed(2)}%
      </span>
    )}
  </div>
</div>
```

```css
.price-change {
  font-size: 1.5rem;
  margin-left: 1rem;
  font-weight: 600;
}

.price-change.up {
  color: var(--color-bullish);
  animation: bounce-up 0.5s;
}

.price-change.down {
  color: var(--color-bearish);
  animation: bounce-down 0.5s;
}

@keyframes bounce-up {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes bounce-down {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(10px); }
}
```

---

### 11. Add Keyboard Shortcuts

```javascript
// Add useEffect
useEffect(() => {
  const handleKeyPress = (e) => {
    // Press 1-9 to switch symbols
    if (e.key >= '1' && e.key <= '9') {
      const index = parseInt(e.key) - 1;
      if (filteredScrips[index]) {
        setSelectedScrip(filteredScrips[index]);
      }
    }
    
    // Press 'D' to toggle dark mode
    if (e.key === 'd' || e.key === 'D') {
      toggleTheme();
    }
    
    // Press 'A' to toggle all alerts
    if (e.key === 'a' || e.key === 'A') {
      // Toggle all alerts logic
    }
  };

  window.addEventListener('keydown', handleKeyPress);
  return () => window.removeEventListener('keydown', handleKeyPress);
}, [filteredScrips, toggleTheme]);
```

---

### 12. Add Chart Integration (TradingView)

```javascript
// Install: npm install react-tradingview-embed

import TradingViewWidget from 'react-tradingview-embed';

// In level card
<div className="level-card-chart">
  <TradingViewWidget
    widgetType="mini"
    symbol={`BINANCE:${selectedScrip.symbol}`}
    width="100%"
    height="200"
    locale="en"
    colorTheme={theme}
    isTransparent={true}
  />
</div>
```

---

### 13. Add Export to CSV

```javascript
const exportToCSV = () => {
  const csvData = sortedLevels.map(level => ({
    'Level': level.originalIndex + 1,
    'Timeframe': level.timeframe,
    'Trigger Price': level.trigger_price,
    'Bottom': level.bottom,
    'Rally High': level.rally_end_high,
    'Rally Length': level.rally_length,
    'Total Move %': level.total_move_pct,
    'Alert Enabled': !level.alert_disabled
  }));

  const csv = [
    Object.keys(csvData[0]).join(','),
    ...csvData.map(row => Object.values(row).join(','))
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${selectedScrip.symbol}_levels_${new Date().toISOString()}.csv`;
  a.click();
};

// Add button
<button className="btn-export" onClick={exportToCSV}>
  📥 Export CSV
</button>
```

---

### 14. Add Price Alerts with Custom Thresholds

```javascript
const [customAlerts, setCustomAlerts] = useState([]);

const addCustomAlert = (price, direction) => {
  const newAlert = {
    id: Date.now(),
    price,
    direction, // 'above' or 'below'
    symbol: selectedScrip.symbol,
    created: new Date()
  };
  
  setCustomAlerts(prev => [...prev, newAlert]);
  localStorage.setItem('customAlerts', JSON.stringify([...customAlerts, newAlert]));
};

// Check in fetchAllPrices
customAlerts.forEach(alert => {
  if (alert.symbol === scrip.symbol) {
    const triggered = alert.direction === 'above' 
      ? price >= alert.price 
      : price <= alert.price;
    
    if (triggered) {
      sendNotification(
        `Custom Alert: ${alert.symbol}`,
        `Price ${alert.direction} $${alert.price}`
      );
      // Remove triggered alert
      setCustomAlerts(prev => prev.filter(a => a.id !== alert.id));
    }
  }
});
```

---

### 15. Add Multi-Symbol Comparison View

```javascript
const [comparisonMode, setComparisonMode] = useState(false);
const [selectedSymbols, setSelectedSymbols] = useState([]);

// In JSX
{comparisonMode && (
  <div className="comparison-grid">
    {selectedSymbols.map(symbol => (
      <div key={symbol} className="comparison-card">
        <h3>{symbol}</h3>
        <div className="comparison-price">
          ${prices[symbol]?.toFixed(2) || '--'}
        </div>
        <div className="comparison-stats">
          {/* Show key stats */}
        </div>
      </div>
    ))}
  </div>
)}
```

---

## 🎨 Theme Presets

### Preset 1: Ocean Blue

```css
:root {
  --color-bullish: #06D6A0;
  --color-bearish: #EF476F;
  --color-info: #118AB2;
  --color-warning: #FFD166;
}

[data-theme="dark"] {
  --bg-primary: #073B4C;
  --bg-card: #0A4F63;
}
```

### Preset 2: Forest Green

```css
:root {
  --color-bullish: #52B788;
  --color-bearish: #D62828;
  --color-info: #2D6A4F;
  --color-warning: #F77F00;
}

[data-theme="dark"] {
  --bg-primary: #1B4332;
  --bg-card: #2D6A4F;
}
```

### Preset 3: Sunset Orange

```css
:root {
  --color-bullish: #06FFA5;
  --color-bearish: #FF006E;
  --color-info: #8338EC;
  --color-warning: #FB5607;
}

[data-theme="dark"] {
  --bg-primary: #240046;
  --bg-card: #3C096C;
}
```

---

## 🚀 Performance Optimizations

### 16. Lazy Load Level Cards

```javascript
import { useState, useEffect, useRef } from 'react';

const LazyLevelCard = ({ level, isVisible }) => {
  if (!isVisible) return <div className="level-card-placeholder" />;
  
  return <div className="level-card">{/* Full card content */}</div>;
};

// Use Intersection Observer
const useLazyLoad = () => {
  const [visibleCards, setVisibleCards] = useState(new Set());
  const observerRef = useRef();

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            setVisibleCards(prev => new Set([...prev, entry.target.dataset.index]));
          }
        });
      },
      { rootMargin: '100px' }
    );
  }, []);

  return { visibleCards, observerRef };
};
```

---

### 17. Debounce Price Updates

```javascript
import { useCallback, useRef } from 'react';

const useDebouncedPrice = (delay = 500) => {
  const timeoutRef = useRef();

  return useCallback((callback) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(callback, delay);
  }, [delay]);
};

// Usage
const debouncedUpdate = useDebouncedPrice(500);

debouncedUpdate(() => {
  setPrices(newPrices);
});
```

---

## 📱 Mobile-Specific Enhancements

### 18. Add Swipe Gestures

```javascript
// Install: npm install react-swipeable

import { useSwipeable } from 'react-swipeable';

const handlers = useSwipeable({
  onSwipedLeft: () => {
    // Next symbol
    const currentIndex = filteredScrips.findIndex(s => s.symbol === selectedScrip.symbol);
    if (currentIndex < filteredScrips.length - 1) {
      setSelectedScrip(filteredScrips[currentIndex + 1]);
    }
  },
  onSwipedRight: () => {
    // Previous symbol
    const currentIndex = filteredScrips.findIndex(s => s.symbol === selectedScrip.symbol);
    if (currentIndex > 0) {
      setSelectedScrip(filteredScrips[currentIndex - 1]);
    }
  }
});

// Apply to container
<div {...handlers} className="price-hero">
  {/* Content */}
</div>
```

---

## 🎉 You're Ready!

These customizations will help you create a truly unique trading dashboard. Mix and match to create your perfect setup!

**Pro Tips:**
- Start with small changes
- Test on multiple devices
- Keep performance in mind
- Get user feedback
- Iterate and improve

Happy customizing! 🚀
