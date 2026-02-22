# EP 19 — Cursor / VS Code 연동

> Module D · 약 20분

## 학습 목표
1. Cursor에서 MCP 서버를 설정하고 개발 워크플로우에 활용한다
2. VS Code에서 MCP 확장을 구성한다
3. IDE 내에서 MCP 기반 개발 시나리오를 실습한다

---

## 1. 인트로 (2분)

EP 18에서 Claude Desktop에 MCP 서버를 연동했습니다. Claude Desktop은 일반 사용자에게 최적화된 인터페이스이지만, **개발자**에게는 IDE에서 직접 MCP를 사용하는 것이 더 효율적입니다.

Cursor와 VS Code — 가장 많이 사용되는 AI 코딩 에디터에서 MCP 서버를 연동하면, 코드를 작성하면서 동시에 재고 조회, 정책 확인, 티켓 생성을 할 수 있습니다.

"이 코드에 보안 취약점이 있는지 정책 기준으로 확인해줘" — 이런 요청을 IDE를 떠나지 않고 바로 처리할 수 있습니다.

---

## 2. 핵심 개념 (6분)

### 2.1 Cursor의 MCP 지원

Cursor는 AI 기능이 내장된 코드 에디터로, MCP를 네이티브하게 지원합니다.

설정 파일 위치: 프로젝트 루트의 `.cursor/mcp.json`

```
프로젝트/
├── .cursor/
│   └── mcp.json       ← MCP 서버 설정
├── src/
├── tests/
└── ...
```

**Cursor MCP 설정의 장점**:
- 프로젝트별 MCP 서버 설정 (전역이 아닌 프로젝트 스코프)
- Git에 포함하여 팀원과 설정 공유 가능
- Cursor의 AI 기능과 자연스럽게 통합

### 2.2 VS Code의 MCP 지원

VS Code도 MCP를 지원하며, 설정 방법이 비슷합니다.

설정 파일 위치: `.vscode/mcp.json` 또는 VS Code settings

```
프로젝트/
├── .vscode/
│   └── mcp.json       ← MCP 서버 설정
├── src/
└── ...
```

### 2.3 설정 파일 구조 비교

```
┌──────────────────────────────────────────────────────┐
│                설정 파일 비교                          │
├──────────────┬───────────────┬───────────────────────┤
│              │  Cursor        │  VS Code              │
├──────────────┼───────────────┼───────────────────────┤
│ 위치          │ .cursor/      │ .vscode/              │
│              │ mcp.json      │ mcp.json              │
├──────────────┼───────────────┼───────────────────────┤
│ 스코프        │ 프로젝트       │ 프로젝트               │
├──────────────┼───────────────┼───────────────────────┤
│ stdio        │ ✅             │ ✅                    │
├──────────────┼───────────────┼───────────────────────┤
│ HTTP         │ ✅             │ ✅                    │
├──────────────┼───────────────┼───────────────────────┤
│ 형식          │ 거의 동일      │ 거의 동일              │
└──────────────┴───────────────┴───────────────────────┘
```

### 2.4 개발 워크플로우에서의 MCP 활용

IDE에서 MCP를 사용하면 개발 워크플로우가 풍부해집니다:

```
┌─────────────────────────────────────────────────┐
│          IDE + MCP 활용 시나리오                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 코드 리뷰 + 정책 확인                        │
│     "이 코드가 보안 정책을 준수하는지 확인해줘"    │
│     → policy://security Resource 참조            │
│                                                 │
│  2. 장비 확인 + 요청 자동화                       │
│     "개발 서버용 모니터가 있는지 확인하고          │
│      없으면 구매 요청 티켓 만들어줘"              │
│     → lookup_inventory + create_ticket           │
│                                                 │
│  3. 인시던트 리포트 작성                          │
│     "이 에러 로그를 기반으로 인시던트 리포트        │
│      작성해줘"                                   │
│     → incident_report Prompt 활용                │
│                                                 │
│  4. 문서 기반 코딩                               │
│     "장비 관리 정책에 맞게 이 API를 수정해줘"      │
│     → policy://equipment-management 참조          │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2.5 Hot Reload 설정

개발 중 서버 코드를 수정할 때마다 재시작하는 것은 비효율적입니다. watchdog을 사용하여 파일 변경 시 자동으로 서버를 재시작합니다.

```bash
# watchfiles 패키지 설치
uv add --dev watchfiles
```

실행:

macOS/Linux:
```bash
uv run watchfiles "python src/server.py --transport streamable-http" src/
```

Windows (PowerShell):
```powershell
uv run watchfiles "python src\server.py --transport streamable-http" src\
```

---

## 3. 라이브 데모 (10분)

### Step 1: Cursor에서 MCP 설정

프로젝트 루트에 `.cursor/mcp.json`을 생성합니다:

macOS/Linux:
```bash
mkdir -p .cursor
```

Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Path .cursor -Force
```

**stdio 모드 설정** (`.cursor/mcp.json`):

macOS:
```json
{
  "mcpServers": {
    "acme-ops": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "src/server.py",
        "--transport", "stdio"
      ]
    }
  }
}
```

Windows:
```json
{
  "mcpServers": {
    "acme-ops": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "src\\server.py",
        "--transport", "stdio"
      ]
    }
  }
}
```

**HTTP 모드 설정** (서버가 별도 실행 중일 때):

```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Step 2: Cursor에서 MCP 서버 확인

1. Cursor를 열고 프로젝트 디렉토리를 엽니다
2. Cursor Settings (Cmd+Shift+J / Ctrl+Shift+J) → MCP 탭 확인
3. `acme-ops` 서버가 등록되어 있고 연결 상태 확인
4. 연결 실패 시 로그 확인

### Step 3: Cursor에서 실전 사용

Cursor의 Chat (Cmd+L / Ctrl+L) 또는 Composer에서 MCP 도구를 사용합니다:

**시나리오 1: 재고 기반 코드 작성**
```
모니터 재고를 확인하고, 재고가 부족하면 알림을 보내는 Python 함수를 작성해줘.
실제 재고 데이터를 참고해서 threshold를 설정해줘.
```
→ Cursor가 `lookup_inventory`로 실제 재고를 확인하고 코드에 반영

**시나리오 2: 정책 기반 코드 리뷰**
```
이 코드가 보안 정책을 준수하는지 확인해줘.
특히 비밀번호 처리와 USB 접근 부분을 중점적으로 봐줘.
```
→ Cursor가 `policy://security` Resource를 참고하여 코드 리뷰

### Step 4: VS Code에서 MCP 설정

`.vscode/mcp.json`을 생성합니다:

macOS/Linux:
```bash
mkdir -p .vscode
```

Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Path .vscode -Force
```

**VS Code MCP 설정** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "acme-ops": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "python",
        "src/server.py",
        "--transport", "stdio"
      ]
    }
  }
}
```

HTTP 모드:
```json
{
  "servers": {
    "acme-ops": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Step 5: VS Code에서 Copilot Chat과 MCP 연동

VS Code에서:
1. GitHub Copilot Chat 패널 열기 (Ctrl+Shift+I)
2. Agent Mode에서 MCP 도구 활용 가능
3. `@acme-ops` 등으로 MCP 서버 참조

```
@acme-ops 재고에서 노트북을 검색해줘
```

### Step 6: Hot Reload 개발 환경

서버를 HTTP 모드로 hot reload 실행:

macOS/Linux:
```bash
uv run watchfiles "python src/server.py --transport streamable-http --port 8000" src/
```

Windows (PowerShell):
```powershell
uv run watchfiles "python src\server.py --transport streamable-http --port 8000" src\
```

이제 `src/` 디렉토리의 파일이 변경되면 서버가 자동으로 재시작됩니다. IDE에서 코드를 수정하고 저장하면, MCP 서버가 즉시 업데이트됩니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- Cursor: `.cursor/mcp.json`에 MCP 서버 설정 (프로젝트 스코프)
- VS Code: `.vscode/mcp.json`에 설정 (Copilot Agent Mode에서 활용)
- stdio/HTTP 모드 모두 설정 가능, 형식이 거의 동일
- IDE에서 MCP를 활용하면 코드 리뷰+정책 확인, 재고 조회+코드 작성 등 가능
- watchfiles로 hot reload 설정하면 개발 중 서버 자동 재시작

### 퀴즈
1. Cursor와 Claude Desktop의 MCP 설정 스코프 차이는? → Claude Desktop은 전역 설정이고, Cursor는 프로젝트별 설정이다. Cursor의 설정은 Git에 포함하여 팀과 공유 가능
2. HTTP 모드를 IDE에서 사용할 때의 장점은? → 서버를 IDE와 독립적으로 관리하므로, IDE를 재시작해도 서버가 유지되고, 여러 IDE에서 같은 서버에 동시 접속 가능
3. Hot reload가 개발 워크플로우에서 중요한 이유는? → 서버 코드 수정 후 수동 재시작 없이 자동으로 반영되어, 빠른 개발-테스트 사이클이 가능

### 다음 편 예고
EP 20에서는 **SSE에서 Streamable HTTP로의 마이그레이션**을 다룹니다. 2025년 3월 MCP 스펙 변경으로 SSE transport가 deprecated되었습니다. 레거시 SSE 서버를 Streamable HTTP로 전환하는 방법과 하위 호환 전략을 배웁니다.
