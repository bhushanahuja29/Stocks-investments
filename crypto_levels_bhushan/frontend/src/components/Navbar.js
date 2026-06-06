import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Navbar.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
function Navbar({ user, onLogout, refreshTrigger }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [triggeredCount, setTriggeredCount] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => location.pathname === path;
  const closeMenu = useCallback(() => setMenuOpen(false), []);

  useEffect(() => {
    closeMenu();
  }, [location.pathname, closeMenu]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [menuOpen]);

  useEffect(() => {
    const fetchTriggeredCount = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scrips`);
        const data = await response.json();
        if (!data.success) return;

        let count = 0;
        const pricePromises = data.scrips.map(async (scrip) => {
          try {
            const priceResponse = await fetch(
              `${API_URL}/api/price/${scrip.symbol}?market_type=${scrip.market_type || 'crypto'}`
            );
            const priceData = await priceResponse.json();
            return {
              symbol: scrip.symbol,
              price: priceData.success ? priceData.mark_price : null,
            };
          } catch {
            return { symbol: scrip.symbol, price: null };
          }
        });

        const prices = await Promise.all(pricePromises);
        const priceMap = {};
        prices.forEach((p) => {
          if (p.price) priceMap[p.symbol] = p.price;
        });

        data.scrips.forEach((scrip) => {
          const currentPrice = priceMap[scrip.symbol];
          if (scrip.trigger_levels && currentPrice) {
            scrip.trigger_levels.forEach((level) => {
              if (!level.alert_disabled && currentPrice <= level.trigger_price) {
                count += 1;
              }
            });
          }
        });
        setTriggeredCount(count);
      } catch {
        /* ignore */
      }
    };

    fetchTriggeredCount();
    const interval = setInterval(fetchTriggeredCount, 30000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  const handleAlertsClick = () => {
    closeMenu();
    navigate('/pins');
  };

  const navItems = [
    { to: '/monitor', label: 'Monitor', icon: '📊' },
    { to: '/pins', label: 'Pins', icon: '📌' },
    { to: '/zone-finder', label: 'Zones', icon: '🔍' },
  ];
  if (user.role === 'admin') {
    navItems.push({ to: '/admin/users', label: 'Users', icon: '👥' });
  }

  return (
    <>
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/monitor" className="navbar-brand" onClick={closeMenu}>
            <span className="brand-icon">◆</span>
            <div className="brand-text">
              <h2>Delta Levels</h2>
              <span>Crypto & NSE tracker</span>
            </div>
          </Link>

          <div className="navbar-desktop">
            <div className="nav-links">
              {navItems.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={isActive(item.to) ? 'active' : ''}
                >
                  {item.label}
                </Link>
              ))}
            </div>
            <div className="navbar-actions-desktop">
              <button
                type="button"
                className="alerts-chip"
                onClick={handleAlertsClick}
                title="Pin alerts & notifications"
              >
                🔔 Alerts
                {triggeredCount > 0 && (
                  <span className="notification-badge">{triggeredCount}</span>
                )}
              </button>
              <div className="user-chip">
                <span className="user-name">{user.name}</span>
                <span className="user-role">{user.role}</span>
              </div>
              <button type="button" className="logout-btn" onClick={onLogout}>
                Logout
              </button>
            </div>
          </div>

          <div className="navbar-mobile-bar">
            <button
              type="button"
              className="mobile-alerts-btn"
              onClick={handleAlertsClick}
              aria-label="Alerts"
            >
              🔔
              {triggeredCount > 0 && (
                <span className="notification-badge">{triggeredCount}</span>
              )}
            </button>
            <button
              type="button"
              className={`hamburger ${menuOpen ? 'open' : ''}`}
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Menu"
              aria-expanded={menuOpen}
            >
              <span />
              <span />
              <span />
            </button>
          </div>
        </div>
      </nav>

      <div
        className={`mobile-drawer-backdrop ${menuOpen ? 'visible' : ''}`}
        onClick={closeMenu}
        aria-hidden={!menuOpen}
      />

      <aside className={`mobile-drawer ${menuOpen ? 'open' : ''}`} aria-hidden={!menuOpen}>
        <div className="mobile-drawer-header">
          <div>
            <strong>{user.name}</strong>
            <span className="user-role">{user.role}</span>
          </div>
          <button type="button" className="drawer-close" onClick={closeMenu} aria-label="Close">
            ✕
          </button>
        </div>

        <nav className="mobile-drawer-nav">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={isActive(item.to) ? 'active' : ''}
              onClick={closeMenu}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </Link>
          ))}
          <button type="button" className="drawer-alerts-link" onClick={handleAlertsClick}>
            <span className="nav-icon">🔔</span>
            Price alerts & push
          </button>
        </nav>

        {user.role !== 'admin' && user.days_remaining !== undefined && (
          <div className={`drawer-days ${user.days_remaining <= 7 ? 'warning' : ''}`}>
            {user.days_remaining} days remaining
          </div>
        )}

        <button type="button" className="drawer-logout" onClick={onLogout}>
          Logout
        </button>
      </aside>
    </>
  );
}

export default Navbar;
