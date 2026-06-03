from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Event, Thread
from time import sleep
from typing import Callable


@dataclass
class DailyScheduler:
    hour: int
    minute: int
    task: Callable[[], None]

    def __post_init__(self) -> None:
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now()
            if now.hour == self.hour and now.minute == self.minute:
                self.task()
                sleep(61)
                continue
            sleep(20)
