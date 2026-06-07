import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { promptInstallFromButton } from './InstallPrompt';
import { isIos, isStandalonePwa } from '../utils/pushPlatform';
import { fetchTriggeredLevelAlerts } from '../utils/triggeredAlerts';
import './Navbar.css';
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
        const levels = await fetchTriggeredLevelAlerts();
        setTriggeredCount(levels.length);
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
    navigate('/notifications');
  };

  const handleInstallClick = async () => {
    closeMenu();
    if (isStandalonePwa()) {
      window.alert('App is already installed.');
      return;
    }
    if (isIos()) {
      window.alert('Safari → Share → Add to Home Screen, then open Delta Levels from your home screen.');
      return;
    }
    const result = await promptInstallFromButton();
    if (!result.ok && result.reason === 'no_prompt') {
      window.alert(
        'Install not ready yet. Use Chrome menu (⋮) → Install app, or Add to Home screen. Visit the site a few times on HTTPS first.'
      );
    }
  };

  const navItems = [
    { to: '/monitor', label: 'Monitor', icon: '📊' },
    { to: '/pins', label: 'Pins', icon: '📌' },
    { to: '/alerts', label: 'TV Alerts', icon: '📡' },
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
              {!isStandalonePwa() && (
                <button type="button" className="alerts-chip" onClick={handleInstallClick} title="Install app">
                  📲 Install
                </button>
              )}
              <button
                type="button"
                className="alerts-chip"
                onClick={handleAlertsClick}
                title="Monitor scrips with triggered support levels"
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
            Monitor level alerts
            {triggeredCount > 0 && (
              <span className="notification-badge">{triggeredCount}</span>
            )}
          </button>
          {!isStandalonePwa() && (
            <button type="button" className="drawer-alerts-link" onClick={handleInstallClick}>
              <span className="nav-icon">📲</span>
              Install app
            </button>
          )}
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
