# EP 20 — SSE에서 Streamable HTTP로 마이그레이션

> Module D · 약 20분

## 학습 목표
1. SSE transport의 역사와 한계를 이해한다
2. SSE에서 Streamable HTTP로의 마이그레이션 절차를 수행한다
3. 하위 호환 전략으로 두 transport를 동시에 지원하는 방법을 익힌다

---

## 1. 인트로 (2분)

MCP 생태계는 빠르게 발전하고 있습니다. 초기에는 원격 통신을 위해 **SSE(Server-Sent Events)** transport를 사용했지만, 2025년 3월 MCP 스펙 개정으로 **Streamable HTTP**가 공식 transport로 지정되었습니다.

기존 SSE 서버를 운영 중이라면, 마이그레이션이 필요합니다. 하지만 모든 클라이언트가 한 번에 업데이트되지는 않으므로, 하위 호환 전략도 함께 고려해야 합니다.

이번 편에서는 SSE의 한계를 이해하고, Streamable HTTP로의 전환 방법과 호환 전략을 배웁니다.

---

## 2. 핵심 개념 (6분)

### 2.1 SSE Transport의 역사

```
┌─────────────────────────────────────────────────┐
│            MCP Transport 타임라인                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  2024 Q4  MCP 최초 발표                          │
│           - stdio: 로컬 통신                     │
│           - SSE: 원격 통신                       │
│                                                 │
│  2025 Q1  SSE의 한계 노출                        │
│           - 단방향 스트림 (서버→클라이언트만)       │
│           - 별도 POST 엔드포인트 필요              │
│           - 재연결 로직 복잡                      │
│                                                 │
│  2025.03  Streamable HTTP 도입                   │
│           - 양방향 통신 (단일 엔드포인트)           │
│           - SSE deprecated                       │
│                                                 │
│  2025 Q4~ SSE 지원 단계적 종료                    │
│           - 새 클라이언트는 Streamable HTTP 우선   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2.2 SSE의 한계

SSE transport는 두 개의 별도 엔드포인트가 필요했습니다:

```
SSE Transport (레거시):
  GET  /sse          → SSE 연결 수립 (서버→클라이언트 스트림)
  POST /messages     → 클라이언트→서버 메시지 전송

  문제점:
  - 두 엔드포인트 간 세션 동기화 필요
  - 연결 끊김 시 재연결 로직이 복잡
  - 프록시/로드밸런서에서 SSE 호환 문제
  - 서버→클라이언트만 스트림 (단방향)
```

```
Streamable HTTP (현재):
  POST /mcp          → 단일 엔드포인트
                       요청: JSON-RPC
                       응답: JSON 또는 SSE 스트림

  장점:
  - 단일 엔드포인트로 단순화
  - 양방향 통신
  - 표준 HTTP로 프록시 호환
  - 세션 관리 간소화
```

### 2.3 마이그레이션 체크리스트

SSE에서 Streamable HTTP로 전환하기 위한 체크리스트:

```
□ 1. MCP SDK 버전 업데이트
     - mcp >= 1.6.0 (Streamable HTTP 지원)

□ 2. Transport 설정 변경
     - "sse" → "streamable-http"

□ 3. 엔드포인트 변경
     - GET /sse + POST /messages → POST /mcp

□ 4. 클라이언트 설정 업데이트
     - claude_desktop_config.json
     - .cursor/mcp.json
     - .vscode/mcp.json

□ 5. 프록시/로드밸런서 설정 업데이트
     - 새 엔드포인트로 라우팅

□ 6. 모니터링/헬스체크 업데이트
     - 새 엔드포인트 기준으로 변경

□ 7. 테스트 실행
     - 통합 테스트로 전체 플로우 검증
```

### 2.4 하위 호환 전략

모든 클라이언트가 동시에 업데이트되지 않으므로, 과도기 동안 두 transport를 동시에 지원하는 전략이 필요합니다:

**전략 1: 라우팅 기반 (reverse proxy)**
```
클라이언트 A (신규) ──→ POST /mcp    ──→ MCP 서버
클라이언트 B (레거시) ──→ GET /sse     ──→ MCP 서버
```

**전략 2: 서버 인스턴스 분리**
```
신규 서버 (port 8000) ──→ Streamable HTTP
레거시 서버 (port 8001) ──→ SSE
```

**전략 3: 단계적 전환**
```
1단계: 새 서버에 Streamable HTTP 추가
2단계: 클라이언트에 업데이트 공지
3단계: SSE 사용량 모니터링
4단계: 충분히 전환되면 SSE 제거
```

### 2.5 클라이언트별 지원 현황

| 클라이언트 | SSE | Streamable HTTP | 비고 |
|-----------|-----|-----------------|------|
| Claude Desktop | ✅ | ✅ | Streamable HTTP 우선 |
| Cursor | ✅ | ✅ | 최신 버전 권장 |
| VS Code | ✅ | ✅ | Copilot Agent Mode |
| MCP Inspector | ✅ | ✅ | 둘 다 테스트 가능 |
| 커스텀 클라이언트 | 구현 필요 | 구현 필요 | SDK 사용 권장 |

---

## 3. 라이브 데모 (10분)

### Step 1: SSE 모드로 서버 실행 (레거시)

MCP Python SDK에서 SSE 모드를 확인합니다:

macOS/Linux:
```bash
# SSE 모드 (레거시 — deprecated)
uv run python src/server.py --transport sse --port 8001
```

Windows (PowerShell):
```powershell
# SSE 모드 (레거시 — deprecated)
uv run python src\server.py --transport sse --port 8001
```

SSE 모드의 엔드포인트:
```
GET  http://localhost:8001/sse        → SSE 연결
POST http://localhost:8001/messages   → 메시지 전송
```

### Step 2: server.py에 SSE 지원 추가 (마이그레이션 전)

레거시 SSE를 지원하려면 transport 선택에 "sse"를 추가합니다:

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],  # sse 추가
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        # 레거시 SSE 지원 (마이그레이션 기간 동안)
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")

    # 참고: SSE 모드에서 deprecation 경고 로그를 추가하면 좋습니다
```

### Step 3: Streamable HTTP로 전환

Streamable HTTP 모드로 실행:

macOS/Linux:
```bash
# Streamable HTTP 모드 (권장)
uv run python src/server.py --transport streamable-http --port 8000
```

Windows (PowerShell):
```powershell
# Streamable HTTP 모드 (권장)
uv run python src\server.py --transport streamable-http --port 8000
```

Streamable HTTP의 엔드포인트:
```
POST http://localhost:8000/mcp        → JSON-RPC 요청/응답 (또는 SSE 스트림)
GET  http://localhost:8000/mcp        → SSE 이벤트 스트림 (알림용)
```

### Step 4: 클라이언트 설정 마이그레이션

**Claude Desktop** — `claude_desktop_config.json`:

SSE (이전):
```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8001/sse",
      "transport": "sse"
    }
  }
}
```

Streamable HTTP (변경 후):
```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Cursor** — `.cursor/mcp.json`:

SSE (이전):
```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8001/sse",
      "transport": "sse"
    }
  }
}
```

Streamable HTTP (변경 후):
```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Step 5: 호환성 테스트

MCP Inspector로 두 모드를 모두 테스트합니다:

macOS/Linux:
```bash
# 터미널 1: SSE 서버 (레거시)
uv run python src/server.py --transport sse --port 8001

# 터미널 2: Streamable HTTP 서버 (신규)
uv run python src/server.py --transport streamable-http --port 8000

# 터미널 3: Inspector로 SSE 테스트
uv run mcp dev --transport sse --url http://localhost:8001/sse

# 터미널 4: Inspector로 Streamable HTTP 테스트
uv run mcp dev --transport streamable-http --url http://localhost:8000/mcp
```

Windows (PowerShell):
```powershell
# 각각 별도 터미널에서 실행
uv run python src\server.py --transport sse --port 8001
uv run python src\server.py --transport streamable-http --port 8000
```

두 서버 모두 동일한 Tool, Resource, Prompt를 제공하는지 확인합니다. 비즈니스 로직은 동일하고 transport만 다릅니다.

### Step 6: 마이그레이션 완료 판단

SSE 사용량이 충분히 줄었으면 SSE 지원을 제거합니다:

```python
# 마이그레이션 완료 후
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],  # sse 제거
        default="stdio",
    )
    # ...
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- SSE transport는 2025년 3월 deprecated, Streamable HTTP가 공식 transport
- SSE의 한계: 별도 엔드포인트, 단방향 스트림, 복잡한 재연결
- Streamable HTTP의 장점: 단일 엔드포인트, 양방향, 표준 HTTP 호환
- 마이그레이션은 SDK 업데이트 + transport 설정 변경 + 클라이언트 설정 업데이트
- 하위 호환: 과도기에 두 transport를 동시 지원 가능

### 퀴즈
1. SSE에서 GET /sse와 POST /messages가 별도로 필요했던 이유는? → SSE는 서버→클라이언트 단방향 스트림이므로, 클라이언트→서버 메시지는 별도 POST 엔드포인트가 필요했다
2. Streamable HTTP로 마이그레이션 시 비즈니스 로직 변경이 필요한가? → 아니오. Transport는 통신 계층이므로 Tool, Resource, Prompt 코드는 변경 없이 그대로 사용 가능
3. 하위 호환을 위한 가장 실용적인 전략은? → 과도기 동안 SSE와 Streamable HTTP를 동시에 지원하고, SSE 사용량을 모니터링하여 충분히 전환되면 SSE를 제거하는 단계적 전환 전략

### 다음 편 예고
EP 21, 마지막 편에서는 **캡스톤 리뷰**를 진행합니다. Module A~D에서 구현한 모든 것을 정리하고, 전체 아키텍처를 점검하며, 향후 확장 방향을 논의합니다. Acme Corp Internal Ops Assistant의 완성입니다.
