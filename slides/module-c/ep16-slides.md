---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 16 — 통합 테스트로 서버 검증"
---

# EP 16 — 통합 테스트로 서버 검증
## Module C · MCP 실전 마스터

---

## 학습 목표

1. 통합 테스트와 단위 테스트의 차이 이해
2. 시나리오 기반 통합 테스트 작성
3. GitHub Actions CI 파이프라인 구성

---

## 단위 vs 통합 테스트

| 구분 | 단위 테스트 (EP 15) | 통합 테스트 (이번 편) |
|------|-------------------|-------------------|
| 대상 | 개별 함수 | 전체 시스템 |
| 의존성 | 모킹 | 실제 사용 |
| 속도 | 빠름 (ms) | 느림 (초) |
| 환경 | 격리 | 실제 서버 인스턴스 |
| 질문 | "이 함수가 맞는가?" | "시스템이 동작하는가?" |

---

## 시나리오 기반 테스트

```
시나리오: 장비 검색 → 정책 확인 → 티켓 생성

Step 1: lookup_inventory("printer")
        → 프린터 재고 확인

Step 2: policy://equipment-management
        → 장비 관리 정책 확인

Step 3: create_ticket("프린터 수리 요청", ...)
        → 티켓 생성

Step 4: 감사 로그에 3개 엔트리 기록 확인
```

---

## Test Isolation 전략

```
1. 파일 시스템  → tmp_path로 매 테스트 격리
2. 데이터       → fixture로 매번 새 데이터 생성
3. 서버         → 매 테스트마다 새 인스턴스
4. 로그         → 별도 로그 디렉토리
```

**테스트 실행 순서와 무관하게 동일한 결과**

---

## 통합 테스트: 재고 검색

```python
class TestInventoryWorkflow:
    async def test_search_and_find_items(self, app_context):
        results = [
            item for item in app_context.inventory
            if "monitor" in item.name.lower()
        ]
        assert len(results) >= 1
        assert any(
            "monitor" in item.name.lower()
            for item in results
        )

    async def test_search_no_results(self, app_context):
        results = [
            item for item in app_context.inventory
            if "spaceship" in item.name.lower()
        ]
        assert len(results) == 0
```

---

## 통합 테스트: 티켓 생성

```python
class TestTicketCreationWorkflow:
    async def test_create_and_persist(self, app_context):
        ticket = {
            "ticket_id": "TKT-0001",
            "title": "프린터 수리 요청",
            "priority": "P3",
            "status": "open",
        }
        with open(app_context.tickets_path, "a") as f:
            f.write(json.dumps(ticket) + "\n")

        content = app_context.tickets_path.read_text()
        saved = json.loads(content.strip())
        assert saved["ticket_id"] == "TKT-0001"
```

---

## 통합 테스트: E2E 시나리오

```python
class TestEndToEndScenario:
    async def test_full_workflow(self, app_context):
        logger = app_context.audit_logger

        # Step 1: 재고 검색
        results = [i for i in app_context.inventory
                   if i.category == "printer"]
        assert len(results) >= 1
        await logger.log(action="tool_call",
            tool_name="lookup_inventory", success=True)

        # Step 2: 정책 확인
        policy = next(p for p in app_context.policies
                      if p.doc_id == "equipment-management")
        assert policy is not None

        # Step 3: 티켓 생성 + 로그 확인
        await logger.log(action="tool_call",
            tool_name="create_ticket", success=True)

        lines = logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 2
```

---

## GitHub Actions CI

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
      - uses: astral-sh/setup-uv@v4
      - run: uv python install ${{ matrix.python-version }}
      - run: uv sync --dev
      - run: uv run pytest --tb=short -v
```

---

## CI 매트릭스의 가치

```
        ubuntu    macOS    Windows
py3.11   ✅        ✅        ✅
py3.12   ✅        ✅        ✅
```

- 파일 경로 구분자 (`/` vs `\`)
- 줄 끝 문자 (LF vs CRLF)
- OS별 파일 시스템 동작 차이

**크로스 플랫폼 버그를 조기 발견**

---

## 테스트 실행

```bash
# 전체 테스트 (단위 + 통합)
uv run pytest -v --tb=short

# 통합 테스트만
uv run pytest tests/test_integration.py -v

# 커버리지 리포트
uv run pytest --cov=src --cov-report=term-missing
```

```
test_validation.py ........       [ 25%]
test_security.py ...........      [ 50%]
test_audit.py .....               [ 65%]
test_integration.py ..........    [100%]
==================== 30+ passed ====================
```

---

## 핵심 정리

- 통합 테스트: 여러 컴포넌트가 **함께** 동작하는 것 검증
- 시나리오 기반: 실제 사용자 워크플로우 시뮬레이션
- Test isolation: `tmp_path` + fixture → 독립성 보장
- GitHub Actions CI: 멀티 OS, 멀티 Python 자동 테스트
- 커버리지 리포트로 미검증 코드 식별

---

## 다음 편 예고

### EP 17: Streamable HTTP Transport (Module D 시작!)

- stdio의 한계
- Streamable HTTP 전환
- 원격 접속, 다중 클라이언트 지원
