"""
TODO (Episode 15): Create shared test fixtures.

Fixture 설계 3단계:
  1. 데이터 Fixture — sample_inventory, sample_policies
  2. 환경 Fixture — sample_db (인메모리 SQLite), audit_logger
  3. 통합 Fixture — app_context (위 두 fixture 조합)

pytest는 conftest.py를 자동 로딩합니다.
여기에 정의된 fixture는 같은 디렉토리의 모든 test 파일에서
import 없이 파라미터 이름만으로 자동 주입됩니다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.models import AppContext, InventoryItem, PolicyDoc


# ---------------------------------------------------------------------------
# 1단계: 데이터 Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_inventory() -> list[InventoryItem]:
    """샘플 재고 데이터 (3개 항목)."""
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
    """임시 마크다운 파일로 정책 문서 2개 생성."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

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


# ---------------------------------------------------------------------------
# 2단계: 환경 Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_db(sample_inventory: list[InventoryItem]) -> sqlite3.Connection:
    """sample_inventory 리스트를 인메모리 SQLite DB로 변환."""
    # TODO:
    #   1. sqlite3.connect(":memory:")
    #   2. db.row_factory = sqlite3.Row
    #   3. CREATE TABLE inventory (item_id, name, category, quantity,
    #      location, status, last_updated)
    #   4. for item in sample_inventory: INSERT INTO inventory VALUES (?,?,?,...)
    #   5. db.commit()
    #   6. return db
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    return db


# TODO: audit_logger fixture 추가
#   - AuditLogger(log_dir=tmp_path / "logs") 반환
#   - from src.audit import AuditLogger


# ---------------------------------------------------------------------------
# 3단계: 통합 Fixture
# ---------------------------------------------------------------------------

# TODO: app_context fixture 추가
#   - 파라미터: tmp_path, sample_db, sample_policies
#   - tickets_file: tmp_path / "tickets" / "tickets.jsonl"
#   - AppContext(
#         db=sample_db,
#         policies=sample_policies,
#         policy_dir=tmp_path / "policies",
#         tickets_file=tickets_file,
#         audit_logger=AuditLogger(log_dir=tmp_path / "logs"),
#     )
