import React, { useEffect, useState } from 'react';
import {
  clearDeferredInstallPrompt,
  setDeferredInstallPrompt,
  triggerInstallPrompt,
} from '../utils/pwa';
import { isIos, isStandalonePwa } from '../utils/pushPlatform';
import './InstallPrompt.css';

const DISMISS_KEY = 'crypto_levels_install_dismissed';

function IosInstallHint({ onDismiss }) {
  return (
    <div className="install-prompt install-prompt-fixed">
      <div className="install-prompt-inner">
        <strong>Install on iPhone</strong>
        <p>
          In Safari tap <strong>Share</strong> (bottom bar), then <strong>Add to Home Screen</strong>.
          Open Delta Levels from your home screen for push alerts.
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
  const [visible, setVisible] = useState(false);
  const [iosHint, setIosHint] = useState(false);
  const [canInstall, setCanInstall] = useState(false);

  useEffect(() => {
    if (isStandalonePwa()) return undefined;

    if (isIos()) {
      const dismissed = localStorage.getItem(DISMISS_KEY) === '1';
      if (!dismissed) setIosHint(true);
    }

    const onInstall = (e) => {
      e.preventDefault();
      setDeferredInstallPrompt(e);
      setCanInstall(true);
      if (localStorage.getItem(DISMISS_KEY) !== '1') {
        setVisible(true);
      }
    };

    const onInstalled = () => {
      clearDeferredInstallPrompt();
      setVisible(false);
      setIosHint(false);
      setCanInstall(false);
    };

    window.addEventListener('beforeinstallprompt', onInstall);
    window.addEventListener('appinstalled', onInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', onInstall);
      window.removeEventListener('appinstalled', onInstalled);
    };
  }, []);

  const install = async () => {
    const result = await triggerInstallPrompt();
    if (result.ok) {
      setVisible(false);
      setCanInstall(false);
    }
  };

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, '1');
    setVisible(false);
    setIosHint(false);
  };

  if (iosHint && !visible && !canInstall) {
    return <IosInstallHint onDismiss={dismiss} />;
  }

  if (!visible || !canInstall) return null;

  return (
    <div className="install-prompt install-prompt-fixed">
      <div className="install-prompt-inner">
        <strong>Install Delta Levels</strong>
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

export async function promptInstallFromButton() {
  if (isStandalonePwa()) {
    return { ok: true, already: true };
  }
  if (isIos()) {
    return { ok: false, reason: 'ios_manual' };
  }
  const result = await triggerInstallPrompt();
  if (result.ok) return result;
  return { ok: false, reason: result.reason || 'no_prompt' };
}

export default InstallPrompt;
