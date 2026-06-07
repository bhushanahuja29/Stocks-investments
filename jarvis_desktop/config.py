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
    jarvis_sync_key: str = os.getenv(
        "JARVIS_SYNC_KEY", "delta-bhushan-jarvis-sync-2026"
    )
    tradingview_chrome_user_data: str = os.getenv(
        "TRADINGVIEW_CHROME_USER_DATA",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
    )
    tradingview_chrome_profile_1: str = os.getenv(
        "TRADINGVIEW_CHROME_PROFILE_1", "Profile 8"
    )
    tradingview_chrome_profile_2: str = os.getenv(
        "TRADINGVIEW_CHROME_PROFILE_2", "Profile 9"
    )
    tradingview_chart_load_sec: float = float(
        os.getenv("TRADINGVIEW_CHART_LOAD_SEC", "8")
    )
    tradingview_chart_layout_id: str = os.getenv(
        "TRADINGVIEW_CHART_LAYOUT_ID", "Vhwft9jB"
    )


CONFIG = JarvisConfig()
