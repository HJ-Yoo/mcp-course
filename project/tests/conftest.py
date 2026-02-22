"""
Shared pytest fixtures for the Internal Ops Assistant test suite.

Provides pre-built sample data and an AppContext wired to temporary
directories so that tests never touch production data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.audit import AuditLogger
from src.models import AppContext, InventoryItem, PolicyDoc


@pytest.fixture
def sample_inventory() -> list[InventoryItem]:
    """Three sample inventory items spanning different categories."""
    return [
        InventoryItem(
            item_id="INV-001",
            name="Dell Latitude 5540 Laptop",
            category="Electronics",
            quantity=25,
            location="Warehouse A",
            status="in_stock",
            last_updated="2026-01-15",
        ),
        InventoryItem(
            item_id="INV-002",
            name="Ergonomic Office Chair",
            category="Furniture",
            quantity=50,
            location="Warehouse B",
            status="in_stock",
            last_updated="2026-01-20",
        ),
        InventoryItem(
            item_id="INV-003",
            name="USB-C Docking Station",
            category="Electronics",
            quantity=0,
            location="Warehouse A",
            status="out_of_stock",
            last_updated="2026-02-01",
        ),
    ]


@pytest.fixture
def sample_policies(tmp_path: Path) -> list[PolicyDoc]:
    """Two temporary policy markdown files with front-matter."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

    # Policy 1
    remote_work = policy_dir / "remote-work.md"
    remote_work.write_text(
        "---\n"
        "title: Remote Work Policy\n"
        "tags: [remote, hr, work-from-home]\n"
        "---\n"
        "\n"
        "# Remote Work Policy\n"
        "\n"
        "## Eligibility\n"
        "All full-time employees who have completed their probation period "
        "are eligible for remote work.\n"
        "\n"
        "## Equipment\n"
        "The company provides a laptop and monitor for remote workers.\n",
        encoding="utf-8",
    )

    # Policy 2
    security = policy_dir / "security-guidelines.md"
    security.write_text(
        "---\n"
        "title: Security Guidelines\n"
        "tags: [security, it, compliance]\n"
        "---\n"
        "\n"
        "# Security Guidelines\n"
        "\n"
        "## Password Policy\n"
        "All passwords must be at least 12 characters and include uppercase, "
        "lowercase, numbers, and special characters.\n"
        "\n"
        "## VPN Usage\n"
        "Employees must use the company VPN when accessing internal resources.\n",
        encoding="utf-8",
    )

    return [
        PolicyDoc(
            doc_id="remote-work",
            title="Remote Work Policy",
            path=remote_work,
            tags=["remote", "hr", "work-from-home"],
        ),
        PolicyDoc(
            doc_id="security-guidelines",
            title="Security Guidelines",
            path=security,
            tags=["security", "it", "compliance"],
        ),
    ]


@pytest.fixture
def app_context(
    tmp_path: Path,
    sample_inventory: list[InventoryItem],
    sample_policies: list[PolicyDoc],
) -> AppContext:
    """Fully wired AppContext using temporary directories."""
    tickets_file = tmp_path / "tickets" / "tickets.jsonl"
    tickets_file.parent.mkdir(parents=True, exist_ok=True)

    audit_log_path = tmp_path / "logs" / "audit.jsonl"
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    policy_dir = tmp_path / "policies"

    return AppContext(
        inventory=sample_inventory,
        policies=sample_policies,
        policy_dir=policy_dir,
        tickets_file=tickets_file,
        audit_log_path=audit_log_path,
    )


@pytest.fixture
def audit_logger(tmp_path: Path) -> AuditLogger:
    """AuditLogger that writes to a temporary file."""
    return AuditLogger(tmp_path / "logs" / "test_audit.jsonl")
