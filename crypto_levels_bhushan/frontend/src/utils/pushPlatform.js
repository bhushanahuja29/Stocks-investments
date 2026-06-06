/** iOS / PWA detection for Web Push (mirrors Gymtra push-platform). */

export function isStandalonePwa() {
  if (typeof window === 'undefined') return false;
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );
}

export function isIos() {
  if (typeof navigator === 'undefined') return false;
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

export function iosWebPushRequiresInstall() {
  return isIos() && !isStandalonePwa();
}

export function pushPlatformHint() {
  if (iosWebPushRequiresInstall()) {
    return 'On iPhone: Safari → Share → Add to Home Screen, open the app from the icon, then enable notifications.';
  }
  if (isIos() && isStandalonePwa()) {
    return 'iOS installed app — tap Enable to allow price alert notifications.';
  }
  return 'Install this site as an app (Chrome menu → Install) for reliable background alerts.';
}
