from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MissingLevelAutomation:
    workspace_root: Path

    def _run_script(self, script_name: str) -> tuple[bool, str]:
        script_path = self.workspace_root / script_name
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.workspace_root),
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            return False, str(exc)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "unknown error").strip()
            return False, err.splitlines()[-1] if err else f"{script_name} failed"
        return True, ""

    def build_levels_for_symbol(self, symbol: str) -> tuple[bool, str]:
        # Batch pipeline for Indian stocks via TradingView screenshots.
        for script in (
            "tradingview_auto_scraper.py",
            "ocr_green_levels.py",
            "push_tradingview_to_mongodb.py",
        ):
            ok, err = self._run_script(script)
            if not ok:
                return False, f"{script} failed for {symbol}: {err}"
        return True, ""
