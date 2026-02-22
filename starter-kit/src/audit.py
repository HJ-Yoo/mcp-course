"""
Audit logger — TODO (Episode 14): Implement JSONL audit logging.
"""
from __future__ import annotations
from pathlib import Path


class AuditLogger:
    def __init__(self, log_path: Path) -> None:
        # TODO: Initialize logger
        pass

    def log(self, *, action: str, tool_name: str, input_summary: str, result_summary: str, success: bool) -> None:
        # TODO: Write JSONL entry
        pass
