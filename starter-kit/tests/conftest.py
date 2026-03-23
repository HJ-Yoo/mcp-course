"""
TODO (Episode 15): Create shared test fixtures.

Fixture 설계 3단계:
  1. 데이터 Fixture — sample_inventory, sample_policies
  2. 환경 Fixture — data_dir (tmp_path), audit_logger
  3. 통합 Fixture — app_context (위 두 fixture 조합)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.models import InventoryItem


# ---------------------------------------------------------------------------
# 1단계: 데이터 Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_inventory() -> list[InventoryItem]:
    """샘플 재고 데이터 (2~3개 항목)."""
    # TODO: InventoryItem 인스턴스 리스트 반환
    #   - INV-001: 노트북 (Electronics, in_stock)
    #   - INV-002: 의자 (Furniture, in_stock)
    #   - INV-003: 도킹스테이션 (Electronics, out_of_stock)
    return []


# TODO: sample_policies fixture 추가
#   - tmp_path 사용하여 임시 마크다운 파일 2개 생성
#   - YAML front-matter 포함 (title, tags)
#   - PolicyDoc 리스트 반환


# ---------------------------------------------------------------------------
# 2단계: 환경 Fixture
# ---------------------------------------------------------------------------

# TODO: audit_logger fixture 추가
#   - tmp_path / "logs" 디렉토리로 AuditLogger 생성
#   - AuditLogger(log_dir=...) 형태


# ---------------------------------------------------------------------------
# 3단계: 통합 Fixture
# ---------------------------------------------------------------------------

# TODO: app_context fixture 추가
#   - sample_inventory, sample_policies, audit_logger 조합
#   - tickets_file: tmp_path / "tickets" / "tickets.jsonl"
#   - AppContext 인스턴스 반환
