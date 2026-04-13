import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './Monitor_Premium.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function MonitorPremium({ onNavbarRefresh }) {
  const [scrips, setScrips] = useState([]);
  const [selectedScrip, setSelectedScrip] = useState(null);
  const [prices, setPrices] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState({});
  const [toast, setToast] = useState(null);
  const [notificationPermission, setNotificationPermission] = useState('default');
  const [timeframeFilter, setTimeframeFilter] = useState('all');
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });
  const [marketFilter, setMarketFilter] = useState('all');

  // Apply theme on mount and when changed
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    document.body.classList.add('theme-switching');
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
    setTimeout(() => {
      document.body.classList.remove('theme-switching');
    }, 300);
  };

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        setNotificationPermission('granted');
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
          setNotificationPermission(permission);
        });
      }
    }
  }, []);

  const sendNotification = useCallback((title, body) => {
    if (notificationPermission === 'granted') {
      try {
        new Notification(title, {
          body: body,
          icon: '/favicon.ico',
          badge: '/favicon.ico',
          tag: 'crypto-alert',
          requireInteraction: true
        });
      } catch (error) {
        console.error('Notification error:', error);
      }
    }
  }, [notificationPermission]);

  const openExchange = (symbolToOpen, marketType) => {
    if (!symbolToOpen) return;
    
    // Indian stocks -> TradingView
    if (marketType === 'indian_stock') {
      const url = `https://www.tradingview.com/chart/?symbol=NSE:${symbolToOpen}`;
      window.open(url, '_blank');
      return;
    }
    
    // Crypto/Forex -> Delta Exchange
    const upperSymbol = symbolToOpen.toUpperCase();
    let baseSymbol = upperSymbol;
    if (upperSymbol.endsWith('USDT')) {
      baseSymbol = upperSymbol.slice(0, -4);
    } else if (upperSymbol.endsWith('USD')) {
      baseSymbol = upperSymbol.slice(0, -3);
    }
    
    const url = `https://www.delta.exchange/app/futures/trade/${baseSymbol}/${upperSymbol}`;
    window.open(url, '_blank');
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadScrips = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/scrips`);
      if (response.data.success) {
        setScrips(response.data.scrips);
        
        // Check if we should auto-select a symbol from notification click
        const selectedSymbol = sessionStorage.getItem('selectedSymbol');
        const selectedLevelIndex = sessionStorage.getItem('selectedLevelIndex');
        
        if (selectedSymbol && response.data.scrips.length > 0) {
          const scripToSelect = response.data.scrips.find(s => s.symbol === selectedSymbol);
          if (scripToSelect) {
            setSelectedScrip(scripToSelect);
            
            // Scroll to the level if index is provided
            if (selectedLevelIndex !== null) {
              setTimeout(() => {
                const levelElement = document.querySelector(`[data-level-index="${selectedLevelIndex}"]`);
                if (levelElement) {
                  levelElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  levelElement.classList.add('highlight-level');
                  setTimeout(() => levelElement.classList.remove('highlight-level'), 2000);
                }
              }, 500);
            }
            
            // Clear sessionStorage
            sessionStorage.removeItem('selectedSymbol');
            sessionStorage.removeItem('selectedLevelIndex');
          }
        } else if (response.data.scrips.length > 0 && !selectedScrip) {
          setSelectedScrip(response.data.scrips[0]);
        }
      }
    } catch (error) {
      console.error('Error loading scrips:', error);
      showToast('Failed to load scrips', 'error');
    } finally {
      setLoading(false);
    }
  }, [selectedScrip]);

  const fetchPriceForSymbol = async (symbol, marketType = 'crypto') => {
    try {
      const response = await axios.get(`${API_URL}/api/price/${symbol}`, { 
        params: { market_type: marketType } 
      });
      if (response.data.success) {
        return response.data.mark_price;
      }
    } catch (error) {
      console.error(`Error fetching price for ${symbol}:`, error);
    }
    return null;
  };

  const fetchAllPrices = useCallback(async () => {
    if (scrips.length === 0) return;

    const newPrices = {};
    const newLastUpdate = {};
    
    await Promise.all(
      scrips.map(async (scrip) => {
        const marketType = scrip.market_type || 'crypto';
        const price = await fetchPriceForSymbol(scrip.symbol, marketType);
        if (price !== null) {
          newPrices[scrip.symbol] = price;
          newLastUpdate[scrip.symbol] = new Date().toLocaleTimeString();
          
          scrip.trigger_levels?.forEach((level) => {
            const wasTriggered = level.triggered || false;
            const isNowTriggered = price <= level.trigger_price;
            const alertEnabled = !level.alert_disabled;
            
            if (!wasTriggered && isNowTriggered && alertEnabled) {
              const timeframeLabel = level.timeframe ? level.timeframe.toUpperCase() : 'UNKNOWN';
              sendNotification(
                `🔔 ${scrip.symbol} Alert Triggered!`,
                `${timeframeLabel} Level: ${level.trigger_price.toFixed(2)}\nCurrent: ${price.toFixed(2)}`
              );
            }
          });
        }
      })
    );

    setPrices(newPrices);
    setLastUpdate(newLastUpdate);
  }, [scrips, sendNotification]);

  const toggleAlert = async (levelIndex) => {
    if (!selectedScrip) return;

    const currentLevel = selectedScrip.trigger_levels[levelIndex];
    const currentlyDisabled = currentLevel.alert_disabled || false;
    const newDisabledStatus = !currentlyDisabled;
    
    try {
      const response = await axios.put(`${API_URL}/api/scrips/${selectedScrip.symbol}/alert`, {
        symbol: selectedScrip.symbol,
        level_index: levelIndex,
        disabled: newDisabledStatus
      });

      if (response.data.success) {
        const updatedScrips = scrips.map(scrip => {
          if (scrip.symbol === selectedScrip.symbol) {
            const updatedLevels = scrip.trigger_levels.map((level, idx) => {
              if (idx === levelIndex) {
                return { ...level, alert_disabled: newDisabledStatus };
              }
              return level;
            });
            return { ...scrip, trigger_levels: updatedLevels };
          }
          return scrip;
        });

        setScrips(updatedScrips);
        const updatedSelectedScrip = updatedScrips.find(s => s.symbol === selectedScrip.symbol);
        setSelectedScrip(updatedSelectedScrip);

        const statusText = newDisabledStatus ? 'disabled' : 'enabled';
        showToast(`Alert ${statusText}`, 'success');
        
        // Refresh navbar notification count
        if (onNavbarRefresh) {
          onNavbarRefresh();
        }
      }
    } catch (error) {
      console.error('Error toggling alert:', error);
      showToast('Failed to update alert', 'error');
    }
  };

  useEffect(() => {
    loadScrips();
  }, [loadScrips]);

  useEffect(() => {
    if (scrips.length === 0) return;
    fetchAllPrices();
    const interval = setInterval(fetchAllPrices, 20000);
    return () => clearInterval(interval);
  }, [scrips, fetchAllPrices]);

  const calculateDistance = (currentPrice, triggerPrice) => {
    if (!currentPrice || !triggerPrice) return null;
    
    if (currentPrice >= triggerPrice) {
      const percentage = ((currentPrice - triggerPrice) / triggerPrice) * 100;
      return {
        percentage,
        triggered: false,
        text: `${percentage.toFixed(1)}% above`,
        color: percentage > 10 ? 'bullish' : percentage > 5 ? 'warning' : 'bearish'
      };
    } else {
      const percentageBelow = ((triggerPrice - currentPrice) / triggerPrice) * 100;
      return {
        percentage: -1,
        triggered: true,
        text: `TRIGGERED (${percentageBelow.toFixed(1)}% below)`,
        color: 'bearish'
      };
    }
  };

  const currentPrice = selectedScrip ? prices[selectedScrip.symbol] : null;

  // Filter by market type
  const filteredScrips = scrips.filter(scrip => {
    if (marketFilter === 'all') return true;
    return scrip.market_type === marketFilter;
  });

  // Debug logging
  console.log('Market Filter:', marketFilter);
  console.log('Total Scrips:', scrips.length);
  console.log('Filtered Scrips:', filteredScrips.length);
  console.log('All scrips:', scrips.map(s => ({ symbol: s.symbol, market_type: s.market_type })));

  // Ensure selected scrip is in filtered list
  useEffect(() => {
    if (selectedScrip && !filteredScrips.find(s => s.symbol === selectedScrip.symbol)) {
      if (filteredScrips.length > 0) {
        console.log('Auto-switching to first filtered scrip:', filteredScrips[0].symbol);
        setSelectedScrip(filteredScrips[0]);
      }
    }
  }, [marketFilter, filteredScrips, selectedScrip]);

  // Filter levels by timeframe
  const filteredLevels = selectedScrip?.trigger_levels ? 
    selectedScrip.trigger_levels.filter(level => 
      timeframeFilter === 'all' || level.timeframe === timeframeFilter
    ) : [];

  const sortedLevels = filteredLevels.length > 0 ? 
    [...filteredLevels]
      .map((level, index) => {
        const originalIndex = selectedScrip.trigger_levels.findIndex(l => l === level);
        return { ...level, originalIndex };
      })
      .sort((a, b) => {
        if (!currentPrice) return a.trigger_price - b.trigger_price;
        
        const distA = calculateDistance(currentPrice, a.trigger_price);
        const distB = calculateDistance(currentPrice, b.trigger_price);
        
        if (distA.triggered && !distB.triggered) return -1;
        if (!distA.triggered && distB.triggered) return 1;
        
        return distA.percentage - distB.percentage;
      })
    : [];

  const availableTimeframes = selectedScrip?.trigger_levels ? 
    [...new Set(selectedScrip.trigger_levels.map(l => l.timeframe || '1w'))].sort((a, b) => {
      const order = { '1M': 0, '1w': 1, '1d': 2, '4h': 3, '1h': 4 };
      return (order[a] || 99) - (order[b] || 99);
    }) : [];

  if (loading) {
    return (
      <div className="monitor">
        <div className="container">
          <div className="loading">Loading trading data...</div>
        </div>
      </div>
    );
  }

  if (scrips.length === 0) {
    return (
      <div className="monitor">
        <div className="container">
          <div className="empty-state">
            <h2>No Scrips Found</h2>
            <p>Go to Zone Finder to add support levels</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="monitor">
      {toast && (
        <div className={`toast ${toast.type} fade-in`}>
          {toast.type === 'success' ? '✓' : '✗'} {toast.message}
        </div>
      )}
      
      <div className="container">
        {/* Market Selector with Theme Toggle */}
        <div className="market-selector">
          <div className="market-tabs">
            <button
              className={`market-tab ${marketFilter === 'all' ? 'active' : ''}`}
              onClick={() => setMarketFilter('all')}
            >
              All Markets
            </button>
            <button
              className={`market-tab ${marketFilter === 'crypto' ? 'active' : ''}`}
              onClick={() => setMarketFilter('crypto')}
            >
              🪙 Crypto
            </button>
            <button
              className={`market-tab ${marketFilter === 'forex' ? 'active' : ''}`}
              onClick={() => setMarketFilter('forex')}
            >
              💱 Forex
            </button>
            <button
              className={`market-tab ${marketFilter === 'indian_stock' ? 'active' : ''}`}
              onClick={() => {
                console.log('Clicked Stocks filter');
                setMarketFilter('indian_stock');
                const stockScrips = scrips.filter(s => s.market_type === 'indian_stock');
                console.log('Stock scrips found:', stockScrips.map(s => s.symbol));
                if (stockScrips.length > 0) {
                  console.log('Setting selected scrip to:', stockScrips[0].symbol);
                  setSelectedScrip(stockScrips[0]);
                }
              }}
            >
              📈 Stocks
            </button>
          </div>
          
          <button className="theme-toggle" onClick={toggleTheme}>
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>

        {/* Symbol Pills */}
        <div className="symbol-selector slide-up">
          <div className="symbol-pills">
            {filteredScrips.map((scrip) => {
              const scripPrice = prices[scrip.symbol];
              const hasTriggered = scrip.trigger_levels?.some(level => 
                scripPrice && scripPrice <= level.trigger_price && !level.alert_disabled
              );
              
              return (
                <button
                  key={scrip.symbol}
                  className={`symbol-pill ${selectedScrip?.symbol === scrip.symbol ? 'active' : ''} ${hasTriggered ? 'triggered' : ''}`}
                  onClick={() => setSelectedScrip(scrip)}
                >
                  {scrip.symbol}
                  <span className="symbol-count">{scrip.trigger_levels?.length || 0}</span>
                </button>
              );
            })}
          </div>
        </div>

        {selectedScrip && (
          <>
            {/* Notification Banner */}
            {notificationPermission !== 'granted' && (
              <div className="notification-banner fade-in">
                <span className="notification-banner-text">
                  🔔 Enable notifications to receive real-time alerts
                </span>
                <button 
                  className="btn-enable-notifications"
                  onClick={() => Notification.requestPermission().then(p => setNotificationPermission(p))}
                >
                  Enable Notifications
                </button>
              </div>
            )}

            {/* Hero Price Display */}
            <div className="price-hero slide-up">
              <div className="price-hero-header">
                <div className="symbol-title">
                  {selectedScrip.symbol}
                  <span className="market-badge">
                    {selectedScrip.market_type === 'forex' ? '💱 Forex' : 
                     selectedScrip.market_type === 'indian_stock' ? '📈 Indian Stock' : '🪙 Crypto'}
                  </span>
                </div>
                <button 
                  className="btn-open-exchange"
                  onClick={() => openExchange(selectedScrip.symbol, selectedScrip.market_type)}
                >
                  📈 {selectedScrip.market_type === 'indian_stock' ? 'Open on TradingView' : 'Open on Delta'}
                </button>
              </div>

              <div className="price-display-main">
                <div className="price-label">Current Mark Price</div>
                <div className={`current-price ${currentPrice ? 'price-tick' : ''}`}>
                  {currentPrice ? `$${currentPrice.toFixed(4)}` : '--'}
                </div>
              </div>

              <div className="price-meta">
                <div className="price-source">
                  <span className="status-dot"></span>
                  <span>Live • {lastUpdate[selectedScrip.symbol] || '--:--:--'}</span>
                </div>
                <span>
                  {selectedScrip.market_type === 'forex' ? 'Twelve Data API' : 
                   selectedScrip.market_type === 'indian_stock' ? 'Yahoo Finance' : 'Delta Exchange'}
                </span>
              </div>
            </div>

            {/* Levels Container */}
            <div className="levels-container slide-up">
              <div className="levels-header">
                <h2 className="levels-title">
                  Support & Resistance Levels ({sortedLevels.length})
                </h2>
                <div className="timeframe-filter">
                  <label className="filter-label">Timeframe:</label>
                  <select 
                    value={timeframeFilter} 
                    onChange={(e) => setTimeframeFilter(e.target.value)}
                    className="filter-select"
                  >
                    <option value="all">All Timeframes</option>
                    {availableTimeframes.map(tf => (
                      <option key={tf} value={tf}>
                        {tf.toUpperCase()} ({selectedScrip.trigger_levels.filter(l => l.timeframe === tf).length})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="levels-grid">
                {sortedLevels.map((level) => {
                  const distance = calculateDistance(currentPrice, level.trigger_price);
                  const alertEnabled = !level.alert_disabled;
                  const timeframeLabel = level.timeframe ? level.timeframe.toUpperCase() : '1W';
                  
                  return (
                    <div 
                      key={level.originalIndex} 
                      className={`level-card ${distance?.triggered ? 'triggered' : ''} fade-in`}
                      data-level-index={level.originalIndex}
                    >
                      <div className="level-card-header">
                        <div className="level-meta">
                          <span className="timeframe-icon">{timeframeLabel}</span>
                          <span className="level-number">Level {level.originalIndex + 1}</span>
                        </div>
                        {distance && (
                          <div className={`distance-indicator ${distance.color}`}>
                            {distance.triggered ? '🔔' : '↓'} {distance.text}
                          </div>
                        )}
                      </div>

                      <div className="level-price-display">
                        <div className="level-price">${level.trigger_price.toFixed(2)}</div>
                      </div>

                      <div className="level-stats">
                        <div className="stat-item">
                          <span className="stat-label">Bottom</span>
                          <span className="stat-value">${level.bottom.toFixed(2)}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Rally High</span>
                          <span className="stat-value">${(level.rally_end_high || level.trigger_price).toFixed(2)}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Rally Length</span>
                          <span className="stat-value">{level.rally_length}w</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Total Move</span>
                          <span className="stat-value">{level.total_move_pct.toFixed(1)}%</span>
                        </div>
                      </div>

                      <div className="progress-section">
                        <div className="progress-bar-container">
                          <div 
                            className="progress-bar-fill"
                            style={{
                              width: distance ? 
                                (distance.triggered ? '100%' : `${Math.max(0, 100 - distance.percentage)}%`) 
                                : '0%',
                              backgroundColor: distance?.color === 'bullish' ? 'var(--color-bullish)' :
                                             distance?.color === 'warning' ? 'var(--color-warning)' :
                                             'var(--color-bearish)'
                            }}
                          />
                        </div>
                      </div>

                      <div className="level-actions">
                        <div 
                          className="alert-switch"
                          onClick={() => toggleAlert(level.originalIndex)}
                        >
                          <span className="alert-label">Alert</span>
                          <div className={`switch ${alertEnabled ? 'active' : ''}`}>
                            <div className="switch-thumb"></div>
                          </div>
                          <span className="alert-icon">{alertEnabled ? '🔔' : '🔕'}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default MonitorPremium;
