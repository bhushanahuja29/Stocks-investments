import React, { useState, useEffect } from 'react';
import {
  isPushSupported,
  requestNotificationPermission,
  sendLocalTestNotification,
  subscribeToPush,
  unsubscribeFromPush,
  sendServerTestPush,
  isPushSubscribed,
} from '../utils/pushNotifications';
import { pushPlatformHint } from '../utils/pushPlatform';
import './PriceAlertPanel.css';

function PriceAlertPanel() {
  const [permission, setPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );
  const [subscribed, setSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [supported] = useState(isPushSupported());

  useEffect(() => {
    isPushSubscribed().then(setSubscribed);
  }, []);

  const handleEnable = async () => {
    setBusy(true);
    setMessage('');
    try {
      const perm = await requestNotificationPermission();
      setPermission(perm);
      if (perm !== 'granted') {
        setMessage('Notifications blocked. Enable them in browser settings.');
        return;
      }
      await sendLocalTestNotification();
      setMessage('Local test sent. Subscribing for pin price alerts…');
      await subscribeToPush();
      setSubscribed(true);
      setMessage('Price alerts enabled — you will be notified when pinned stocks cross alert levels.');
    } catch (err) {
      setMessage(err.message || String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleServerTest = async () => {
    setBusy(true);
    setMessage('');
    try {
      const result = await sendServerTestPush();
      setMessage(
        result.sent > 0
          ? `Push sent to ${result.sent} device(s). Check your phone notification tray (not this page).`
          : 'No subscription found — tap Enable first.'
      );
    } catch (err) {
      setMessage(err.message || String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleDisable = async () => {
    setBusy(true);
    setMessage('');
    try {
      await unsubscribeFromPush();
      setSubscribed(false);
      setMessage('Push alerts disabled.');
    } catch (err) {
      setMessage(err.message || String(err));
    } finally {
      setBusy(false);
    }
  };

  if (!supported) {
    return (
      <div className="price-alert-panel">
        <p className="price-alert-muted">Web Push not supported in this browser.</p>
      </div>
    );
  }

  return (
    <div className="price-alert-panel">
      <h4 className="price-alert-title">Pin price alerts (phone)</h4>
      <p className="price-alert-desc">{pushPlatformHint()}</p>
      <p className="price-alert-status">
        Permission: <strong>{permission}</strong>
        {subscribed ? ' · Subscribed' : ''}
      </p>
      <div className="price-alert-actions">
        {!subscribed ? (
          <button
            type="button"
            className="price-btn primary"
            onClick={handleEnable}
            disabled={busy || permission === 'denied'}
          >
            {busy ? 'Working…' : 'Enable price alert notifications'}
          </button>
        ) : (
          <>
            <button
              type="button"
              className="price-btn secondary"
              onClick={handleServerTest}
              disabled={busy}
            >
              Send test push
            </button>
            <button
              type="button"
              className="price-btn danger"
              onClick={handleDisable}
              disabled={busy}
            >
              Disable
            </button>
          </>
        )}
      </div>
      {message && <p className="price-alert-msg">{message}</p>}
      {permission === 'denied' && (
        <p className="price-alert-warn">Unblock notifications in browser site settings.</p>
      )}
    </div>
  );
}

export default PriceAlertPanel;
