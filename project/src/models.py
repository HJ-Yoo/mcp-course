"""
Data models for the Internal Ops Assistant.

Defines the core domain objects (InventoryItem, PolicyDoc, Ticket)
and the shared AppContext that is initialized at server startup via lifespan.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFLICT = "CONFLICT"


class ToolError(Exception):
    """Standardised error that MCP clients can act on."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code.value}] {message}")


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

@dataclass
class InventoryItem:
    item_id: str
    name: str
    category: str
    quantity: int
    location: str
    status: str
    last_updated: str


@dataclass
class PolicyDoc:
    doc_id: str
    title: str
    path: Path
    tags: list[str] = field(default_factory=list)


@dataclass
class Ticket:
    ticket_id: str
    title: str
    priority: str
    body: str
    status: str
    created_at: str
    idempotency_key: str | None = None
    assigned_to: str | None = None


# ---------------------------------------------------------------------------
# Application context — initialised once in lifespan
# ---------------------------------------------------------------------------

@dataclass
class AppContext:
    inventory: list[InventoryItem]
    policies: list[PolicyDoc]
    policy_dir: Path
    tickets_file: Path
    audit_log_path: Path

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, base_dir: Path | None = None) -> "AppContext":
        base = base_dir or Path(__file__).resolve().parent.parent
        data_dir = base / "data"
        policy_dir = data_dir / "policies"

        inventory = cls._load_inventory(data_dir / "inventory.csv")
        policies = cls._load_policy_index(policy_dir)

        tickets_file = data_dir / "tickets" / "tickets.jsonl"
        tickets_file.parent.mkdir(parents=True, exist_ok=True)

        audit_log_path = base / "logs" / "audit.jsonl"
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        return cls(
            inventory=inventory,
            policies=policies,
            policy_dir=policy_dir,
            tickets_file=tickets_file,
            audit_log_path=audit_log_path,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_inventory(path: Path) -> list[InventoryItem]:
        items: list[InventoryItem] = []
        if not path.exists():
            return items
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                items.append(
                    InventoryItem(
                        item_id=row["item_id"],
                        name=row["name"],
                        category=row["category"],
                        quantity=int(row["quantity"]),
                        location=row["location"],
                        status=row["status"],
                        last_updated=row["last_updated"],
                    )
                )
        return items

    @staticmethod
    def _load_policy_index(policy_dir: Path) -> list[PolicyDoc]:
        docs: list[PolicyDoc] = []
        if not policy_dir.exists():
            return docs
        for md_file in sorted(policy_dir.glob("*.md")):
            doc_id = md_file.stem
            title = doc_id.replace("-", " ").title()
            tags: list[str] = []
            # Parse front-matter for title & tags
            text = md_file.read_text(encoding="utf-8")
            fm_match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if fm_match:
                for line in fm_match.group(1).splitlines():
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip()
                    if line.startswith("tags:"):
                        raw = line.split(":", 1)[1].strip().strip("[]")
                        tags = [t.strip() for t in raw.split(",")]
            docs.append(PolicyDoc(doc_id=doc_id, title=title, path=md_file, tags=tags))
        return docs

    # ------------------------------------------------------------------
    # Ticket helpers
    # ------------------------------------------------------------------
    def load_tickets(self) -> list[Ticket]:
        tickets: list[Ticket] = []
        if not self.tickets_file.exists():
            return tickets
        for line in self.tickets_file.read_text(encoding="utf-8").strip().splitlines():
            if line.strip():
                d = json.loads(line)
                tickets.append(Ticket(**d))
        return tickets

    def next_ticket_id(self) -> str:
        existing = self.load_tickets()
        if not existing:
            return "TKT-006"
        nums = [int(t.ticket_id.split("-")[1]) for t in existing]
        return f"TKT-{max(nums) + 1:03d}"

    def append_ticket(self, ticket: Ticket) -> None:
        with self.tickets_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ticket.__dict__, ensure_ascii=False) + "\n")
