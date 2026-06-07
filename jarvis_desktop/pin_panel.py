from __future__ import annotations

import threading
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import tkinter as tk

from .pin_alert_sound import play_price_alert
from .pin_market_hours import pin_session_status, should_poll_pin
from .pin_store import PinnedEntry, load_pins, save_pins
from .quote_service import fetch_market_quote, normalize_market_type
from .tradingview_urls import tradingview_chart_url

_BG = "#02030A"
_ACCENT = "#56C9FF"
_MUTED = "#8CD9FF"
_UP = "#84FFC9"
_DOWN = "#FF6B8A"
_COLLAPSED_W = 28
_EXPANDED_W = 300
_COLLAPSED_H = 120
_EXPANDED_H = 320
_SLOT_GAP = 6
_REFRESH_MS = 5_000
_IDLE_POLL_MS = 60_000
_COLLAPSE_DELAY_MS = 400
_MAX_PINS = 12


@dataclass
class _PinState:
    symbol: str
    market_type: str
    display_name: str
    alert_above: float | None = None
    alert_below: float | None = None


class _SinglePinWidget:
    """One always-on-top tab + expandable panel for a single symbol."""

    def __init__(
        self,
        parent: tk.Misc,
        state: _PinState,
        fetch_quote: Callable[[str, str], dict[str, Any]],
        on_unpin: Callable[[str], None],
        on_layout: Callable[[], None],
        on_alerts_changed: Callable[[str], None],
        on_stop_alert: Callable[[str], None] | None = None,
    ) -> None:
        self._parent = parent
        self._state = state
        self._fetch_quote = fetch_quote
        self._on_unpin = on_unpin
        self._on_layout = on_layout
        self._on_alerts_changed = on_alerts_changed
        self._on_stop_alert = on_stop_alert
        self._win: tk.Toplevel | None = None
        self._expanded = False
        self._refresh_after: str | None = None
        self._collapse_after: str | None = None
        self._last_quote: dict[str, Any] | None = None
        self._y_offset = 0
        self._prev_ltp: float | None = None
        self._above_armed = True
        self._below_armed = True
        self._had_first_quote = False
        self._alert_ringing = False

        self._tab_label: tk.Label | None = None
        self._detail_frame: tk.Frame | None = None
        self._price_label: tk.Label | None = None
        self._open_label: tk.Label | None = None
        self._prev_label: tk.Label | None = None
        self._change_label: tk.Label | None = None
        self._title_label: tk.Label | None = None
        self._alert_status_label: tk.Label | None = None
        self._session_status_label: tk.Label | None = None
        self._alert_above_var: tk.StringVar | None = None
        self._alert_below_var: tk.StringVar | None = None
        self._stop_alert_btn: tk.Button | None = None

        self._build()

    @property
    def symbol(self) -> str:
        return self._state.symbol

    def get_alerts(self) -> tuple[float | None, float | None]:
        return self._state.alert_above, self._state.alert_below

    def destroy(self) -> None:
        self._cancel_timers()
        if self._win is not None:
            self._win.destroy()
            self._win = None

    def set_y_offset(self, y_offset: int) -> None:
        self._y_offset = y_offset
        self._apply_geometry()

    def pin_refresh(self) -> dict[str, Any] | None:
        self._schedule_refresh(0)
        quote_holder: list[dict[str, Any] | None] = [None]
        done = threading.Event()

        def worker() -> None:
            try:
                quote_holder[0] = self._fetch_quote(self._state.symbol, self._state.market_type)
            except Exception:
                quote_holder[0] = None
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        done.wait(timeout=25)
        if quote_holder[0]:
            self._apply_quote(quote_holder[0])
        return quote_holder[0]

    def _build(self) -> None:
        sym = self._state.symbol
        self._win = tk.Toplevel(self._parent)
        self._win.overrideredirect(True)
        self._win.configure(bg=_BG)
        self._win.wm_attributes("-topmost", True)
        self._win.protocol("WM_DELETE_WINDOW", lambda: self._on_unpin(sym))

        outer = tk.Frame(self._win, bg=_BG, highlightthickness=1, highlightbackground="#1a3a55")
        outer.pack(fill="both", expand=True)
        outer.bind("<Enter>", self._on_enter)
        outer.bind("<Leave>", self._on_leave)

        self._tab_label = tk.Label(
            outer,
            text="",
            bg="#0a1628",
            fg=_ACCENT,
            font=("Segoe UI", 9, "bold"),
            width=2,
            padx=4,
            pady=8,
            cursor="hand2",
        )
        self._tab_label.pack(side="left", fill="y")
        self._tab_label.bind("<Enter>", self._on_enter)
        self._tab_label.bind("<Leave>", self._on_leave)
        self._update_tab_text()

        self._detail_frame = tk.Frame(outer, bg=_BG, padx=12, pady=10)
        self._detail_frame.bind("<Enter>", self._on_enter)
        self._detail_frame.bind("<Leave>", self._on_leave)

        self._title_label = tk.Label(
            self._detail_frame,
            text=sym,
            bg=_BG,
            fg=_ACCENT,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self._title_label.pack(fill="x")

        self._price_label = tk.Label(
            self._detail_frame,
            text="",
            bg=_BG,
            fg="#FFFFFF",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        )
        self._price_label.pack(fill="x", pady=(6, 4))

        self._open_label = tk.Label(
            self._detail_frame,
            text="",
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self._prev_label = tk.Label(
            self._detail_frame,
            text="",
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self._change_label = tk.Label(
            self._detail_frame,
            text="",
            bg=_BG,
            fg=_UP,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )

        alert_frame = tk.Frame(self._detail_frame, bg=_BG)
        alert_frame.pack(fill="x", pady=(6, 4))

        tk.Label(
            alert_frame,
            text="Price alerts",
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x")

        row = tk.Frame(alert_frame, bg=_BG)
        row.pack(fill="x", pady=(4, 2))

        self._alert_above_var = tk.StringVar(
            value=self._fmt_alert_input(self._state.alert_above)
        )
        self._alert_below_var = tk.StringVar(
            value=self._fmt_alert_input(self._state.alert_below)
        )

        tk.Label(row, text="Above", bg=_BG, fg=_MUTED, font=("Segoe UI", 9)).pack(side="left")
        above_entry = tk.Entry(
            row,
            textvariable=self._alert_above_var,
            width=10,
            bg="#0d2840",
            fg="#FFFFFF",
            insertbackground=_ACCENT,
            relief="flat",
            font=("Segoe UI", 9),
        )
        above_entry.pack(side="left", padx=(4, 10))
        above_entry.bind("<Return>", lambda _e: self._save_alerts())
        above_entry.bind("<FocusOut>", lambda _e: self._save_alerts())

        tk.Label(row, text="Below", bg=_BG, fg=_MUTED, font=("Segoe UI", 9)).pack(side="left")
        below_entry = tk.Entry(
            row,
            textvariable=self._alert_below_var,
            width=10,
            bg="#0d2840",
            fg="#FFFFFF",
            insertbackground=_ACCENT,
            relief="flat",
            font=("Segoe UI", 9),
        )
        below_entry.pack(side="left", padx=(4, 0))
        below_entry.bind("<Return>", lambda _e: self._save_alerts())
        below_entry.bind("<FocusOut>", lambda _e: self._save_alerts())

        tk.Button(
            alert_frame,
            text="Save alerts",
            command=self._save_alerts,
            bg="#0d2840",
            fg=_ACCENT,
            activebackground="#143550",
            activeforeground=_ACCENT,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=2,
            cursor="hand2",
        ).pack(anchor="w", pady=(2, 0))

        self._alert_status_label = tk.Label(
            alert_frame,
            text=self._alert_status_text(),
            bg=_BG,
            fg="#FFB347",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self._alert_status_label.pack(fill="x", pady=(2, 0))

        self._stop_alert_btn = tk.Button(
            alert_frame,
            text="Stop alert",
            command=self._stop_alert,
            bg="#8b2030",
            fg="#FFFFFF",
            activebackground="#a02838",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            cursor="hand2",
        )

        self._session_status_label = tk.Label(
            self._detail_frame,
            text="",
            bg=_BG,
            fg="#6a8aaa",
            font=("Segoe UI", 8),
            anchor="w",
            wraplength=260,
            justify="left",
        )

        self._btn_row = tk.Frame(self._detail_frame, bg=_BG)
        self._btn_row.pack(fill="x", pady=(6, 0))

        tk.Button(
            self._btn_row,
            text="TradingView",
            command=self._open_tradingview,
            bg="#0d2840",
            fg=_ACCENT,
            activebackground="#143550",
            activeforeground=_ACCENT,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            self._btn_row,
            text="Unpin",
            command=lambda: self._on_unpin(sym),
            bg="#2a1020",
            fg=_DOWN,
            activebackground="#3a1830",
            activeforeground=_DOWN,
            relief="flat",
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left")

        self._set_collapsed()
        self._schedule_refresh(0)

    @staticmethod
    def _fmt_alert_input(value: float | None) -> str:
        if value is None:
            return ""
        if value == int(value):
            return str(int(value))
        return f"{value:g}"

    def _parse_alert_field(self, raw: str) -> float | None:
        text = raw.strip().replace(",", "")
        if not text:
            return None
        try:
            value = float(text)
        except ValueError:
            return None
        return value if value > 0 else None

    def _current_ltp(self) -> float | None:
        if isinstance(self._prev_ltp, (int, float)):
            return float(self._prev_ltp)
        if self._last_quote and isinstance(self._last_quote.get("ltp"), (int, float)):
            return float(self._last_quote["ltp"])
        return None

    def _save_alerts(self) -> None:
        if self._alert_above_var is None or self._alert_below_var is None:
            return
        above = self._parse_alert_field(self._alert_above_var.get())
        below = self._parse_alert_field(self._alert_below_var.get())
        changed = above != self._state.alert_above or below != self._state.alert_below
        self._state.alert_above = above
        self._state.alert_below = below
        self._above_armed = True
        self._below_armed = True

        current = self._current_ltp()
        fired_now = False
        if current is not None:
            if above is not None and current >= above:
                fired_now = True
                self._above_armed = False
            if below is not None and current <= below:
                fired_now = True
                self._below_armed = False

        if changed:
            self._had_first_quote = False
            self._prev_ltp = None
            self._alert_ringing = False
            self._update_ringing_ui()

        if self._alert_status_label:
            self._alert_status_label.config(text=self._alert_status_text())
        if fired_now:
            self._start_ringing()
        if changed:
            self._on_alerts_changed(self._state.symbol)

    def _is_breached(self, ltp: float) -> bool:
        above = self._state.alert_above
        below = self._state.alert_below
        if above is not None and ltp >= above:
            return True
        if below is not None and ltp <= below:
            return True
        return False

    def _start_ringing(self) -> None:
        self._alert_ringing = True
        play_price_alert()
        self._update_ringing_ui()

    def _stop_alert(self) -> None:
        self._alert_ringing = False
        self._update_ringing_ui()
        if self._on_stop_alert:
            sym = self._state.symbol

            def _worker() -> None:
                try:
                    self._on_stop_alert(sym)
                except Exception:
                    pass

            threading.Thread(target=_worker, daemon=True).start()

    def _update_ringing_ui(self) -> None:
        if not self._stop_alert_btn:
            return
        if self._alert_ringing:
            self._stop_alert_btn.pack(fill="x", pady=(6, 0))
            if self._alert_status_label:
                self._alert_status_label.config(
                    text="Alert ringing — repeats until you stop",
                    fg="#FF6B6B",
                )
        else:
            self._stop_alert_btn.pack_forget()
            if self._alert_status_label:
                self._alert_status_label.config(
                    text=self._alert_status_text(),
                    fg="#FFB347",
                )

    def _alert_status_text(self) -> str:
        parts: list[str] = []
        if self._state.alert_above is not None:
            parts.append(f"ring above {self._state.alert_above:,.2f}")
        if self._state.alert_below is not None:
            parts.append(f"ring below {self._state.alert_below:,.2f}")
        if not parts:
            return "Set a price above/below to get a sound alert."
        return "Will " + " and ".join(parts) + "."

    def _update_tab_text(self, ltp: float | None = None) -> None:
        if not self._tab_label:
            return
        name = self._state.display_name[:6]
        lines = list(name)
        if ltp is not None:
            if ltp >= 1000:
                price_line = f"{ltp:,.0f}"
            elif ltp >= 100:
                price_line = f"{ltp:.1f}"
            else:
                price_line = f"{ltp:.2f}"
            if len(price_line) > 6:
                price_line = price_line[:6]
            lines.append(price_line)
        self._tab_label.config(text="\n".join(lines))

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        if self._collapse_after and self._win:
            self._win.after_cancel(self._collapse_after)
            self._collapse_after = None
        self._set_expanded()
        self._schedule_refresh(0)
        self._on_layout()

    def _on_leave(self, _event: tk.Event | None = None) -> None:
        if self._win is None:
            return
        if self._collapse_after:
            self._win.after_cancel(self._collapse_after)

        def collapse() -> None:
            self._collapse_after = None
            self._set_collapsed()
            self._on_layout()

        self._collapse_after = self._win.after(_COLLAPSE_DELAY_MS, collapse)

    def _set_collapsed(self) -> None:
        if self._win is None:
            return
        self._expanded = False
        if self._detail_frame:
            self._detail_frame.pack_forget()
        self._apply_geometry(collapsed=True)

    def _set_expanded(self) -> None:
        if self._win is None:
            return
        self._expanded = True
        if self._detail_frame:
            self._detail_frame.pack(side="left", fill="both", expand=True)
        self._apply_geometry(collapsed=False)
        if self._last_quote:
            self._render_quote(self._last_quote)
        else:
            self._update_session_status()

    def _apply_geometry(self, *, collapsed: bool | None = None) -> None:
        if self._win is None:
            return
        is_collapsed = collapsed if collapsed is not None else not self._expanded
        width = _COLLAPSED_W if is_collapsed else _EXPANDED_W
        height = _COLLAPSED_H if is_collapsed else _EXPANDED_H
        self._win.update_idletasks()
        sw = self._win.winfo_screenwidth()
        x = max(0, sw - width)
        y = max(0, self._y_offset)
        self._win.geometry(f"{width}x{height}+{x}+{y}")

    def _cancel_timers(self) -> None:
        if self._win:
            if self._refresh_after:
                self._win.after_cancel(self._refresh_after)
            if self._collapse_after:
                self._win.after_cancel(self._collapse_after)
        self._refresh_after = None
        self._collapse_after = None

    def _schedule_refresh(self, delay_ms: int) -> None:
        if self._win is None:
            return
        if self._refresh_after:
            self._win.after_cancel(self._refresh_after)

        def tick() -> None:
            self._refresh_after = None
            active = should_poll_pin(self._state.symbol, self._state.market_type)
            if active:
                self._refresh_async()
            else:
                self._update_session_status()
            next_ms = _REFRESH_MS if active else _IDLE_POLL_MS
            if self._win is not None:
                self._refresh_after = self._win.after(next_ms, tick)

        self._refresh_after = self._win.after(delay_ms, tick)

    def _update_session_status(self) -> None:
        if not self._expanded or not self._session_status_label:
            return
        msg = pin_session_status(self._state.symbol, self._state.market_type)
        if msg:
            self._session_status_label.config(text=msg)
            self._session_status_label.pack(fill="x", pady=(4, 0), before=self._btn_row)
        else:
            self._session_status_label.pack_forget()

    def _refresh_async(self) -> None:
        if not should_poll_pin(self._state.symbol, self._state.market_type):
            self._update_session_status()
            return
        sym = self._state.symbol
        mtype = self._state.market_type

        def worker() -> None:
            try:
                quote = self._fetch_quote(sym, mtype)
            except Exception:
                return
            if self._parent.winfo_exists() and self._win is not None:
                self._parent.after(0, lambda q=quote: self._apply_quote(q))

        threading.Thread(target=worker, daemon=True).start()

    def _check_price_alerts(self, ltp: float | None) -> None:
        if ltp is None or not isinstance(ltp, (int, float)):
            return
        if not should_poll_pin(self._state.symbol, self._state.market_type):
            return

        current = float(ltp)
        if self._alert_ringing and not self._is_breached(current):
            self._alert_ringing = False
            self._update_ringing_ui()

        above = self._state.alert_above
        below = self._state.alert_below
        prev = self._prev_ltp

        if not self._had_first_quote:
            self._had_first_quote = True
            self._prev_ltp = current
            fired = False
            if above is not None:
                if current >= above:
                    fired = True
                    self._above_armed = False
                else:
                    self._above_armed = True
            if below is not None:
                if current <= below:
                    fired = True
                    self._below_armed = False
                else:
                    self._below_armed = True
            if fired:
                self._start_ringing()
            elif self._alert_ringing:
                play_price_alert()
            return

        fired = False

        if above is not None and self._above_armed and prev is not None:
            if prev < above <= current:
                fired = True
                self._above_armed = False
        if current < (above or float("inf")):
            self._above_armed = True

        if below is not None and self._below_armed and prev is not None:
            if prev > below >= current:
                fired = True
                self._below_armed = False
        if current > (below or 0):
            self._below_armed = True

        self._prev_ltp = current
        if fired:
            self._start_ringing()
        elif self._alert_ringing:
            play_price_alert()

    def _apply_quote(self, quote: dict[str, Any]) -> None:
        self._last_quote = quote
        ltp = quote.get("ltp")
        if isinstance(ltp, (int, float)):
            self._check_price_alerts(float(ltp))
        if self._expanded:
            self._render_quote(quote)
        else:
            self._update_tab_text(float(ltp) if isinstance(ltp, (int, float)) else None)

    def _render_quote(self, quote: dict[str, Any]) -> None:
        if not self._win:
            return
        sym = quote.get("symbol", self._state.symbol)
        if self._title_label:
            self._title_label.config(text=sym)

        ltp = quote.get("ltp")
        if self._price_label:
            if ltp is not None:
                prefix = "₹" if quote.get("market_type") == "indian_stocks" else ""
                self._price_label.config(
                    text=f"{prefix}{ltp:,.2f}" if isinstance(ltp, (int, float)) else str(ltp)
                )
            else:
                self._price_label.config(text="—")

        open_p = quote.get("open")
        if self._open_label:
            if open_p is not None:
                self._open_label.config(text=f"Today's open: {open_p:,.2f}")
                self._open_label.pack(fill="x")
            else:
                self._open_label.pack_forget()

        prev = quote.get("previous_close")
        if self._prev_label:
            if prev is not None:
                self._prev_label.config(text=f"Prev close: {prev:,.2f}")
                self._prev_label.pack(fill="x")
            else:
                self._prev_label.pack_forget()

        pct = quote.get("change_pct")
        inr = quote.get("change_inr")
        if self._change_label and pct is not None:
            sign = "+" if pct >= 0 else ""
            extra = f" ({sign}{inr:,.2f})" if inr is not None else ""
            self._change_label.config(
                text=f"{sign}{pct:.2f}%{extra}",
                fg=_UP if pct >= 0 else _DOWN,
            )
            self._change_label.pack(fill="x", pady=(4, 4))

        if self._alert_status_label:
            self._alert_status_label.config(text=self._alert_status_text())
        self._update_session_status()

    def _open_tradingview(self) -> None:
        url = tradingview_chart_url(self._state.symbol, self._state.market_type)
        webbrowser.open(url)


class PinSidePanel:
    """Manages multiple pinned scrips stacked on the right edge of the screen."""

    def __init__(
        self,
        parent: tk.Misc,
        fetch_quote: Callable[[str, str], dict[str, Any]],
        sync_pins: Callable[[list[dict[str, Any]]], None] | None = None,
        stop_alert: Callable[[str], None] | None = None,
    ) -> None:
        self._parent = parent
        self._fetch_quote = fetch_quote
        self._sync_pins = sync_pins
        self._stop_alert = stop_alert
        self._widgets: dict[str, _SinglePinWidget] = {}
        self._order: list[str] = []

    def is_pinned(self, symbol: str | None = None) -> bool:
        if symbol is None:
            return bool(self._widgets)
        return symbol.upper().strip() in self._widgets

    def pinned_symbols(self) -> list[str]:
        return list(self._order)

    def pin(
        self,
        symbol: str,
        market_type: str,
        display_name: str | None = None,
        *,
        wait_for_quote: bool = True,
        alert_above: float | None = None,
        alert_below: float | None = None,
    ) -> dict[str, Any] | None:
        sym = symbol.upper().strip()
        mtype = normalize_market_type(market_type)

        if sym in self._widgets:
            if wait_for_quote:
                quote = self._widgets[sym].pin_refresh()
            else:
                self._widgets[sym]._schedule_refresh(0)
                quote = None
            self._persist()
            return quote

        if len(self._order) >= _MAX_PINS:
            return None

        state = _PinState(
            symbol=sym,
            market_type=mtype,
            display_name=display_name or sym,
            alert_above=alert_above,
            alert_below=alert_below,
        )
        widget = _SinglePinWidget(
            self._parent,
            state,
            self._fetch_quote,
            on_unpin=self.unpin,
            on_layout=self._layout_all,
            on_alerts_changed=lambda _s: self._persist(),
            on_stop_alert=self._stop_alert,
        )
        self._widgets[sym] = widget
        self._order.append(sym)
        self._layout_all()
        if wait_for_quote:
            quote = widget.pin_refresh()
        else:
            widget._schedule_refresh(0)
            quote = None
        self._persist()
        return quote

    def unpin(self, symbol: str | None = None) -> int:
        """Remove one symbol, or all if symbol is None. Returns count removed."""
        if symbol is None:
            keys = list(self._order)
            for sym in keys:
                self._remove_one(sym)
            self._persist()
            return len(keys)

        sym = symbol.upper().strip()
        if sym not in self._widgets:
            return 0
        self._remove_one(sym)
        self._persist()
        return 1

    def restore_persisted(self) -> int:
        """Load pins from disk and show widgets. Returns count restored."""
        entries = load_pins()
        restored = 0
        for entry in entries:
            if len(self._order) >= _MAX_PINS:
                break
            if entry.key() in self._widgets:
                continue
            self.pin(
                entry.symbol,
                entry.market_type,
                wait_for_quote=False,
                alert_above=entry.alert_above,
                alert_below=entry.alert_below,
            )
            restored += 1
        return restored

    def _remove_one(self, sym: str) -> None:
        widget = self._widgets.pop(sym, None)
        if sym in self._order:
            self._order.remove(sym)
        if widget:
            widget.destroy()
        self._layout_all()

    def _persist(self) -> None:
        entries = [
            PinnedEntry(
                symbol=sym,
                market_type=self._widgets[sym]._state.market_type,
                alert_above=self._widgets[sym]._state.alert_above,
                alert_below=self._widgets[sym]._state.alert_below,
            )
            for sym in self._order
            if sym in self._widgets
        ]
        save_pins(entries)
        if self._sync_pins:
            payload = [
                {
                    "symbol": e.symbol,
                    "market_type": e.market_type,
                    "alert_above": e.alert_above,
                    "alert_below": e.alert_below,
                }
                for e in entries
            ]

            def _worker() -> None:
                try:
                    self._sync_pins(payload)
                except Exception:
                    pass

            threading.Thread(target=_worker, daemon=True).start()

    def _layout_all(self) -> None:
        n = len(self._order)
        if n == 0:
            return
        sample = next(iter(self._widgets.values()))._win
        if sample is None:
            return
        sample.update_idletasks()
        sh = sample.winfo_screenheight()
        slot_h = _COLLAPSED_H + _SLOT_GAP
        total_h = n * slot_h - _SLOT_GAP
        y0 = max(0, (sh - total_h) // 2)
        for i, sym in enumerate(self._order):
            w = self._widgets.get(sym)
            if w:
                w.set_y_offset(y0 + i * slot_h)


def create_pin_panel(parent: tk.Misc, backend: Any) -> PinSidePanel:
    from .backend_client import BackendClient

    client: BackendClient = backend

    def fetch(symbol: str, market_type: str) -> dict[str, Any]:
        return fetch_market_quote(client, symbol, market_type)

    def sync(entries: list[dict[str, Any]]) -> None:
        client.sync_pins(entries)

    def stop_alert(symbol: str) -> None:
        client.stop_pin_alert(symbol)

    return PinSidePanel(parent, fetch_quote=fetch, sync_pins=sync, stop_alert=stop_alert)
