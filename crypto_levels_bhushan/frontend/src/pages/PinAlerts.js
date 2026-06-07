import React, { useState, useEffect, useCallback } from 'react';
import PushNotificationPanel from '../components/PushNotificationPanel';
import { fetchPins, stopPinAlert } from '../utils/pinAlertApi';
import './PinAlerts.css';
import '../components/PinAlertBanner.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function formatPrice(value, marketType) {
  if (value == null) return '—';
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  if (marketType === 'indian_stocks') return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2 });
}

function PinCard({ pin, isAdmin, onSaved, onStop, stopping }) {
  const [above, setAbove] = useState(pin.alert_above ?? '');
  const [below, setBelow] = useState(pin.alert_below ?? '');
  const [busy, setBusy] = useState(false);
  const quote = pin.quote || {};
  const ltp = quote.ltp;
  const pct = quote.change_pct;
  const ringing = pin.alert_ringing;
  const direction = pin.alert_direction;
  const triggerPrice = pin.alert_trigger_price;

  const ringingLabel = () => {
    if (!ringing || !direction) {
      return 'Alert ringing — tap Stop to silence';
    }
    const level = formatPrice(triggerPrice, pin.market_type);
    if (direction === 'above') {
      return `Triggered: price is ABOVE ${level}`;
    }
    return `Triggered: price is BELOW ${level}`;
  };

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
    <div className={`pin-card ${pin.polling_active ? 'live' : 'paused'} ${ringing ? 'ringing' : ''}`}>
      <div className="pin-card-header">
        <h3>{pin.symbol}</h3>
        <span className="pin-market-type">{pin.market_type}</span>
      </div>
      {ringing && (
        <div className="pin-ringing-badge">
          {ringingLabel()}
        </div>
      )}
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
      {ringing && (
        <button
          type="button"
          className="pin-stop-alert-btn-card"
          disabled={stopping === pin.symbol}
          onClick={() => onStop(pin.symbol)}
        >
          {stopping === pin.symbol ? 'Stopping…' : 'Stop alert'}
        </button>
      )}
    </div>
  );
}

function PinAlerts({ user }) {
  const [pins, setPins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stopping, setStopping] = useState('');
  const isAdmin = user?.role === 'admin';

  const loadPins = useCallback(async () => {
    try {
      setPins(await fetchPins());
      setError('');
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPins();
    const id = setInterval(loadPins, 10000);
    return () => clearInterval(id);
  }, [loadPins]);

  const handleStop = async (symbol) => {
    setStopping(symbol);
    try {
      await stopPinAlert(symbol);
      await loadPins();
    } catch (err) {
      alert(err.message || 'Failed to stop alert');
    } finally {
      setStopping('');
    }
  };

  return (
    <div className="pin-alerts-page">
      <div className="pin-alerts-container">
        <header className="pin-alerts-header">
          <h1>Pinned stocks</h1>
          <p>
            Set above/below price alerts for pinned scrips. When triggered you get a phone push
            (&quot;price is ABOVE/BELOW your level&quot;) and sound until you tap <strong>Stop alert</strong>.
            Monitor support levels are separate — use the Alerts button in the nav bar.
          </p>
        </header>

        <section className="pin-notify-section">
          <PushNotificationPanel />
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
              onStop={handleStop}
              stopping={stopping}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default PinAlerts;
