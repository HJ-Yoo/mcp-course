---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 19 — Cursor / VS Code 연동"
---

# EP 19 — Cursor / VS Code 연동
## Module D · MCP 실전 마스터

---

## 학습 목표

1. Cursor에서 MCP 서버 설정 및 활용
2. VS Code에서 MCP 확장 구성
3. IDE 내 MCP 기반 개발 워크플로우

---

## IDE에서 MCP를 사용하는 이유

- Claude Desktop = **일반 사용자**용
- Cursor / VS Code = **개발자**용

코드를 작성하면서 동시에:
- 재고 조회
- 정책 확인
- 티켓 생성
- 코드 리뷰 + 정책 준수 확인

**IDE를 떠나지 않고 모든 작업 수행**

---

## 설정 파일 비교

| 항목 | Cursor | VS Code |
|------|--------|---------|
| 위치 | `.cursor/mcp.json` | `.vscode/mcp.json` |
| 스코프 | 프로젝트별 | 프로젝트별 |
| Git 포함 | 가능 (팀 공유) | 가능 (팀 공유) |
| stdio | 지원 | 지원 |
| HTTP | 지원 | 지원 |

---

## Cursor: stdio 모드 설정

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "acme-ops": {
      "command": "uv",
      "args": [
        "run", "python",
        "src/server.py",
        "--transport", "stdio"
      ]
    }
  }
}
```

---

## Cursor: HTTP 모드 설정

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

서버를 먼저 실행:
```bash
uv run python src/server.py \
  --transport streamable-http --port 8000
```

---

## VS Code MCP 설정

`.vscode/mcp.json`:

```json
{
  "servers": {
    "acme-ops": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run", "python",
        "src/server.py",
        "--transport", "stdio"
      ]
    }
  }
}
```

HTTP 모드: `"type": "http"`, `"url": "http://localhost:8000/mcp"`

---

## Cursor에서 MCP 서버 확인

1. Cursor 열기 → 프로젝트 디렉토리
2. Settings (Cmd+Shift+J / Ctrl+Shift+J)
3. MCP 탭 → `acme-ops` 연결 상태 확인
4. Chat (Cmd+L / Ctrl+L) 에서 MCP 도구 사용

---

## 활용 시나리오 1: 재고 기반 코드 작성

```
모니터 재고를 확인하고,
재고가 부족하면 알림을 보내는
Python 함수를 작성해줘.
실제 재고 데이터를 참고해서 threshold를 설정해줘.
```

Cursor 동작:
1. `lookup_inventory` Tool로 실제 재고 확인
2. 실제 데이터 기반으로 코드 작성
3. threshold를 현실적인 값으로 설정

---

## 활용 시나리오 2: 정책 기반 코드 리뷰

```
이 코드가 보안 정책을 준수하는지 확인해줘.
특히 비밀번호 처리와 USB 접근 부분을
중점적으로 봐줘.
```

Cursor 동작:
1. `policy://security` Resource 참조
2. 실제 보안 정책 기준으로 코드 분석
3. 위반 사항과 개선 제안 제공

---

## Hot Reload 개발 환경

```bash
# watchfiles 설치
uv add --dev watchfiles

# 파일 변경 시 자동 재시작
# macOS/Linux
uv run watchfiles \
  "python src/server.py --transport streamable-http" src/

# Windows
uv run watchfiles `
  "python src\server.py --transport streamable-http" src\
```

`src/` 파일 수정 → 서버 자동 재시작 → IDE 즉시 반영

---

## 프로젝트별 설정의 장점

```
프로젝트 A/
├── .cursor/mcp.json  → 재고 관리 MCP
└── src/

프로젝트 B/
├── .cursor/mcp.json  → 고객 지원 MCP
└── src/
```

- 프로젝트마다 다른 MCP 서버
- Git에 포함 → 팀원과 설정 공유
- 전역 설정 오염 없음

---

## Cursor vs Claude Desktop

| 항목 | Claude Desktop | Cursor |
|------|---------------|--------|
| 대상 | 일반 사용자 | 개발자 |
| 설정 스코프 | 전역 | 프로젝트별 |
| Git 공유 | 불가 | 가능 |
| 코드 편집 | 없음 | 통합 |
| AI 기능 | 대화 중심 | 코드 생성 중심 |

---

## 핵심 정리

- Cursor: `.cursor/mcp.json` (프로젝트 스코프)
- VS Code: `.vscode/mcp.json` (프로젝트 스코프)
- stdio / HTTP 모두 지원, 형식 거의 동일
- IDE + MCP → 코드 리뷰+정책 확인, 재고 조회+코드 작성
- `watchfiles`로 hot reload → 빠른 개발 사이클

---

## 다음 편 예고

### EP 20: SSE → Streamable HTTP 마이그레이션

- SSE transport의 역사와 한계
- 마이그레이션 체크리스트
- 하위 호환 전략
