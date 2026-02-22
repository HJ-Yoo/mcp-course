# EP 26 — Observability: 메트릭 & 트레이싱

> Module E (Advanced) · 약 20분

## 학습 목표

1. Observability의 3대 요소(Logs, Metrics, Traces)를 이해하고 MCP 서버에 적용할 수 있다
2. Prometheus 클라이언트를 사용하여 MCP 도구 호출 메트릭을 수집할 수 있다
3. OpenTelemetry 기초를 이해하고 분산 트레이싱의 개념을 설명할 수 있다

---

## 1. 인트로 (2분)

EP25에서 여러 MCP 서버를 조합하는 방법을 배웠습니다. 서버가 하나일 때는 로그 파일 하나를 열어보면 됐지만, 여러 서버가 돌아가면 상황이 달라집니다.

> "갑자기 응답이 느려졌는데, 어떤 서버가 문제인지 모르겠어요."

프로덕션 환경에서 이런 말이 나오면 이미 늦은 겁니다. 문제가 **발생하기 전에 감지**하고, 발생했을 때 **빠르게 원인을 파악**하려면 체계적인 모니터링이 필요합니다.

이번 에피소드에서는 **Observability의 3대 요소**인 Logs, Metrics, Traces를 MCP 서버에 적용합니다. EP14에서 구현한 AuditLogger가 Logs를 담당했다면, 이번에는 **Metrics와 Traces**를 추가합니다.

---

## 2. 핵심 개념 (6분)

### 2.1 Observability의 3 Pillar

```
┌──────────────────────────────────────────────────────────────┐
│                    Observability                             │
│                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │    Logs       │  │   Metrics    │  │   Traces     │     │
│   │              │  │              │  │              │     │
│   │ "무엇이      │  │ "얼마나      │  │ "어디서      │     │
│   │  일어났나?"  │  │  일어나나?"  │  │  일어났나?"  │     │
│   │              │  │              │  │              │     │
│   │ - 이벤트 기록│  │ - 수치 집계  │  │ - 요청 흐름  │     │
│   │ - 디버깅     │  │ - 대시보드   │  │ - 병목 파악  │     │
│   │ - 감사 추적  │  │ - 알림 설정  │  │ - 분산 추적  │     │
│   │              │  │              │  │              │     │
│   │ EP14 완료!   │  │ 이번 편!     │  │ 이번 편!     │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

- **Logs**: 개별 이벤트의 상세 기록. EP14에서 AuditLogger로 구현 완료
- **Metrics**: 수치형 데이터의 시계열 집계. 전체적인 건강 상태 파악
- **Traces**: 하나의 요청이 시스템을 통과하는 경로. 병목 파악

### 2.2 Metrics: Prometheus 클라이언트

Prometheus는 오픈소스 모니터링 시스템으로, **Pull 기반** 메트릭 수집을 사용합니다:

```
┌──────────────┐     GET /metrics    ┌──────────────┐
│ Prometheus   │ ──────────────────→ │ MCP 서버      │
│ (수집기)     │ ←────────────────── │ :9090/metrics │
│              │   메트릭 텍스트      │              │
│  15초마다     │                     │              │
│  수집 (scrape)│                    │              │
└──────┬───────┘                     └──────────────┘
       │
       ▼
┌──────────────┐
│ Grafana      │  ← 시각화 & 알림
│ (대시보드)    │
└──────────────┘
```

핵심 메트릭 타입:

| 타입 | 설명 | MCP 서버 예시 |
|------|------|-------------|
| **Counter** | 단조 증가하는 숫자 | 도구 호출 횟수, 에러 횟수 |
| **Histogram** | 값의 분포 | 응답 시간 (P50, P95, P99) |
| **Gauge** | 증감 가능한 숫자 | 현재 활성 연결 수 |
| **Summary** | 클라이언트 사이드 분위수 | 요청 크기 분포 |

### 2.3 MCP 서버의 핵심 메트릭

프로덕션 MCP 서버에서 반드시 수집해야 하는 메트릭:

```
1. mcp_tool_calls_total (Counter)
   - 도구별 호출 횟수
   - 레이블: tool_name, status (success/error)
   - 용도: 어떤 도구가 가장 많이 쓰이는지, 에러율은 얼마인지

2. mcp_tool_duration_seconds (Histogram)
   - 도구별 응답 시간 분포
   - 레이블: tool_name
   - 용도: P50(중앙값), P95, P99 레이턴시 추적

3. mcp_tool_errors_total (Counter)
   - 도구별 에러 횟수
   - 레이블: tool_name, error_type
   - 용도: 에러 급증 시 알림

4. mcp_active_sessions (Gauge)
   - 현재 활성 MCP 세션 수
   - 용도: 서버 부하 모니터링

5. mcp_rate_limit_hits_total (Counter)
   - Rate Limit 발동 횟수 (EP24에서 구현한 Rate Limiter)
   - 레이블: tool_name, user_id
   - 용도: Rate Limit 설정 조정 근거
```

### 2.4 Traces: OpenTelemetry

OpenTelemetry(OTel)는 분산 추적의 표준입니다. 핵심 개념:

```
하나의 MCP 요청 트레이스:

Trace ID: abc123
├── Span: "MCP Request" (전체 요청)
│   ├── Span: "Auth Middleware" (인증 검증, 2ms)
│   ├── Span: "Rate Limit Check" (Rate Limit 검사, 1ms)
│   ├── Span: "Tool: lookup_inventory" (도구 실행, 45ms)
│   │   ├── Span: "Cache Check" (캐시 확인, 0.5ms) → MISS
│   │   ├── Span: "Database Query" (데이터 조회, 40ms) ← 병목!
│   │   └── Span: "Cache Store" (캐시 저장, 0.3ms)
│   └── Span: "Audit Log" (감사 로그 기록, 3ms)
│
총 소요시간: 51ms, 병목: Database Query (40ms, 78%)
```

**Span**: 하나의 작업 단위 (시작 시각, 종료 시각, 메타데이터)
**Trace**: 관련된 Span들의 집합 (하나의 요청 전체)
**Context Propagation**: 서비스 간 Trace ID 전달

### 2.5 Grafana 대시보드 설계

MCP 서버 운영을 위한 핵심 대시보드 패널:

```
┌──────────────────────────────────────────────────────────────┐
│  MCP Server Dashboard                                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ RPS (초당    │  │ 에러율       │  │ P95 레이턴시  │      │
│  │  요청 수)    │  │              │  │              │      │
│  │   ████       │  │   2.3%       │  │   127ms      │      │
│  │   ████ 42    │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Tool Call Volume (도구별 호출 추이)                  │     │
│  │  ──── lookup_inventory                              │     │
│  │  ---- search_policy                                 │     │
│  │  ···· create_ticket                                 │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Response Time Distribution (응답 시간 분포)         │     │
│  │  P50: 23ms  P95: 127ms  P99: 342ms                │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 라이브 데모 (10분)

### Step 1: Prometheus 클라이언트 설치

macOS/Linux:
```bash
cd /path/to/ops-assistant
uv add prometheus-client opentelemetry-api opentelemetry-sdk
```

Windows (PowerShell):
```powershell
cd C:\path\to\ops-assistant
uv add prometheus-client opentelemetry-api opentelemetry-sdk
```

### Step 2: 메트릭 정의 및 계측 모듈

`src/metrics.py` 파일을 생성합니다:

```python
"""MCP 서버 Prometheus 메트릭"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import functools
import time

# ========================================
# 메트릭 정의
# ========================================

# 도구 호출 횟수
TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Total number of MCP tool calls",
    ["tool_name", "status"],  # success, error
)

# 도구 응답 시간 (히스토그램)
TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "MCP tool call duration in seconds",
    ["tool_name"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# 도구 에러 횟수
TOOL_ERRORS = Counter(
    "mcp_tool_errors_total",
    "Total number of MCP tool errors",
    ["tool_name", "error_type"],
)

# 활성 세션 수
ACTIVE_SESSIONS = Gauge(
    "mcp_active_sessions",
    "Number of active MCP sessions",
)

# Rate Limit 발동 횟수
RATE_LIMIT_HITS = Counter(
    "mcp_rate_limit_hits_total",
    "Number of rate limit hits",
    ["tool_name", "user_id"],
)

# 캐시 히트/미스
CACHE_OPERATIONS = Counter(
    "mcp_cache_operations_total",
    "Cache hit/miss counts",
    ["tool_name", "result"],  # hit, miss
)


# ========================================
# 계측 데코레이터
# ========================================

def instrument_tool(tool_name: str):
    """도구 호출 메트릭을 자동으로 수집하는 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                TOOL_CALLS.labels(tool_name=tool_name, status="success").inc()
                return result
            except Exception as e:
                TOOL_CALLS.labels(tool_name=tool_name, status="error").inc()
                TOOL_ERRORS.labels(
                    tool_name=tool_name,
                    error_type=type(e).__name__,
                ).inc()
                raise
            finally:
                duration = time.monotonic() - start
                TOOL_DURATION.labels(tool_name=tool_name).observe(duration)
        return wrapper
    return decorator


def start_metrics_server(port: int = 9090):
    """Prometheus 메트릭 HTTP 서버 시작"""
    start_http_server(port)
    print(f"[Metrics] Prometheus metrics available at http://localhost:{port}/metrics")
```

### Step 3: 도구에 메트릭 적용

기존 도구에 계측 데코레이터를 적용합니다:

```python
# src/server.py (관련 부분)
from metrics import instrument_tool, start_metrics_server, CACHE_OPERATIONS

# 서버 시작 시 메트릭 서버 가동
start_metrics_server(port=9090)


@mcp.tool()
@instrument_tool("lookup_inventory")
async def lookup_inventory(item_name: str) -> str:
    """재고 조회 — 메트릭 자동 수집"""
    # 캐시 확인
    cache_key = inventory_cache._make_key("lookup_inventory", item_name=item_name)
    cached = inventory_cache.get(cache_key)
    if cached is not None:
        CACHE_OPERATIONS.labels(tool_name="lookup_inventory", result="hit").inc()
        return f"[캐시] {cached}"
    CACHE_OPERATIONS.labels(tool_name="lookup_inventory", result="miss").inc()

    # 실제 조회 로직
    result = _do_inventory_lookup(item_name)
    inventory_cache.set(cache_key, result)
    return result


@mcp.tool()
@instrument_tool("search_policy")
async def search_policy(query: str, department: str = "") -> str:
    """정책 검색 — 메트릭 자동 수집"""
    cache_key = policy_cache._make_key("search_policy", query=query, department=department)
    cached = policy_cache.get(cache_key)
    if cached is not None:
        CACHE_OPERATIONS.labels(tool_name="search_policy", result="hit").inc()
        return f"[캐시] {cached}"
    CACHE_OPERATIONS.labels(tool_name="search_policy", result="miss").inc()

    result = _do_policy_search(query, department)
    policy_cache.set(cache_key, result)
    return result


@mcp.tool()
@instrument_tool("create_ticket")
async def create_ticket(title: str, description: str, priority: str = "medium") -> str:
    """티켓 생성 — 메트릭 자동 수집"""
    result = _do_create_ticket(title, description, priority)
    return result
```

### Step 4: 메트릭 확인

macOS/Linux:
```bash
# 서버 시작 (메트릭 서버 포함)
uv run python src/server.py --transport streamable-http --port 8000 &

# 몇 번 도구를 호출한 후...

# Prometheus 메트릭 확인
curl -s http://localhost:9090/metrics | grep mcp_

# 도구 호출 횟수 확인
curl -s http://localhost:9090/metrics | grep mcp_tool_calls_total

# 응답 시간 분포 확인
curl -s http://localhost:9090/metrics | grep mcp_tool_duration_seconds
```

Windows (PowerShell):
```powershell
# 메트릭 확인
(Invoke-WebRequest -Uri http://localhost:9090/metrics).Content | Select-String "mcp_"

# 도구 호출 횟수
(Invoke-WebRequest -Uri http://localhost:9090/metrics).Content | Select-String "mcp_tool_calls_total"

# 응답 시간 분포
(Invoke-WebRequest -Uri http://localhost:9090/metrics).Content | Select-String "mcp_tool_duration_seconds"
```

출력 예시:
```
# HELP mcp_tool_calls_total Total number of MCP tool calls
# TYPE mcp_tool_calls_total counter
mcp_tool_calls_total{tool_name="lookup_inventory",status="success"} 42.0
mcp_tool_calls_total{tool_name="search_policy",status="success"} 18.0
mcp_tool_calls_total{tool_name="create_ticket",status="success"} 7.0
mcp_tool_calls_total{tool_name="create_ticket",status="error"} 2.0

# HELP mcp_tool_duration_seconds MCP tool call duration in seconds
# TYPE mcp_tool_duration_seconds histogram
mcp_tool_duration_seconds_bucket{le="0.01",tool_name="lookup_inventory"} 5.0
mcp_tool_duration_seconds_bucket{le="0.025",tool_name="lookup_inventory"} 28.0
mcp_tool_duration_seconds_bucket{le="0.05",tool_name="lookup_inventory"} 39.0
mcp_tool_duration_seconds_bucket{le="0.1",tool_name="lookup_inventory"} 42.0
```

### Step 5: OpenTelemetry 트레이싱 설정

`src/tracing.py` 파일을 생성합니다:

```python
"""MCP 서버 OpenTelemetry 트레이싱"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.resources import Resource
import functools


def setup_tracing(service_name: str = "ops-assistant"):
    """OpenTelemetry 트레이싱 초기화"""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # 콘솔 출력 (프로덕션에서는 OTLP Exporter 사용)
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


# 전역 트레이서
tracer = setup_tracing()


def traced(span_name: str):
    """도구 호출에 트레이싱 스팬을 추가하는 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # 입력 파라미터를 스팬 속성에 기록
                for key, value in kwargs.items():
                    if not key.startswith("_"):
                        span.set_attribute(f"mcp.tool.param.{key}", str(value))

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("mcp.tool.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("mcp.tool.status", "error")
                    span.set_attribute("mcp.tool.error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


# 사용 예시:
# @mcp.tool()
# @instrument_tool("lookup_inventory")  # 메트릭
# @traced("tool.lookup_inventory")      # 트레이싱
# async def lookup_inventory(item_name: str) -> str:
#     with tracer.start_as_current_span("cache_check"):
#         cached = cache.get(key)
#     with tracer.start_as_current_span("database_query"):
#         result = db.query(item_name)
#     return result
```

### Step 6: Grafana 대시보드 JSON (기본)

Prometheus 데이터를 시각화하는 Grafana 대시보드 설정:

```json
{
  "dashboard": {
    "title": "MCP Server Monitoring",
    "panels": [
      {
        "title": "Tool Calls per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_tool_calls_total[5m])",
            "legendFormat": "{{tool_name}} ({{status}})"
          }
        ]
      },
      {
        "title": "Error Rate (%)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(mcp_tool_calls_total{status='error'}[5m])) / sum(rate(mcp_tool_calls_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "P95 Latency (ms)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(mcp_tool_duration_seconds_bucket[5m])) * 1000",
            "legendFormat": "{{tool_name}}"
          }
        ]
      },
      {
        "title": "Cache Hit Rate (%)",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(mcp_cache_operations_total{result='hit'}[5m])) / sum(rate(mcp_cache_operations_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "Rate Limit Hits",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_rate_limit_hits_total[5m])",
            "legendFormat": "{{tool_name}}"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "mcp_active_sessions"
          }
        ]
      }
    ]
  }
}
```

### Step 7: docker-compose에 Grafana 추가

EP23의 docker-compose에 Grafana를 추가합니다:

```yaml
# docker-compose.yml에 추가
  grafana:
    image: grafana/grafana:latest
    container_name: ops-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - mcp-network

# volumes에 추가
volumes:
  grafana-data:
```

macOS/Linux:
```bash
# 전체 모니터링 스택 실행
docker compose up -d --build

# Grafana 접속: http://localhost:3000
# 초기 계정: admin / admin
# Prometheus 데이터소스 추가: http://prometheus:9090
```

Windows (PowerShell):
```powershell
# 전체 모니터링 스택 실행
docker compose up -d --build

# Grafana 접속: http://localhost:3000
# 초기 계정: admin / admin
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- Observability의 3대 요소: **Logs**(EP14 완료), **Metrics**(이번 편), **Traces**(이번 편)
- **Prometheus Counter**로 도구 호출 횟수와 에러 횟수를 추적합니다
- **Prometheus Histogram**으로 응답 시간 분포(P50/P95/P99)를 파악합니다
- `@instrument_tool` 데코레이터로 **메트릭 수집을 비침습적으로** 적용합니다
- **OpenTelemetry**로 분산 환경에서 요청의 전체 경로를 추적합니다
- **Grafana 대시보드**로 메트릭을 시각화하고 이상 징후를 빠르게 발견합니다

### 퀴즈

1. Counter와 Histogram의 차이는?
   → Counter는 단조 증가하는 숫자 (호출 횟수), Histogram은 값의 분포를 버킷별로 기록 (응답 시간)

2. Prometheus가 Pull 기반인 이유는?
   → 서버가 메트릭을 push할 필요 없이, Prometheus가 주기적으로 /metrics를 scrape. 서버 코드가 단순해지고, 서버 장애 시에도 메트릭 시스템이 영향을 받지 않음

3. OpenTelemetry의 Span과 Trace의 관계는?
   → Trace는 하나의 요청 전체를 나타내며, 여러 Span으로 구성됨. 각 Span은 하나의 작업 단위

### 다음 편 예고

모든 준비가 끝났습니다! 최종 에피소드 EP27에서 **프로덕션 체크리스트**를 하나씩 점검하고, 전체 과정을 회고합니다. 우리의 MCP 서버가 진짜 프로덕션에 나갈 준비가 되었는지 확인해 봅시다.
