/**
 * Web Push — morning Nifty + pin price alerts
 */

import { iosWebPushRequiresInstall } from './pushPlatform';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function isPushSupported() {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = window.atob(base64);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) {
    output[i] = raw.charCodeAt(i);
  }
  return output;
}

export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    throw new Error('Service workers not supported');
  }
  return navigator.serviceWorker.register(`${process.env.PUBLIC_URL || ''}/sw.js`);
}

export async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    throw new Error('Notifications not supported');
  }
  if (iosWebPushRequiresInstall()) {
    throw new Error(
      'On iPhone, add Crypto Levels to your Home Screen first, then open it from there.'
    );
  }
  return Notification.requestPermission();
}

/** Mobile/PWA requires showNotification via service worker, not new Notification(). */
export async function sendLocalTestNotification() {
  if (Notification.permission !== 'granted') {
    throw new Error('Notification permission not granted');
  }
  await registerServiceWorker();
  const registration = await navigator.serviceWorker.ready;
  await registration.showNotification('Crypto Levels — test', {
    body: 'Local test OK. Pin price alerts and 8 AM Nifty alerts will arrive here.',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: 'test-local',
    data: { url: '/pins', event: 'pin_alert' },
    renotify: true,
  });
}

export async function fetchVapidPublicKey() {
  const res = await fetch(`${API_URL}/api/push/vapid-public-key`);
  const data = await res.json();
  if (!res.ok || !data.publicKey) {
    throw new Error(data.detail || 'VAPID key not available on server');
  }
  return data.publicKey;
}

export async function subscribeToPush() {
  const registration = await registerServiceWorker();
  await navigator.serviceWorker.ready;

  const publicKey = await fetchVapidPublicKey();
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey),
  });

  const subJson = subscription.toJSON();
  const res = await fetch(`${API_URL}/api/push/subscribe`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      endpoint: subJson.endpoint,
      keys: subJson.keys,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Subscribe failed');
  }
  localStorage.setItem('pushSubscribed', '1');
  return data;
}

export async function unsubscribeFromPush() {
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();
  if (subscription) {
    const endpoint = subscription.endpoint;
    await fetch(`${API_URL}/api/push/unsubscribe`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      body: JSON.stringify({ endpoint }),
    });
    await subscription.unsubscribe();
  }
  localStorage.removeItem('pushSubscribed');
  localStorage.removeItem('morningPushSubscribed');
}

export async function sendServerTestPush() {
  const res = await fetch(`${API_URL}/api/push/test`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Test push failed');
  }
  return data;
}

export async function isPushSubscribed() {
  if (!('serviceWorker' in navigator)) return false;
  try {
    const registration = await navigator.serviceWorker.ready;
    const sub = await registration.pushManager.getSubscription();
    return Boolean(sub);
  } catch {
    return false;
  }
}

// Re-export for backward compatibility with morningPush.js consumers
export {
  isPushSupported as defaultSupported,
};
