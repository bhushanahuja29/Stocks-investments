import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar({ user, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

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

        {menuOpen && (
          <div className="menu-overlay" onClick={() => setMenuOpen(false)}></div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
