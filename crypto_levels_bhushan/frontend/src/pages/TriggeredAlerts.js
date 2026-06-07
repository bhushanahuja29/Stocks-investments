import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAllTriggeredNotifications } from '../utils/triggeredAlerts';
import { stopPinAlert } from '../utils/pinAlertApi';
import './TriggeredAlerts.css';

function formatPrice(value, marketType) {
  if (value == null) return '—';
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  if (marketType === 'indian_stock' || marketType === 'indian_stocks') {
    return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  }
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2 });
}

function TriggeredAlerts() {
  const navigate = useNavigate();
  const [levels, setLevels] = useState([]);
  const [pins, setPins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stopping, setStopping] = useState('');

  const load = useCallback(async () => {
    try {
      const data = await fetchAllTriggeredNotifications();
      setLevels(data.levels);
      setPins(data.pins);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load]);

  const openInMonitor = (symbol, levelIndex) => {
    sessionStorage.setItem('selectedSymbol', symbol);
    if (levelIndex != null) {
      sessionStorage.setItem('selectedLevelIndex', String(levelIndex));
    } else {
      sessionStorage.removeItem('selectedLevelIndex');
    }
    navigate('/monitor');
  };

  const handleStopPin = async (symbol) => {
    setStopping(symbol);
    try {
      await stopPinAlert(symbol);
      await load();
    } catch (err) {
      alert(err.message || 'Failed to stop alert');
    } finally {
      setStopping('');
    }
  };

  const total = levels.length + pins.length;

  return (
    <div className="triggered-alerts-page">
      <div className="triggered-alerts-container">
        <header className="triggered-alerts-header">
          <h1>Triggered alerts</h1>
          <p>
            Support levels hit and pin price alerts ringing right now.
            {total > 0 ? ` ${total} active.` : ' None active.'}
          </p>
        </header>

        {loading && <p className="triggered-loading">Loading alerts…</p>}
        {error && <p className="triggered-error">{error}</p>}

        {!loading && !error && total === 0 && (
          <p className="triggered-empty">No triggered alerts. Levels appear here when price hits a support trigger.</p>
        )}

        {pins.length > 0 && (
          <section className="triggered-section">
            <h2>Pin price alerts</h2>
            <div className="triggered-list">
              {pins.map((pin) => (
                <div key={pin.id} className="triggered-card ringing">
                  <div className="triggered-card-top">
                    <span className="triggered-symbol">{pin.symbol}</span>
                    <span className="triggered-badge pin">Ringing</span>
                  </div>
                  <div className="triggered-prices">
                    <span>LTP {formatPrice(pin.current_price, pin.market_type)}</span>
                    {pin.alert_above != null && (
                      <span className="triggered-meta">Above {formatPrice(pin.alert_above, pin.market_type)}</span>
                    )}
                    {pin.alert_below != null && (
                      <span className="triggered-meta">Below {formatPrice(pin.alert_below, pin.market_type)}</span>
                    )}
                  </div>
                  <div className="triggered-actions">
                    <button
                      type="button"
                      className="triggered-btn stop"
                      disabled={stopping === pin.symbol}
                      onClick={() => handleStopPin(pin.symbol)}
                    >
                      {stopping === pin.symbol ? 'Stopping…' : 'Stop alert'}
                    </button>
                    <button type="button" className="triggered-btn" onClick={() => navigate('/pins')}>
                      Manage pins
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {levels.length > 0 && (
          <section className="triggered-section">
            <h2>Level triggers</h2>
            <div className="triggered-list">
              {levels.map((item) => (
                <div key={item.id} className="triggered-card">
                  <div className="triggered-card-top">
                    <span className="triggered-symbol">{item.symbol}</span>
                    <span className="triggered-badge level">
                      {(item.timeframe || '1w').toUpperCase()}
                    </span>
                  </div>
                  <div className="triggered-prices">
                    <span className="triggered-hit">
                      Trigger {formatPrice(item.trigger_price, item.market_type)}
                    </span>
                    <span className="triggered-current">
                      Now {formatPrice(item.current_price, item.market_type)}
                    </span>
                  </div>
                  <div className="triggered-actions">
                    <button
                      type="button"
                      className="triggered-btn primary"
                      onClick={() => openInMonitor(item.symbol, item.level_index)}
                    >
                      View on Monitor
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default TriggeredAlerts;
