# EP 02 — MCP 아키텍처 한눈에 보기

> Module A: MCP 기초 · 약 20분

## 학습 목표

1. MCP의 Host/Client/Server 3-tier 구조를 도식으로 설명할 수 있다
2. JSON-RPC 2.0 기반 메시지 포맷과 흐름을 이해할 수 있다
3. Transport 레이어(stdio, Streamable HTTP)의 차이를 비교할 수 있다

---

## 1. 인트로 (2분)

EP01에서 MCP가 **"무엇"**인지, 왜 필요한지를 배웠습니다. 이번 에피소드에서는 한 단계 더 들어가서 MCP가 **"어떻게"** 동작하는지를 살펴봅니다.

건물을 지으려면 설계도가 필요하듯, MCP 서버를 만들려면 아키텍처를 이해해야 합니다. Host, Client, Server가 각각 무엇이고, 이들 사이를 오가는 메시지는 어떤 형태이며, 통신은 어떤 채널로 이루어지는지 알아보겠습니다.

---

## 2. 핵심 개념 (6분)

### 2.1 3-Tier 구조: Host → Client → Server

MCP 아키텍처는 세 계층으로 구성됩니다:

```
┌─────────────────────────────────────┐
│            Host (호스트)              │
│  예: Claude Desktop, Cursor, IDE     │
│                                      │
│  ┌───────────────────────────────┐  │
│  │       Client (클라이언트)       │  │
│  │  프로토콜 계층 — 자동 관리      │  │
│  └──────────┬────────────────────┘  │
└─────────────┼───────────────────────┘
              │ JSON-RPC 2.0
              │ (stdio 또는 HTTP)
┌─────────────┴───────────────────────┐
│          Server (서버)               │
│  우리가 작성하는 코드                  │
│  Tools, Resources, Prompts 제공      │
└─────────────────────────────────────┘
```

**Host (호스트)**: 사용자가 직접 상호작용하는 애플리케이션입니다. Claude Desktop, Cursor, VS Code 같은 프로그램이 Host입니다. Host는 하나 이상의 Client를 생성하고 관리합니다.

**Client (클라이언트)**: MCP 프로토콜을 구현하는 계층입니다. 우리가 직접 코드를 작성하지 않습니다. Host 내부에서 자동으로 생성되어 Server와의 통신을 담당합니다. 하나의 Client는 하나의 Server와 1:1 연결을 유지합니다.

**Server (서버)**: **우리가 작성하는 코드**입니다. Tools, Resources, Prompts를 정의하고 Client의 요청에 응답합니다. 이 과정의 캡스톤 프로젝트 Internal Ops Assistant가 바로 Server입니다.

### 2.2 JSON-RPC 2.0 메시지 포맷

MCP는 JSON-RPC 2.0을 메시지 포맷으로 사용합니다. 세 가지 종류의 메시지가 있습니다:

**Request (요청)**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "lookup_inventory",
    "arguments": {
      "query": "노트북"
    }
  }
}
```

**Response (응답)**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "MacBook Pro 14\" - 재고: 23대"
      }
    ]
  }
}
```

**Notification (알림)** — `id` 필드 없음, 응답 불필요:
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

핵심 포인트: `id`가 있으면 응답을 기대하는 Request, `id`가 없으면 일방적 알림인 Notification입니다.

### 2.3 Transport 레이어

Client와 Server 사이의 통신 채널을 Transport라고 합니다. 두 가지 주요 Transport가 있습니다:

**stdio (Standard I/O)**:
- 서버가 자식 프로세스로 실행됨
- stdin/stdout으로 JSON-RPC 메시지 교환
- 로컬 환경에 적합 (같은 머신)
- 설정이 간단, 별도 포트 불필요
- Claude Desktop의 기본 Transport

**Streamable HTTP**:
- 서버가 HTTP 엔드포인트를 제공
- 단일 엔드포인트(`/mcp`)로 양방향 통신
- 원격 환경에 적합 (다른 머신, 클라우드)
- 방화벽 통과 가능, 표준 HTTP 인프라 활용
- SSE(Server-Sent Events)를 대체하는 최신 Transport

### 2.4 Capability Negotiation

서버가 시작되면 "나는 이런 기능을 제공합니다"라고 선언합니다. 이를 Capability Negotiation이라고 합니다.

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "resources": {
      "subscribe": true,
      "listChanged": true
    },
    "prompts": {
      "listChanged": true
    }
  }
}
```

클라이언트는 이 선언을 보고 사용 가능한 기능을 파악합니다. Tools만 지원하는 서버, Resources만 지원하는 서버, 전부 지원하는 서버 — 각각 다를 수 있습니다.

### 2.5 Session Lifecycle

MCP 세션은 명확한 라이프사이클을 가집니다:

```
1. Client → Server : initialize (request)
   - 프로토콜 버전, 클라이언트 정보 전송

2. Server → Client : initialize (response)
   - 서버 정보, capabilities 선언

3. Client → Server : notifications/initialized
   - "초기화 완료, 이제 시작하자"

4. Normal Operation
   - tools/list, tools/call
   - resources/list, resources/read
   - prompts/list, prompts/get

5. Client → Server : 연결 종료
   - Transport에 따라 프로세스 종료 또는 HTTP 세션 종료
```

`initialize` → `initialized` → 정상 운영 → 종료. 이 순서는 항상 동일합니다.

### 2.6 메시지 흐름 예시: Tool 호출

사용자가 Claude에게 "노트북 재고 알려줘"라고 말하면:

```
사용자 → Host(Claude Desktop): "노트북 재고 알려줘"
         │
Host → LLM: 사용자 메시지 + 사용 가능한 Tool 목록
         │
LLM → Host: "lookup_inventory(query='노트북') 호출하겠습니다"
         │
Host → Client: Tool 호출 요청
         │
Client → Server: tools/call JSON-RPC Request
         │
Server: lookup_inventory 함수 실행
         │
Server → Client: JSON-RPC Response (결과)
         │
Client → Host → LLM: Tool 실행 결과 전달
         │
LLM → Host → 사용자: "MacBook Pro 14인치 재고는 23대입니다."
```

---

## 3. 라이브 데모 (10분)

### Step 1: MCP Inspector 설치

MCP Inspector는 MCP 서버를 테스트하고 디버그하는 공식 도구입니다. 실시간으로 JSON-RPC 메시지를 확인할 수 있습니다.

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector
```

브라우저에서 `http://localhost:6274`가 열립니다.

### Step 2: 샘플 서버 연결

Inspector에서 Transport 타입을 `stdio`로 선택하고, 서버 실행 커맨드를 입력합니다:

macOS/Linux:
```bash
uv run python src/server.py
```

Windows (PowerShell):
```powershell
uv run python src\server.py
```

### Step 3: initialize 메시지 관찰

서버가 연결되면 Inspector의 로그 패널에서 initialize 메시지 교환을 확인합니다:

1. **Client → Server**: `initialize` request
   - `protocolVersion`: "2025-03-26"
   - `clientInfo`: Inspector 정보

2. **Server → Client**: `initialize` response
   - `serverInfo`: { "name": "ops-assistant", "version": "0.1.0" }
   - `capabilities`: { "tools": {}, "resources": {}, "prompts": {} }

3. **Client → Server**: `notifications/initialized`

### Step 4: tools/list 관찰

Inspector에서 "Tools" 탭을 클릭하면 내부적으로 `tools/list` 요청이 발생합니다:

```json
// Request
{ "jsonrpc": "2.0", "id": 2, "method": "tools/list" }

// Response
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "lookup_inventory",
        "description": "재고 데이터베이스에서 품목을 검색합니다",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": { "type": "string", "description": "검색 키워드" }
          },
          "required": ["query"]
        }
      }
    ]
  }
}
```

### Step 5: 메시지 흐름 정리

Inspector의 History 탭에서 전체 메시지 흐름을 시간 순으로 확인합니다. 모든 통신이 JSON-RPC 2.0 포맷을 따르고 있음을 직접 눈으로 확인할 수 있습니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- MCP는 **Host → Client → Server** 3-tier 구조로 동작한다
- 메시지는 **JSON-RPC 2.0** 포맷을 사용한다 (Request, Response, Notification)
- Transport는 **stdio**(로컬)와 **Streamable HTTP**(원격) 두 가지가 있다
- 세션은 **initialize → initialized → 정상 운영 → 종료** 순서로 진행된다
- **Capability Negotiation**으로 서버가 제공하는 기능을 선언한다

### 퀴즈

1. **stdio와 Streamable HTTP Transport의 차이는?**
   → stdio는 로컬 프로세스 간 stdin/stdout 통신, Streamable HTTP는 네트워크를 통한 HTTP 기반 통신. stdio는 로컬, HTTP는 원격에 적합.

2. **initialize 메시지에 포함되는 정보는?**
   → 클라이언트/서버 정보(이름, 버전), 프로토콜 버전, 서버의 capabilities(지원하는 기능 목록).

3. **JSON-RPC의 Request와 Notification의 차이는?**
   → Request는 `id` 필드가 있고 응답을 기대함. Notification은 `id`가 없고 일방적 알림.

### 다음 편 예고

EP03에서는 이론을 넘어 **직접 코드를 작성**합니다. FastMCP 라이브러리로 첫 번째 MCP 서버를 만들고, Claude Desktop에 연결해보겠습니다.
