"""
Audit logger — writes a JSONL line for every tool / resource call.

Schema per line:
  {timestamp, action, tool_name, input_summary, result_summary, success}
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, log_path: Path) -> None:
        self._path = log_path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        action: str,
        tool_name: str,
        input_summary: str,
        result_summary: str,
        success: bool,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "tool_name": tool_name,
            "input_summary": input_summary,
            "result_summary": result_summary,
            "success": success,
        }
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
