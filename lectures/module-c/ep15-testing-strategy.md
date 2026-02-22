# EP 15 — 테스트 전략과 pytest 셋업

> Module C · 약 20분

## 학습 목표
1. MCP 서버 테스트의 특수성과 테스트 피라미드를 이해한다
2. pytest-asyncio와 fixture를 활용한 테스트 환경을 설계한다
3. 단위 테스트를 작성하고 커버리지를 확인한다

---

## 1. 인트로 (2분)

EP 5~14에서 우리는 Acme Corp Internal Ops Assistant의 핵심 기능을 모두 구현했습니다. 3개 Tool, 2개 Resource, 2개 Prompt, 입력 검증, 감사 로깅까지. 기능은 완성되었지만 한 가지 중요한 것이 빠져 있습니다 — **테스트**.

"동작하는 코드"와 "신뢰할 수 있는 코드"는 다릅니다. 코드를 수정할 때 기존 기능이 깨지지 않는다는 확신을 주는 것이 테스트의 역할입니다. 특히 MCP 서버는 비동기, 컨텍스트 의존, 파일 I/O 등 테스트가 까다로운 요소가 많습니다.

이번 편에서 테스트 전략을 세우고 pytest를 셋업합니다.

---

## 2. 핵심 개념 (6분)

### 2.1 MCP 서버 테스트의 특수성

MCP 서버는 일반적인 웹 서버와 다른 테스트 과제가 있습니다:

```
┌─────────────────────────────────────────────┐
│         MCP 서버 테스트 과제                  │
├─────────────────────────────────────────────┤
│                                             │
│  1. 비동기 (Async)                           │
│     - 모든 핸들러가 async 함수               │
│     - pytest-asyncio 필요                   │
│                                             │
│  2. 컨텍스트 의존 (Context)                   │
│     - mcp.get_context()로 AppContext 접근    │
│     - 테스트에서 컨텍스트를 모킹해야 함        │
│                                             │
│  3. 파일 I/O                                │
│     - CSV 읽기, JSONL 쓰기, Markdown 읽기   │
│     - tmp_path로 격리 필요                   │
│                                             │
│  4. 상태 관리                                │
│     - 티켓 번호 자동 증가                     │
│     - 테스트 간 상태 격리 필요                │
│                                             │
└─────────────────────────────────────────────┘
```

### 2.2 테스트 피라미드

```
           /\
          /  \           E2E 테스트
         / E2E\          (Claude Desktop에서 실제 사용)
        /──────\         → 느리지만 현실적
       /        \
      / 통합 테스트\      통합 테스트
     /  (EP 16)   \     (실제 MCP 서버 인스턴스)
    /──────────────\     → EP 16에서 다룸
   /                \
  /   단위 테스트     \   단위 테스트
 /    (이번 편)       \  (함수 레벨, 빠르고 격리됨)
/──────────────────────\ → 이번 편에서 다룸
```

이번 편에서는 피라미드 하단인 **단위 테스트**에 집중합니다:
- 개별 함수의 입출력을 검증
- 빠른 실행 (수 밀리초)
- 외부 의존성 없음 (모킹 사용)

### 2.3 pytest-asyncio 설정

MCP 핸들러가 모두 async이므로 pytest-asyncio가 필요합니다.

`pyproject.toml` 설정:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

`asyncio_mode = "auto"`를 설정하면 모든 async 테스트 함수가 자동으로 비동기로 실행됩니다. `@pytest.mark.asyncio` 데코레이터를 일일이 붙이지 않아도 됩니다.

### 2.4 Fixture 설계 전략

테스트의 핵심은 **fixture** 설계입니다. 테스트 데이터와 환경을 재사용 가능하게 만듭니다.

```python
# 데이터 Fixture — 테스트용 샘플 데이터
@pytest.fixture
def sample_inventory():
    return [...]

@pytest.fixture
def sample_policies():
    return [...]

# 환경 Fixture — 파일 시스템, 경로
@pytest.fixture
def data_dir(tmp_path):
    # tmp_path는 pytest 내장 fixture (임시 디렉토리)
    ...

# 통합 Fixture — AppContext 조립
@pytest.fixture
def app_context(sample_inventory, sample_policies, data_dir):
    return AppContext(...)
```

### 2.5 테스트 네이밍 컨벤션

```
tests/
├── conftest.py              # 공유 fixture
├── test_validation.py       # 입력 검증 테스트
├── test_security.py         # 보안 테스트 (EP 12)
├── test_inventory_tool.py   # 재고 검색 Tool 테스트
├── test_policy_tool.py      # 정책 검색 Tool 테스트
├── test_ticket_tool.py      # 티켓 생성 Tool 테스트
├── test_audit.py            # 감사 로깅 테스트
└── test_integration.py      # 통합 테스트 (EP 16)
```

파일명: `test_<모듈명>.py`
함수명: `test_<기능>_<시나리오>` (예: `test_lookup_inventory_returns_matching_items`)

---

## 3. 라이브 데모 (10분)

### Step 1: 의존성 설치

macOS/Linux:
```bash
cd ~/mcp-course/acme-ops-assistant
uv add --dev pytest pytest-asyncio pytest-cov
```

Windows (PowerShell):
```powershell
cd $HOME\mcp-course\acme-ops-assistant
uv add --dev pytest pytest-asyncio pytest-cov
```

### Step 2: conftest.py 작성

`tests/conftest.py`:

```python
"""공유 테스트 Fixture"""

import json
from pathlib import Path

import pytest

from models import AppContext, InventoryItem, PolicyDoc
from audit import AuditLogger


# ─── 데이터 Fixture ─────────────────────────────────────

@pytest.fixture
def sample_inventory():
    """테스트용 재고 아이템 목록"""
    return [
        InventoryItem(
            item_id="INV-001",
            name='MacBook Pro 14"',
            category="laptop",
            quantity=10,
            location="HQ-2F",
            status="in_stock",
            last_updated="2026-01-01",
        ),
        InventoryItem(
            item_id="INV-002",
            name="Dell UltraSharp 27 Monitor",
            category="monitor",
            quantity=5,
            location="HQ-3F",
            status="in_stock",
            last_updated="2026-01-01",
        ),
        InventoryItem(
            item_id="INV-003",
            name="Logitech MX Keys Keyboard",
            category="peripheral",
            quantity=0,
            location="HQ-2F",
            status="out_of_stock",
            last_updated="2026-01-01",
        ),
        InventoryItem(
            item_id="INV-004",
            name="HP LaserJet Pro Printer",
            category="printer",
            quantity=2,
            location="HQ-3F",
            status="in_stock",
            last_updated="2026-01-01",
        ),
    ]


@pytest.fixture
def sample_policies():
    """테스트용 정책 문서 목록"""
    return [
        PolicyDoc(
            doc_id="remote-work",
            title="원격근무 정책",
            tags=["remote", "wfh", "flexible"],
            content="# 원격근무 정책\n\n## 1. 적용 범위\n모든 정규직 직원에게 적용됩니다.\n\n## 2. VPN 사용\n원격근무 시 반드시 VPN을 사용해야 합니다.\n\n## 3. 근무 시간\n코어타임(10:00-16:00)은 반드시 근무해야 합니다.",
            last_updated="2026-01-15",
        ),
        PolicyDoc(
            doc_id="security",
            title="보안 정책",
            tags=["security", "compliance", "data"],
            content="# 보안 정책\n\n## 1. 비밀번호\n최소 12자, 대소문자+숫자+특수문자 조합.\n\n## 2. USB 사용\n개인 USB 사용 금지. 회사 승인 USB만 허용.",
            last_updated="2026-01-10",
        ),
        PolicyDoc(
            doc_id="equipment-management",
            title="장비 관리 정책",
            tags=["equipment", "asset", "management"],
            content="# 장비 관리 정책\n\n## 1. 장비 신청\nIT 포탈에서 신청서 작성 후 팀장 승인.\n\n## 2. 반납\n퇴직 시 모든 장비는 IT팀에 반납.",
            last_updated="2026-01-05",
        ),
    ]


# ─── 환경 Fixture ───────────────────────────────────────

@pytest.fixture
def data_dir(tmp_path):
    """테스트용 데이터 디렉토리 (tmp_path 기반)"""
    tickets_path = tmp_path / "tickets.jsonl"
    tickets_path.touch()  # 빈 파일 생성
    return tmp_path


@pytest.fixture
def log_dir(tmp_path):
    """테스트용 로그 디렉토리"""
    log_path = tmp_path / "logs"
    log_path.mkdir()
    return log_path


# ─── 통합 Fixture ───────────────────────────────────────

@pytest.fixture
def audit_logger(log_dir):
    """테스트용 AuditLogger (임시 디렉토리에 기록)"""
    return AuditLogger(log_dir=log_dir)


@pytest.fixture
def app_context(sample_inventory, sample_policies, data_dir, audit_logger):
    """테스트용 AppContext"""
    return AppContext(
        inventory=sample_inventory,
        policies=sample_policies,
        tickets_path=data_dir / "tickets.jsonl",
        audit_logger=audit_logger,
    )
```

### Step 3: 검증 함수 단위 테스트

`tests/test_validation.py`:

```python
"""입력 검증 함수 단위 테스트"""

import pytest
from validation import (
    validate_priority,
    validate_text_length,
    sanitize_query,
    validate_doc_id,
)


class TestValidatePriority:
    """우선순위 검증 테스트"""

    @pytest.mark.parametrize("valid", ["P1", "P2", "P3", "P4"])
    def test_valid_priorities(self, valid):
        assert validate_priority(valid) == valid

    @pytest.mark.parametrize("invalid", ["P0", "P5", "high", "", "p1"])
    def test_invalid_priorities(self, invalid):
        with pytest.raises(ValueError, match="priority"):
            validate_priority(invalid)


class TestValidateTextLength:
    """텍스트 길이 검증 테스트"""

    def test_valid_length(self):
        text = "정상적인 텍스트"
        assert validate_text_length(text, max_length=100) == text

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError):
            validate_text_length("", max_length=100)

    def test_too_long_rejected(self):
        with pytest.raises(ValueError):
            validate_text_length("a" * 1001, max_length=1000)

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValueError):
            validate_text_length("   ", max_length=100)


class TestSanitizeQuery:
    """쿼리 새니타이징 테스트"""

    def test_normal_query(self):
        assert sanitize_query("monitor") == "monitor"

    def test_strips_whitespace(self):
        assert sanitize_query("  monitor  ") == "monitor"

    def test_empty_query_rejected(self):
        with pytest.raises(ValueError):
            sanitize_query("")

    def test_too_long_query_rejected(self):
        with pytest.raises(ValueError):
            sanitize_query("a" * 201)
```

### Step 4: 감사 로깅 테스트

`tests/test_audit.py`:

```python
"""AuditLogger 단위 테스트"""

import json
from pathlib import Path

import pytest
from audit import AuditLogger


@pytest.fixture
def logger(tmp_path):
    return AuditLogger(log_dir=tmp_path)


class TestAuditLogger:
    """AuditLogger 테스트"""

    async def test_log_creates_file(self, logger):
        """로그 호출 시 파일이 생성되어야 한다."""
        await logger.log(
            action="tool_call",
            tool_name="test_tool",
            success=True,
        )
        assert logger.log_path.exists()

    async def test_log_entry_format(self, logger):
        """로그 엔트리가 올바른 JSON 형식이어야 한다."""
        await logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            input_summary={"query": "monitor"},
            result_summary="Found 3 items",
            success=True,
            duration_ms=12.45,
        )

        content = logger.log_path.read_text()
        entry = json.loads(content.strip())

        assert entry["action"] == "tool_call"
        assert entry["tool_name"] == "lookup_inventory"
        assert entry["input_summary"] == {"query": "monitor"}
        assert entry["success"] is True
        assert entry["duration_ms"] == 12.45
        assert "timestamp" in entry

    async def test_multiple_entries_appended(self, logger):
        """여러 로그가 같은 파일에 추가되어야 한다."""
        for i in range(5):
            await logger.log(
                action="tool_call",
                tool_name=f"tool_{i}",
                success=True,
            )

        lines = logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 5

    async def test_failed_log_entry(self, logger):
        """실패 로그에 에러 메시지가 포함되어야 한다."""
        await logger.log(
            action="tool_call",
            tool_name="create_ticket",
            success=False,
            error="Invalid priority",
        )

        content = logger.log_path.read_text()
        entry = json.loads(content.strip())

        assert entry["success"] is False
        assert entry["error"] == "Invalid priority"

    def test_timer(self, logger):
        """타이머가 양수 값을 반환해야 한다."""
        start = logger.start_timer()
        elapsed = logger.elapsed_ms(start)
        assert elapsed >= 0
```

### Step 5: 테스트 실행

macOS/Linux:
```bash
# 전체 테스트 실행
uv run pytest -v

# 커버리지 포함
uv run pytest --cov=src --cov-report=term-missing -v

# 특정 파일만 실행
uv run pytest tests/test_validation.py -v
```

Windows (PowerShell):
```powershell
# 전체 테스트 실행
uv run pytest -v

# 커버리지 포함
uv run pytest --cov=src --cov-report=term-missing -v

# 특정 파일만 실행
uv run pytest tests\test_validation.py -v
```

예상 출력:
```
tests/test_validation.py::TestValidatePriority::test_valid_priorities[P1] PASSED
tests/test_validation.py::TestValidatePriority::test_valid_priorities[P2] PASSED
tests/test_validation.py::TestValidatePriority::test_invalid_priorities[P0] PASSED
tests/test_audit.py::TestAuditLogger::test_log_creates_file PASSED
tests/test_audit.py::TestAuditLogger::test_log_entry_format PASSED
tests/test_audit.py::TestAuditLogger::test_multiple_entries_appended PASSED
tests/test_security.py::TestValidateDocId::test_path_traversal_blocked PASSED
...
==================== 25 passed in 0.3s ====================
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- MCP 서버는 비동기, 컨텍스트 의존, 파일 I/O 때문에 테스트에 특별한 고려가 필요
- 테스트 피라미드: 단위(빠르고 많이) → 통합(EP 16) → E2E(수동)
- `asyncio_mode = "auto"` 설정으로 모든 async 테스트 자동 실행
- `tmp_path` fixture로 파일 I/O를 격리하여 테스트 간 간섭 방지
- fixture 계층: 데이터 → 환경 → 통합(AppContext) 순서로 조립

### 퀴즈
1. `asyncio_mode = "auto"`의 효과는? → 모든 async 테스트 함수가 자동으로 비동기 이벤트 루프에서 실행되어 `@pytest.mark.asyncio`를 일일이 붙이지 않아도 된다
2. `tmp_path` fixture를 사용하는 이유는? → 각 테스트가 독립된 임시 디렉토리에서 파일 I/O를 수행하여 테스트 간 상태 오염을 방지한다
3. `pytest.mark.parametrize`의 장점은? → 같은 테스트 로직을 여러 입력값으로 반복 실행하여 코드 중복 없이 다양한 케이스를 검증할 수 있다

### 다음 편 예고
EP 16에서는 테스트 피라미드의 다음 단계인 **통합 테스트**를 작성합니다. 실제 MCP 서버 인스턴스를 띄워 전체 플로우를 검증하고, GitHub Actions CI 파이프라인을 구성합니다.
