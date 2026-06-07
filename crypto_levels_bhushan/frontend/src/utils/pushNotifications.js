/**
 * Web Push — pin price alerts + morning Nifty 50 alerts
 */

import { iosWebPushRequiresInstall } from './pushPlatform';
import { waitForServiceWorkerRegistration } from './pwa';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const VAPID_STORAGE_KEY = 'pushVapidPublicKey';

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
  const reg = await waitForServiceWorkerRegistration();
  if (!reg) throw new Error('Service workers not supported');
  return reg;
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
  const registration = await registerServiceWorker();
  await navigator.serviceWorker.ready;
  await registration.showNotification('Test — push notifications', {
    body: 'Local test OK. Pin alerts and 8 AM Nifty morning alerts will arrive here.',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    tag: 'test-local',
    data: { url: '/pins', event: 'test' },
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

async function syncSubscriptionToServer(subscription) {
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
  return data;
}

async function clearStaleSubscription(registration, publicKey) {
  const storedKey = localStorage.getItem(VAPID_STORAGE_KEY);
  const existing = await registration.pushManager.getSubscription();
  if (!existing) return null;
  if (storedKey && storedKey !== publicKey) {
    await existing.unsubscribe();
    return null;
  }
  return existing;
}

export async function subscribeToPush() {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Login required to enable push notifications');
  }

  const registration = await registerServiceWorker();
  await navigator.serviceWorker.ready;

  const publicKey = await fetchVapidPublicKey();
  let subscription = await clearStaleSubscription(registration, publicKey);

  if (!subscription) {
    try {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
    } catch (err) {
      const stale = await registration.pushManager.getSubscription();
      if (stale) await stale.unsubscribe();
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
    }
  }

  await syncSubscriptionToServer(subscription);
  localStorage.setItem('pushSubscribed', '1');
  localStorage.setItem(VAPID_STORAGE_KEY, publicKey);
  return subscription;
}

/** Re-sync browser subscription to server when app reopens (PWA cold start). */
export async function ensurePushSubscription() {
  if (!isPushSupported()) return { ok: false, reason: 'unsupported' };
  if (!localStorage.getItem('token')) return { ok: false, reason: 'not_logged_in' };
  if (Notification.permission !== 'granted') return { ok: false, reason: 'permission' };

  try {
    await subscribeToPush();
    return { ok: true, synced: true };
  } catch (err) {
    console.warn('[push] ensure failed:', err);
    return { ok: false, reason: err.message || String(err) };
  }
}

export async function fetchPushStatus() {
  const res = await fetch(`${API_URL}/api/push/status`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Could not load push status');
  }
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
  localStorage.removeItem(VAPID_STORAGE_KEY);
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

export async function getPushSubscriptionState() {
  let browser = false;
  try {
    browser = await isPushSubscribed();
  } catch {
    browser = false;
  }

  let server = false;
  let devices = 0;
  if (localStorage.getItem('token')) {
    try {
      const status = await fetchPushStatus();
      server = Boolean(status.subscribed);
      devices = status.devices || 0;
    } catch {
      server = false;
    }
  }

  return {
    browser,
    server,
    devices,
    active: browser && server,
    needsSync: browser && !server,
  };
}
