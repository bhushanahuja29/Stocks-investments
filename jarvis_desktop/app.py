from __future__ import annotations

from pathlib import Path
from threading import Lock, Thread

from .automation import MissingLevelAutomation
from .backend_client import BackendClient, MongoLevelClient
from .config import CONFIG
from .agent import is_agent_query
from .intents import IntentRouter
from .llm import OllamaClient
from .scheduler import DailyScheduler
from .pin_panel import create_pin_panel
from .ui import JarvisUI
from .voice import TextToSpeech, WakeAndSpeech


class JarvisApp:
    def __init__(self, workspace_root: str | None = None) -> None:
        self._command_lock = Lock()
        self._command_busy = False

        self.tts = TextToSpeech()
        self.backend = BackendClient()
        self.mongo = MongoLevelClient()
        self.llm = OllamaClient(
            base_url=CONFIG.ollama_base_url,
            model=CONFIG.ollama_model,
        )
        root = Path(workspace_root) if workspace_root else Path(__file__).resolve().parents[1]
        self.automation = MissingLevelAutomation(workspace_root=root)
        self.ui = JarvisUI(
            on_command=self._handle_typed_command,
            on_wake=self._handle_wake_button,
            on_stop_speaking=self._handle_stop_speaking,
        )
        self.pin_panel = create_pin_panel(self.ui.root, self.backend)
        self.ui.root.after(800, self._restore_pinned_scrips)
        self.router = IntentRouter(self.backend, self.mongo, self.automation, self.llm)
        self.router.on_agent_progress = self._on_agent_progress
        self.router.pin_panel = self.pin_panel
        self.listener = WakeAndSpeech(wake_phrases=CONFIG.wake_phrases, on_wake=None)
        self.scheduler = DailyScheduler(
            hour=CONFIG.scheduler_hour,
            minute=CONFIG.scheduler_minute,
            task=self.run_morning_brief,
        )

        self.ui.append("System", self.tts.status_message)
        self.ui.append("System", f"Backend API: {CONFIG.backend_url}")
        self.ui.append("System", "Levels: GET /api/scrips (Mongo) | Price: GET /api/price/{{symbol}}")
        try:
            health = self.backend.health()
            self.ui.append("System", f"Backend health: {health.get('status', 'unknown')}")
            if not health.get("market_api"):
                self.ui.append(
                    "System",
                    "Market API not on backend (404) — restart python main.py. "
                    "Nifty tools will use local yfinance fallback.",
                )
        except Exception as exc:
            self.ui.append("System", f"Backend health check failed: {exc}")

    def _restore_pinned_scrips(self) -> None:
        def work() -> None:
            try:
                n = self.pin_panel.restore_persisted()
                if n and self.ui.root.winfo_exists():
                    syms = ", ".join(self.pin_panel.pinned_symbols())
                    msg = f"Restored {n} pinned scrip(s): {syms}"
                    self.ui.root.after(0, lambda: self.ui.append("System", msg))
            except Exception as exc:
                if self.ui.root.winfo_exists():
                    err = f"Could not restore pinned scrips: {exc}"
                    self.ui.root.after(0, lambda: self.ui.append("System", err))

        Thread(target=work, daemon=True).start()

    def _on_agent_progress(self, message: str) -> None:
        """Keep spinner + activity label updated during Ollama/tool steps."""
        self._update_status("thinking", message, loading=True)
        self.ui.flush()

    def _update_status(
        self,
        state: str,
        activity: str,
        log_line: str | None = None,
        *,
        loading: bool = False,
    ) -> None:
        self.ui.set_state(state)
        self.ui.set_activity(activity)
        self.ui.set_loading(loading)
        if log_line:
            self.ui.append("System", log_line)

    def _set_command_busy(self, busy: bool) -> None:
        with self._command_lock:
            self._command_busy = busy
        self.ui.set_input_enabled(not busy)

    def _handle_typed_command(self, text: str) -> None:
        with self._command_lock:
            if self._command_busy:
                self.ui.append("System", "Still processing previous command. Please wait.")
                return
            self._command_busy = True
        self.ui.set_input_enabled(False)
        Thread(target=self._process_command, args=(text,), daemon=True).start()

    def _handle_wake_button(self) -> None:
        Thread(target=self._wake_session, daemon=True).start()

    def _handle_stop_speaking(self) -> None:
        self.tts.stop()
        self._update_status("idle", "Speech stopped — ready for next command", loading=False)
        self.ui.append("System", "Speech stopped.")
        self.ui.focus_command_entry()

    def _wake_session(self) -> None:
        greeting = f"What can I do for you {CONFIG.user_name}?"
        self._present_text("Krypto", greeting)
        self._update_status("ready", "Type a command below or speak after the tone")
        self.ui.flush()
        self.ui.focus_command_entry()

    def _process_command(self, text: str) -> None:
        try:
            self.ui.append("Bhushan", text)
            self.ui.flush()
            if is_agent_query(text):
                activity = "Krypto agent thinking (Ollama + tools)"
            else:
                activity = "Analyzing and fetching data from Mongo/API"
            self._update_status("thinking", activity, loading=True)
            self.ui.flush()
            reply = self.router.handle(text)
            if reply.log_detail:
                self.ui.append("Krypto", reply.log_detail)
                self.ui.flush()
            self._present_text("Krypto", reply.text)
            self._update_status("idle", "Ready — voice, Hey Krypto button, or type below", loading=False)
        except Exception as exc:
            self._present_text("System", f"Something went wrong: {exc}", speak=False)
            self._update_status("idle", "Ready — voice, Hey Krypto button, or type below", loading=False)
        finally:
            self._set_command_busy(False)

    def _present_text(self, who: str, text: str, *, speak: bool = True) -> None:
        """Show full text in UI first, then speak (avoids TTS ahead of on-screen text)."""
        self.ui.append(who, text)
        self.ui.flush()
        if speak and text.strip():
            self._update_status("speaking", "Speaking response", loading=False)
            self.ui.flush()
            self.tts.say(text)
        self.ui.flush()

    def run_morning_brief(self) -> None:
        self._update_status(
            "morning-scan",
            "Scanning all symbols from Mongo",
            "Morning scan started.",
            loading=True,
        )
        self.ui.flush()
        try:
            report = self.router.near_trigger_report(CONFIG.near_trigger_threshold)
            self._present_text("Krypto", report.text)
        except Exception as exc:
            self._present_text("System", f"Morning scan failed: {exc}", speak=False)
        finally:
            self.ui.set_loading(False)
            self.ui.flush()
        self._update_status("idle", "Ready — voice, Hey Krypto button, or type below", loading=False)

    def _listen_loop(self) -> None:
        self._update_status("idle", "Ready — voice, Hey Krypto button, or type below", "Voice listener initialized.")
        while True:
            self._update_status("listening-wake-word", "Listening for Hey Krypto / Crypto")
            did_wake = self.listener.listen_for_wake()
            if not did_wake:
                continue

            self._wake_session()
            with self._command_lock:
                if self._command_busy:
                    continue

            self._update_status("listening-command", "Listening to your command")
            self.ui.flush()
            spoken = self.listener.capture_command()
            if not spoken.strip():
                self.ui.append("Bhushan", "[silence]")
                self.ui.flush()
                self._update_status("idle", "Ready — voice, Hey Krypto button, or type below")
                continue
            self._handle_typed_command(spoken)

    def run(self) -> None:
        self.scheduler.start()
        Thread(target=self._listen_loop, daemon=True).start()
        self.ui.run()


def main() -> None:
    app = JarvisApp()
    app.run()


if __name__ == "__main__":
    main()
