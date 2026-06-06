"""
Keep-alive service for Render deployment.
Self-pings GET /api/keepalive every 14 minutes to prevent free-tier spin-down.
"""

from __future__ import annotations

import os
import threading
import time

import requests

_keepalive_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _backend_url() -> str:
    port = os.getenv("PORT", "8000")
    return os.getenv("RENDER_EXTERNAL_URL", f"http://127.0.0.1:{port}").rstrip("/")


def _ping_interval() -> int:
    return int(os.getenv("KEEPALIVE_INTERVAL", "840"))


def ping_self() -> bool:
    url = f"{_backend_url()}/api/keepalive"
    try:
        response = requests.get(url, timeout=30)
        if response.ok:
            data = response.json()
            print(f"[KEEPALIVE] {data.get('message', 'OK')}")
            return True
        print(f"[KEEPALIVE] ping returned status {response.status_code}")
    except requests.Timeout:
        print("[KEEPALIVE] ping timed out")
    except Exception as exc:
        print(f"[KEEPALIVE] ping failed: {exc}")
    return False


def _keepalive_loop() -> None:
    interval = _ping_interval()
    print(f"[KEEPALIVE] Backend URL: {_backend_url()}")
    print(f"[KEEPALIVE] Ping interval: {interval}s ({interval / 60:.1f} min)")
    time.sleep(120)
    while not _stop_event.is_set():
        ping_self()
        if _stop_event.wait(interval):
            break
    print("[KEEPALIVE] Service stopped")


def start_keepalive() -> None:
    global _keepalive_thread
    if not os.getenv("RENDER"):
        return
    if _keepalive_thread and _keepalive_thread.is_alive():
        return
    _stop_event.clear()
    _keepalive_thread = threading.Thread(target=_keepalive_loop, daemon=True, name="render-keepalive")
    _keepalive_thread.start()
    print("[KEEPALIVE] Service started (Render detected)")


def stop_keepalive() -> None:
    _stop_event.set()
    global _keepalive_thread
    if _keepalive_thread:
        _keepalive_thread.join(timeout=2)
        _keepalive_thread = None
