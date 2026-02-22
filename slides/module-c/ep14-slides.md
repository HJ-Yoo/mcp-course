---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 14 — 감사 로깅 (Audit Logging)"
---

# EP 14 — 감사 로깅 (Audit Logging)
## Module C · MCP 실전 마스터

---

## 학습 목표

1. AI 도구에서 감사 로깅이 필요한 이유
2. Thread-safe JSONL 기반 AuditLogger 구현
3. Tool에 감사 로깅 통합 및 로그 분석

---

## 왜 감사 로깅인가?

| 목적 | 설명 |
|------|------|
| **규정 준수** | AI 도구 사용 내역 감사, GDPR/SOC2 |
| **보안** | 이상 행동 탐지, 사고 원인 추적 |
| **디버깅** | 에러 재현, 입/출력 쌍 분석 |
| **분석** | 사용 패턴, 서비스 개선 |

"누가, 언제, 어떤 도구를, 어떤 입력으로, 어떤 결과를 받았는지"

---

## JSONL 포맷의 장점

```jsonl
{"timestamp":"...","tool":"lookup_inventory","success":true}
{"timestamp":"...","tool":"create_ticket","success":true}
{"timestamp":"...","tool":"lookup_inventory","success":false}
```

- **한 줄 = 한 레코드** → 파싱 간단
- **Append-only** → 고성능 쓰기
- **독립적 레코드** → 한 줄 손상해도 다른 줄 영향 없음
- **도구 호환** → `jq`, `grep`, Python으로 분석

---

## 로그 스키마

```python
{
    "timestamp": "2026-01-15T09:30:00.123456",
    "action": "tool_call",
    "tool_name": "lookup_inventory",
    "input_summary": {"query": "monitor"},
    "result_summary": "Found 3 items",
    "success": True,
    "error": None,
    "duration_ms": 45,
}
```

**주의**: 민감 데이터는 `input_summary`에 포함하지 않음

---

## AuditLogger 핵심 구현

```python
class AuditLogger:
    def __init__(self, log_dir="logs"):
        self._log_dir = Path(log_dir)
        self._lock = asyncio.Lock()  # thread-safe

    async def log(self, action, tool_name, **kwargs):
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "tool_name": tool_name,
            **kwargs,
        }
        async with self._lock:  # 동시 쓰기 방지
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
```

---

## Thread Safety가 필요한 이유

```
요청 A → lookup_inventory → 로그 쓰기 ─┐
                                        ├→ 파일이 섞임!
요청 B → create_ticket    → 로그 쓰기 ─┘

asyncio.Lock()으로 해결:
요청 A → 로그 쓰기 (lock 획득) → 완료
요청 B → 대기 → 로그 쓰기 (lock 획득) → 완료
```

MCP 서버는 여러 요청을 동시 처리하므로 **Lock 필수**

---

## Tool에 감사 로깅 통합

```python
@mcp.tool()
async def lookup_inventory(query: str) -> str:
    logger = app.audit_logger
    start = logger.start_timer()

    try:
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
            action="tool_call", tool_name="lookup_inventory",
            success=False, error=str(e),
            duration_ms=logger.elapsed_ms(start),
        )
        raise
```

---

## AppContext에 AuditLogger 추가

```python
@dataclass
class AppContext:
    inventory: list[InventoryItem]
    policies: list[PolicyDoc]
    tickets_path: Path
    audit_logger: AuditLogger  # 추가!
```

lifespan에서 초기화:
```python
audit_logger = AuditLogger(log_dir="logs")
app = AppContext(..., audit_logger=audit_logger)
```

---

## 로그 분석 (macOS/Linux)

```bash
# 전체 로그 확인
cat logs/audit_2026-01-15.jsonl | python3 -m json.tool

# 실패한 요청만
cat logs/audit_*.jsonl | jq 'select(.success == false)'

# 도구별 사용 횟수
cat logs/audit_*.jsonl | jq -r '.tool_name' \
  | sort | uniq -c | sort -rn

# 평균 응답 시간
cat logs/audit_*.jsonl | jq '.duration_ms' \
  | awk '{s+=$1; n++} END {print s/n "ms"}'
```

---

## 로그 분석 (Windows)

```powershell
# 전체 로그 확인
Get-Content logs\audit_*.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Format-List

# 실패한 요청만
Get-Content logs\audit_*.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.success -eq $false }

# 도구별 사용 횟수
Get-Content logs\audit_*.jsonl |
  ForEach-Object { ($_ | ConvertFrom-Json).tool_name } |
  Group-Object | Sort-Object Count -Descending
```

---

## 실제 로그 예시

```jsonl
{"timestamp":"...","action":"tool_call","tool_name":"lookup_inventory",
 "input_summary":{"query":"monitor"},"success":true,"duration_ms":12.45}

{"timestamp":"...","action":"tool_call","tool_name":"create_ticket",
 "input_summary":{"title":"프린터 수리","priority":"P3"},
 "success":true,"duration_ms":25.67}

{"timestamp":"...","action":"tool_call","tool_name":"lookup_inventory",
 "input_summary":{"query":"../etc/passwd"},
 "success":false,"error":"Invalid query","duration_ms":1.23}
```

마지막 줄: **보안 이벤트 기록!**

---

## 핵심 정리

- 감사 로깅 = AI 도구 운영의 필수 요소
- JSONL: append-only, 스트리밍 파싱, 도구 호환
- `asyncio.Lock()`으로 thread-safe 구현
- 모든 Tool에 try/except로 성공/실패 기록
- `jq`/PowerShell로 로그 분석

---

## 다음 편 예고

### EP 15: 테스트 전략과 pytest 셋업

- MCP 서버 테스트의 특수성
- pytest-asyncio + fixture 설계
- 단위 테스트 작성
