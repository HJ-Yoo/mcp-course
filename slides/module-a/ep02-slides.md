---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 02 — MCP 아키텍처 한눈에 보기"
---

# EP 02 — MCP 아키텍처 한눈에 보기
## Module A: MCP 기초 · MCP 실전 마스터

---

## 학습 목표

1. Host/Client/Server 3-tier 구조를 도식으로 설명할 수 있다
2. JSON-RPC 2.0 기반 메시지 포맷과 흐름을 이해한다
3. Transport 레이어(stdio, Streamable HTTP)의 차이를 비교할 수 있다

---

## 3-Tier 구조

```
┌──────────────────────────────┐
│     Host (Claude Desktop)     │
│  ┌────────────────────────┐  │
│  │   Client (프로토콜 계층)  │  │
│  └──────────┬─────────────┘  │
└─────────────┼────────────────┘
              │  JSON-RPC 2.0
┌─────────────┴────────────────┐
│     Server (우리 코드)         │
│  Tools / Resources / Prompts  │
└──────────────────────────────┘
```

---

## 각 계층의 역할

| 계층 | 역할 | 예시 | 우리가 코딩? |
|------|------|------|------------|
| **Host** | 사용자 UI | Claude Desktop, Cursor | X |
| **Client** | 프로토콜 관리 | 자동 생성 (Host 내부) | X |
| **Server** | 기능 제공 | Internal Ops Assistant | **O** |

우리가 작성하는 것은 **Server**뿐!

---

## JSON-RPC 2.0: Request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "lookup_inventory",
    "arguments": { "query": "노트북" }
  }
}
```

- `id` 있음 → 응답 기대
- `method` → 호출할 기능
- `params` → 전달할 데이터

---

## JSON-RPC 2.0: Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "MacBook Pro 14\" - 재고: 23대"
    }]
  }
}
```

- `id`가 Request와 매칭
- `result`에 실행 결과

---

## JSON-RPC 2.0: Notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

- **`id` 없음** → 응답 불필요
- 일방적 알림 메시지

---

## Transport: stdio vs Streamable HTTP

| 기준 | stdio | Streamable HTTP |
|------|-------|----------------|
| 통신 | stdin/stdout | HTTP 엔드포인트 |
| 환경 | 로컬 (같은 머신) | 원격 (네트워크) |
| 설정 | 간단 | 포트/CORS 필요 |
| 보안 | 프로세스 격리 | HTTPS + 인증 |
| 사용처 | Claude Desktop | 클라우드 배포 |

---

## Capability Negotiation

서버가 선언: "나는 이런 기능을 제공합니다"

```json
{
  "capabilities": {
    "tools": { "listChanged": true },
    "resources": { "subscribe": true },
    "prompts": { "listChanged": true }
  }
}
```

클라이언트는 이 선언을 보고 사용 가능한 기능을 파악

---

## Session Lifecycle

```
1. Client → Server : initialize (request)
2. Server → Client : initialize (response + capabilities)
3. Client → Server : notifications/initialized
4. ── 정상 운영 ──
   tools/list, tools/call
   resources/list, resources/read
   prompts/list, prompts/get
5. 연결 종료
```

---

## 메시지 흐름 예시: Tool 호출

```
사용자 → "노트북 재고 알려줘"
  → Host → LLM (사용자 메시지 + Tool 목록)
    → LLM 판단: lookup_inventory 호출
      → Client → Server: tools/call
        → Server: 함수 실행
      → Server → Client: 결과 반환
    → LLM: 결과를 자연어로 변환
  → "MacBook Pro 14인치 재고는 23대입니다."
```

---

## 데모: MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

- 브라우저에서 `http://localhost:6274` 열기
- Transport: stdio 선택
- 서버 연결 후 메시지 실시간 관찰
- initialize → tools/list → tools/call 순서 확인

---

## 핵심 정리

- **Host → Client → Server** 3-tier 구조
- **JSON-RPC 2.0**: Request(id 있음), Response, Notification(id 없음)
- **Transport**: stdio(로컬) vs Streamable HTTP(원격)
- **Capability Negotiation**: 서버가 기능을 선언
- **Session Lifecycle**: initialize → initialized → 운영 → 종료

---

## 퀴즈

1. stdio와 Streamable HTTP Transport의 차이는?
   → stdio는 로컬 프로세스 간 통신, HTTP는 네트워크 기반. 로컬 vs 원격.

2. JSON-RPC Request와 Notification의 차이는?
   → Request는 `id`가 있어 응답 기대, Notification은 `id` 없이 일방적 알림.

---

## 다음 편 예고

### EP 03: 첫 번째 MCP 서버 만들기

- FastMCP 라이브러리로 서버 초기화
- Lifespan 패턴으로 데이터 로딩
- Claude Desktop 연결 확인
