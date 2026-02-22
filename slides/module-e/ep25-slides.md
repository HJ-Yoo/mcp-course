---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 25 — Multi-Server 오케스트레이션"
---

# EP 25 — Multi-Server 오케스트레이션
## Module E (Advanced) · MCP 실전 마스터

---

## 학습 목표

1. 여러 MCP 서버를 조합하는 3가지 패턴을 비교할 수 있다
2. Gateway/Aggregator 서버를 설계하고 구현할 수 있다
3. MCP ClientSession으로 서버 간 통신을 구현할 수 있다

---

## 왜 Multi-Server인가?

```
모놀리식 MCP 서버 (50개 도구):
  - LLM이 도구 선택에 혼동
  - 한 팀의 변경이 전체에 영향
  - 권한 관리 복잡
  - 독립 배포/스케일링 불가

Multi-Server:
  ops-server   → 재고, 티켓 (운영팀)
  hr-server    → 정책, 휴가 (인사팀)
  fin-server   → 예산, 보고서 (재무팀)
```

> 마이크로서비스처럼 **관심사 분리**!

---

## 패턴 1: 클라이언트 직접 연결

```
               ┌──────────────┐
          ┌───→│ ops-server   │
          │    └──────────────┘
[Claude] ─┼───→[hr-server    ]
          │
          └───→[finance-server]
```

- Claude Desktop `mcpServers`에 여러 서버 등록
- 각 서버는 **독립 프로세스**
- 장점: 단순 / 단점: 클라이언트 설정 복잡

---

## 패턴 1: 설정 예시

```json
{
  "mcpServers": {
    "ops-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/ops-project"
    },
    "hr-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/hr-project"
    },
    "finance-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/finance-project"
    }
  }
}
```

---

## 패턴 2: Gateway/Aggregator 서버

```
                ┌─────────────────────────┐
[Claude] ──────→│     Gateway Server      │
                │                         │
                │  ops/lookup → ops-srv   │
                │  hr/search  → hr-srv    │
                │  fin/budget → fin-srv   │
                │         |    |    |     │
                └─────────┼────┼────┼─────┘
                          v    v    v
                [ops]   [hr]   [fin]
```

- 클라이언트는 **게이트웨이만 연결**
- 중앙 집중: 인증, Rate Limiting, 로깅
- 단점: SPOF (게이트웨이 이중화 필요)

---

## 패턴 3: 서버 체이닝

```
[Claude] → [orchestrator] → [ops-srv  ]
                           → [hr-srv   ]
                           → [fin-srv  ]
              ↑ 결과를 조합하여 최종 응답 생성
```

- MCP 서버가 **다른 MCP 서버의 클라이언트** 역할
- `mcp.ClientSession` 활용
- 장점: 복잡한 워크플로우 / 단점: 디버깅 어려움

---

## 네이밍 충돌 방지

```
문제:
  ops-server:  search(query)  → 재고 검색
  hr-server:   search(query)  → 정책 검색
  → LLM: "어떤 search를 쓰지?"

해결: 서버별 접두사
  ops/search(query)  → 재고 검색
  hr/search(query)   → 정책 검색
  fin/search(query)  → 비용 검색
```

---

## Gateway 핵심 코드

```python
class GatewayRouter:
    async def call_tool(self, prefixed_name, arguments):
        prefix, tool_name = prefixed_name.split("/", 1)
        session = self._sessions[prefix]
        return await session.call_tool(tool_name, arguments)

@gateway.tool()
async def route_tool(server_prefix: str,
                     tool_name: str,
                     arguments: str) -> str:
    args = json.loads(arguments)
    result = await router.call_tool(
        f"{server_prefix}/{tool_name}", args
    )
    return str(result)
```

---

## 서버 체이닝 예시

```python
@orchestrator.tool()
async def incident_report(item_name: str) -> str:
    """여러 서버의 결과를 조합"""

    # 1) 재고 확인 (ops-server)
    inventory = await call_backend(
        ops_server, "lookup_inventory", {"item_name": item_name}
    )

    # 2) 관련 정책 (hr-server)
    policy = await call_backend(
        hr_server, "search_policy", {"query": item_name}
    )

    # 3) 결과 조합
    return f"재고: {inventory}\n정책: {policy}"
```

---

## 서비스 디스커버리

| 방식 | 설명 | 적합한 경우 |
|------|------|-----------|
| **하드코딩** | 설정 파일에 주소 고정 | 소규모 |
| **환경변수** | `OPS_URL=http://...` | 컨테이너 |
| **DNS 기반** | K8s Service DNS | Kubernetes |
| **레지스트리** | Consul, etcd | 대규모 동적 |

---

## docker-compose 멀티 서버

```yaml
services:
  gateway:
    build: ./gateway
    ports: ["8000:8000"]
    environment:
      - OPS_URL=http://ops-server:8001/mcp
      - HR_URL=http://hr-server:8002/mcp
    depends_on: [ops-server, hr-server]

  ops-server:
    build: ./ops-assistant
    ports: ["8001:8001"]

  hr-server:
    build: ./hr-assistant
    ports: ["8002:8002"]
```

---

## 패턴 비교 요약

| | 직접 연결 | 게이트웨이 | 서버 체이닝 |
|--|---------|----------|-----------|
| **복잡도** | 낮음 | 중간 | 높음 |
| **중앙 관리** | X | O | O |
| **유연성** | 낮음 | 중간 | 높음 |
| **SPOF 위험** | 없음 | 있음 | 있음 |
| **적합** | 소규모 | 중규모 | 복잡 워크플로우 |

---

## 핵심 정리

- **패턴 1**: 클라이언트 직접 연결 (단순, 소규모)
- **패턴 2**: 게이트웨이 (중앙 관리, 중규모)
- **패턴 3**: 서버 체이닝 (워크플로우, 복잡)
- **접두사**로 네이밍 충돌 방지 (`ops/`, `hr/`, `fin/`)
- docker-compose로 **멀티 서버 통합 관리**

---

## 다음 편 예고

**EP 26 — Observability: 메트릭 & 트레이싱**

여러 서버가 돌아가면 모니터링이 더 중요하다!
Prometheus 메트릭 + OpenTelemetry 트레이싱
