from __future__ import annotations

import os
import subprocess
import time

import win32api
import win32con
import win32gui

from .config import CONFIG
from .tradingview_urls import tradingview_chart_url

_CHROME_PATHS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
)

# Profile, TradingView interval param, grid index (0=top-left .. 3=bottom-right)
_QUAD_CHARTS: tuple[tuple[str, str, int], ...] = (
    (CONFIG.tradingview_chrome_profile_1, "15", 0),   # 15m
    (CONFIG.tradingview_chrome_profile_1, "60", 1),  # 1h
    (CONFIG.tradingview_chrome_profile_2, "W", 2),   # 1W
    (CONFIG.tradingview_chrome_profile_2, "D", 3),   # 1D
)

_OPEN_DELAY_SEC = 3.0


def _chrome_exe() -> str:
    for path in _CHROME_PATHS:
        if os.path.isfile(path):
            return path
    raise RuntimeError(
        "Google Chrome not found. Install Chrome or set TRADINGVIEW_CHROME_EXE."
    )


def _screen_quadrants() -> list[tuple[int, int, int, int]]:
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    half_w, half_h = screen_w // 2, screen_h // 2
    return [
        (0, 0, half_w, half_h),
        (half_w, 0, half_w, half_h),
        (0, half_h, half_w, half_h),
        (half_w, half_h, half_w, half_h),
    ]


def _symbol_chrome_windows(symbol: str) -> set[int]:
    needle = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
    found: set[int] = set()

    def callback(hwnd: int, _: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if needle in title.upper() and "chrome" in title.lower():
            found.add(hwnd)
        return True

    win32gui.EnumWindows(callback, None)
    return found


def _launch_chart_window(
    profile: str,
    symbol: str,
    market_type: str,
    interval: str,
    position: tuple[int, int, int, int],
) -> int:
    layout_id = CONFIG.tradingview_chart_layout_id or None
    url = tradingview_chart_url(
        symbol,
        market_type,
        interval=interval,
        layout_id=layout_id,
    )
    x, y, width, height = position
    before = _symbol_chrome_windows(symbol)
    chrome = os.getenv("TRADINGVIEW_CHROME_EXE") or _chrome_exe()
    try:
        subprocess.Popen(
            [
                chrome,
                f"--user-data-dir={CONFIG.tradingview_chrome_user_data}",
                f"--profile-directory={profile}",
                "--new-window",
                f"--window-position={x},{y}",
                f"--window-size={width},{height}",
                url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except OSError as exc:
        raise RuntimeError(
            f"Could not launch Chrome with {profile}: {exc}"
        ) from exc

    deadline = time.time() + 12
    while time.time() < deadline:
        time.sleep(0.5)
        after = _symbol_chrome_windows(symbol)
        new_windows = after - before
        if new_windows:
            hwnd = max(new_windows)
            _arrange_windows([hwnd], [position])
            return hwnd
    raise RuntimeError(
        f"Chrome window for {symbol} ({interval}) did not appear. "
        f"Check that {profile} exists and TradingView can load."
    )


def _arrange_windows(
    hwnds: list[int],
    positions: list[tuple[int, int, int, int]],
) -> None:
    for hwnd, (x, y, width, height) in zip(hwnds, positions):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            x,
            y,
            width,
            height,
            win32con.SWP_SHOWWINDOW,
        )


def open_tradingview_quad(symbol: str, market_type: str) -> None:
    """Open 4 TradingView charts via Chrome profiles (subprocess, not Selenium)."""
    if not symbol or not symbol.strip():
        raise RuntimeError("No symbol to open on TradingView.")

    positions = _screen_quadrants()

    for profile, interval, grid_idx in _QUAD_CHARTS:
        _launch_chart_window(
            profile, symbol, market_type, interval, positions[grid_idx]
        )
        time.sleep(_OPEN_DELAY_SEC)
