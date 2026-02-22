---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 26 — Observability: 메트릭 & 트레이싱"
---

# EP 26 — Observability: 메트릭 & 트레이싱
## Module E (Advanced) · MCP 실전 마스터

---

## 학습 목표

1. Observability의 3대 요소 (Logs, Metrics, Traces)를 이해한다
2. Prometheus 메트릭을 MCP 서버에 적용할 수 있다
3. OpenTelemetry 분산 트레이싱의 개념을 설명할 수 있다

---

## Observability 3 Pillar

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    Logs       │ │   Metrics    │ │   Traces     │
│              │ │              │ │              │
│ "무엇이      │ │ "얼마나      │ │ "어디서      │
│  일어났나?"  │ │  일어나나?"  │ │  일어났나?"  │
│              │ │              │ │              │
│ EP14 완료!   │ │ 이번 편!     │ │ 이번 편!     │
└──────────────┘ └──────────────┘ └──────────────┘
```

- **Logs**: 이벤트 상세 기록 (AuditLogger)
- **Metrics**: 수치 집계 (호출 수, 응답 시간)
- **Traces**: 요청 경로 추적 (병목 파악)

---

## Prometheus: Pull 기반 메트릭

```
┌──────────┐  GET /metrics  ┌──────────┐
│Prometheus│ ─────────────→ │MCP 서버  │
│ (수집기) │ ←───────────── │:9090     │
│          │  메트릭 텍스트   │          │
│ 15초마다  │                │          │
└────┬─────┘                └──────────┘
     │
     v
┌──────────┐
│ Grafana  │  ← 시각화 & 알림
└──────────┘
```

서버는 `/metrics`만 노출, Prometheus가 주기적으로 수집

---

## 핵심 메트릭 타입

| 타입 | 설명 | 예시 |
|------|------|------|
| **Counter** | 단조 증가 숫자 | 호출 횟수, 에러 수 |
| **Histogram** | 값의 분포 | 응답 시간 P50/P95/P99 |
| **Gauge** | 증감 가능 숫자 | 활성 연결 수 |

---

## MCP 서버 필수 메트릭

```python
from prometheus_client import Counter, Histogram, Gauge

# 1) 도구 호출 횟수
TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Total tool calls",
    ["tool_name", "status"]      # success / error
)

# 2) 응답 시간 분포
TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Tool call duration",
    ["tool_name"]
)

# 3) 활성 세션 수
ACTIVE_SESSIONS = Gauge(
    "mcp_active_sessions",
    "Active MCP sessions"
)
```

---

## 계측 데코레이터

```python
def instrument_tool(tool_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                TOOL_CALLS.labels(
                    tool_name=tool_name, status="success"
                ).inc()
                return result
            except Exception:
                TOOL_CALLS.labels(
                    tool_name=tool_name, status="error"
                ).inc()
                raise
            finally:
                duration = time.monotonic() - start
                TOOL_DURATION.labels(
                    tool_name=tool_name
                ).observe(duration)
        return wrapper
    return decorator
```

---

## 도구에 적용

```python
# 메트릭 서버 시작
start_http_server(9090)  # localhost:9090/metrics

@mcp.tool()
@instrument_tool("lookup_inventory")
async def lookup_inventory(item_name: str) -> str:
    """메트릭 자동 수집 — 비침습적!"""
    ...

@mcp.tool()
@instrument_tool("create_ticket")
async def create_ticket(title: str, ...) -> str:
    ...
```

> 비즈니스 로직 변경 없이 **데코레이터만 추가**

---

## 메트릭 확인

```bash
curl http://localhost:9090/metrics | grep mcp_

# 출력 예시:
mcp_tool_calls_total{tool_name="lookup_inventory",
                     status="success"} 42.0
mcp_tool_calls_total{tool_name="create_ticket",
                     status="error"} 2.0

mcp_tool_duration_seconds_bucket{le="0.05",
  tool_name="lookup_inventory"} 39.0
mcp_tool_duration_seconds_bucket{le="0.1",
  tool_name="lookup_inventory"} 42.0
```

---

## OpenTelemetry 트레이싱

```
Trace ID: abc123
├── Span: "MCP Request" (전체)
│   ├── Span: "Auth" (2ms)
│   ├── Span: "Rate Limit" (1ms)
│   ├── Span: "Tool: lookup" (45ms)
│   │   ├── Span: "Cache Check" (0.5ms) MISS
│   │   ├── Span: "DB Query" (40ms) ← 병목!
│   │   └── Span: "Cache Store" (0.3ms)
│   └── Span: "Audit Log" (3ms)

총: 51ms, 병목: DB Query (78%)
```

**Span** = 작업 단위 / **Trace** = Span들의 집합

---

## 트레이싱 코드

```python
from opentelemetry import trace

tracer = trace.get_tracer("ops-assistant")

def traced(span_name):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("mcp.tool.params",
                                   str(kwargs))
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator
```

---

## Grafana 대시보드 핵심 패널

```
┌──────────────────────────────────────────┐
│ MCP Server Dashboard                     │
│                                          │
│  [RPS: 42]  [에러율: 2.3%]  [P95: 127ms]│
│                                          │
│  ┌──────────────────────────────┐       │
│  │ Tool Call Volume (추이)       │       │
│  │ ── lookup_inventory           │       │
│  │ -- search_policy              │       │
│  └──────────────────────────────┘       │
│                                          │
│  ┌──────────────────────────────┐       │
│  │ Response Time P50/P95/P99    │       │
│  └──────────────────────────────┘       │
└──────────────────────────────────────────┘
```

---

## PromQL 핵심 쿼리

```promql
# 초당 도구 호출 수 (RPS)
rate(mcp_tool_calls_total[5m])

# 에러율 (%)
sum(rate(mcp_tool_calls_total{status="error"}[5m]))
/ sum(rate(mcp_tool_calls_total[5m])) * 100

# P95 레이턴시 (ms)
histogram_quantile(0.95,
  rate(mcp_tool_duration_seconds_bucket[5m])
) * 1000

# 캐시 히트율 (%)
sum(rate(mcp_cache_operations_total{result="hit"}[5m]))
/ sum(rate(mcp_cache_operations_total[5m])) * 100
```

---

## 핵심 정리

- **Logs**(EP14) + **Metrics**(이번 편) + **Traces**(이번 편) = 완전한 Observability
- **Counter**: 호출 횟수, 에러 횟수 추적
- **Histogram**: P50/P95/P99 레이턴시 분포
- `@instrument_tool` 데코레이터로 **비침습적** 메트릭 수집
- **OpenTelemetry**로 분산 환경 요청 경로 추적
- **Grafana** 대시보드로 실시간 시각화 & 알림

---

## 다음 편 예고

**EP 27 — 프로덕션 체크리스트 & 마무리**

모든 준비가 끝났다! 최종 체크리스트 점검,
배포 아키텍처 결정, 그리고 전체 과정 회고
