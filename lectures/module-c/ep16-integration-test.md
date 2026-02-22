# EP 16 — 통합 테스트로 서버 검증

> Module C · 약 20분

## 학습 목표
1. 통합 테스트와 단위 테스트의 차이를 설명하고, 실제 MCP 서버를 테스트한다
2. 시나리오 기반 통합 테스트를 작성하여 전체 플로우를 검증한다
3. GitHub Actions CI 파이프라인을 구성한다

---

## 1. 인트로 (2분)

EP 15에서 pytest 환경을 세팅하고 단위 테스트를 작성했습니다. 개별 함수들이 올바르게 동작하는 것을 확인했죠.

하지만 각 함수가 개별적으로 잘 동작한다고 해서, **함께 동작할 때도** 잘 동작한다는 보장은 없습니다. 재고 검색 결과가 정책 조회와 연결되고, 그 결과로 티켓이 생성되는 전체 플로우 — 이걸 검증하려면 **통합 테스트**가 필요합니다.

이번 편에서는 실제 MCP 서버 인스턴스를 사용하는 통합 테스트를 작성하고, CI에서 자동으로 실행되는 파이프라인을 구성합니다.

---

## 2. 핵심 개념 (6분)

### 2.1 단위 테스트 vs 통합 테스트

```
단위 테스트 (EP 15)                통합 테스트 (이번 편)
──────────────                    ──────────────
개별 함수 테스트                    전체 시스템 테스트
의존성 모킹                        실제 의존성 사용
빠른 실행 (ms)                     느린 실행 (초)
격리된 환경                        실제 서버 인스턴스
"이 함수가 맞는가?"                 "시스템이 동작하는가?"
```

### 2.2 MCP SDK의 테스트 유틸리티

MCP Python SDK는 테스트를 위한 클라이언트 세션을 제공합니다:

```python
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# 또는 in-memory transport 활용
from mcp.server.stdio import stdio_server
```

통합 테스트에서는 실제 MCP 서버를 인스턴스화하고, 클라이언트로 연결하여 Tool, Resource, Prompt를 호출합니다.

### 2.3 시나리오 기반 테스트

실제 사용자 워크플로우를 시뮬레이션합니다:

```
시나리오: "사용자가 장비를 검색하고, 정책을 확인하고, 티켓을 생성한다"

Step 1: lookup_inventory("printer") → 프린터 재고 확인
Step 2: policy://equipment-management → 장비 관리 정책 확인
Step 3: create_ticket("프린터 수리 요청", ...) → 티켓 생성
Step 4: 감사 로그에 3개 엔트리 기록 확인
```

### 2.4 Test Isolation

통합 테스트에서 가장 중요한 원칙 — 각 테스트가 독립적으로 실행되어야 합니다:

```
┌────────────────────────────────────────────────┐
│             Test Isolation 전략                  │
├────────────────────────────────────────────────┤
│                                                │
│  1. 파일 시스템: tmp_path로 매 테스트 격리       │
│  2. 데이터: fixture로 매번 새 데이터 생성        │
│  3. 서버: 매 테스트마다 새 서버 인스턴스          │
│  4. 로그: 별도 로그 디렉토리                     │
│                                                │
│  → 테스트 실행 순서에 무관하게 동일 결과          │
└────────────────────────────────────────────────┘
```

### 2.5 CI/CD 파이프라인

코드가 변경될 때마다 자동으로 테스트를 실행하는 것이 CI(Continuous Integration)입니다:

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Push   │ →  │  Lint    │ →  │  Test    │ →  │  Report  │
│  코드    │    │  코드검사 │    │  테스트   │    │  결과보고 │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 3. 라이브 데모 (10분)

### Step 1: 통합 테스트 fixture 준비

`tests/conftest.py`에 통합 테스트용 fixture를 추가합니다:

```python
# ─── 통합 테스트 Fixture ────────────────────────────────

import csv
from contextlib import asynccontextmanager


@pytest.fixture
def inventory_csv(data_dir):
    """테스트용 inventory.csv 파일 생성"""
    csv_path = data_dir / "inventory.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "item_id", "name", "category", "quantity",
            "location", "status", "last_updated"
        ])
        writer.writerow([
            "INV-001", "MacBook Pro 14\"", "laptop", "10",
            "HQ-2F", "in_stock", "2026-01-01"
        ])
        writer.writerow([
            "INV-002", "Dell Monitor 27\"", "monitor", "5",
            "HQ-3F", "in_stock", "2026-01-01"
        ])
        writer.writerow([
            "INV-003", "HP Printer", "printer", "2",
            "HQ-3F", "in_stock", "2026-01-01"
        ])
    return csv_path


@pytest.fixture
def policy_dir(data_dir):
    """테스트용 정책 문서 디렉토리 생성"""
    policies = data_dir / "policies"
    policies.mkdir()

    (policies / "remote-work.md").write_text(
        "# 원격근무 정책\n\n## VPN\n반드시 VPN을 사용해야 합니다.\n\n## 코어타임\n10:00-16:00",
        encoding="utf-8",
    )
    (policies / "security.md").write_text(
        "# 보안 정책\n\n## USB\n개인 USB 사용 금지.\n\n## 비밀번호\n최소 12자 이상.",
        encoding="utf-8",
    )

    return policies
```

### Step 2: 통합 테스트 작성

`tests/test_integration.py`:

```python
"""통합 테스트 — 실제 MCP 서버 인스턴스를 사용한 전체 플로우 검증"""

import json
from pathlib import Path

import pytest


class TestInventoryWorkflow:
    """재고 검색 워크플로우 통합 테스트"""

    async def test_search_and_find_items(self, app_context):
        """재고 검색 시 매칭되는 아이템을 반환해야 한다."""
        from tools.inventory_tool import _search_inventory

        results = _search_inventory(app_context.inventory, "monitor")
        assert len(results) >= 1
        assert any("monitor" in item.name.lower() for item in results)

    async def test_search_no_results(self, app_context):
        """매칭되는 아이템이 없으면 빈 목록을 반환해야 한다."""
        from tools.inventory_tool import _search_inventory

        results = _search_inventory(app_context.inventory, "spaceship")
        assert len(results) == 0


class TestPolicyResourceWorkflow:
    """정책 Resource 워크플로우 통합 테스트"""

    async def test_policy_index_lists_all(self, app_context):
        """policy://index는 모든 정책을 나열해야 한다."""
        policies = app_context.policies
        assert len(policies) == 3
        doc_ids = [p.doc_id for p in policies]
        assert "remote-work" in doc_ids
        assert "security" in doc_ids

    async def test_policy_detail_returns_content(self, app_context):
        """policy://{doc_id}는 해당 정책의 내용을 반환해야 한다."""
        policy = next(
            p for p in app_context.policies if p.doc_id == "remote-work"
        )
        assert "VPN" in policy.content
        assert "원격근무" in policy.title


class TestTicketCreationWorkflow:
    """티켓 생성 워크플로우 통합 테스트"""

    async def test_create_and_persist_ticket(self, app_context):
        """티켓 생성 시 JSONL 파일에 기록되어야 한다."""
        ticket_data = {
            "title": "프린터 수리 요청",
            "description": "3층 HP 프린터가 용지 걸림 발생",
            "priority": "P3",
        }

        # 티켓 파일에 직접 기록 (Tool 시뮬레이션)
        ticket = {
            "ticket_id": "TKT-0001",
            **ticket_data,
            "status": "open",
            "created_at": "2026-01-15T09:30:00",
        }

        with open(app_context.tickets_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ticket, ensure_ascii=False) + "\n")

        # 파일에서 읽어서 검증
        content = app_context.tickets_path.read_text(encoding="utf-8")
        saved_ticket = json.loads(content.strip())
        assert saved_ticket["ticket_id"] == "TKT-0001"
        assert saved_ticket["title"] == "프린터 수리 요청"
        assert saved_ticket["priority"] == "P3"

    async def test_multiple_tickets_appended(self, app_context):
        """여러 티켓이 순서대로 추가되어야 한다."""
        for i in range(3):
            ticket = {
                "ticket_id": f"TKT-{i+1:04d}",
                "title": f"테스트 티켓 {i+1}",
                "priority": "P3",
            }
            with open(app_context.tickets_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ticket, ensure_ascii=False) + "\n")

        lines = app_context.tickets_path.read_text().strip().split("\n")
        assert len(lines) == 3


class TestAuditLoggingWorkflow:
    """감사 로깅 워크플로우 통합 테스트"""

    async def test_audit_records_tool_calls(self, app_context):
        """Tool 호출이 감사 로그에 기록되어야 한다."""
        logger = app_context.audit_logger

        # 여러 Tool 호출 시뮬레이션
        await logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            input_summary={"query": "monitor"},
            result_summary="Found 1 item",
            success=True,
            duration_ms=10.5,
        )
        await logger.log(
            action="tool_call",
            tool_name="create_ticket",
            input_summary={"title": "프린터 수리"},
            result_summary="TKT-0001 created",
            success=True,
            duration_ms=25.3,
        )

        # 로그 파일 검증
        lines = logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        first = json.loads(lines[0])
        assert first["tool_name"] == "lookup_inventory"
        assert first["success"] is True

        second = json.loads(lines[1])
        assert second["tool_name"] == "create_ticket"

    async def test_audit_records_failures(self, app_context):
        """실패한 호출도 감사 로그에 기록되어야 한다."""
        logger = app_context.audit_logger

        await logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            input_summary={"query": "../etc/passwd"},
            success=False,
            error="Invalid query: path traversal detected",
        )

        content = logger.log_path.read_text()
        entry = json.loads(content.strip())
        assert entry["success"] is False
        assert "path traversal" in entry["error"]


class TestEndToEndScenario:
    """E2E 시나리오: 장비 검색 → 정책 확인 → 티켓 생성 → 로그 확인"""

    async def test_full_workflow(self, app_context):
        """전체 워크플로우가 정상적으로 동작해야 한다."""
        logger = app_context.audit_logger

        # Step 1: 재고 검색
        results = [
            item for item in app_context.inventory
            if "printer" in item.name.lower() or item.category == "printer"
        ]
        assert len(results) >= 1

        await logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            input_summary={"query": "printer"},
            result_summary=f"Found {len(results)} items",
            success=True,
        )

        # Step 2: 정책 확인
        policy = next(
            (p for p in app_context.policies if p.doc_id == "equipment-management"),
            None,
        )
        assert policy is not None

        # Step 3: 티켓 생성
        ticket = {
            "ticket_id": "TKT-0001",
            "title": "프린터 수리 요청",
            "description": "3층 HP 프린터 수리 필요",
            "priority": "P3",
        }
        with open(app_context.tickets_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ticket, ensure_ascii=False) + "\n")

        await logger.log(
            action="tool_call",
            tool_name="create_ticket",
            input_summary={"title": ticket["title"]},
            result_summary=f"Ticket {ticket['ticket_id']} created",
            success=True,
        )

        # Step 4: 로그 검증
        lines = logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 2
        tool_names = [json.loads(l)["tool_name"] for l in lines]
        assert "lookup_inventory" in tool_names
        assert "create_ticket" in tool_names
```

### Step 3: GitHub Actions CI 구성

`.github/workflows/test.yml`:

```yaml
name: MCP Server Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --dev

      - name: Run linting
        run: uv run ruff check src/ tests/

      - name: Run tests
        run: uv run pytest --tb=short -v

      - name: Run tests with coverage
        run: uv run pytest --cov=src --cov-report=xml -v

      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

### Step 4: 전체 테스트 실행

macOS/Linux:
```bash
# 전체 테스트 (단위 + 통합)
uv run pytest -v --tb=short

# 통합 테스트만 실행
uv run pytest tests/test_integration.py -v

# 커버리지 리포트
uv run pytest --cov=src --cov-report=term-missing
```

Windows (PowerShell):
```powershell
# 전체 테스트 (단위 + 통합)
uv run pytest -v --tb=short

# 통합 테스트만 실행
uv run pytest tests\test_integration.py -v

# 커버리지 리포트
uv run pytest --cov=src --cov-report=term-missing
```

예상 출력:
```
tests/test_validation.py ........                   [ 25%]
tests/test_security.py ...........                  [ 50%]
tests/test_audit.py .....                           [ 65%]
tests/test_integration.py .........                 [ 100%]

---------- coverage: platform darwin, python 3.12 ----------
Name                          Stmts   Miss  Cover   Missing
------------------------------------------------------------
src/audit.py                     35      2    94%   48-49
src/validation.py                28      0   100%
src/models.py                    15      0   100%
------------------------------------------------------------
TOTAL                           178     12    93%

==================== 30 passed in 1.2s ====================
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- 통합 테스트는 여러 컴포넌트가 함께 동작하는 것을 검증 (단위 테스트의 다음 단계)
- 시나리오 기반 테스트로 실제 사용자 워크플로우를 시뮬레이션
- Test isolation: tmp_path, fixture로 테스트 간 독립성 보장
- GitHub Actions CI로 코드 변경 시 자동 테스트 (멀티 OS, 멀티 Python)
- 커버리지 리포트로 테스트되지 않은 코드 식별

### 퀴즈
1. 통합 테스트에서 tmp_path를 사용하는 이유는? → 각 테스트가 독립된 파일 시스템 환경에서 실행되어, 이전 테스트의 티켓 파일이나 로그 파일이 다음 테스트에 영향을 주지 않도록 하기 위함
2. CI에서 멀티 OS 매트릭스를 설정하는 이유는? → 파일 경로 구분자(`/` vs `\`), 줄 끝 문자 등 OS별 차이로 인한 버그를 조기에 발견하기 위함
3. 테스트 커버리지 93%에서 남은 7%는 어떻게 해야 하는가? → 100%가 목표가 아니라 의미 있는 코드가 테스트되었는지가 중요. 에러 핸들링, 엣지 케이스 등 누락된 부분을 확인하고 필요시 추가

### 다음 편 예고
EP 17부터는 **Module D: 배포와 통합**에 진입합니다. 지금까지 stdio 모드로 로컬에서 실행했던 서버를 **Streamable HTTP Transport**로 전환하여 원격 접속, 다중 클라이언트, 로드밸런싱을 가능하게 만듭니다.
