import React, { useState, useEffect, useCallback } from 'react';
import './TradingViewAlerts.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function formatPrice(value, marketType) {
  if (value == null) return '—';
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  if (marketType === 'indian_stocks') {
    return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  }
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2 });
}

function formatTime(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function AlertCard({ alert }) {
  return (
    <div className="tv-alert-card">
      <div className="tv-alert-header">
        <h3>{alert.symbol || '—'}</h3>
        <span className="tv-alert-market">{alert.market_type}</span>
      </div>
      {alert.action && <div className="tv-alert-action">{alert.action}</div>}
      <div className="tv-alert-price">{formatPrice(alert.price, alert.market_type)}</div>
      {alert.message && <p className="tv-alert-message">{alert.message}</p>}
      <div className="tv-alert-meta">
        {alert.interval && <span>{alert.interval}</span>}
        <span>{formatTime(alert.created_at)}</span>
      </div>
    </div>
  );
}

function TradingViewAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadAlerts = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/alerts/tradingview?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load alerts');
      setAlerts(data.alerts || []);
      setError('');
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
    const id = setInterval(loadAlerts, 30000);
    return () => clearInterval(id);
  }, [loadAlerts]);

  return (
    <div className="tv-alerts-page">
      <div className="tv-alerts-container">
        <header className="tv-alerts-header">
          <h1>TradingView alerts</h1>
          <p>
            Alerts fired from your Pine Script via webhook. Push notifications are sent
            to all subscribed users when TradingView triggers an alert.
          </p>
        </header>

        {loading && <p className="tv-loading">Loading alerts…</p>}
        {error && <p className="tv-error">{error}</p>}

        {!loading && !error && alerts.length === 0 && (
          <p className="tv-empty">
            No TradingView alerts yet — set up your Pine Script webhook on Render.
          </p>
        )}

        <div className="tv-alert-list">
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default TradingViewAlerts;
