---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 20 — SSE → Streamable HTTP 마이그레이션"
---

# EP 20 — SSE → Streamable HTTP 마이그레이션
## Module D · MCP 실전 마스터

---

## 학습 목표

1. SSE transport의 역사와 한계
2. SSE → Streamable HTTP 마이그레이션 절차
3. 하위 호환 전략

---

## MCP Transport 타임라인

```
2024 Q4   MCP 최초 발표
          - stdio: 로컬 통신
          - SSE: 원격 통신

2025 Q1   SSE 한계 노출
          - 단방향, 별도 POST 필요

2025.03   Streamable HTTP 도입
          - SSE deprecated

2025 Q4~  SSE 지원 단계적 종료
```

---

## SSE의 구조와 한계

```
SSE Transport (레거시):
  GET  /sse       → SSE 연결 (서버→클라이언트)
  POST /messages  → 메시지 전송 (클라이언트→서버)
```

**문제점:**
- 두 엔드포인트 간 세션 동기화
- 연결 끊김 시 복잡한 재연결
- 프록시/로드밸런서 호환 문제
- 서버→클라이언트만 스트림 (단방향)

---

## Streamable HTTP의 구조

```
Streamable HTTP (현재):
  POST /mcp  → 단일 엔드포인트
               요청: JSON-RPC
               응답: JSON 또는 SSE 스트림
```

**장점:**
- 단일 엔드포인트로 단순화
- 양방향 통신
- 표준 HTTP로 프록시 호환
- 세션 관리 간소화

---

## 마이그레이션 체크리스트

```
□ 1. MCP SDK 버전 업데이트 (>= 1.6.0)
□ 2. Transport 설정: "sse" → "streamable-http"
□ 3. 엔드포인트: GET /sse + POST /messages → POST /mcp
□ 4. 클라이언트 설정 업데이트
     - claude_desktop_config.json
     - .cursor/mcp.json
     - .vscode/mcp.json
□ 5. 프록시/로드밸런서 설정 업데이트
□ 6. 모니터링/헬스체크 업데이트
□ 7. 테스트 실행
```

---

## 서버 코드 변경

**이전 (SSE):**
```python
mcp.run(transport="sse", host="0.0.0.0", port=8001)
```

**이후 (Streamable HTTP):**
```python
mcp.run(transport="streamable-http",
        host="0.0.0.0", port=8000)
```

**비즈니스 로직 (Tool/Resource/Prompt) 변경 없음!**

---

## 클라이언트 설정 변경

**Claude Desktop — 이전:**
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

**Claude Desktop — 이후:**
```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## 하위 호환 전략

**전략 1: 라우팅 기반 (reverse proxy)**
```
신규 클라이언트 → POST /mcp  → MCP 서버
레거시 클라이언트 → GET /sse   → MCP 서버
```

**전략 2: 서버 인스턴스 분리**
```
port 8000 → Streamable HTTP
port 8001 → SSE (레거시)
```

**전략 3: 단계적 전환**
```
1. Streamable HTTP 추가
2. 클라이언트 업데이트 공지
3. SSE 사용량 모니터링
4. 충분히 전환되면 SSE 제거
```

---

## 과도기: 두 Transport 동시 지원

```python
parser.add_argument(
    "--transport",
    choices=["stdio", "streamable-http", "sse"],
    default="stdio",
)

if args.transport == "streamable-http":
    mcp.run(transport="streamable-http", port=8000)
elif args.transport == "sse":
    # 레거시 지원 (deprecation 로깅 권장)
    mcp.run(transport="sse", port=8001)
else:
    mcp.run(transport="stdio")
```

---

## 클라이언트별 지원 현황

| 클라이언트 | SSE | Streamable HTTP |
|-----------|-----|-----------------|
| Claude Desktop | O | O (우선) |
| Cursor | O | O |
| VS Code | O | O |
| MCP Inspector | O | O |
| 커스텀 클라이언트 | 구현 필요 | 구현 필요 |

**모든 주요 클라이언트가 Streamable HTTP 지원**

---

## 호환성 테스트

```bash
# 터미널 1: SSE (레거시)
uv run python src/server.py --transport sse --port 8001

# 터미널 2: Streamable HTTP (신규)
uv run python src/server.py \
  --transport streamable-http --port 8000

# Inspector로 각각 테스트
uv run mcp dev --transport sse \
  --url http://localhost:8001/sse

uv run mcp dev --transport streamable-http \
  --url http://localhost:8000/mcp
```

---

## 마이그레이션 완료

SSE 사용량이 충분히 줄면 레거시 제거:

```python
parser.add_argument(
    "--transport",
    choices=["stdio", "streamable-http"],  # sse 제거
    default="stdio",
)
```

- SSE 코드 정리
- 레거시 엔드포인트 제거
- 문서 업데이트

---

## 핵심 정리

- SSE → Streamable HTTP (2025.03 스펙 변경)
- SSE 한계: 별도 엔드포인트, 단방향
- Streamable HTTP: 단일 엔드포인트, 양방향, 표준 HTTP
- 마이그레이션: SDK 업데이트 + 설정 변경 + 클라이언트 업데이트
- 하위 호환: 과도기에 두 transport 동시 지원 가능

---

## 다음 편 예고

### EP 21: 캡스톤 리뷰 — 전체 시스템 점검

- 전체 아키텍처 다이어그램
- 코드 품질 체크리스트
- 확장 아이디어
- Core 트랙 수료!
