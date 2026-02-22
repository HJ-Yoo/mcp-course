# EP 14 — 감사 로깅 (Audit Logging)

> Module C · 약 20분

## 학습 목표
1. AI 도구에서 감사 로깅이 필요한 이유를 설명할 수 있다
2. Thread-safe한 JSONL 기반 AuditLogger를 구현한다
3. 기존 Tool에 감사 로깅을 통합하고 로그를 분석한다

---

## 1. 인트로 (2분)

EP 5~13까지 3개의 Tool, 2개의 Resource, 2개의 Prompt를 구현했습니다. 기능적으로는 잘 동작하지만, 한 가지 빠진 것이 있습니다.

"누가, 언제, 어떤 도구를, 어떤 입력으로, 어떤 결과를 받았는지" — 아무도 기록하고 있지 않습니다.

기업 환경에서 AI 도구를 운영하려면 **감사 로깅(Audit Logging)** 은 선택이 아닌 필수입니다. 규정 준수, 보안 감사, 장애 디버깅, 사용 패턴 분석 — 모두 로그에서 시작됩니다.

---

## 2. 핵심 개념 (6분)

### 2.1 왜 감사 로깅인가?

```
┌─────────────────────────────────────────────────┐
│            감사 로깅이 필요한 이유                │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 규정 준수 (Compliance)                       │
│     - AI 도구 사용 내역 감사 가능                 │
│     - GDPR, SOC2 등 규제 요건 충족               │
│                                                 │
│  2. 보안 (Security)                              │
│     - 이상 행동 탐지 (비정상적 요청 패턴)          │
│     - 사고 발생 시 원인 추적                      │
│                                                 │
│  3. 디버깅 (Debugging)                           │
│     - 에러 재현 및 원인 분석                      │
│     - 입력/출력 쌍으로 문제 격리                   │
│                                                 │
│  4. 분석 (Analytics)                             │
│     - 가장 많이 사용되는 도구 파악                 │
│     - 사용 패턴 기반 서비스 개선                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2.2 JSONL 포맷의 장점

감사 로그에는 **JSONL(JSON Lines)** 포맷이 적합합니다:

```jsonl
{"timestamp":"2026-01-15T09:30:00","action":"tool_call","tool":"lookup_inventory","input":{"query":"monitor"},"success":true}
{"timestamp":"2026-01-15T09:30:05","action":"tool_call","tool":"create_ticket","input":{"title":"프린터 수리"},"success":true}
{"timestamp":"2026-01-15T09:31:00","action":"tool_call","tool":"lookup_inventory","input":{"query":"../etc"},"success":false}
```

JSONL의 특성:
- **한 줄 = 한 레코드**: 파싱이 간단하고 스트리밍 처리 가능
- **Append-only**: 파일 끝에 추가만 하므로 고성능
- **독립적 레코드**: 한 줄이 손상되어도 다른 줄에 영향 없음
- **도구 호환**: `jq`, `grep`, Python 등으로 쉽게 분석

### 2.3 로그 스키마 설계

각 로그 엔트리에 포함할 필드:

```python
{
    "timestamp": "2026-01-15T09:30:00.123456",  # ISO 형식
    "action": "tool_call",                       # 동작 유형
    "tool_name": "lookup_inventory",             # 도구 이름
    "input_summary": {"query": "monitor"},       # 입력 요약
    "result_summary": "Found 3 items",           # 결과 요약
    "success": True,                             # 성공/실패
    "error": None,                               # 에러 메시지 (실패 시)
    "duration_ms": 45,                           # 처리 시간(ms)
}
```

**주의**: 민감한 데이터(비밀번호, 개인정보)는 로그에 포함하지 않습니다. `input_summary`는 전체 입력이 아닌 요약만 포함합니다.

### 2.4 Thread Safety

MCP 서버는 비동기(async)로 동작하며 여러 요청을 동시에 처리할 수 있습니다. 로그 파일에 동시에 쓰면 데이터가 섞일 수 있으므로 thread-safe한 구현이 필요합니다.

```python
import asyncio

class AuditLogger:
    def __init__(self, log_path):
        self._lock = asyncio.Lock()  # 비동기 락
        self._log_path = log_path

    async def log(self, entry):
        async with self._lock:  # 동시 쓰기 방지
            with open(self._log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
```

---

## 3. 라이브 데모 (10분)

### Step 1: AuditLogger 구현

`src/audit.py` 파일을 생성합니다:

```python
"""감사 로깅 모듈 — Thread-safe JSONL 기반 AuditLogger"""

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    """Thread-safe한 JSONL 감사 로거.

    모든 Tool 호출을 기록하여 규정 준수와 디버깅을 지원합니다.
    """

    def __init__(self, log_dir: str | Path = "logs"):
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    @property
    def log_path(self) -> Path:
        """오늘 날짜의 로그 파일 경로를 반환합니다."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self._log_dir / f"audit_{today}.jsonl"

    async def log(
        self,
        action: str,
        tool_name: str,
        input_summary: dict[str, Any] | None = None,
        result_summary: str | None = None,
        success: bool = True,
        error: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """감사 로그 엔트리를 기록합니다.

        Args:
            action: 동작 유형 (tool_call, resource_access, error 등)
            tool_name: 도구 또는 리소스 이름
            input_summary: 입력 파라미터 요약 (민감 정보 제외)
            result_summary: 결과 요약 문자열
            success: 성공 여부
            error: 에러 메시지 (실패 시)
            duration_ms: 처리 시간 (밀리초)
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "tool_name": tool_name,
            "input_summary": input_summary or {},
            "result_summary": result_summary,
            "success": success,
            "error": error,
            "duration_ms": duration_ms,
        }

        async with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def start_timer(self) -> float:
        """타이머를 시작합니다. log()의 duration_ms에 사용합니다."""
        return time.monotonic()

    def elapsed_ms(self, start: float) -> float:
        """시작 시점부터 경과 시간을 밀리초로 반환합니다."""
        return round((time.monotonic() - start) * 1000, 2)
```

### Step 2: AppContext에 AuditLogger 추가

`src/models.py`의 AppContext에 audit_logger를 추가합니다:

```python
from audit import AuditLogger

@dataclass
class AppContext:
    inventory: list[InventoryItem]
    policies: list[PolicyDoc]
    tickets_path: Path
    audit_logger: AuditLogger  # 추가!
```

`src/server.py`의 lifespan에서 초기화:

```python
@asynccontextmanager
async def app_lifespan(server):
    audit_logger = AuditLogger(log_dir="logs")
    app = AppContext(
        inventory=load_inventory(),
        policies=load_policies(),
        tickets_path=Path("data/tickets.jsonl"),
        audit_logger=audit_logger,  # 추가!
    )
    yield {"app": app}
```

### Step 3: Tool에 감사 로깅 통합

`src/tools/inventory_tool.py`에 로깅을 추가합니다:

```python
def register(mcp):

    @mcp.tool()
    async def lookup_inventory(query: str) -> str:
        """IT 장비 재고를 검색합니다."""
        ctx = mcp.get_context()
        app = ctx.request_context.lifespan_context["app"]
        logger = app.audit_logger

        start = logger.start_timer()

        try:
            query = sanitize_query(query)
            results = fuzzy_search(app.inventory, query)

            await logger.log(
                action="tool_call",
                tool_name="lookup_inventory",
                input_summary={"query": query},
                result_summary=f"Found {len(results)} items",
                success=True,
                duration_ms=logger.elapsed_ms(start),
            )

            return format_results(results)

        except Exception as e:
            await logger.log(
                action="tool_call",
                tool_name="lookup_inventory",
                input_summary={"query": query},
                success=False,
                error=str(e),
                duration_ms=logger.elapsed_ms(start),
            )
            raise
```

`create_ticket`에도 동일 패턴을 적용합니다:

```python
@mcp.tool()
async def create_ticket(title: str, description: str, priority: str) -> str:
    """IT 지원 티켓을 생성합니다."""
    ctx = mcp.get_context()
    app = ctx.request_context.lifespan_context["app"]
    logger = app.audit_logger

    start = logger.start_timer()

    try:
        # ... 기존 로직 ...
        await logger.log(
            action="tool_call",
            tool_name="create_ticket",
            input_summary={"title": title, "priority": priority},
            result_summary=f"Ticket {ticket_id} created",
            success=True,
            duration_ms=logger.elapsed_ms(start),
        )
        return result

    except Exception as e:
        await logger.log(
            action="tool_call",
            tool_name="create_ticket",
            input_summary={"title": title, "priority": priority},
            success=False,
            error=str(e),
            duration_ms=logger.elapsed_ms(start),
        )
        raise
```

### Step 4: 로그 확인 및 분석

서버를 실행하고 여러 Tool을 호출한 후 로그를 분석합니다.

macOS/Linux:
```bash
# 로그 파일 내용 확인 (읽기 좋게 포맷팅)
cat logs/audit_2026-01-15.jsonl | python3 -m json.tool --json-lines

# jq로 실패한 요청만 필터링
cat logs/audit_2026-01-15.jsonl | jq 'select(.success == false)'

# 도구별 호출 횟수
cat logs/audit_2026-01-15.jsonl | jq -r '.tool_name' | sort | uniq -c | sort -rn

# 평균 응답 시간
cat logs/audit_2026-01-15.jsonl | jq '[.duration_ms] | add / length'
```

Windows (PowerShell):
```powershell
# 로그 파일 내용 확인
Get-Content logs\audit_2026-01-15.jsonl | ForEach-Object { $_ | ConvertFrom-Json } | Format-List

# 실패한 요청만 필터링
Get-Content logs\audit_2026-01-15.jsonl | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.success -eq $false }

# 도구별 호출 횟수
Get-Content logs\audit_2026-01-15.jsonl | ForEach-Object { ($_ | ConvertFrom-Json).tool_name } | Group-Object | Sort-Object Count -Descending
```

### Step 5: 실제 로그 예시

여러 시나리오를 실행하면 다음과 같은 로그가 생성됩니다:

```jsonl
{"timestamp":"2026-01-15T00:30:00.123456+00:00","action":"tool_call","tool_name":"lookup_inventory","input_summary":{"query":"monitor"},"result_summary":"Found 3 items","success":true,"error":null,"duration_ms":12.45}
{"timestamp":"2026-01-15T00:30:15.789012+00:00","action":"tool_call","tool_name":"search_policy","input_summary":{"query":"remote work vpn"},"result_summary":"Found 2 policies","success":true,"error":null,"duration_ms":8.23}
{"timestamp":"2026-01-15T00:30:30.456789+00:00","action":"tool_call","tool_name":"create_ticket","input_summary":{"title":"프린터 수리 요청","priority":"P3"},"result_summary":"Ticket TKT-0042 created","success":true,"error":null,"duration_ms":25.67}
{"timestamp":"2026-01-15T00:31:00.111111+00:00","action":"tool_call","tool_name":"lookup_inventory","input_summary":{"query":"../etc/passwd"},"success":false,"error":"Invalid query: contains path traversal pattern","duration_ms":1.23}
```

네 번째 줄에서 path traversal 시도가 기록되었습니다. 이런 보안 이벤트를 모니터링할 수 있습니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- 감사 로깅은 AI 도구 운영에서 규정 준수, 보안, 디버깅을 위해 필수
- JSONL 포맷은 append-only, 스트리밍 파싱, 도구 호환성이 뛰어남
- AuditLogger는 asyncio.Lock으로 thread-safe하게 구현
- 각 Tool에 try/except로 성공/실패 모두 기록
- `jq` 등의 도구로 로그 분석 가능 (실패 필터, 통계 등)

### 퀴즈
1. JSONL 포맷이 일반 JSON 배열보다 로깅에 적합한 이유는? → JSONL은 append-only로 기존 내용을 읽지 않고 끝에 추가만 하면 되어 고성능이고, 한 줄 손상이 전체 파일에 영향을 주지 않는다
2. `input_summary`에 전체 입력이 아닌 요약만 기록하는 이유는? → 민감한 데이터(개인정보, 비밀번호 등)가 로그에 포함되는 것을 방지하고, 로그 파일 크기를 관리하기 위함
3. `asyncio.Lock`이 필요한 이유는? → MCP 서버가 여러 요청을 동시에 비동기 처리하므로, 동시에 같은 파일에 쓰면 데이터가 섞일 수 있기 때문

### 다음 편 예고
EP 15에서는 **테스트 전략과 pytest 셋업**을 다룹니다. MCP 서버의 비동기 특성, 컨텍스트 의존성, 파일 I/O를 고려한 테스트 전략을 세우고, pytest fixture를 설계합니다.
