import React, { useState, useEffect, useCallback } from 'react';
import InstallPrompt from '../components/InstallPrompt';
import PriceAlertPanel from '../components/PriceAlertPanel';
import MorningAlertPanel from '../components/MorningAlertPanel';
import './PinAlerts.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function formatPrice(value, marketType) {
  if (value == null) return '—';
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  if (marketType === 'indian_stocks') return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2 });
}

function PinCard({ pin, isAdmin, onSaved }) {
  const [above, setAbove] = useState(pin.alert_above ?? '');
  const [below, setBelow] = useState(pin.alert_below ?? '');
  const [busy, setBusy] = useState(false);
  const quote = pin.quote || {};
  const ltp = quote.ltp;
  const pct = quote.change_pct;

  const save = async () => {
    setBusy(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/pins/${pin.symbol}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          symbol: pin.symbol,
          market_type: pin.market_type,
          alert_above: above === '' ? null : Number(above),
          alert_below: below === '' ? null : Number(below),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Save failed');
      onSaved();
    } catch (err) {
      alert(err.message || 'Failed to save');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`pin-card ${pin.polling_active ? 'live' : 'paused'}`}>
      <div className="pin-card-header">
        <h3>{pin.symbol}</h3>
        <span className="pin-market-type">{pin.market_type}</span>
      </div>
      <div className="pin-price">{formatPrice(ltp, pin.market_type)}</div>
      {pct != null && (
        <div className={`pin-change ${pct >= 0 ? 'up' : 'down'}`}>
          {pct >= 0 ? '+' : ''}
          {Number(pct).toFixed(2)}%
        </div>
      )}
      {pin.session_status && (
        <div className="pin-session">{pin.session_status}</div>
      )}
      <div className="pin-alerts-row">
        <label>
          Above
          <input
            type="number"
            value={above}
            onChange={(e) => setAbove(e.target.value)}
            disabled={!isAdmin}
            placeholder="—"
          />
        </label>
        <label>
          Below
          <input
            type="number"
            value={below}
            onChange={(e) => setBelow(e.target.value)}
            disabled={!isAdmin}
            placeholder="—"
          />
        </label>
      </div>
      {isAdmin && (
        <button type="button" className="pin-save-btn" onClick={save} disabled={busy}>
          {busy ? 'Saving…' : 'Save alerts'}
        </button>
      )}
    </div>
  );
}

function PinAlerts({ user }) {
  const [pins, setPins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const isAdmin = user?.role === 'admin';

  const loadPins = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/pins`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load pins');
      setPins(data.pins || []);
      setError('');
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPins();
    const id = setInterval(loadPins, 30000);
    return () => clearInterval(id);
  }, [loadPins]);

  return (
    <div className="pin-alerts-page">
      <div className="pin-alerts-container">
        <header className="pin-alerts-header">
          <h1>Pinned stocks</h1>
          <p>
            Alerts set from Krypto desktop sync here. All subscribed users get a phone
            notification when price crosses an alert level.
          </p>
        </header>

        <section className="pin-notify-section">
          <InstallPrompt />
          <PriceAlertPanel />
          <MorningAlertPanel />
        </section>

        {loading && <p className="pin-loading">Loading pins…</p>}
        {error && <p className="pin-error">{error}</p>}

        {!loading && !error && pins.length === 0 && (
          <p className="pin-empty">
            No pins yet. Say <strong>pin tcs</strong> or <strong>pin btc</strong> in Krypto desktop.
          </p>
        )}

        <div className="pin-grid">
          {pins.map((pin) => (
            <PinCard
              key={pin.symbol}
              pin={pin}
              isAdmin={isAdmin}
              onSaved={loadPins}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default PinAlerts;
