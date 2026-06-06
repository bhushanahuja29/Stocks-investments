import React, { useEffect, useState } from 'react';
import './InstallPrompt.css';

const DISMISS_KEY = 'crypto_levels_install_dismissed';

function InstallPrompt() {
  const [deferred, setDeferred] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (localStorage.getItem(DISMISS_KEY) === '1') return undefined;

    const onInstall = (e) => {
      e.preventDefault();
      setDeferred(e);
      setVisible(true);
    };
    const onInstalled = () => {
      setVisible(false);
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
    deferred.prompt();
    await deferred.userChoice;
    setVisible(false);
    setDeferred(null);
  };

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, '1');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="install-prompt">
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
