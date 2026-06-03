from __future__ import annotations

import threading
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field
from queue import Empty, Queue
from tkinter import ttk


@dataclass
class JarvisUI:
    title: str = "Krypto Desktop Agent"
    on_command: Callable[[str], None] | None = field(default=None, repr=False)
    on_wake: Callable[[], None] | None = field(default=None, repr=False)
    on_stop_speaking: Callable[[], None] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("940x720")
        self.root.minsize(720, 560)
        self.root.configure(bg="#02030A")
        self._queue: Queue[tuple[str, str]] = Queue()
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._build()
        self._drain_queue()
        self.root.after(200, self.focus_command_entry)

    def _build(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Jarvis.TLabel", background="#02030A", foreground="#8CD9FF")
        style.configure("JarvisHeader.TLabel", background="#02030A", foreground="#56C9FF", font=("Segoe UI", 22, "bold"))
        style.configure("JarvisState.TLabel", background="#02030A", foreground="#84FFC9", font=("Segoe UI", 13, "bold"))
        style.configure("JarvisActivity.TLabel", background="#02030A", foreground="#F5D06F", font=("Segoe UI", 15, "bold"))

        top_row = tk.Frame(self.root, bg="#02030A")
        top_row.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 6))

        header = ttk.Label(top_row, text="KRYPTO", style="JarvisHeader.TLabel")
        header.pack(side=tk.LEFT)

        wake_btn = tk.Button(
            top_row,
            text="Hey Krypto",
            command=self._trigger_wake,
            bg="#2569A6",
            fg="#FFFFFF",
            activebackground="#56C9FF",
            activeforeground="#02030A",
            relief=tk.FLAT,
            font=("Segoe UI", 11, "bold"),
            padx=14,
            pady=6,
        )
        wake_btn.pack(side=tk.RIGHT, padx=(8, 0))

        stop_speak_btn = tk.Button(
            top_row,
            text="Stop Speaking",
            command=self._trigger_stop_speaking,
            bg="#7A2E2E",
            fg="#FFFFFF",
            activebackground="#B33A3A",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
        )
        stop_speak_btn.pack(side=tk.RIGHT)

        self.state = ttk.Label(self.root, text="State: idle", style="JarvisState.TLabel")
        self.state.grid(row=1, column=0, pady=(0, 4))

        status_row = tk.Frame(self.root, bg="#02030A")
        status_row.grid(row=2, column=0, pady=(0, 8))

        self._spinner_canvas = tk.Canvas(
            status_row,
            width=32,
            height=32,
            bg="#02030A",
            highlightthickness=0,
            bd=0,
        )
        self._spinner_angle = 0
        self._spinner_running = False

        self.activity = ttk.Label(
            status_row,
            text="Activity: Waiting to start",
            style="JarvisActivity.TLabel",
        )
        self.activity.pack(side=tk.LEFT)

        log_frame = tk.Frame(self.root, bg="#02030A")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=18, pady=(8, 8))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log = tk.Text(
            log_frame,
            bg="#050B19",
            fg="#A7D8FF",
            insertbackground="#A7D8FF",
            relief=tk.FLAT,
            font=("Consolas", 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=16,
            padx=8,
            pady=8,
        )
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        def _on_log_mousewheel(event) -> str:
            self.log.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        self.log.bind("<MouseWheel>", _on_log_mousewheel)
        log_frame.bind("<MouseWheel>", _on_log_mousewheel)

        input_panel = tk.Frame(self.root, bg="#0A1628", highlightbackground="#56C9FF", highlightthickness=1)
        input_panel.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 16))

        cmd_label = tk.Label(
            input_panel,
            text="Type command:",
            bg="#0A1628",
            fg="#84FFC9",
            font=("Segoe UI", 10, "bold"),
        )
        cmd_label.pack(anchor="w", padx=10, pady=(8, 4))

        input_frame = tk.Frame(input_panel, bg="#0A1628")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.command_entry = tk.Entry(
            input_frame,
            bg="#050B19",
            fg="#A7D8FF",
            insertbackground="#A7D8FF",
            relief=tk.SOLID,
            bd=1,
            highlightthickness=2,
            highlightcolor="#56C9FF",
            highlightbackground="#1A4D7A",
            font=("Segoe UI", 13),
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 8))
        self.command_entry.bind("<Return>", self._on_enter_key)
        self.command_entry.bind("<KP_Enter>", self._on_enter_key)

        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self._submit_command,
            bg="#1A4D7A",
            fg="#E8F4FF",
            activebackground="#2569A6",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=8,
        )
        send_btn.pack(side=tk.RIGHT)

        self._append("System", "Krypto ready. Click Hey Krypto, use voice, or type below and press Enter.")

    def _on_enter_key(self, _event) -> str:
        self._submit_command()
        return "break"

    def _trigger_wake(self) -> None:
        if self.on_wake:
            self.on_wake()

    def _trigger_stop_speaking(self) -> None:
        if self.on_stop_speaking:
            self.on_stop_speaking()

    def focus_command_entry(self) -> None:
        self.root.after(0, lambda: self.command_entry.focus_set())

    def set_state(self, value: str) -> None:
        self._queue.put(("state", value))

    def set_activity(self, value: str) -> None:
        self._queue.put(("activity", value))

    def set_loading(self, active: bool) -> None:
        self._queue.put(("loading", "on" if active else "off"))

    def set_input_enabled(self, enabled: bool) -> None:
        self._queue.put(("input", "on" if enabled else "off"))

    def append(self, who: str, text: str) -> None:
        self._queue.put(("log", f"{who}\x1f{text}"))

    def _append(self, who: str, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"{who}: {text}\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _apply_pending(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "state":
                    self.state.configure(text=f"State: {payload}")
                elif kind == "activity":
                    self.activity.configure(text=f"Activity: {payload}")
                elif kind == "loading":
                    if payload == "on":
                        self._start_spinner()
                    else:
                        self._stop_spinner()
                elif kind == "input":
                    state = tk.NORMAL if payload == "on" else tk.DISABLED
                    self.command_entry.configure(state=state)
                else:
                    who, text = payload.split("\x1f", 1)
                    self._append(who, text)
        except Empty:
            pass
        self.root.update_idletasks()

    def _drain_queue(self) -> None:
        self._apply_pending()
        self.root.after(100, self._drain_queue)

    def _submit_command(self) -> None:
        if str(self.command_entry.cget("state")) == tk.DISABLED:
            return
        text = self.command_entry.get().strip()
        if not text:
            return
        self.command_entry.delete(0, tk.END)
        handler = self.on_command
        if handler is None:
            self._append("System", "Command handler not connected. Restart Krypto.")
            return
        handler(text)

    def _draw_spinner(self) -> None:
        self._spinner_canvas.delete("all")
        self._spinner_canvas.create_oval(2, 2, 30, 30, outline="#123A5C", width=2)
        self._spinner_canvas.create_arc(
            4,
            4,
            28,
            28,
            start=self._spinner_angle,
            extent=110,
            outline="#56C9FF",
            width=3,
            style=tk.ARC,
        )
        self._spinner_canvas.create_arc(
            4,
            4,
            28,
            28,
            start=(self._spinner_angle + 180) % 360,
            extent=70,
            outline="#84FFC9",
            width=2,
            style=tk.ARC,
        )

    def _tick_spinner(self) -> None:
        if not self._spinner_running:
            return
        self._spinner_angle = (self._spinner_angle + 20) % 360
        self._draw_spinner()
        self.root.after(60, self._tick_spinner)

    def _start_spinner(self) -> None:
        if self._spinner_running:
            return
        self._spinner_running = True
        self._spinner_canvas.pack(side=tk.LEFT, padx=(0, 10))
        self._tick_spinner()

    def _stop_spinner(self) -> None:
        self._spinner_running = False
        self._spinner_canvas.pack_forget()
        self._spinner_canvas.delete("all")

    def flush(self) -> None:
        """Paint all queued log/state updates before TTS (safe from background threads)."""
        done = threading.Event()

        def _work() -> None:
            self._apply_pending()
            done.set()

        self.root.after(0, _work)
        done.wait(timeout=2.0)

    def run(self) -> None:
        self.root.mainloop()
