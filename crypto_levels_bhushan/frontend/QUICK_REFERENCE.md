# Quick Reference Card

## 🚀 Getting Started (30 seconds)

```bash
cd crypto_levels_bhushan/frontend
npm start
```

Navigate to: **http://localhost:3000/monitor**

---

## 🎨 Key Files

| File | Purpose |
|------|---------|
| `Monitor_Premium.js` | Main component |
| `Monitor_Premium.css` | All styles |
| `App.js` | Routes (already updated) |
| `App_Premium.css` | Navigation styles |

---

## 🎯 Common Tasks

### Change Theme Colors
```css
/* Edit Monitor_Premium.css */
:root {
  --color-bullish: #10B981;  /* Your green */
  --color-bearish: #EF4444;  /* Your red */
  --color-info: #3B82F6;     /* Your blue */
}
```

### Adjust Card Spacing
```css
.levels-grid {
  gap: 1.5rem; /* Change from 1rem */
}
```

### Modify Price Size
```css
.current-price {
  font-size: 5rem; /* Change from 4rem */
}
```

### Change Border Roundness
```css
:root {
  --radius-md: 16px; /* More rounded */
  --radius-lg: 20px;
}
```

---

## 🌓 Dark Mode

**Toggle:** Click moon/sun icon (top right)

**Customize Dark Colors:**
```css
[data-theme="dark"] {
  --bg-primary: #0F1419;
  --bg-card: #1C1F26;
  --text-primary: #E7E9EA;
}
```

---

## 📱 Responsive Breakpoints

```css
Mobile:  < 768px
Tablet:  769-1024px
Desktop: > 1024px
```

**Test Mobile:**
- Press F12 in Chrome
- Click device toolbar
- Select iPhone/Android

---

## 🎨 CSS Classes Reference

### Containers
```css
.monitor              /* Main wrapper */
.container            /* Content container */
.market-selector      /* Top navigation */
.symbol-selector      /* Symbol pills */
.price-hero           /* Large price display */
.levels-container     /* Levels section */
```

### Components
```css
.market-tab           /* Market button */
.market-tab.active    /* Selected market */
.symbol-pill          /* Symbol button */
.symbol-pill.active   /* Selected symbol */
.symbol-pill.triggered /* Has alerts */
.level-card           /* Level card */
.level-card.triggered  /* Alert triggered */
```

### States
```css
.active               /* Selected state */
.triggered            /* Alert state */
.bullish              /* Green indicator */
.warning              /* Amber indicator */
.bearish              /* Red indicator */
```

### Animations
```css
.fade-in              /* Fade in animation */
.slide-up             /* Slide up animation */
.price-tick           /* Price update flash */
```

---

## 🎭 Animation Classes

```javascript
// Add to element
className="fade-in"      // Fade in
className="slide-up"     // Slide up
className="price-tick"   // Price flash
```

---

## 🔧 State Variables

```javascript
const [scrips, setScrips]           // All symbols
const [selectedScrip, setSelectedScrip] // Current symbol
const [prices, setPrices]           // Real-time prices
const [theme, setTheme]             // light/dark
const [marketFilter, setMarketFilter] // crypto/forex/stocks
const [timeframeFilter, setTimeframeFilter] // 1M/1w/etc
```

---

## 📊 Key Functions

```javascript
loadScrips()              // Load all symbols
fetchPriceForSymbol()     // Get single price
fetchAllPrices()          // Update all prices
toggleAlert()             // Toggle alert on/off
toggleTheme()             // Switch light/dark
openDeltaExchange()       // Open exchange link
showToast()               // Show notification
```

---

## 🎨 Color Variables

```css
/* Backgrounds */
--bg-primary              /* Main background */
--bg-card                 /* Card background */
--bg-hover                /* Hover state */

/* Text */
--text-primary            /* Main text */
--text-secondary          /* Secondary text */
--text-tertiary           /* Tertiary text */

/* Accents */
--color-bullish           /* Green */
--color-bearish           /* Red */
--color-warning           /* Amber */
--color-info              /* Blue */
```

---

## 📏 Spacing Variables

```css
--spacing-xs: 0.25rem;    /* 4px */
--spacing-sm: 0.5rem;     /* 8px */
--spacing-md: 1rem;       /* 16px */
--spacing-lg: 1.5rem;     /* 24px */
--spacing-xl: 2rem;       /* 32px */
--spacing-2xl: 3rem;      /* 48px */
```

---

## 🔄 Data Flow

```
Load → Fetch Scrips → Select First → Fetch Prices → Render
  ↓
Every 20s: Fetch Prices → Check Triggers → Update UI
  ↓
User Action → Update State → Re-render
```

---

## 🐛 Quick Fixes

### Styles not loading?
```bash
rm -rf node_modules/.cache
npm start
```

### Theme not saving?
```javascript
// Check localStorage
localStorage.getItem('theme')
```

### Animations laggy?
```css
/* Disable temporarily */
* { animation: none !important; }
```

### Mobile layout broken?
```html
<!-- Check index.html has: -->
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

---

## 📱 Mobile Testing

```bash
# Get your IP
ipconfig  # Windows
ifconfig  # Mac/Linux

# Access from phone
http://YOUR_IP:3000/monitor
```

---

## 🎯 Feature Checklist

- [x] Dark mode toggle
- [x] Market filters (Crypto/Forex/Stocks)
- [x] Symbol pills with counts
- [x] Large price display
- [x] Animated progress bars
- [x] iOS-style alert switches
- [x] Color-coded distance indicators
- [x] Timeframe filtering
- [x] Toast notifications
- [x] Mobile responsive
- [x] Hover effects
- [x] Smooth animations

---

## 🚀 Performance Tips

1. **Debounce rapid updates**
```javascript
const debouncedUpdate = useCallback(
  debounce(() => setPrices(newPrices), 500),
  []
);
```

2. **Lazy load cards**
```javascript
const LazyCard = ({ isVisible, children }) => 
  isVisible ? children : <Placeholder />;
```

3. **Memoize computed values**
```javascript
const sortedLevels = useMemo(
  () => levels.sort(...),
  [levels, currentPrice]
);
```

---

## 📚 Documentation Files

| File | What's Inside |
|------|---------------|
| `README_PREMIUM.md` | Overview & features |
| `INTEGRATION_GUIDE.md` | Setup steps |
| `DESIGN_COMPARISON.md` | Classic vs Premium |
| `CUSTOMIZATION_EXAMPLES.md` | Code examples |
| `COMPONENT_STRUCTURE.md` | Architecture |
| `QUICK_REFERENCE.md` | This file |

---

## 🎨 Theme Presets

### Ocean Blue
```css
--color-bullish: #06D6A0;
--color-bearish: #EF476F;
--color-info: #118AB2;
```

### Forest Green
```css
--color-bullish: #52B788;
--color-bearish: #D62828;
--color-info: #2D6A4F;
```

### Sunset Orange
```css
--color-bullish: #06FFA5;
--color-bearish: #FF006E;
--color-info: #8338EC;
```

---

## 🔔 Notification Setup

```javascript
// Request permission
Notification.requestPermission()

// Send notification
new Notification('Title', {
  body: 'Message',
  icon: '/favicon.ico'
})
```

---

## 💡 Pro Tips

1. **Dark mode at night** - Reduces eye strain
2. **Filter by timeframe** - Focus on what matters
3. **Enable notifications** - Never miss alerts
4. **Test on mobile** - Monitor anywhere
5. **Customize colors** - Match your brand
6. **Hover for details** - Discover interactions

---

## 🎯 Keyboard Shortcuts (Future)

```javascript
// Add to useEffect
'D' - Toggle dark mode
'1-9' - Switch symbols
'A' - Toggle all alerts
'R' - Refresh data
'/' - Focus search
```

---

## 📊 API Endpoints

```javascript
GET  /api/scrips              // Get all symbols
GET  /api/price/:symbol       // Get price
PUT  /api/scrips/:symbol/alert // Toggle alert
GET  /api/usage               // API usage
```

---

## 🎉 Quick Wins

### 1. Change accent color (1 min)
```css
:root { --color-info: #YOUR_COLOR; }
```

### 2. Adjust spacing (1 min)
```css
:root { --spacing-lg: 2rem; }
```

### 3. More rounded cards (1 min)
```css
:root { --radius-lg: 20px; }
```

### 4. Larger price (1 min)
```css
.current-price { font-size: 5rem; }
```

### 5. Custom dark background (2 min)
```css
[data-theme="dark"] {
  --bg-primary: #YOUR_COLOR;
}
```

---

## 🔗 Useful Links

- **React Docs:** https://react.dev
- **CSS Variables:** https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties
- **Flexbox Guide:** https://css-tricks.com/snippets/css/a-guide-to-flexbox/
- **Grid Guide:** https://css-tricks.com/snippets/css/complete-guide-grid/

---

## 📞 Need Help?

1. Check browser console for errors
2. Clear cache and restart
3. Test in incognito mode
4. Review documentation files
5. Check GitHub issues

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Light theme works
- [ ] Dark theme works
- [ ] Theme persists on reload
- [ ] Market filters work
- [ ] Symbol pills clickable
- [ ] Price updates
- [ ] Progress bars animate
- [ ] Alert toggles work
- [ ] Triggered levels show red
- [ ] Toast notifications appear
- [ ] Mobile layout responsive
- [ ] Hover effects smooth

---

## 🎊 You're All Set!

**Enjoy your premium trading dashboard!**

For detailed examples, see:
- `CUSTOMIZATION_EXAMPLES.md`
- `COMPONENT_STRUCTURE.md`

**Happy Trading! 📈**

---

*Quick Reference v1.0 - February 2, 2026*
