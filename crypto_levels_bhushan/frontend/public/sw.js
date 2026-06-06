/* Crypto Levels — Web Push service worker v2 */
const SW_VERSION = 'v2';

const ROUTE_BY_EVENT = {
  morning_nifty: '/monitor',
  pin_alert: '/pins',
};

self.addEventListener('push', (event) => {
  let data = {
    title: 'Crypto Levels',
    body: 'Price alert',
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
  const tag = data.tag || (eventType === 'pin_alert' ? 'pin-alert' : 'morning-nifty');

  const options = {
    body: data.body,
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    data: { url, event: eventType },
    tag,
    renotify: true,
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
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
