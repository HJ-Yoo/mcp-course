# EP 25 — Multi-Server 오케스트레이션

> Module E (Advanced) · 약 20분

## 학습 목표

1. 여러 MCP 서버를 조합하는 세 가지 패턴을 비교하고 적절한 패턴을 선택할 수 있다
2. Gateway/Aggregator 서버를 설계하고 구현할 수 있다
3. MCP 서버 간 통신을 위해 ClientSession을 활용할 수 있다

---

## 1. 인트로 (2분)

지금까지 우리는 하나의 MCP 서버(Internal Ops Assistant)에 모든 기능을 넣었습니다. 하지만 실제 기업 환경을 생각해 봅시다.

> "운영팀은 재고 관리, 인사팀은 정책 관리, 재무팀은 비용 관리... 하나의 서버로 다 감당할 수 있을까?"

마이크로서비스 아키텍처처럼 MCP 서버도 **관심사를 분리**할 수 있습니다. 팀별로 독립적인 MCP 서버를 운영하고, 필요할 때 조합하는 것이죠.

이번 에피소드에서는 **Multi-Server 오케스트레이션**의 세 가지 패턴을 배우고, 실제로 게이트웨이 서버를 구현해 봅니다.

---

## 2. 핵심 개념 (6분)

### 2.1 왜 Multi-Server인가?

단일 서버의 한계:

```
모놀리식 MCP 서버:
┌────────────────────────────────────────┐
│           ops-assistant                │
│                                        │
│  lookup_inventory  (운영팀)            │
│  search_policy     (인사팀)            │
│  create_ticket     (운영팀)            │
│  calculate_budget  (재무팀)            │
│  approve_leave     (인사팀)            │
│  generate_report   (재무팀)            │
│  ...50개 도구...                       │
│                                        │
│  문제점:                                │
│  - 도구가 많아지면 LLM이 혼동           │
│  - 한 팀의 변경이 전체 서비스에 영향    │
│  - 권한 관리가 복잡                     │
│  - 독립적 배포/스케일링 불가            │
└────────────────────────────────────────┘
```

Multi-Server의 이점:
- **관심사 분리**: 팀별 독립 개발 및 배포
- **도구 이름 충돌 방지**: 서버별 네임스페이스
- **독립적 스케일링**: 트래픽이 많은 서버만 스케일 아웃
- **권한 분리**: 서버별 다른 접근 권한 설정

### 2.2 패턴 1: 클라이언트 직접 연결

가장 단순한 패턴으로, 클라이언트가 여러 MCP 서버에 **동시에** 연결합니다.

```
                     ┌──────────────┐
                ┌───→│ ops-server   │  재고, 티켓
                │    └──────────────┘
┌──────────┐    │    ┌──────────────┐
│  Claude  │────┼───→│ hr-server    │  정책, 휴가
│ Desktop  │    │    └──────────────┘
└──────────┘    │    ┌──────────────┐
                └───→│ finance-server│  예산, 보고서
                     └──────────────┘

각 서버는 독립 프로세스, 클라이언트가 모두 관리
```

**장점**: 구현 단순, 서버 간 의존성 없음
**단점**: 클라이언트 설정 복잡, 도구 이름 충돌 가능

### 2.3 패턴 2: Gateway/Aggregator 서버

하나의 **게이트웨이 서버**가 여러 백엔드 서버를 프록시합니다.

```
                     ┌──────────────────────────────────────┐
                     │         Gateway Server               │
┌──────────┐         │                                      │
│  Claude  │────────→│  ┌────────────────────────────────┐  │
│ Desktop  │         │  │ ops/lookup_inventory → ops-srv  │  │
│          │←────────│  │ ops/create_ticket  → ops-srv   │  │
└──────────┘         │  │ hr/search_policy   → hr-srv    │  │
                     │  │ hr/approve_leave   → hr-srv    │  │
  클라이언트는        │  │ fin/calculate_budget→ fin-srv  │  │
  게이트웨이만 연결   │  └────────────────────────────────┘  │
                     │          │        │        │         │
                     └──────────┼────────┼────────┼─────────┘
                                │        │        │
                     ┌──────────┘  ┌─────┘  ┌─────┘
                     ▼             ▼        ▼
               ┌──────────┐ ┌──────────┐ ┌──────────┐
               │ ops-srv  │ │ hr-srv   │ │ fin-srv  │
               └──────────┘ └──────────┘ └──────────┘
```

**장점**: 클라이언트 설정 단순, 중앙 집중 관리 (인증, Rate Limiting, 로깅)
**단점**: 게이트웨이가 단일 장애점(SPOF), 추가 레이턴시

### 2.4 패턴 3: 서버 체이닝

MCP 서버가 **다른 MCP 서버의 클라이언트** 역할을 합니다.

```
┌──────────┐     ┌──────────────────┐     ┌──────────────┐
│  Claude  │────→│ orchestrator-srv │────→│ ops-srv      │
│ Desktop  │     │                  │     └──────────────┘
│          │←────│ (MCP 서버이자    │────→┌──────────────┐
└──────────┘     │  MCP 클라이언트)  │     │ hr-srv       │
                 │                  │     └──────────────┘
                 │ 결과를 조합하여   │────→┌──────────────┐
                 │ 최종 응답 생성    │     │ fin-srv      │
                 └──────────────────┘     └──────────────┘
```

**장점**: 복잡한 워크플로우 구현 가능, 서버 간 데이터 조합
**단점**: 구현 복잡도 높음, 디버깅 어려움

### 2.5 네이밍 충돌 방지

여러 서버를 조합할 때 가장 흔한 문제는 **도구 이름 충돌**입니다:

```
ops-server:    search(query) → 재고 검색
hr-server:     search(query) → 정책 검색
finance-server: search(query) → 비용 검색

→ LLM: "search가 3개인데 어떤 걸 써야 하지?"
```

해결 전략: **서버별 접두사(prefix)**

```
ops/search(query)     → 재고 검색
hr/search(query)      → 정책 검색
finance/search(query) → 비용 검색

→ LLM: 컨텍스트에 따라 적절한 도구 선택 가능
```

### 2.6 서비스 디스커버리

백엔드 서버의 위치를 어떻게 알 수 있을까요?

| 방식 | 설명 | 적합한 경우 |
|------|------|-----------|
| **하드코딩** | 설정 파일에 서버 주소 고정 | 소규모, 변경 적음 |
| **환경변수** | `OPS_SERVER_URL=http://...` | 컨테이너 환경 |
| **서비스 레지스트리** | Consul, etcd 등 | 대규모 동적 환경 |
| **DNS 기반** | Kubernetes Service DNS | K8s 환경 |

---

## 3. 라이브 데모 (10분)

### Step 1: 패턴 1 — Claude Desktop 멀티 서버 설정

`claude_desktop_config.json` 파일에 여러 서버를 등록합니다:

macOS/Linux:
```bash
# Claude Desktop 설정 파일 위치
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Linux: ~/.config/Claude/claude_desktop_config.json
```

Windows (PowerShell):
```powershell
# Windows: %APPDATA%\Claude\claude_desktop_config.json
```

```json
{
  "mcpServers": {
    "ops-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/ops-project",
      "env": {
        "MCP_LOG_LEVEL": "INFO"
      }
    },
    "hr-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/hr-project",
      "env": {
        "MCP_LOG_LEVEL": "INFO"
      }
    },
    "finance-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/path/to/finance-project",
      "env": {
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

이 설정으로 Claude Desktop은 세 개의 독립된 MCP 서버 프로세스를 시작하고, 각각의 도구를 사용할 수 있습니다.

### Step 2: 패턴 2 — Gateway 서버 구현

`src/gateway.py` 파일을 생성합니다:

```python
"""MCP Gateway Server — 여러 백엔드 MCP 서버를 통합"""

from mcp.server.fastmcp import FastMCP
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class BackendServer:
    """백엔드 MCP 서버 설정"""
    name: str
    url: str
    prefix: str


# 백엔드 서버 목록 (환경변수로 관리 권장)
BACKENDS = [
    BackendServer(name="ops", url="http://localhost:8001/mcp", prefix="ops"),
    BackendServer(name="hr", url="http://localhost:8002/mcp", prefix="hr"),
    BackendServer(name="finance", url="http://localhost:8003/mcp", prefix="fin"),
]

# Gateway MCP 서버
gateway = FastMCP("Acme Corp Gateway")


class GatewayRouter:
    """백엔드 서버로 요청을 라우팅"""

    def __init__(self, backends: list[BackendServer]):
        self.backends = {b.prefix: b for b in backends}
        self._sessions: dict[str, ClientSession] = {}

    async def connect_all(self):
        """모든 백엔드 서버에 연결"""
        for prefix, backend in self.backends.items():
            try:
                session = await self._create_session(backend.url)
                self._sessions[prefix] = session
                print(f"[Gateway] Connected to {backend.name} ({backend.url})")
            except Exception as e:
                print(f"[Gateway] Failed to connect to {backend.name}: {e}")

    async def _create_session(self, url: str) -> ClientSession:
        """백엔드 서버에 MCP 세션 생성"""
        read_stream, write_stream, _ = await streamablehttp_client(url).__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.initialize()
        return session

    async def list_all_tools(self) -> list[dict]:
        """모든 백엔드의 도구 목록 (접두사 포함)"""
        all_tools = []
        for prefix, session in self._sessions.items():
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                all_tools.append({
                    "name": f"{prefix}/{tool.name}",
                    "description": f"[{prefix.upper()}] {tool.description}",
                    "inputSchema": tool.inputSchema,
                })
        return all_tools

    async def call_tool(self, prefixed_name: str, arguments: dict) -> Any:
        """접두사 기반으로 적절한 백엔드에 도구 호출 라우팅"""
        if "/" not in prefixed_name:
            raise ValueError(f"도구 이름에 접두사가 필요합니다: {prefixed_name}")

        prefix, tool_name = prefixed_name.split("/", 1)

        if prefix not in self._sessions:
            raise ValueError(f"알 수 없는 서버 접두사: {prefix}")

        session = self._sessions[prefix]
        result = await session.call_tool(tool_name, arguments)
        return result


# 전역 라우터 인스턴스
router = GatewayRouter(BACKENDS)


@gateway.tool()
async def route_tool(server_prefix: str, tool_name: str, arguments: str) -> str:
    """
    백엔드 MCP 서버의 도구를 호출합니다.

    Args:
        server_prefix: 서버 접두사 (ops, hr, fin)
        tool_name: 호출할 도구 이름
        arguments: JSON 문자열 형태의 도구 인자
    """
    args = json.loads(arguments)
    result = await router.call_tool(f"{server_prefix}/{tool_name}", args)
    return str(result)


@gateway.tool()
async def list_available_tools() -> str:
    """모든 백엔드 서버에서 사용 가능한 도구 목록을 반환합니다."""
    tools = await router.list_all_tools()
    output = []
    for tool in tools:
        output.append(f"- {tool['name']}: {tool['description']}")
    return "\n".join(output)
```

### Step 3: 패턴 3 — 서버 체이닝 (ClientSession 활용)

MCP 서버 내에서 다른 MCP 서버를 클라이언트로 호출하는 예시:

```python
"""서버 체이닝 예시: Orchestrator가 여러 서버의 결과를 조합"""

from mcp.server.fastmcp import FastMCP
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

orchestrator = FastMCP("Orchestrator")


async def call_backend(server_command: list[str], tool_name: str, args: dict):
    """백엔드 MCP 서버에 도구 호출"""
    server_params = StdioServerParameters(
        command=server_command[0],
        args=server_command[1:],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return result


@orchestrator.tool()
async def incident_full_report(item_name: str) -> str:
    """
    인시던트 전체 보고서 생성.
    1) 재고 확인 (ops-server)
    2) 관련 정책 검색 (hr-server)
    3) 비용 산출 (finance-server)
    4) 결과 조합
    """
    # 1) 재고 확인
    inventory = await call_backend(
        ["uv", "run", "python", "ops/server.py"],
        "lookup_inventory",
        {"item_name": item_name},
    )

    # 2) 관련 정책 검색
    policy = await call_backend(
        ["uv", "run", "python", "hr/server.py"],
        "search_policy",
        {"query": f"{item_name} 관련 정책"},
    )

    # 3) 결과 조합
    report = f"""
=== 인시던트 보고서: {item_name} ===

[재고 현황]
{inventory}

[관련 정책]
{policy}

[종합 의견]
위 정보를 바탕으로 적절한 조치를 취해주세요.
"""
    return report
```

### Step 4: 동적 도구 등록

게이트웨이가 시작 시 백엔드 서버의 도구를 자동으로 등록하는 고급 패턴:

```python
async def register_backend_tools(gateway: FastMCP, router: GatewayRouter):
    """백엔드 서버의 도구를 게이트웨이에 동적으로 등록"""
    all_tools = await router.list_all_tools()

    for tool_info in all_tools:
        prefixed_name = tool_info["name"]
        description = tool_info["description"]

        # 동적으로 도구 함수 생성
        async def make_handler(name: str):
            async def handler(**kwargs) -> str:
                return str(await router.call_tool(name, kwargs))
            handler.__name__ = name.replace("/", "_")
            handler.__doc__ = description
            return handler

        handler = await make_handler(prefixed_name)
        gateway.tool()(handler)

    print(f"[Gateway] Registered {len(all_tools)} tools from backends")
```

### Step 5: docker-compose로 멀티 서버 실행

```yaml
# docker-compose.multi.yml
version: "3.9"

services:
  gateway:
    build:
      context: ./gateway
    ports:
      - "8000:8000"
    environment:
      - OPS_SERVER_URL=http://ops-server:8001/mcp
      - HR_SERVER_URL=http://hr-server:8002/mcp
      - FIN_SERVER_URL=http://finance-server:8003/mcp
    depends_on:
      - ops-server
      - hr-server
      - finance-server
    networks:
      - mcp-network

  ops-server:
    build:
      context: ./ops-assistant
    ports:
      - "8001:8001"
    networks:
      - mcp-network

  hr-server:
    build:
      context: ./hr-assistant
    ports:
      - "8002:8002"
    networks:
      - mcp-network

  finance-server:
    build:
      context: ./finance-assistant
    ports:
      - "8003:8003"
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

macOS/Linux:
```bash
# 멀티 서버 스택 실행
docker compose -f docker-compose.multi.yml up -d --build

# 게이트웨이를 통해 ops 서버의 도구 호출
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "route_tool",
      "arguments": {
        "server_prefix": "ops",
        "tool_name": "lookup_inventory",
        "arguments": "{\"item_name\": \"노트북\"}"
      }
    }
  }'
```

Windows (PowerShell):
```powershell
# 멀티 서버 스택 실행
docker compose -f docker-compose.multi.yml up -d --build

# 게이트웨이를 통해 ops 서버의 도구 호출
$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "tools/call"
    params = @{
        name = "route_tool"
        arguments = @{
            server_prefix = "ops"
            tool_name = "lookup_inventory"
            arguments = '{"item_name": "노트북"}'
        }
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:8000/mcp -Method POST -ContentType "application/json" -Body $body
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- **패턴 1 (직접 연결)**: 클라이언트가 여러 서버에 직접 연결. 가장 단순하지만 설정 복잡
- **패턴 2 (게이트웨이)**: 하나의 서버가 여러 백엔드를 프록시. 중앙 관리 가능
- **패턴 3 (서버 체이닝)**: 서버가 다른 서버의 클라이언트 역할. 복잡한 워크플로우 가능
- **네이밍 충돌**은 서버별 **접두사**(ops/, hr/, fin/)로 해결합니다
- **서비스 디스커버리**는 환경에 따라 하드코딩부터 서비스 레지스트리까지 선택합니다
- docker-compose로 **멀티 서버를 통합 관리**할 수 있습니다

### 퀴즈

1. 게이트웨이 패턴의 가장 큰 위험은?
   → 게이트웨이가 단일 장애점(SPOF)이 될 수 있음. 게이트웨이 이중화로 해결

2. 도구 이름 충돌을 방지하는 방법은?
   → 서버별 접두사를 붙여 네임스페이스를 분리 (ops/search, hr/search)

3. 패턴 3(서버 체이닝)이 적합한 시나리오는?
   → 여러 서버의 결과를 조합하여 새로운 결과를 만들어야 하는 경우 (인시던트 보고서 등)

### 다음 편 예고

여러 서버가 돌아가면 모니터링은 더 중요해집니다. EP26에서 **Observability: 메트릭 & 트레이싱**으로 MCP 서버의 상태를 실시간으로 관찰하는 방법을 다룹니다.
