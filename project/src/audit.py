"""
Audit logger — writes a JSONL line for every tool / resource call.

Schema per line:
  {timestamp, action, tool_name, ...kwargs}
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, log_dir: str | Path = "logs"):
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    @property
    def log_path(self) -> Path:
        return self._log_dir / "audit.jsonl"

    def start_timer(self) -> float:
        return time.perf_counter()

    def elapsed_ms(self, start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 2)

    async def log(self, action: str, tool_name: str, **kwargs) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "tool_name": tool_name,
            **kwargs,
        }
        async with self._lock:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
