import React, { useState, useEffect, useCallback, useRef } from 'react';
import { usePinAlertSound, getRingingPins, clearLocalPinRinging } from '../utils/usePinAlertSound';
import { fetchPins, stopPinAlert } from '../utils/pinAlertApi';
import './PinAlertBanner.css';

const POLL_MS = 10_000;

function PinAlertBanner({ pins, onStop, stopping }) {
  const ringing = pins.filter((p) => p.alert_ringing);
  if (!ringing.length) return null;

  return (
    <div className="pin-alert-banner" role="alert">
      <div className="pin-alert-banner-inner">
        <span className="pin-alert-banner-icon">🔔</span>
        <div className="pin-alert-banner-text">
          <strong>Price alert active</strong>
          {ringing.map((pin) => (
            <span key={pin.symbol} className="pin-alert-banner-item">
              {pin.symbol}
              {pin.alert_direction ? ` (${pin.alert_direction})` : ''}
            </span>
          ))}
        </div>
        <div className="pin-alert-banner-actions">
          {ringing.map((pin) => (
            <button
              key={pin.symbol}
              type="button"
              className="pin-stop-alert-btn"
              disabled={stopping === pin.symbol}
              onClick={() => onStop(pin.symbol)}
            >
              {stopping === pin.symbol ? 'Stopping…' : `Stop ${pin.symbol}`}
            </button>
          ))}
          {ringing.length > 1 && (
            <button
              type="button"
              className="pin-stop-alert-btn pin-stop-all-btn"
              disabled={Boolean(stopping)}
              onClick={() => ringing.forEach((p) => onStop(p.symbol))}
            >
              Stop all
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/** Polls pins app-wide, repeats sound while ringing, shows stop banner. */
export default function PinAlertSoundWatcher() {
  const [pins, setPins] = useState([]);
  const [stopping, setStopping] = useState('');
  const stateRef = useRef({});

  const loadPins = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      setPins(await fetchPins());
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadPins();
    const id = setInterval(loadPins, POLL_MS);
    return () => clearInterval(id);
  }, [loadPins]);

  usePinAlertSound(pins, stateRef);

  const handleStop = async (symbol) => {
    setStopping(symbol);
    try {
      await stopPinAlert(symbol);
      clearLocalPinRinging(stateRef, symbol);
      await loadPins();
    } catch (err) {
      console.warn('[pin alert] stop failed:', err);
    } finally {
      setStopping('');
    }
  };

  const ringingFromServer = pins.filter((p) => p.alert_ringing);
  const localRinging = getRingingPins(pins, stateRef).filter((p) => !p.alert_ringing);
  const bannerPins = [...ringingFromServer, ...localRinging];

  return (
    <PinAlertBanner pins={bannerPins} onStop={handleStop} stopping={stopping} />
  );
}
