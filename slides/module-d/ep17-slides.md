---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 17 — Streamable HTTP Transport"
---

# EP 17 — Streamable HTTP Transport
## Module D · MCP 실전 마스터

---

## 학습 목표

1. stdio transport의 한계와 Streamable HTTP의 장점
2. FastMCP에서 transport 전환 방법
3. HTTP 모드 서버 실행 및 curl/Inspector 테스트

---

## stdio의 한계

```
Client ──spawn──→ MCP Server Process
       ←stdin/stdout→
```

- 로컬 전용 (같은 머신)
- 1:1 연결 (하나의 클라이언트)
- 클라이언트가 프로세스 관리
- 로드밸런싱 불가
- 모니터링 어려움

**개발에는 OK, 프로덕션에는 부족**

---

## Streamable HTTP의 장점

```
Client A ─┐
Client B ──┼──HTTP──→ MCP Server (port 8000)
Client C ─┘
```

- 원격 접속 (네트워크 통해)
- 다중 클라이언트 동시 접속
- 로드밸런서 뒤에 배치 가능
- 표준 HTTP 도구로 모니터링
- Docker/K8s 배포 용이
- CORS, 인증 헤더 활용

---

## HTTP 엔드포인트 구조

| Method | Path | 역할 |
|--------|------|------|
| `POST` | `/mcp` | JSON-RPC 요청/응답 (메인) |
| `GET` | `/mcp` | SSE 스트림 (서버→클라이언트 알림) |
| `DELETE` | `/mcp` | 세션 종료 |

```json
// POST /mcp 요청
{"jsonrpc": "2.0", "id": 1,
 "method": "tools/call",
 "params": {"name": "lookup_inventory",
            "arguments": {"query": "monitor"}}}
```

---

## Transport 전환: 한 줄!

```python
# stdio 모드 (기존)
mcp.run(transport="stdio")

# Streamable HTTP 모드 (새로운!)
mcp.run(transport="streamable-http",
        host="127.0.0.1", port=8000)
```

**Tool, Resource, Prompt 코드 변경 없음!**
Transport는 통신 레이어, 비즈니스 로직과 분리됨

---

## CLI 인자로 Transport 선택

```python
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
    mcp.run(transport="streamable-http",
            host=args.host, port=args.port)
else:
    mcp.run(transport="stdio")
```

---

## 데모: HTTP 모드 실행

```bash
# macOS/Linux
uv run python src/server.py \
  --transport streamable-http --port 8000

# Windows
uv run python src\server.py `
  --transport streamable-http --port 8000
```

```
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## 데모: curl로 JSON-RPC 요청

```bash
# 서버 초기화
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,
       "method":"initialize",
       "params":{"protocolVersion":"2025-03-26",
                 "capabilities":{},
                 "clientInfo":{"name":"curl","version":"1.0"}}}'

# Tool 호출
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,
       "method":"tools/call",
       "params":{"name":"lookup_inventory",
                 "arguments":{"query":"monitor"}}}'
```

---

## 데모: Inspector HTTP 모드

```bash
uv run mcp dev src/server.py --transport streamable-http
```

Inspector에서:
1. Transport: **Streamable HTTP** 선택
2. URL: `http://localhost:8000/mcp`
3. Connect
4. Tools, Resources, Prompts 모두 동작 확인

---

## stdio vs HTTP 비교

```
stdio:
  $ uv run python src/server.py
  → Claude Desktop이 프로세스 실행
  → stdin/stdout 통신
  → 1:1 연결

HTTP:
  $ uv run python src/server.py --transport streamable-http
  → 서버가 독립 실행
  → HTTP 통신
  → 여러 클라이언트 동시 접속
  → curl, Inspector, Claude Desktop 모두 연결
```

비즈니스 로직 **동일**, transport만 다름

---

## 프로덕션 고려사항

- `host="0.0.0.0"` 직접 노출 금지
- Reverse proxy (nginx, Caddy) 뒤에 배치
- TLS/HTTPS 설정
- 인증 헤더 (API Key, Bearer Token)
- Health check 엔드포인트

---

## 핵심 정리

- stdio: 로컬, 1:1 → 개발/테스트용
- Streamable HTTP: 원격, 다중 클라이언트 → 프로덕션
- `mcp.run(transport="streamable-http")` 한 줄로 전환
- POST /mcp (요청), GET /mcp (SSE 스트림)
- CLI 인자로 하나의 코드로 두 모드 지원

---

## 다음 편 예고

### EP 18: Claude Desktop 연동

- `claude_desktop_config.json` 설정
- stdio / HTTP 모드 설정 방법
- 실전 사용 시나리오 및 디버깅
