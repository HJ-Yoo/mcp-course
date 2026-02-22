---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 15 — 테스트 전략과 pytest 셋업"
---

# EP 15 — 테스트 전략과 pytest 셋업
## Module C · MCP 실전 마스터

---

## 학습 목표

1. MCP 서버 테스트의 특수성과 테스트 피라미드
2. pytest-asyncio + fixture 기반 테스트 환경 설계
3. 단위 테스트 작성 및 커버리지 확인

---

## MCP 서버 테스트의 특수성

| 과제 | 설명 | 해결 |
|------|------|------|
| 비동기 | 모든 핸들러가 `async` | pytest-asyncio |
| 컨텍스트 의존 | `mcp.get_context()` | fixture로 모킹 |
| 파일 I/O | CSV, JSONL, Markdown | `tmp_path` fixture |
| 상태 관리 | 티켓 번호 자동 증가 | 테스트 간 격리 |

---

## 테스트 피라미드

```
           /\
          / E2E \         Claude Desktop 실제 사용
         /────────\
        /          \
       / 통합 테스트  \    실제 서버 인스턴스 (EP 16)
      /──────────────\
     /                \
    /   단위 테스트     \  함수 레벨, 빠르고 격리 (이번 편)
   /────────────────────\
```

이번 편: 단위 테스트 (빠르고, 많이)
다음 편: 통합 테스트 (느리지만, 현실적)

---

## pytest-asyncio 설정

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"    # 모든 async 함수 자동 실행
testpaths = ["tests"]
```

`asyncio_mode = "auto"` → `@pytest.mark.asyncio` 불필요

---

## Fixture 설계: 3 단계

```
1. 데이터 Fixture
   sample_inventory, sample_policies

2. 환경 Fixture
   data_dir (tmp_path), log_dir

3. 통합 Fixture
   app_context (위 두 fixture 조합)
```

작은 것 → 큰 것 순서로 조립

---

## 데이터 Fixture 예시

```python
@pytest.fixture
def sample_inventory():
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
            name="Dell Monitor 27",
            category="monitor",
            quantity=5, ...
        ),
    ]
```

---

## 환경 Fixture: tmp_path 활용

```python
@pytest.fixture
def data_dir(tmp_path):
    """각 테스트가 독립된 임시 디렉토리 사용"""
    tickets_path = tmp_path / "tickets.jsonl"
    tickets_path.touch()
    return tmp_path

@pytest.fixture
def audit_logger(tmp_path):
    log_path = tmp_path / "logs"
    log_path.mkdir()
    return AuditLogger(log_dir=log_path)
```

`tmp_path` = pytest 내장, 테스트 후 자동 삭제

---

## 통합 Fixture: AppContext

```python
@pytest.fixture
def app_context(sample_inventory, sample_policies,
                data_dir, audit_logger):
    return AppContext(
        inventory=sample_inventory,
        policies=sample_policies,
        tickets_path=data_dir / "tickets.jsonl",
        audit_logger=audit_logger,
    )
```

모든 테스트에서 **일관된 AppContext** 사용

---

## 단위 테스트: 입력 검증

```python
class TestValidatePriority:
    @pytest.mark.parametrize("valid", ["P1", "P2", "P3", "P4"])
    def test_valid_priorities(self, valid):
        assert validate_priority(valid) == valid

    @pytest.mark.parametrize("invalid",
        ["P0", "P5", "high", "", "p1"])
    def test_invalid_priorities(self, invalid):
        with pytest.raises(ValueError, match="priority"):
            validate_priority(invalid)
```

`parametrize` = 같은 로직, 여러 입력 반복 실행

---

## 단위 테스트: AuditLogger

```python
class TestAuditLogger:
    async def test_log_entry_format(self, logger):
        await logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            input_summary={"query": "monitor"},
            success=True,
            duration_ms=12.45,
        )
        content = logger.log_path.read_text()
        entry = json.loads(content.strip())

        assert entry["tool_name"] == "lookup_inventory"
        assert entry["success"] is True
        assert entry["duration_ms"] == 12.45
```

---

## 테스트 실행

```bash
# macOS/Linux
uv run pytest -v
uv run pytest --cov=src --cov-report=term-missing -v

# Windows
uv run pytest -v
uv run pytest --cov=src --cov-report=term-missing -v
```

```
test_validation.py ........         [ 40%]
test_security.py ...........        [ 75%]
test_audit.py .....                 [100%]

TOTAL coverage: 93%
==================== 25 passed in 0.3s ====================
```

---

## 테스트 파일 구조

```
tests/
├── conftest.py              # 공유 fixture
├── test_validation.py       # 입력 검증 테스트
├── test_security.py         # 보안 테스트 (EP 12)
├── test_audit.py            # 감사 로깅 테스트
├── test_inventory_tool.py   # 재고 검색 테스트
├── test_policy_tool.py      # 정책 검색 테스트
├── test_ticket_tool.py      # 티켓 생성 테스트
└── test_integration.py      # 통합 테스트 (EP 16)
```

---

## 핵심 정리

- MCP 서버: 비동기, 컨텍스트 의존 → 특별한 테스트 전략 필요
- `asyncio_mode = "auto"` → async 테스트 자동 실행
- `tmp_path` → 파일 I/O 격리
- Fixture 계층: 데이터 → 환경 → 통합(AppContext)
- `parametrize`로 다양한 케이스 효율적 검증

---

## 다음 편 예고

### EP 16: 통합 테스트로 서버 검증

- 전체 플로우 통합 테스트
- 시나리오 기반 테스트
- GitHub Actions CI 파이프라인
