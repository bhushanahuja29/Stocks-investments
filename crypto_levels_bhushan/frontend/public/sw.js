/* Crypto Levels — Web Push service worker v5 */
const SW_VERSION = 'v5';

const ROUTE_BY_EVENT = {
  morning_nifty: '/monitor',
  pin_alert: '/pins',
  tradingview_alert: '/alerts',
  test: '/pins',
};

const TITLE_BY_EVENT = {
  pin_alert: 'Pin alert',
  morning_nifty: 'Morning alert',
  tradingview_alert: 'TradingView alert',
  test: 'Test notification',
};

self.addEventListener('push', (event) => {
  let data = {
    title: 'Pin alert',
    body: 'Price crossed your alert level',
    url: '/pins',
    tag: 'crypto-levels',
    event: 'pin_alert',
  };
  try {
    if (event.data) {
      data = { ...data, ...event.data.json() };
    }
  } catch (e) {
    if (event.data) {
      data.body = event.data.text();
    }
  }

  const eventType = data.event || 'pin_alert';
  const url = data.url || ROUTE_BY_EVENT[eventType] || '/pins';
  const tag = data.tag || (eventType === 'pin_alert' ? 'pin-alert' : eventType);
  const title = data.title || TITLE_BY_EVENT[eventType] || 'Crypto Levels';

  const options = {
    body: data.body,
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    data: { url, event: eventType },
    tag,
    renotify: true,
    silent: false,
  };

  const notifyClients = self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
    clientList.forEach((client) => {
      client.postMessage({ type: 'play_alert_sound', event: eventType });
    });
  });

  event.waitUntil(
    Promise.all([self.registration.showNotification(title, options), notifyClients])
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = event.notification.data?.url || '/pins';
  const url = new URL(target, self.location.origin).href;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});
