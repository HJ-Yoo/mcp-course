"""
Shared pytest fixtures for the Internal Ops Assistant test suite.

Provides pre-built sample data and an AppContext wired to temporary
directories so that tests never touch production data.
"""

from __future__ import annotations

import sqlite3
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
def sample_db(sample_inventory: list[InventoryItem]) -> sqlite3.Connection:
    """In-memory SQLite DB populated with sample inventory data."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE inventory (
        item_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        location TEXT NOT NULL,
        status TEXT NOT NULL,
        last_updated TEXT NOT NULL
    )""")
    for item in sample_inventory:
        db.execute(
            "INSERT INTO inventory VALUES (?,?,?,?,?,?,?)",
            (item.item_id, item.name, item.category,
             item.quantity, item.location, item.status,
             item.last_updated),
        )
    db.commit()
    return db


@pytest.fixture
def sample_policies(tmp_path: Path) -> list[PolicyDoc]:
    """임시 마크다운 파일로 정책 문서 2개 생성."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

    # 정책 1: 재택근무
    remote_work = policy_dir / "remote-work.md"
    remote_work.write_text(
        "---\n"
        "title: 재택근무 정책\n"
        "tags: [remote, hr, work-from-home]\n"
        "---\n"
        "\n"
        "# 재택근무 정책\n"
        "\n"
        "## 자격 요건\n"
        "수습 기간을 완료한 모든 정규직 직원이 재택근무 대상입니다.\n"
        "\n"
        "## 장비 지원\n"
        "회사에서 노트북과 모니터를 지급합니다.\n",
        encoding="utf-8",
    )

    # 정책 2: 보안 가이드라인
    security = policy_dir / "security-guidelines.md"
    security.write_text(
        "---\n"
        "title: 보안 가이드라인\n"
        "tags: [security, it, compliance]\n"
        "---\n"
        "\n"
        "# 보안 가이드라인\n"
        "\n"
        "## 비밀번호 정책\n"
        "비밀번호는 최소 12자 이상, 대소문자·숫자·특수문자를 포함해야 합니다.\n"
        "\n"
        "## VPN 사용\n"
        "사내 시스템 접근 시 반드시 VPN을 사용해야 합니다.\n",
        encoding="utf-8",
    )

    return [
        PolicyDoc(
            doc_id="remote-work",
            title="재택근무 정책",
            path=remote_work,
            tags=["remote", "hr", "work-from-home"],
        ),
        PolicyDoc(
            doc_id="security-guidelines",
            title="보안 가이드라인",
            path=security,
            tags=["security", "it", "compliance"],
        ),
    ]


@pytest.fixture
def app_context(
    tmp_path: Path,
    sample_db: sqlite3.Connection,
    sample_policies: list[PolicyDoc],
) -> AppContext:
    """Fully wired AppContext using temporary directories."""
    tickets_file = tmp_path / "tickets" / "tickets.jsonl"
    tickets_file.parent.mkdir(parents=True, exist_ok=True)

    policy_dir = tmp_path / "policies"
    audit_logger = AuditLogger(log_dir=tmp_path / "logs")

    return AppContext(
        db=sample_db,
        policies=sample_policies,
        policy_dir=policy_dir,
        tickets_file=tickets_file,
        audit_logger=audit_logger,
    )


@pytest.fixture
def audit_logger(tmp_path: Path) -> AuditLogger:
    """AuditLogger that writes to a temporary directory."""
    return AuditLogger(log_dir=tmp_path / "logs")
