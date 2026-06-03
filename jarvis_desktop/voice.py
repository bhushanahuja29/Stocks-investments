from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover
    sr = None

# Windows SAPI speak flags
_SVSFAsync = 1
_SVSFPurgeBeforeSpeak = 2
_SRSpeaking = 2


def _sapi_available() -> bool:
    try:
        import win32com.client

        win32com.client.Dispatch("SAPI.SpVoice")
        return True
    except Exception:
        return False


def _init_pyttsx3():
    import pyttsx3

    engine = pyttsx3.init(driverName="sapi5")
    voices = engine.getProperty("voices")
    if voices:
        engine.setProperty("voice", voices[0].id)
    engine.setProperty("rate", 178)
    return engine


@dataclass
class TextToSpeech:
    _speak_lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _stop_requested: bool = field(default=False, init=False, repr=False)
    _sapi_voice: Any = field(default=None, init=False, repr=False)
    _ps_proc: subprocess.Popen[str] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._engine = None
        self._enabled = False
        self.backend = "none"

        try:
            self._engine = _init_pyttsx3()
            self._enabled = True
            self.backend = "pyttsx3"
        except Exception:
            self._engine = None

        if _sapi_available():
            try:
                import win32com.client

                self._sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
                self._enabled = True
                self.backend = "windows_sapi"
            except Exception:
                self._sapi_voice = None

        if not self._enabled and sys.platform == "win32":
            self._enabled = True
            self.backend = "powershell"

    def stop(self) -> None:
        """Interrupt current speech immediately."""
        self._stop_requested = True
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass
        if self._sapi_voice is not None:
            try:
                self._sapi_voice.Speak("", _SVSFPurgeBeforeSpeak)
            except Exception:
                pass
        if self._ps_proc is not None and self._ps_proc.poll() is None:
            try:
                self._ps_proc.terminate()
            except Exception:
                pass
            self._ps_proc = None

    def say(self, text: str) -> None:
        if not text.strip():
            return
        with self._speak_lock:
            self._stop_requested = False
            self._say_unlocked(text.strip())

    def _say_unlocked(self, text: str) -> None:
        if self._stop_requested:
            return

        if self.backend == "pyttsx3" and self._engine is not None:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                return
            except Exception:
                self._engine = None
                self.backend = "windows_sapi" if self._sapi_voice else "none"

        if self._sapi_voice is not None:
            self._say_sapi(text)
            return

        if sys.platform == "win32":
            self._say_powershell(text)

    def _say_sapi(self, text: str) -> None:
        try:
            self._sapi_voice.Speak(text, _SVSFAsync)
            while self._sapi_voice.Status.RunningState == _SRSpeaking:
                if self._stop_requested:
                    self._sapi_voice.Speak("", _SVSFPurgeBeforeSpeak)
                    return
                time.sleep(0.05)
        except Exception:
            pass

    def _say_powershell(self, text: str) -> None:
        safe = text.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Speak('{safe}')"
        )
        try:
            self._ps_proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            while self._ps_proc.poll() is None:
                if self._stop_requested:
                    self._ps_proc.terminate()
                    self._ps_proc = None
                    return
                time.sleep(0.05)
            self._ps_proc = None
        except Exception:
            self._ps_proc = None

    @property
    def status_message(self) -> str:
        if not self._enabled:
            return "TTS: disabled (pyttsx3 voice registry issue; install pywin32 or fix default voice)"
        return f"TTS: enabled via {self.backend}"


@dataclass
class WakeAndSpeech:
    wake_phrases: tuple[str, ...]
    on_wake: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        if sr is None:
            raise RuntimeError("speech_recognition is required for microphone listening.")
        self._recognizer = sr.Recognizer()
        self._mic = sr.Microphone()
        self._wake_phrases = tuple(sorted(self.wake_phrases, key=len, reverse=True))

    def _heard_wake(self, text: str) -> bool:
        lowered = text.lower().strip()
        return any(phrase in lowered for phrase in self._wake_phrases)

    def listen_for_wake(self) -> bool:
        with self._mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = self._recognizer.listen(source, timeout=10, phrase_time_limit=4)
        try:
            text = self._recognizer.recognize_google(audio).lower().strip()
        except Exception:
            return False
        if self._heard_wake(text):
            if self.on_wake:
                self.on_wake()
            return True
        return False

    def capture_command(self) -> str:
        with self._mic as source:
            audio = self._recognizer.listen(source, timeout=12, phrase_time_limit=8)
        try:
            return self._recognizer.recognize_google(audio).strip()
        except Exception:
            return ""
