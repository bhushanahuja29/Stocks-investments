from __future__ import annotations

import threading
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import tkinter as tk

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
_EXPANDED_H = 240
_SLOT_GAP = 6
_REFRESH_MS = 30_000
_COLLAPSE_DELAY_MS = 400
_MAX_PINS = 12


@dataclass
class _PinState:
    symbol: str
    market_type: str
    display_name: str


class _SinglePinWidget:
    """One always-on-top tab + expandable panel for a single symbol."""

    def __init__(
        self,
        parent: tk.Misc,
        state: _PinState,
        fetch_quote: Callable[[str, str], dict[str, Any]],
        on_unpin: Callable[[str], None],
        on_layout: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._state = state
        self._fetch_quote = fetch_quote
        self._on_unpin = on_unpin
        self._on_layout = on_layout
        self._win: tk.Toplevel | None = None
        self._expanded = False
        self._refresh_after: str | None = None
        self._collapse_after: str | None = None
        self._last_quote: dict[str, Any] | None = None
        self._y_offset = 0

        self._tab_label: tk.Label | None = None
        self._detail_frame: tk.Frame | None = None
        self._price_label: tk.Label | None = None
        self._open_label: tk.Label | None = None
        self._prev_label: tk.Label | None = None
        self._change_label: tk.Label | None = None
        self._title_label: tk.Label | None = None

        self._build()

    @property
    def symbol(self) -> str:
        return self._state.symbol

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

        btn_row = tk.Frame(self._detail_frame, bg=_BG)
        btn_row.pack(fill="x")

        tk.Button(
            btn_row,
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
            btn_row,
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

    def _update_tab_text(self) -> None:
        if self._tab_label:
            name = self._state.display_name[:8]
            self._tab_label.config(text="\n".join(name))

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
            self._refresh_async()
            if self._win is not None:
                self._refresh_after = self._win.after(_REFRESH_MS, tick)

        self._refresh_after = self._win.after(delay_ms, tick)

    def _refresh_async(self) -> None:
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

    def _apply_quote(self, quote: dict[str, Any]) -> None:
        self._last_quote = quote
        if self._expanded:
            self._render_quote(quote)

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
            self._change_label.pack(fill="x", pady=(4, 8))

    def _open_tradingview(self) -> None:
        url = tradingview_chart_url(self._state.symbol, self._state.market_type)
        webbrowser.open(url)


class PinSidePanel:
    """Manages multiple pinned scrips stacked on the right edge of the screen."""

    def __init__(
        self,
        parent: tk.Misc,
        fetch_quote: Callable[[str, str], dict[str, Any]],
    ) -> None:
        self._parent = parent
        self._fetch_quote = fetch_quote
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

        state = _PinState(symbol=sym, market_type=mtype, display_name=display_name or sym)
        widget = _SinglePinWidget(
            self._parent,
            state,
            self._fetch_quote,
            on_unpin=self.unpin,
            on_layout=self._layout_all,
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
            self.pin(entry.symbol, entry.market_type, wait_for_quote=False)
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
            PinnedEntry(symbol=sym, market_type=self._widgets[sym]._state.market_type)
            for sym in self._order
            if sym in self._widgets
        ]
        save_pins(entries)

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

    return PinSidePanel(parent, fetch_quote=fetch)
