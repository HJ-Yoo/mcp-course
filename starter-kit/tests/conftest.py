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
    # TODO: InventoryItem 인스턴스 리스트 반환
    #   - INV-001: Dell Latitude 5540 Laptop (Electronics, in_stock)
    #   - INV-002: Ergonomic Office Chair (Furniture, in_stock)
    #   - INV-003: USB-C Docking Station (Electronics, out_of_stock)
    return []


@pytest.fixture
def sample_policies(tmp_path: Path) -> list[PolicyDoc]:
    """임시 마크다운 파일로 정책 문서 2개 생성."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

    # TODO: 정책 1 — 재택근무 (remote-work.md)
    #   - YAML front-matter: title, tags
    #   - policy_dir / "remote-work.md" 에 write_text()
    #
    # TODO: 정책 2 — 보안 가이드라인 (security-guidelines.md)
    #   - YAML front-matter: title, tags
    #   - policy_dir / "security-guidelines.md" 에 write_text()
    #
    # TODO: PolicyDoc 리스트 반환
    #   - PolicyDoc(doc_id="remote-work", title="재택근무 정책",
    #               path=remote_work, tags=[...])
    return []


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
