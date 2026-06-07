/**
 * Play a short alert tone in the browser (Web Audio API).
 * Used when pin price levels are crossed or a push alert arrives.
 */

let audioCtx = null;

function getAudioContext() {
  if (typeof window === 'undefined') return null;
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return null;
  if (!audioCtx) audioCtx = new Ctx();
  return audioCtx;
}

function beep(ctx, frequency, durationMs, startMs, volume = 0.35) {
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = 'sine';
  osc.frequency.value = frequency;
  gain.gain.value = volume;
  osc.connect(gain);
  gain.connect(ctx.destination);
  const start = ctx.currentTime + startMs / 1000;
  const end = start + durationMs / 1000;
  gain.gain.setValueAtTime(volume, start);
  gain.gain.exponentialRampToValueAtTime(0.001, end);
  osc.start(start);
  osc.stop(end + 0.05);
}

export function unlockAlertSound() {
  try {
    const ctx = getAudioContext();
    if (ctx?.state === 'suspended') {
      ctx.resume().catch(() => undefined);
    }
  } catch {
    /* ignore */
  }
}

export function playAlertSound() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => undefined);
    }
    beep(ctx, 1200, 180, 0);
    beep(ctx, 900, 220, 220);
    beep(ctx, 1100, 160, 480);
  } catch {
    /* ignore — autoplay may be blocked until user gesture */
  }
}

export function registerAlertSoundListener() {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
    return () => undefined;
  }
  const handler = (event) => {
    if (event.data?.type === 'play_alert_sound') {
      playAlertSound();
    }
  };
  navigator.serviceWorker.addEventListener('message', handler);
  return () => navigator.serviceWorker.removeEventListener('message', handler);
}
