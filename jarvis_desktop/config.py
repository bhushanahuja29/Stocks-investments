from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JarvisConfig:
    # Default to LAN backend; override with JARVIS_BACKEND_URL if needed.
    backend_url: str = os.getenv("JARVIS_BACKEND_URL", "http://192.168.29.31:8000")
    mongo_uri: str = os.getenv(
        "JARVIS_MONGODB_URI",
        os.getenv(
            "MONGODB_URI",
            "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker",
        ),
    )
    mongo_db: str = os.getenv("JARVIS_MONGO_DB", "delta_tracker")
    mongo_collection: str = os.getenv("JARVIS_MONGO_COLLECTION", "monitored_scrips")
    wake_phrases: tuple[str, ...] = tuple(
        p.strip().lower()
        for p in os.getenv(
            "KRYPTO_WAKE_WORDS",
            os.getenv("KRYPTO_WAKE_WORD", "hey krypto,crypto,krypto,hey crypto"),
        ).split(",")
        if p.strip()
    )
    user_name: str = os.getenv("JARVIS_USER_NAME", "Bhushan")
    scheduler_hour: int = int(os.getenv("JARVIS_SCHED_HOUR", "8"))
    scheduler_minute: int = int(os.getenv("JARVIS_SCHED_MINUTE", "30"))
    near_trigger_threshold: float = float(os.getenv("JARVIS_NEAR_TRIGGER_PCT", "2.0"))
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    agent_max_steps: int = int(os.getenv("AGENT_MAX_STEPS", "5"))


CONFIG = JarvisConfig()
