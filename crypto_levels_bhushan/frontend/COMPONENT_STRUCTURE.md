# Component Structure Guide

## 🏗️ Architecture Overview

```
MonitorPremium Component
│
├── State Management
│   ├── scrips (all symbols)
│   ├── selectedScrip (current symbol)
│   ├── prices (real-time prices)
│   ├── theme (light/dark)
│   ├── marketFilter (crypto/forex/stocks)
│   ├── timeframeFilter (1M/1w/1d/etc)
│   └── notifications
│
├── Data Fetching
│   ├── loadScrips() - Load all symbols
│   ├── fetchPriceForSymbol() - Get single price
│   ├── fetchAllPrices() - Update all prices
│   └── Auto-refresh (20s interval)
│
└── UI Components
    ├── Market Selector (sticky nav)
    ├── Symbol Pills (segmented control)
    ├── Price Hero (large display)
    ├── Levels Container
    │   └── Level Cards (grid)
    └── Toast Notifications
```

---

## 📦 Component Breakdown

### 1. Market Selector (Sticky Navigation)

```jsx
<div className="market-selector">
  <div className="market-tabs">
    <button className="market-tab">All Markets</button>
    <button className="market-tab">🪙 Crypto</button>
    <button className="market-tab">💱 Forex</button>
    <button className="market-tab">📈 Stocks</button>
  </div>
  <button className="theme-toggle">🌙</button>
</div>
```

**Features:**
- Sticky positioning (always visible)
- Market filtering
- Theme toggle
- Backdrop blur effect

**CSS Classes:**
- `.market-selector` - Container
- `.market-tabs` - Button group
- `.market-tab` - Individual button
- `.market-tab.active` - Selected state
- `.theme-toggle` - Theme button

---

### 2. Symbol Pills (Segmented Control)

```jsx
<div className="symbol-selector">
  <div className="symbol-pills">
    {filteredScrips.map(scrip => (
      <button className="symbol-pill">
        {scrip.symbol}
        <span className="symbol-count">{count}</span>
      </button>
    ))}
  </div>
</div>
```

**Features:**
- Pill-style buttons
- Level count badges
- Triggered alert indicators
- Smooth transitions

**CSS Classes:**
- `.symbol-selector` - Container
- `.symbol-pills` - Button group
- `.symbol-pill` - Individual pill
- `.symbol-pill.active` - Selected
- `.symbol-pill.triggered` - Has alerts
- `.symbol-count` - Badge

---

### 3. Price Hero (Large Display)

```jsx
<div className="price-hero">
  <div className="price-hero-header">
    <div className="symbol-title">
      {symbol}
      <span className="market-badge">🪙 Crypto</span>
    </div>
    <button className="btn-open-exchange">
      📈 Open on Delta
    </button>
  </div>

  <div className="price-display-main">
    <div className="price-label">Current Mark Price</div>
    <div className="current-price">$45,234.5600</div>
  </div>

  <div className="price-meta">
    <div className="price-source">
      <span className="status-dot"></span>
      <span>Live • 14:23:45</span>
    </div>
    <span>Delta Exchange</span>
  </div>
</div>
```

**Features:**
- Large, readable price
- Animated tick effect
- Live status indicator
- Exchange link button

**CSS Classes:**
- `.price-hero` - Container
- `.price-hero-header` - Top section
- `.symbol-title` - Symbol name
- `.market-badge` - Market type
- `.btn-open-exchange` - Action button
- `.price-display-main` - Price section
- `.price-label` - Label text
- `.current-price` - Large price
- `.price-tick` - Animation class
- `.price-meta` - Bottom info
- `.status-dot` - Live indicator

---

### 4. Levels Container

```jsx
<div className="levels-container">
  <div className="levels-header">
    <h2 className="levels-title">
      Support & Resistance Levels (5)
    </h2>
    <div className="timeframe-filter">
      <label className="filter-label">Timeframe:</label>
      <select className="filter-select">
        <option>All Timeframes</option>
        <option>1M</option>
        <option>1W</option>
      </select>
    </div>
  </div>

  <div className="levels-grid">
    {/* Level cards here */}
  </div>
</div>
```

**Features:**
- Timeframe filtering
- Level count display
- Grid layout

**CSS Classes:**
- `.levels-container` - Container
- `.levels-header` - Top section
- `.levels-title` - Title text
- `.timeframe-filter` - Filter group
- `.filter-label` - Label
- `.filter-select` - Dropdown
- `.levels-grid` - Card grid

---

### 5. Level Card (Individual)

```jsx
<div className="level-card">
  {/* Header */}
  <div className="level-card-header">
    <div className="level-meta">
      <span className="timeframe-icon">1M</span>
      <span className="level-number">Level 1</span>
    </div>
    <div className="distance-indicator bullish">
      ↓ 2.3% above
    </div>
  </div>

  {/* Price */}
  <div className="level-price-display">
    <div className="level-price">$44,000.00</div>
  </div>

  {/* Stats */}
  <div className="level-stats">
    <div className="stat-item">
      <span className="stat-label">Bottom</span>
      <span className="stat-value">$42,000</span>
    </div>
    {/* More stats... */}
  </div>

  {/* Progress */}
  <div className="progress-section">
    <div className="progress-bar-container">
      <div className="progress-bar-fill"></div>
    </div>
  </div>

  {/* Actions */}
  <div className="level-actions">
    <div className="alert-switch">
      <span className="alert-label">Alert</span>
      <div className="switch">
        <div className="switch-thumb"></div>
      </div>
      <span className="alert-icon">🔔</span>
    </div>
  </div>
</div>
```

**Features:**
- Timeframe badge
- Distance indicator
- Stats grid
- Animated progress bar
- iOS-style switch

**CSS Classes:**
- `.level-card` - Container
- `.level-card.triggered` - Alert state
- `.level-card-header` - Top section
- `.level-meta` - Metadata group
- `.timeframe-icon` - Badge
- `.level-number` - Level ID
- `.distance-indicator` - Distance badge
- `.distance-indicator.bullish` - Green
- `.distance-indicator.warning` - Amber
- `.distance-indicator.bearish` - Red
- `.level-price-display` - Price section
- `.level-price` - Price text
- `.level-stats` - Stats grid
- `.stat-item` - Individual stat
- `.stat-label` - Stat label
- `.stat-value` - Stat value
- `.progress-section` - Progress area
- `.progress-bar-container` - Bar container
- `.progress-bar-fill` - Animated fill
- `.level-actions` - Actions section
- `.alert-switch` - Switch group
- `.alert-label` - Label
- `.switch` - Switch container
- `.switch.active` - On state
- `.switch-thumb` - Sliding circle
- `.alert-icon` - Icon

---

### 6. Toast Notification

```jsx
<div className="toast success">
  ✓ Alert enabled
</div>
```

**Features:**
- Slide-in animation
- Auto-dismiss (3s)
- Success/error states

**CSS Classes:**
- `.toast` - Container
- `.toast.success` - Green
- `.toast.error` - Red
- `.fade-in` - Animation

---

## 🎨 CSS Variable System

### Colors
```css
--bg-primary       /* Main background */
--bg-secondary     /* Secondary background */
--bg-card          /* Card background */
--bg-hover         /* Hover state */

--text-primary     /* Main text */
--text-secondary   /* Secondary text */
--text-tertiary    /* Tertiary text */

--border-light     /* Light border */
--border-medium    /* Medium border */

--color-bullish    /* Green */
--color-bearish    /* Red */
--color-warning    /* Amber */
--color-info       /* Blue */
--color-neutral    /* Gray */
```

### Spacing
```css
--spacing-xs       /* 4px */
--spacing-sm       /* 8px */
--spacing-md       /* 16px */
--spacing-lg       /* 24px */
--spacing-xl       /* 32px */
--spacing-2xl      /* 48px */
```

### Border Radius
```css
--radius-sm        /* 6px */
--radius-md        /* 12px */
--radius-lg        /* 16px */
--radius-xl        /* 24px */
--radius-full      /* 9999px */
```

### Shadows
```css
--shadow-sm        /* Subtle */
--shadow-md        /* Medium */
--shadow-lg        /* Large */
--shadow-xl        /* Extra large */
```

---

## 🔄 State Flow

### 1. Initial Load
```
App Loads
  ↓
loadScrips()
  ↓
Set scrips state
  ↓
Select first scrip
  ↓
fetchAllPrices()
  ↓
Render UI
```

### 2. Price Updates
```
Every 20 seconds
  ↓
fetchAllPrices()
  ↓
For each scrip:
  - Fetch price
  - Check triggers
  - Send notifications
  ↓
Update prices state
  ↓
Re-render affected components
```

### 3. User Interactions
```
User clicks symbol pill
  ↓
setSelectedScrip()
  ↓
Re-render with new data

User toggles alert
  ↓
toggleAlert()
  ↓
API call
  ↓
Update local state
  ↓
Show toast
```

### 4. Theme Toggle
```
User clicks theme button
  ↓
toggleTheme()
  ↓
Update theme state
  ↓
Set data-theme attribute
  ↓
Save to localStorage
  ↓
CSS variables update
```

---

## 📱 Responsive Behavior

### Desktop (>1024px)
```
┌─────────────────────────────────┐
│ [Market Tabs]          [Theme]  │
├─────────────────────────────────┤
│ [Pill] [Pill] [Pill] [Pill]     │
├─────────────────────────────────┤
│         BTCUSDT 🪙              │
│      $45,234.5600               │
├─────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐        │
│ │ Card 1  │ │ Card 2  │        │
│ └─────────┘ └─────────┘        │
└─────────────────────────────────┘
```

### Tablet (769-1024px)
```
┌─────────────────────────────────┐
│ [Market Tabs]          [Theme]  │
├─────────────────────────────────┤
│ [Pill] [Pill] [Pill]            │
├─────────────────────────────────┤
│         BTCUSDT 🪙              │
│      $45,234.56                 │
├─────────────────────────────────┤
│ ┌─────────────────────────────┐ │
│ │ Card 1                      │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ Card 2                      │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### Mobile (<768px)
```
┌───────────────────┐
│ [All] [Crypto]    │
│ [Forex] [Stocks]  │
│        [Theme]    │
├───────────────────┤
│ [Pill 1]          │
│ [Pill 2]          │
├───────────────────┤
│    BTCUSDT 🪙     │
│   $45,234.56      │
├───────────────────┤
│ ┌───────────────┐ │
│ │ Card 1        │ │
│ │ (Stacked)     │ │
│ └───────────────┘ │
└───────────────────┘
```

---

## 🎭 Animation Timeline

### Page Load
```
0ms:   Start
100ms: Market selector fades in
200ms: Symbol pills slide up
300ms: Price hero slides up
400ms: Level cards fade in (staggered)
600ms: All animations complete
```

### Price Update
```
0ms:   New price received
0ms:   Add .price-tick class
150ms: Scale to 1.02
300ms: Scale back to 1
300ms: Remove .price-tick class
```

### Alert Toggle
```
0ms:   User clicks
0ms:   Switch thumb starts moving
300ms: Thumb reaches end position
300ms: Icon changes
300ms: Toast appears
3000ms: Toast disappears
```

---

## 🔧 Customization Points

### Easy (CSS Variables)
- Colors
- Spacing
- Border radius
- Shadows
- Fonts

### Medium (CSS Classes)
- Layout structure
- Grid columns
- Card styling
- Animation timing

### Advanced (React Code)
- Data fetching logic
- State management
- Custom hooks
- New features

---

## 📚 File Organization

```
src/pages/
├── Monitor_Premium.js       # Main component (400 lines)
│   ├── State hooks
│   ├── Data fetching
│   ├── Event handlers
│   └── JSX render
│
└── Monitor_Premium.css      # Styles (600 lines)
    ├── Design system variables
    ├── Base styles
    ├── Component styles
    ├── Animations
    ├── Dark theme
    └── Responsive breakpoints
```

---

## 🎯 Best Practices

### Component Structure
1. ✅ State at top
2. ✅ Effects after state
3. ✅ Handlers after effects
4. ✅ Computed values before render
5. ✅ JSX at bottom

### CSS Organization
1. ✅ Variables first
2. ✅ Base styles
3. ✅ Components (alphabetical)
4. ✅ Modifiers
5. ✅ Responsive last

### Performance
1. ✅ useCallback for handlers
2. ✅ useMemo for computed values
3. ✅ Debounce rapid updates
4. ✅ Lazy load heavy components
5. ✅ Optimize re-renders

---

This structure provides a solid foundation for understanding and extending the premium dashboard!
