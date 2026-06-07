import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTriggeredLevelAlerts } from '../utils/triggeredAlerts';
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      setLevels(await fetchTriggeredLevelAlerts());
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
    sessionStorage.setItem('selectedLevelIndex', String(levelIndex));
    navigate('/monitor');
  };

  return (
    <div className="triggered-alerts-page">
      <div className="triggered-alerts-container">
        <header className="triggered-alerts-header">
          <h1>Monitor level alerts</h1>
          <p>
            Scrips from Monitor whose support level has been hit (price at or below trigger).
            {levels.length > 0 ? ` ${levels.length} triggered.` : ' None triggered right now.'}
            {' '}Pin alerts are separate — manage them under Pins; phone push fires when a pin level triggers.
          </p>
        </header>

        {loading && <p className="triggered-loading">Loading monitor alerts…</p>}
        {error && <p className="triggered-error">{error}</p>}

        {!loading && !error && levels.length === 0 && (
          <p className="triggered-empty">
            No monitor levels triggered. They appear here when live price drops to a support trigger.
          </p>
        )}

        {levels.length > 0 && (
          <section className="triggered-section">
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
                      Level {formatPrice(item.trigger_price, item.market_type)}
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
