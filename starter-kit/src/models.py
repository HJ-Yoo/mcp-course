"""
Data models for the Internal Ops Assistant.
TODO (Episode 3): Complete the domain models and AppContext.
"""
from __future__ import annotations
import csv
import json
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    # TODO (Episode 9): Add remaining error codes


class ToolError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code.value}] {message}")


@dataclass
class InventoryItem:
    item_id: str
    name: str
    category: str
    quantity: int
    location: str
    status: str
    last_updated: str


# TODO (Episode 7): Define PolicyDoc dataclass
# TODO (Episode 8): Define Ticket dataclass


@dataclass
class AppContext:
    db: sqlite3.Connection
    # TODO (Episode 7): Add policies field
    # TODO (Episode 8): Add tickets_file field
    # TODO (Episode 14): Add audit_log_path field

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "AppContext":
        base = base_dir or Path(__file__).resolve().parent.parent
        data_dir = base / "data"

        db = cls._init_db(data_dir / "inventory.csv")

        return cls(db=db)

    @staticmethod
    def _init_db(csv_path: Path) -> sqlite3.Connection:
        # TODO (Episode 5): Create in-memory SQLite DB from CSV
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        return db
