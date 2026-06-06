import React, { useEffect, useState } from 'react';
import { isIos, isStandalonePwa } from '../utils/pushPlatform';
import './InstallPrompt.css';

const DISMISS_KEY = 'crypto_levels_install_dismissed';
const VISITS_KEY = 'crypto_levels_visits';

function shouldShowInstallPrompt() {
  if (localStorage.getItem(DISMISS_KEY) === '1') return false;
  if (isStandalonePwa()) return false;
  const visits = Number(localStorage.getItem(VISITS_KEY) || 0);
  return visits >= 1;
}

function IosInstallHint({ onDismiss }) {
  return (
    <div className="install-prompt install-prompt-fixed">
      <div className="install-prompt-inner">
        <strong>Install on iPhone</strong>
        <p>
          Tap <strong>Share</strong> in Safari, then <strong>Add to Home Screen</strong>.
          Open the app from your home screen for push alerts.
        </p>
        <div className="install-prompt-actions">
          <button type="button" className="install-btn ghost" onClick={onDismiss}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}

function InstallPrompt() {
  const [deferred, setDeferred] = useState(null);
  const [visible, setVisible] = useState(false);
  const [iosHint, setIosHint] = useState(false);

  useEffect(() => {
    const visits = Number(localStorage.getItem(VISITS_KEY) || 0);
    localStorage.setItem(VISITS_KEY, String(visits + 1));

    if (isStandalonePwa()) return undefined;

    if (isIos() && shouldShowInstallPrompt()) {
      setIosHint(true);
    }

    const onInstall = (e) => {
      e.preventDefault();
      setDeferred(e);
      if (shouldShowInstallPrompt()) {
        setVisible(true);
      }
    };
    const onInstalled = () => {
      setVisible(false);
      setIosHint(false);
      setDeferred(null);
    };

    window.addEventListener('beforeinstallprompt', onInstall);
    window.addEventListener('appinstalled', onInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', onInstall);
      window.removeEventListener('appinstalled', onInstalled);
    };
  }, []);

  const install = async () => {
    if (!deferred?.prompt) return;
    await deferred.prompt();
    await deferred.userChoice;
    setVisible(false);
    setDeferred(null);
  };

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, '1');
    setVisible(false);
    setIosHint(false);
  };

  if (iosHint && !visible) {
    return <IosInstallHint onDismiss={dismiss} />;
  }

  if (!visible) return null;

  return (
    <div className="install-prompt install-prompt-fixed">
      <div className="install-prompt-inner">
        <strong>Install Crypto Levels</strong>
        <p>Add to your home screen for pin price alerts even when the browser is closed.</p>
        <div className="install-prompt-actions">
          <button type="button" className="install-btn primary" onClick={install}>
            Install app
          </button>
          <button type="button" className="install-btn ghost" onClick={dismiss}>
            Not now
          </button>
        </div>
      </div>
    </div>
  );
}

export default InstallPrompt;
