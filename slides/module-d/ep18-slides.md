---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 18 — Claude Desktop 연동"
---

# EP 18 — Claude Desktop 연동
## Module D · MCP 실전 마스터

---

## 학습 목표

1. Claude Desktop MCP 설정 파일 위치와 구조
2. stdio / HTTP 모드 각각의 설정 방법
3. 실전 사용 및 디버깅

---

## 설정 파일 위치

| OS | 경로 |
|----|------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "서버이름": {
      // stdio 또는 HTTP 설정
    }
  }
}
```

---

## stdio 모드 설정

Claude Desktop이 서버 프로세스를 **직접 실행**:

```json
{
  "mcpServers": {
    "acme-ops": {
      "command": "uv",
      "args": [
        "run", "python", "src/server.py",
        "--transport", "stdio"
      ],
      "cwd": "/path/to/acme-ops-assistant"
    }
  }
}
```

- `command`: 실행 명령어
- `args`: 인자 배열
- `cwd`: 작업 디렉토리

---

## HTTP 모드 설정

서버가 **이미 실행 중**이어야 함:

```json
{
  "mcpServers": {
    "acme-ops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

장점:
- 서버를 독립 관리
- 원격 서버 연결 가능
- 서버 재시작이 Claude Desktop에 영향 없음

---

## macOS vs Windows 경로 차이

**macOS (stdio)**:
```json
{
  "cwd": "/Users/yourname/mcp-course/acme-ops-assistant"
}
```

**Windows (stdio)**:
```json
{
  "args": ["run", "python", "src\\server.py", ...],
  "cwd": "C:\\Users\\yourname\\mcp-course\\acme-ops-assistant"
}
```

`\` 대신 `\\` (JSON 이스케이프)

---

## 설정 후 재시작 필수!

```bash
# macOS
osascript -e 'quit app "Claude"'
sleep 2
open -a Claude
```

```powershell
# Windows
Stop-Process -Name "Claude" -Force
Start-Sleep -Seconds 2
Start-Process "Claude"
```

**설정 변경 후 반드시 Claude Desktop 재시작**

---

## 연결 확인

1. Claude Desktop 대화창 좌측 하단 확인
2. MCP 서버 아이콘이 표시되는지 확인
3. 클릭 → Tool, Resource, Prompt 목록 확인

연결 실패 시:
- JSON 문법 오류 확인
- 경로 오타 확인
- 터미널에서 서버 단독 실행 테스트

---

## 실전 시나리오 1: 재고 검색

```
"IT 장비 재고에서 모니터를 검색해줘"
```

Claude 동작:
1. `lookup_inventory` Tool 호출
2. `query: "모니터"` 파라미터 전달
3. 검색 결과를 사용자에게 반환

---

## 실전 시나리오 2: 정책 확인

```
"원격근무 정책을 요약해줘"
```

Claude 동작:
1. `policy://remote-work` Resource 로드
2. 정책 전문을 컨텍스트로 참고
3. 요약문 생성

---

## 실전 시나리오 3: 복합 워크플로우

```
"보안 정책을 확인하고,
 USB 관련 내용을 정리한 후,
 USB 정책 위반 사례를 보고하는 티켓을 만들어줘."
```

Claude 동작:
1. [Resource] `policy://security` 로드
2. USB 관련 내용 추출/정리
3. [Prompt] `incident_report` 양식 활용
4. [Tool] `create_ticket` 호출

---

## 디버깅 체크리스트

```
1. JSON 문법    → 쉼표, 따옴표, 괄호
2. 경로 확인    → cwd, command 경로
3. 서버 단독 실행 → 터미널에서 직접 테스트
4. 로그 확인    → Claude Desktop 로그 파일
5. 재시작       → 설정 변경 후 필수
```

**로그 위치:**
- macOS: `~/Library/Logs/Claude/`
- Windows: `%APPDATA%\Claude\logs\`

---

## stdio vs HTTP: 어느 것을 선택?

| 상황 | 추천 |
|------|------|
| 로컬 개발/테스트 | stdio |
| 단일 사용자 | stdio |
| 팀 공유 서버 | HTTP |
| 원격 서버 | HTTP |
| CI/CD 통합 | HTTP |
| 간단한 설정 | stdio |

---

## 핵심 정리

- `claude_desktop_config.json`으로 MCP 서버 등록
- stdio: `command` + `args` + `cwd`
- HTTP: `url` (서버 별도 실행 필요)
- 설정 변경 후 Claude Desktop **재시작 필수**
- 디버깅: 로그 파일 + 서버 단독 실행 테스트

---

## 다음 편 예고

### EP 19: Cursor / VS Code 연동

- `.cursor/mcp.json` 설정
- `.vscode/mcp.json` 설정
- IDE 내 MCP 활용 워크플로우
