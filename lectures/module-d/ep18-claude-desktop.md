# EP 18 — Claude Desktop 연동

> Module D · 약 20분

## 학습 목표
1. Claude Desktop의 MCP 설정 파일 위치와 구조를 이해한다
2. stdio 모드와 HTTP 모드 각각의 설정 방법을 익힌다
3. Claude Desktop에서 Acme Ops Assistant를 실전 사용하고 디버깅한다

---

## 1. 인트로 (2분)

지금까지 MCP Inspector와 curl로 서버를 테스트했습니다. 이번에는 실제 최종 사용자가 사용할 **Claude Desktop**에 연동합니다.

Claude Desktop은 Anthropic의 공식 데스크톱 앱으로, MCP 서버를 플러그인처럼 연결하여 Claude에게 새로운 능력을 부여할 수 있습니다. 설정 파일 하나면 됩니다.

EP 17에서 stdio와 Streamable HTTP 두 가지 transport를 지원하도록 만들었으니, Claude Desktop에서도 두 가지 방식 모두 설정해 보겠습니다.

---

## 2. 핵심 개념 (6분)

### 2.1 claude_desktop_config.json

Claude Desktop은 JSON 설정 파일로 MCP 서버를 등록합니다.

**파일 위치**:

| OS | 경로 |
|-----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

### 2.2 설정 구조

```json
{
  "mcpServers": {
    "서버이름": {
      // stdio 모드 또는 HTTP 모드 설정
    }
  }
}
```

`mcpServers` 아래에 여러 MCP 서버를 등록할 수 있습니다. 각 서버는 고유한 이름으로 식별됩니다.

### 2.3 stdio 모드 설정

stdio 모드에서는 Claude Desktop이 MCP 서버 프로세스를 직접 실행합니다:

```json
{
  "mcpServers": {
    "internal-ops-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py", "--transport", "stdio"],
      "cwd": "/path/to/acme-ops-assistant"
    }
  }
}
```

설정 항목:
- `command`: 실행할 명령어 (`uv`)
- `args`: 명령어 인자 배열
- `cwd`: 작업 디렉토리 (프로젝트 루트)

### 2.4 HTTP 모드 설정

HTTP 모드에서는 서버가 이미 실행되어 있어야 합니다:

```json
{
  "mcpServers": {
    "internal-ops-assistant": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

HTTP 모드의 장점:
- 서버를 별도로 관리 (Claude Desktop과 독립)
- 서버 재시작 없이 설정 변경 가능
- 원격 서버 연결 가능

### 2.5 디버깅 방법

Claude Desktop이 MCP 서버와 통신에 실패할 때 확인할 사항:

```
┌─────────────────────────────────────────────────┐
│          디버깅 체크리스트                         │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 설정 파일 문법                               │
│     - JSON 문법 오류 없는지 확인                  │
│     - 쉼표, 따옴표, 괄호 확인                    │
│                                                 │
│  2. 경로 확인                                    │
│     - cwd가 올바른 프로젝트 경로인지               │
│     - command가 시스템 PATH에 있는지              │
│                                                 │
│  3. 서버 단독 실행 테스트                         │
│     - 터미널에서 직접 서버 실행                    │
│     - 에러 메시지 확인                           │
│                                                 │
│  4. Claude Desktop 로그                          │
│     macOS: ~/Library/Logs/Claude/                │
│     Windows: %APPDATA%\Claude\logs\              │
│                                                 │
│  5. Claude Desktop 재시작                        │
│     - 설정 변경 후 반드시 재시작 필요              │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 3. 라이브 데모 (10분)

### Step 1: stdio 모드 설정

먼저 stdio 모드로 설정합니다.

macOS:
```bash
# 설정 파일 열기 (없으면 생성)
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Windows (PowerShell):
```powershell
# 설정 파일 열기 (없으면 생성)
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

설정 내용:

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
      ],
      "cwd": "/Users/yourname/mcp-course/acme-ops-assistant"
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
      ],
      "cwd": "C:\\Users\\yourname\\mcp-course\\acme-ops-assistant"
    }
  }
}
```

**중요**: `cwd`를 실제 프로젝트 경로로 변경하세요.

### Step 2: Claude Desktop 재시작

설정 파일을 저장한 후 Claude Desktop을 완전히 종료하고 다시 실행합니다.

macOS:
```bash
# Claude Desktop 종료
osascript -e 'quit app "Claude"'
# 잠시 대기 후 실행
sleep 2
open -a Claude
```

Windows (PowerShell):
```powershell
# Claude Desktop 종료
Stop-Process -Name "Claude" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
# Claude Desktop 실행 (설치 경로에 따라 다를 수 있음)
Start-Process "Claude"
```

### Step 3: 연결 확인

Claude Desktop 대화창에서:
1. 좌측 하단에 MCP 서버 아이콘이 표시되는지 확인
2. 아이콘을 클릭하면 `acme-ops` 서버의 Tool, Resource, Prompt 목록이 표시됨

### Step 4: 실전 사용 시나리오

**시나리오 1: 재고 검색**
```
"IT 장비 재고에서 모니터를 검색해줘"
```
→ Claude가 `lookup_inventory` Tool을 호출하여 모니터 재고 정보 반환

**시나리오 2: 정책 확인**
```
"원격근무 정책을 요약해줘"
```
→ Claude가 `policy://remote-work` Resource를 로드하여 정책 요약

**시나리오 3: 티켓 생성**
```
"3층 프린터가 고장났어. 수리 티켓을 만들어줘."
```
→ Claude가 사용자에게 상세 정보를 확인한 후 `create_ticket` Tool 호출

**시나리오 4: 복합 워크플로우**
```
"보안 정책을 확인하고, USB 관련 내용을 정리한 후,
USB 정책 위반 사례를 보고하는 티켓을 만들어줘."
```
→ Claude가 Resource → Tool → Prompt를 조합하여 작업 수행

### Step 5: HTTP 모드로 전환

서버를 HTTP 모드로 별도 실행합니다:

macOS/Linux:
```bash
uv run python src/server.py --transport streamable-http --port 8000
```

Windows (PowerShell):
```powershell
uv run python src\server.py --transport streamable-http --port 8000
```

설정 파일을 HTTP 모드로 변경합니다:

```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Claude Desktop을 재시작하고 동일한 시나리오를 테스트합니다. 사용자 경험은 동일하지만, 통신 방식이 stdio에서 HTTP로 바뀌었습니다.

### Step 6: 디버깅 실습

의도적으로 에러를 발생시켜 디버깅 방법을 익힙니다:

1. **경로 오타**: `cwd`를 잘못된 경로로 설정 → 서버 시작 실패
2. **포트 충돌**: 이미 사용 중인 포트 지정 → 연결 실패

macOS 로그 확인:
```bash
# Claude Desktop MCP 로그
ls ~/Library/Logs/Claude/
cat ~/Library/Logs/Claude/mcp*.log
```

Windows 로그 확인:
```powershell
Get-ChildItem "$env:APPDATA\Claude\logs\"
Get-Content "$env:APPDATA\Claude\logs\mcp*.log"
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- Claude Desktop은 `claude_desktop_config.json`으로 MCP 서버 등록
- macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`
- stdio 모드: `command` + `args` + `cwd` 설정
- HTTP 모드: `url` 설정 (서버가 별도 실행되어 있어야 함)
- 설정 변경 후 Claude Desktop 재시작 필수
- 디버깅: Claude Desktop 로그 파일 확인

### 퀴즈
1. stdio 모드와 HTTP 모드 설정의 가장 큰 차이는? → stdio는 Claude Desktop이 서버 프로세스를 직접 spawn하지만, HTTP는 이미 실행 중인 서버의 URL만 지정한다
2. 설정 파일 변경 후 무엇을 해야 하는가? → Claude Desktop을 완전히 종료하고 다시 실행해야 새 설정이 적용된다
3. MCP 서버 연결 실패 시 가장 먼저 확인할 것은? → Claude Desktop의 로그 파일에서 에러 메시지를 확인하고, 터미널에서 서버를 직접 실행하여 단독 동작 여부를 테스트

### 다음 편 예고
EP 19에서는 개발 환경인 **Cursor와 VS Code**에서 MCP 서버를 연동합니다. 개발 중에 MCP 서버를 활용하여 코드 리뷰, 정책 확인 등을 IDE 내에서 직접 수행하는 워크플로우를 구축합니다.
