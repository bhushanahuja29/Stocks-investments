"""Play a short sound when a pinned scrip hits its alert price."""

from __future__ import annotations

import sys
import threading

_play_lock = threading.Lock()


def play_price_alert() -> None:
    """Non-blocking alert tone (Windows winsound, else terminal bell)."""
    if not _play_lock.acquire(blocking=False):
        return

    def _run() -> None:
        try:
            if sys.platform == "win32":
                import winsound

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                winsound.Beep(1200, 180)
                winsound.Beep(900, 220)
            else:
                print("\a", end="", flush=True)
        except Exception:
            try:
                print("\a", end="", flush=True)
            except Exception:
                pass
        finally:
            _play_lock.release()

    threading.Thread(target=_run, daemon=True).start()
