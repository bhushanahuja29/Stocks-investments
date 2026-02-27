import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Navbar.css';

function Navbar({ user, onLogout, refreshTrigger }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState('default');
  const [triggeredCount, setTriggeredCount] = useState(0);
  const [triggeredLevels, setTriggeredLevels] = useState([]);
  const [showNotificationDropdown, setShowNotificationDropdown] = useState(false);
  const location = useLocation();
  const navigate = useNavigate(); // Always call hook unconditionally

  const isActive = (path) => location.pathname === path;

  // Check notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  // Fetch triggered levels count and details
  useEffect(() => {
    const fetchTriggeredCount = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/scrips');
        const data = await response.json();
        
        if (data.success) {
          let count = 0;
          const levels = [];
          
          // Fetch prices for all scrips
          const pricePromises = data.scrips.map(async (scrip) => {
            try {
              const priceResponse = await fetch(
                `http://localhost:8000/api/price/${scrip.symbol}?market_type=${scrip.market_type || 'crypto'}`
              );
              const priceData = await priceResponse.json();
              return {
                symbol: scrip.symbol,
                price: priceData.success ? priceData.mark_price : null
              };
            } catch (error) {
              console.error(`Error fetching price for ${scrip.symbol}:`, error);
              return { symbol: scrip.symbol, price: null };
            }
          });
          
          const prices = await Promise.all(pricePromises);
          const priceMap = {};
          prices.forEach(p => {
            if (p.price) priceMap[p.symbol] = p.price;
          });
          
          // Check each level against current price
          data.scrips.forEach(scrip => {
            const currentPrice = priceMap[scrip.symbol];
            
            if (scrip.trigger_levels && currentPrice) {
              scrip.trigger_levels.forEach((level, idx) => {
                // Check if alert is enabled
                if (level.alert_disabled) return;
                
                // Check if price has triggered the level (price <= trigger_price)
                const isTriggered = currentPrice <= level.trigger_price;
                
                if (isTriggered) {
                  count++;
                  levels.push({
                    symbol: scrip.symbol,
                    levelIndex: idx,
                    triggerPrice: level.trigger_price,
                    bottom: level.bottom,
                    timeframe: level.timeframe || 'UNKNOWN',
                    rallyLength: level.rally_length,
                    totalMovePct: level.total_move_pct,
                    marketType: scrip.market_type || 'crypto',
                    currentPrice: currentPrice
                  });
                }
              });
            }
          });
          
          setTriggeredCount(count);
          setTriggeredLevels(levels);
        }
      } catch (error) {
        console.error('Error fetching triggered count:', error);
      }
    };

    // Fetch immediately
    fetchTriggeredCount();

    // Refresh every 30 seconds
    const interval = setInterval(fetchTriggeredCount, 30000);

    return () => clearInterval(interval);
  }, [refreshTrigger]); // Re-fetch when refreshTrigger changes

  const handleNotificationClick = async () => {
    if (triggeredCount > 0) {
      // Show dropdown with triggered levels
      setShowNotificationDropdown(!showNotificationDropdown);
    } else if ('Notification' in window) {
      if (Notification.permission === 'default') {
        const permission = await Notification.requestPermission();
        setNotificationPermission(permission);
        if (permission === 'granted') {
          new Notification('Notifications Enabled!', {
            body: 'You will now receive alerts when price levels are triggered.',
            icon: '/favicon.ico'
          });
        }
      } else if (Notification.permission === 'denied') {
        alert('Notifications are blocked. Please enable them in your browser settings.');
      } else {
        // Show dropdown even if no triggered levels
        setShowNotificationDropdown(!showNotificationDropdown);
      }
    } else {
      alert('Your browser does not support notifications.');
    }
  };

  const handleLevelClick = async (level) => {
    // Navigate to monitor page with the symbol selected
    setShowNotificationDropdown(false);
    
    // Store the selected symbol in sessionStorage so Monitor page can select it
    sessionStorage.setItem('selectedSymbol', level.symbol);
    sessionStorage.setItem('selectedLevelIndex', level.levelIndex.toString());
    
    // Navigate to monitor page
    navigate('/monitor');
  };

  const handleDisableAlert = async (level, e) => {
    e.stopPropagation(); // Prevent level click
    
    try {
      const response = await fetch(`http://localhost:8000/api/scrips/${level.symbol}/alert`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: level.symbol,
          level_index: level.levelIndex,
          disabled: true
        })
      });

      const data = await response.json();
      
      if (data.success) {
        // Remove from triggered levels
        setTriggeredLevels(prev => prev.filter(l => 
          !(l.symbol === level.symbol && l.levelIndex === level.levelIndex)
        ));
        setTriggeredCount(prev => prev - 1);
        
        // Trigger refresh in parent
        if (refreshTrigger !== undefined) {
          // This will trigger a re-fetch
          window.dispatchEvent(new Event('alertToggled'));
        }
      }
    } catch (error) {
      console.error('Error disabling alert:', error);
      alert('Failed to disable alert');
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="brand-icon">🎯</span>
          <div className="brand-text">
            <h2>Delta Levels</h2>
            <span>Support & Resistance Tracker</span>
          </div>
        </div>

        {user.role === 'admin' && (
          <button 
            className="hamburger"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        )}

        <div className={`navbar-menu ${menuOpen ? 'open' : ''}`}>
          <div className="nav-links">
            <Link 
              to="/monitor" 
              className={isActive('/monitor') ? 'active' : ''}
              onClick={() => setMenuOpen(false)}
            >
              📊 Monitor
            </Link>
            <Link 
              to="/zone-finder" 
              className={isActive('/zone-finder') ? 'active' : ''}
              onClick={() => setMenuOpen(false)}
            >
              🔍 Zone Finder
            </Link>
            {user.role === 'admin' && (
              <Link 
                to="/admin/users" 
                className={isActive('/admin/users') ? 'active' : ''}
                onClick={() => setMenuOpen(false)}
              >
                👥 Users
              </Link>
            )}
          </div>

          <div className="navbar-actions">
            <div className="notification-container">
              <button 
                className={`notification-btn ${notificationPermission === 'granted' ? 'enabled' : ''}`}
                onClick={handleNotificationClick}
                title={
                  notificationPermission === 'granted' 
                    ? `Notifications enabled${triggeredCount > 0 ? ` - ${triggeredCount} triggered` : ''}` 
                    : notificationPermission === 'denied'
                    ? 'Notifications blocked'
                    : 'Enable notifications'
                }
              >
                {notificationPermission === 'granted' ? '🔔' : '🔕'}
                {triggeredCount > 0 && (
                  <span className="notification-badge">{triggeredCount}</span>
                )}
              </button>

              {showNotificationDropdown && (
                <>
                  <div className="notification-dropdown">
                    <div className="notification-header">
                      <h3>Triggered Levels ({triggeredCount})</h3>
                      <button 
                        className="close-dropdown"
                        onClick={() => setShowNotificationDropdown(false)}
                      >
                        ✕
                      </button>
                    </div>
                    
                    {triggeredLevels.length === 0 ? (
                      <div className="no-notifications">
                        <p>No triggered levels</p>
                        <span>All clear! 🎉</span>
                      </div>
                    ) : (
                      <div className="notification-list">
                        {triggeredLevels.map((level, idx) => (
                          <div 
                            key={`${level.symbol}-${level.levelIndex}`}
                            className="notification-item"
                            onClick={() => handleLevelClick(level)}
                          >
                            <div className="notification-item-header">
                              <span className="notification-symbol">{level.symbol}</span>
                              <span className="notification-timeframe">{level.timeframe}</span>
                            </div>
                            <div className="notification-item-details">
                              <span className="notification-price">
                                Trigger: ${level.triggerPrice.toFixed(2)} | Current: ${level.currentPrice.toFixed(2)}
                              </span>
                              <span className="notification-move">
                                {level.rallyLength} bars • {level.totalMovePct.toFixed(1)}%
                              </span>
                            </div>
                            <button 
                              className="disable-alert-btn"
                              onClick={(e) => handleDisableAlert(level, e)}
                              title="Disable alert for this level"
                            >
                              🔕 Disable
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div 
                    className="notification-overlay"
                    onClick={() => setShowNotificationDropdown(false)}
                  ></div>
                </>
              )}
            </div>

            <div className="navbar-user">
              <div className="user-info">
                <div className="user-details">
                  <span className="user-name">{user.name}</span>
                  <span className="user-role">{user.role}</span>
                </div>
                {user.role !== 'admin' && user.days_remaining !== undefined && (
                  <div className={`days-remaining ${user.days_remaining <= 7 ? 'warning' : ''}`}>
                    {user.days_remaining} days left
                  </div>
                )}
              </div>
              <button className="logout-btn" onClick={onLogout}>
                Logout
              </button>
            </div>
          </div>
        </div>

        {menuOpen && (
          <div className="menu-overlay" onClick={() => setMenuOpen(false)}></div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
