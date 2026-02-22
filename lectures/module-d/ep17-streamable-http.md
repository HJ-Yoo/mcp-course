# EP 17 — Streamable HTTP Transport

> Module D · 약 20분

## 학습 목표
1. stdio transport의 한계와 Streamable HTTP의 장점을 설명한다
2. FastMCP에서 transport를 전환하는 방법을 익힌다
3. HTTP 모드로 서버를 실행하고 curl/Inspector로 테스트한다
4. Anthropic/OpenAI/Google 각 SDK에서 MCP 도구를 호출하는 차이를 이해한다

---

## 1. 인트로 (2분)

Module C까지 우리는 모든 기능을 **stdio transport**로 실행했습니다. stdio는 간단하고 빠르지만, 근본적인 한계가 있습니다.

- 로컬 프로세스로만 동작 → 원격 접속 불가
- 1:1 연결만 가능 → 여러 클라이언트 동시 접속 불가
- 프로세스 관리 부담 → 클라이언트가 서버 프로세스를 직접 관리

Module D에서는 이 한계를 넘어 **Streamable HTTP Transport**로 전환합니다. 이것은 MCP를 실제 서비스로 운영할 수 있게 만드는 핵심 기술입니다.

놀라운 점은 — 서버 코드를 거의 변경하지 않아도 된다는 것입니다.

---

## 2. 핵심 개념 (6분)

### 2.1 stdio의 한계

```
┌───────────────────────────────────────────────┐
│            stdio Transport                     │
│                                               │
│  클라이언트 ──stdin/stdout──→ 서버 프로세스      │
│                                               │
│  한계:                                         │
│  ❌ 로컬 전용 (같은 머신)                       │
│  ❌ 1:1 연결 (하나의 클라이언트)                 │
│  ❌ 클라이언트가 서버 프로세스를 spawn/관리       │
│  ❌ 로드밸런싱 불가                             │
│  ❌ 서버 상태 모니터링 어려움                    │
└───────────────────────────────────────────────┘
```

stdio는 개발, 테스트, 단일 사용자 시나리오에 적합하지만, 팀이나 조직 단위로 MCP 서버를 운영하기에는 부족합니다.

### 2.2 Streamable HTTP의 장점

```
┌───────────────────────────────────────────────┐
│         Streamable HTTP Transport              │
│                                               │
│  클라이언트 A ─┐                               │
│  클라이언트 B ──┼──HTTP──→ MCP 서버             │
│  클라이언트 C ─┘                               │
│                                               │
│  장점:                                         │
│  ✅ 원격 접속 (네트워크를 통해)                  │
│  ✅ 다중 클라이언트 동시 접속                    │
│  ✅ 로드밸런서 뒤에 배치 가능                    │
│  ✅ 표준 HTTP 인프라 활용 (CORS, 인증, TLS)     │
│  ✅ 서버 독립 실행 (클라이언트와 분리)           │
│  ✅ 서버 모니터링 (health check 등)             │
└───────────────────────────────────────────────┘
```

### 2.3 HTTP 엔드포인트 구조

Streamable HTTP transport는 두 개의 엔드포인트를 제공합니다:

```
POST /mcp     → JSON-RPC 요청 수신 (Tool 호출, Resource 조회 등)
                응답: JSON-RPC 결과 또는 SSE 스트림

GET  /mcp     → SSE(Server-Sent Events) 스트림 연결
                서버 → 클라이언트 방향의 알림/이벤트

DELETE /mcp   → 세션 종료
```

모든 통신은 JSON-RPC 2.0 프로토콜을 따릅니다:

```json
// 요청
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "lookup_inventory",
    "arguments": {"query": "monitor"}
  }
}

// 응답
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{"type": "text", "text": "Found 3 items..."}]
  }
}
```

### 2.4 Transport 전환의 용이성

FastMCP의 강력한 설계 덕분에 transport 전환이 매우 간단합니다:

```python
# stdio 모드 (기존)
mcp.run(transport="stdio")

# Streamable HTTP 모드 (새로운!)
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

**코드 변경 없이** transport만 바꿀 수 있는 이유:
- Tool, Resource, Prompt 핸들러는 transport에 무관
- MCP 프로토콜이 transport 추상화를 제공
- 비즈니스 로직과 통신 레이어가 완전히 분리됨

### 2.5 CLI 인자로 transport 선택

실행 시 transport를 선택할 수 있게 합니다:

```python
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
        )
    else:
        mcp.run(transport="stdio")
```

---

## 3. 라이브 데모 (10분)

### Step 1: server.py에 transport 선택 추가

`src/server.py`를 수정합니다:

```python
"""Acme Internal Ops Assistant — MCP Server"""

import argparse
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from models import AppContext
from audit import AuditLogger
from tools import inventory_tool, policy_tool, ticket_tool
from resources import policy_resource
from prompts import ops_prompts


@asynccontextmanager
async def app_lifespan(server):
    """서버 시작 시 AppContext를 초기화합니다."""
    audit_logger = AuditLogger(log_dir="logs")
    app = AppContext(
        inventory=load_inventory("data/inventory.csv"),
        policies=load_policies("data/policies"),
        tickets_path="data/tickets.jsonl",
        audit_logger=audit_logger,
    )
    yield {"app": app}


mcp = FastMCP(
    "Acme Internal Ops Assistant",
    lifespan=app_lifespan,
)

# Tool, Resource, Prompt 등록
inventory_tool.register(mcp)
policy_tool.register(mcp)
ticket_tool.register(mcp)
policy_resource.register(mcp)
ops_prompts.register(mcp)


def main():
    parser = argparse.ArgumentParser(
        description="Acme Internal Ops Assistant MCP Server"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind (HTTP mode only, default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (HTTP mode only, default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### Step 2: HTTP 모드로 실행

macOS/Linux:
```bash
uv run python src/server.py --transport streamable-http --port 8000
```

Windows (PowerShell):
```powershell
uv run python src\server.py --transport streamable-http --port 8000
```

서버가 시작되면 다음과 같은 로그가 출력됩니다:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 3: curl로 JSON-RPC 요청 보내기

새 터미널을 열고 curl로 직접 요청을 보냅니다.

macOS/Linux:
```bash
# 서버 초기화 (initialize)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "curl-test", "version": "1.0"}
    }
  }'

# Tool 목록 조회
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Tool 호출 (재고 검색)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "lookup_inventory",
      "arguments": {"query": "monitor"}
    }
  }'
```

Windows (PowerShell):
```powershell
# Tool 호출 (재고 검색)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/mcp" `
  -ContentType "application/json" `
  -Body '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"lookup_inventory","arguments":{"query":"monitor"}}}'
```

### Step 4: MCP Inspector에서 HTTP 모드 연결

macOS/Linux:
```bash
uv run mcp dev src/server.py --transport streamable-http
```

Windows (PowerShell):
```powershell
uv run mcp dev src\server.py --transport streamable-http
```

Inspector에서:
1. Transport를 "Streamable HTTP"로 선택
2. URL에 `http://localhost:8000/mcp` 입력
3. Connect 클릭
4. Tools, Resources, Prompts가 모두 표시되는지 확인
5. `lookup_inventory` Tool 호출 테스트

### Step 5: stdio와 HTTP 비교

같은 서버, 두 가지 모드:

```
stdio 모드:
$ uv run python src/server.py
→ Claude Desktop이 프로세스를 직접 실행
→ stdin/stdout으로 통신
→ 1:1 연결

HTTP 모드:
$ uv run python src/server.py --transport streamable-http --port 8000
→ 서버가 독립 실행
→ HTTP로 통신
→ 여러 클라이언트 동시 접속 가능
→ curl, Inspector, Claude Desktop 모두 연결 가능
```

비즈니스 로직(Tool, Resource, Prompt)은 **동일**합니다. transport만 다릅니다.

---

## 3.5 멀티 LLM 클라이언트: 같은 서버, 다른 SDK (보너스)

MCP 서버를 만들면 **어떤 LLM에서든** 동일하게 사용할 수 있습니다.
하지만 LLM 제공자마다 MCP 도구를 호출하는 **SDK 코드**가 다릅니다.

### 왜 이것이 중요한가?

```
┌─────────────────────────────────────────────────┐
│        동일한 MCP 서버 (Internal Ops Assistant)    │
│        Tools: lookup_inventory, search_policy, ...│
└──────────────────┬──────────────────────────────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
  Anthropic     OpenAI       Google
  Claude API    Responses    Gemini API
  (tool_use)    (functions)  (function_calling)
```

**핵심 차이점:**

| 항목 | Anthropic Claude | OpenAI GPT | Google Gemini |
|------|-----------------|------------|--------------|
| **stdio 지원** | ✅ 지원 | ❌ 미지원 | ❌ 미지원 |
| **HTTP 지원** | ✅ 지원 | ✅ 지원 | ✅ 지원 |
| **도구 호출 방식** | `tool_use` block | `tool_calls` (function calling) | `function_call` in parts |
| **결과 반환** | `tool_result` | `role: "tool"` | `function_response` |

> **💡 중요:** OpenAI와 Google은 **stdio transport를 지원하지 않습니다.**
> 이들 SDK로 MCP 서버에 연결하려면 반드시 **Streamable HTTP** 모드로 서버를 실행해야 합니다.
> 이것이 HTTP transport가 프로덕션에서 필수인 또 다른 이유입니다.

### 3.5.1 Anthropic Claude — `tool_use` 패턴

Anthropic은 MCP의 창시자이므로 가장 자연스럽게 통합됩니다.
`mcp` Python SDK의 `ClientSession`으로 stdio/HTTP 모두 연결 가능하고,
Claude API의 `tool_use` 블록이 MCP tool schema와 1:1 대응합니다.

```python
import anthropic
from mcp import ClientSession

# 1. MCP 클라이언트로 도구 목록 가져오기
tools = await mcp_session.list_tools()

# 2. Claude API에 도구 전달 (MCP schema → Claude tool 형식)
claude_tools = [
    {
        "name": t.name,
        "description": t.description,
        "input_schema": t.inputSchema,
    }
    for t in tools
]

# 3. Claude에게 메시지 전송
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=claude_tools,
    messages=[{"role": "user", "content": "노트북 재고 알려줘"}],
)

# 4. tool_use 블록이 있으면 MCP로 실행
for block in response.content:
    if block.type == "tool_use":
        result = await mcp_session.call_tool(block.name, block.input)
        # result를 tool_result로 Claude에게 돌려주기
```

**핵심:** Claude의 `tool_use` → MCP `call_tool` → `tool_result` 루프.

### 3.5.2 OpenAI GPT — Function Calling 패턴

OpenAI는 자체 MCP 클라이언트 SDK를 제공하지 않습니다.
따라서 **HTTP 엔드포인트에 직접 연결**하거나, Python `mcp` SDK의 `streamablehttp_client`를 사용합니다.

> ⚠️ **OpenAI는 stdio를 지원하지 않습니다.** 반드시 HTTP 모드로 서버를 실행하세요.

```python
from openai import OpenAI
from mcp.client.streamable_http import streamablehttp_client

# 1. MCP 서버에 HTTP로 연결
async with streamablehttp_client("http://localhost:8000/mcp") as (r, w, _):
    async with ClientSession(r, w) as session:
        await session.initialize()
        tools = await session.list_tools()

# 2. OpenAI function calling 형식으로 변환
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": t.inputSchema,
        },
    }
    for t in tools
]

# 3. OpenAI에게 요청
response = client.chat.completions.create(
    model="gpt-4o",
    tools=openai_tools,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "노트북 재고 알려줘"},
    ],
)

# 4. tool_calls가 있으면 MCP로 실행
choice = response.choices[0]
if choice.finish_reason == "tool_calls":
    for tc in choice.message.tool_calls:
        args = json.loads(tc.function.arguments)
        result = await session.call_tool(tc.function.name, args)
        # role: "tool"로 OpenAI에게 돌려주기
```

**핵심:** OpenAI의 `tool_calls` → MCP `call_tool` → `role: "tool"` 루프.

### 3.5.3 Google Gemini — Function Calling 패턴

Google도 HTTP 연결만 지원합니다.

```python
from google import genai
from google.genai import types

# 1. MCP tools → Gemini FunctionDeclaration 변환
declarations = [
    types.FunctionDeclaration(
        name=t.name,
        description=t.description,
        parameters=t.inputSchema,
    )
    for t in tools
]

# 2. Gemini에게 요청
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[{"role": "user", "parts": [{"text": "노트북 재고 알려줘"}]}],
    config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=declarations)],
    ),
)

# 3. function_call이 있으면 MCP로 실행
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = await session.call_tool(
            part.function_call.name,
            dict(part.function_call.args),
        )
        # function_response로 Gemini에게 돌려주기
```

### 3.5.4 정리: 패턴은 동일하다

세 제공자 모두 **같은 패턴**을 따릅니다:

```
1. MCP에서 도구 목록 가져오기
2. 각 SDK 형식으로 변환
3. LLM에게 사용자 메시지 + 도구 전달
4. LLM이 도구 호출을 요청하면 → MCP로 실행
5. 결과를 LLM에게 반환
6. 반복 (agentic loop)
```

변환 레이어만 다를 뿐, MCP 서버 코드는 **완전히 동일**합니다.
이것이 MCP의 진정한 가치입니다 — **한 번 만들면 어디서든 쓴다.**

> 💡 **Gradio 데모 참고:** 프로젝트의 `ui/app.py`에서 세 가지 제공자를 모두 지원하는
> 멀티 LLM 채팅 UI를 확인할 수 있습니다. API 키를 입력하면 자동으로 제공자가 감지되어
> 드롭다운에 표시됩니다. 같은 MCP 서버에 대해 Claude, GPT, Gemini를 전환하며 비교해 보세요.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- stdio는 로컬 전용, 1:1 연결 — 개발/테스트에 적합
- Streamable HTTP는 원격 접속, 다중 클라이언트 — 프로덕션에 적합
- `mcp.run(transport="streamable-http")` 한 줄로 전환
- HTTP 엔드포인트: POST /mcp (요청), GET /mcp (SSE 스트림)
- CLI 인자로 transport를 선택하면 하나의 코드로 두 모드 지원
- **OpenAI/Google은 stdio 미지원** → HTTP가 멀티 LLM 호환의 필수 조건
- 도구 호출 패턴은 3사 모두 동일: 도구 목록 → 변환 → LLM 호출 → MCP 실행 → 결과 반환

### 퀴즈
1. Streamable HTTP가 stdio보다 프로덕션에 적합한 이유 두 가지는? → 원격 접속이 가능하고, 여러 클라이언트가 동시에 접속할 수 있으며, 로드밸런서 뒤에 배치 가능
2. transport 전환 시 비즈니스 로직(Tool/Resource/Prompt) 코드를 변경해야 하는가? → 아니오. MCP 프로토콜이 transport를 추상화하므로 비즈니스 로직은 그대로 사용
3. `POST /mcp`와 `GET /mcp`의 역할 차이는? → POST는 클라이언트의 JSON-RPC 요청을 수신하고, GET은 서버에서 클라이언트로의 SSE 이벤트 스트림을 제공
4. OpenAI SDK로 MCP 서버에 연결할 때 반드시 HTTP를 사용해야 하는 이유는? → OpenAI는 stdio transport를 지원하지 않으므로, 서버를 HTTP 모드로 실행해야 연결 가능

### 다음 편 예고
EP 18에서는 Streamable HTTP로 전환한 서버를 **Claude Desktop**에 연동합니다. `claude_desktop_config.json` 설정 방법, stdio/HTTP 모드별 설정 차이, 디버깅 팁까지 다룹니다.
