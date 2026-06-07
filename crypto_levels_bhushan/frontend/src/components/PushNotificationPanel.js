import React, { useState, useEffect, useCallback } from 'react';
import {
  isPushSupported,
  requestNotificationPermission,
  sendLocalTestNotification,
  subscribeToPush,
  unsubscribeFromPush,
  sendServerTestPush,
  ensurePushSubscription,
  getPushSubscriptionState,
} from '../utils/pushNotifications';
import { pushPlatformHint } from '../utils/pushPlatform';
import './PriceAlertPanel.css';

function PushNotificationPanel() {
  const [permission, setPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );
  const [subscribed, setSubscribed] = useState(false);
  const [devices, setDevices] = useState(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [supported] = useState(isPushSupported());

  const refreshState = useCallback(async () => {
    const state = await getPushSubscriptionState();
    setSubscribed(state.active || state.browser);
    setDevices(state.devices);
    if (state.needsSync && Notification.permission === 'granted') {
      const result = await ensurePushSubscription();
      if (result.ok) {
        const synced = await getPushSubscriptionState();
        setSubscribed(synced.active || synced.browser);
        setDevices(synced.devices);
      }
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (Notification.permission === 'granted' && localStorage.getItem('token')) {
        await ensurePushSubscription();
      }
      if (!cancelled) await refreshState();
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshState]);

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
      setMessage('Local test sent. Registering this device…');
      await subscribeToPush();
      await refreshState();
      setMessage(
        'Notifications enabled — Pin alerts when prices cross levels, and Morning Nifty 50 at 8 AM IST.'
      );
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
      if (!subscribed) {
        await ensurePushSubscription();
      }
      const result = await sendServerTestPush();
      setMessage(
        result.sent > 0
          ? `Test push sent to ${result.sent} device(s). Check your phone notification tray.`
          : 'Could not deliver — tap Enable notifications again.'
      );
      await refreshState();
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
      setDevices(0);
      setMessage('Push notifications disabled on this device.');
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
      <h4 className="price-alert-title">Phone notifications</h4>
      <p className="price-alert-desc">{pushPlatformHint()}</p>
      <ul className="price-alert-desc" style={{ marginTop: '0.5rem', paddingLeft: '1.2rem' }}>
        <li><strong>Pin alert</strong> — when a pinned stock crosses your above/below level</li>
        <li><strong>Morning alert</strong> — Nifty 50 movers ≥2% at 8 AM IST</li>
      </ul>
      <p className="price-alert-status">
        Permission: <strong>{permission}</strong>
        {subscribed ? ` · Subscribed${devices > 1 ? ` (${devices} devices)` : ''}` : ''}
      </p>
      <div className="price-alert-actions">
        {!subscribed ? (
          <button
            type="button"
            className="price-btn primary"
            onClick={handleEnable}
            disabled={busy || permission === 'denied'}
          >
            {busy ? 'Working…' : 'Enable notifications'}
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

export default PushNotificationPanel;
