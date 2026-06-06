/**
 * Service worker registration — must run on app boot for PWA installability.
 */

let registrationPromise = null;

export function waitForServiceWorkerRegistration() {
  if (!('serviceWorker' in navigator)) {
    return Promise.resolve(null);
  }
  if (!registrationPromise) {
    registrationPromise = navigator.serviceWorker
      .register(`${process.env.PUBLIC_URL || ''}/sw.js`, { scope: '/' })
      .then((registration) => {
        registration.update().catch(() => undefined);
        return registration;
      })
      .catch((err) => {
        console.warn('[PWA] Service worker registration failed:', err);
        return null;
      });
  }
  return registrationPromise;
}

export function registerServiceWorker() {
  void waitForServiceWorkerRegistration();
}

/** Store deferred install prompt for manual Install button. */
export function setDeferredInstallPrompt(event) {
  window.__deferredInstallPrompt = event;
}

export function getDeferredInstallPrompt() {
  return window.__deferredInstallPrompt || null;
}

export function clearDeferredInstallPrompt() {
  window.__deferredInstallPrompt = null;
}

export async function triggerInstallPrompt() {
  const deferred = getDeferredInstallPrompt();
  if (!deferred?.prompt) {
    return { ok: false, reason: 'no_prompt' };
  }
  await deferred.prompt();
  const choice = await deferred.userChoice;
  clearDeferredInstallPrompt();
  return { ok: choice.outcome === 'accepted', outcome: choice.outcome };
}
