# EP 21 — 캡스톤 리뷰: 전체 시스템 점검

> Module D · 약 20분

## 학습 목표
1. 프로젝트 전체 아키텍처를 다이어그램으로 정리하고 리뷰한다
2. 코드 품질 체크리스트로 보안, 에러 처리, 테스트를 점검한다
3. 향후 확장 포인트를 식별하고 다음 단계를 설계한다

---

## 1. 인트로 (2분)

축하합니다. EP 1부터 EP 21까지, 우리는 MCP 프로토콜을 이해하고 실전 프로젝트를 완성했습니다.

지금부터 전체를 돌아봅니다. 각 모듈에서 무엇을 했고, 어떤 기술을 익혔고, 최종 결과물이 어떤 구조인지 — 큰 그림을 정리합니다.

그리고 코드 품질 체크리스트로 우리 프로젝트를 점검합니다. 프로덕션에 배포하기 전에 확인해야 할 항목들입니다.

마지막으로, 이 프로젝트를 어떻게 확장할 수 있는지 — 다음 단계를 논의합니다.

---

## 2. 핵심 개념 (6분)

### 2.1 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    Acme Internal Ops Assistant                    │
│                         MCP Server                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    Transport Layer                        │    │
│  │                                                          │    │
│  │   stdio (로컬)  ←→  MCP Protocol  ←→  Streamable HTTP    │    │
│  │                      (JSON-RPC)        (원격, 멀티)       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                  FastMCP Framework                        │    │
│  │                                                          │    │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │    │
│  │  │   Tools    │  │ Resources  │  │    Prompts       │   │    │
│  │  │            │  │            │  │                  │   │    │
│  │  │ lookup_    │  │ policy://  │  │ incident_report  │   │    │
│  │  │ inventory  │  │ index      │  │ policy_answer    │   │    │
│  │  │            │  │            │  │                  │   │    │
│  │  │ search_    │  │ policy://  │  └──────────────────┘   │    │
│  │  │ policy     │  │ {doc_id}   │                         │    │
│  │  │            │  │            │                         │    │
│  │  │ create_    │  └────────────┘                         │    │
│  │  │ ticket     │                                         │    │
│  │  └────────────┘                                         │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                 Application Layer                         │    │
│  │                                                          │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐     │    │
│  │  │ Validation │  │  Audit     │  │   AppContext    │     │    │
│  │  │            │  │  Logger    │  │                │     │    │
│  │  │ priority   │  │  JSONL     │  │ inventory[]    │     │    │
│  │  │ text_len   │  │  thread-   │  │ policies[]     │     │    │
│  │  │ query      │  │  safe      │  │ tickets_path   │     │    │
│  │  │ doc_id     │  │            │  │ audit_logger   │     │    │
│  │  └────────────┘  └────────────┘  └────────────────┘     │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    Data Layer                             │    │
│  │                                                          │    │
│  │  inventory.csv    policies/*.md    tickets.jsonl          │    │
│  │  (30+ IT items)   (5 policy docs)  (append-only)          │    │
│  │                                                          │    │
│  │  logs/audit_YYYY-MM-DD.jsonl   (감사 로그)                │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

             연결 가능한 클라이언트:
      ┌──────────────────────────────────────┐
      │  Claude Desktop  │  Cursor  │ VS Code│
      └──────────────────────────────────────┘
```

### 2.2 모듈별 학습 내용 정리

```
Module A: 기초 (EP 1~4)
─────────────────────
- MCP 프로토콜 이해
- JSON-RPC, 클라이언트-서버 모델
- FastMCP 설치, 첫 서버 실행
- MCP Inspector 사용법

Module B: 핵심 구현 (EP 5~9)
─────────────────────────
- lifespan 패턴, AppContext
- Tool 구현 (lookup_inventory, search_policy, create_ticket)
- 입력 검증, 에러 처리
- Confirm gate, 멱등성

Module C: 리소스, 프롬프트, 품질 (EP 10~16)
──────────────────────────────────────────
- Resource 기초와 실전 구현
- Path traversal 보안
- Prompt Template
- 감사 로깅 (AuditLogger)
- pytest 테스트 전략
- 통합 테스트, CI 파이프라인

Module D: 배포와 통합 (EP 17~21)
──────────────────────────────
- Streamable HTTP Transport
- Claude Desktop 연동
- Cursor / VS Code 연동
- SSE 마이그레이션
- 캡스톤 리뷰 (이번 편)
```

### 2.3 코드 리뷰 체크리스트

프로덕션 배포 전 확인할 항목:

```
보안 (Security)
──────────────
□ validate_doc_id()로 path traversal 방어
□ sanitize_query()로 입력 새니타이징
□ validate_priority()로 우선순위 검증
□ validate_text_length()로 텍스트 길이 제한
□ 민감한 데이터가 로그에 포함되지 않는지 확인

에러 처리 (Error Handling)
────────────────────────
□ 모든 Tool에 try/except 적용
□ ToolError로 구조화된 에러 반환
□ ErrorCode로 에러 유형 분류
□ 존재하지 않는 Resource 요청 시 적절한 에러

로깅 (Logging)
─────────────
□ AuditLogger가 모든 Tool 호출 기록
□ 성공/실패 모두 기록
□ 처리 시간(duration_ms) 기록
□ 로그 파일 rotation 고려 (프로덕션)

테스트 (Testing)
───────────────
□ 입력 검증 단위 테스트
□ 보안 테스트 (공격 패턴)
□ 감사 로깅 테스트
□ 통합 테스트 (전체 플로우)
□ CI 파이프라인 구성

배포 (Deployment)
────────────────
□ stdio / Streamable HTTP 모드 모두 동작
□ Claude Desktop 설정 검증
□ Cursor / VS Code 설정 검증
□ 환경별 설정 분리 (dev / staging / prod)
```

### 2.4 구현 현황 요약

| 카테고리 | 항목 | 수량 |
|---------|------|------|
| Tools | lookup_inventory, search_policy, create_ticket | 3 |
| Resources | policy://index, policy://{doc_id} | 2 |
| Prompts | incident_report, policy_answer | 2 |
| Validation | validate_priority, validate_text_length, sanitize_query, validate_doc_id | 4 |
| Models | InventoryItem, PolicyDoc, Ticket, AppContext, ToolError, ErrorCode | 6 |
| Transports | stdio, Streamable HTTP | 2 |
| Clients | Claude Desktop, Cursor, VS Code | 3 |
| Tests | 단위 테스트, 보안 테스트, 감사 로깅 테스트, 통합 테스트 | 4종 |

### 2.5 확장 아이디어

```
┌─────────────────────────────────────────────────┐
│              향후 확장 방향                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 데이터베이스 연동                             │
│     - CSV → SQLite/PostgreSQL                   │
│     - 실시간 재고 관리                            │
│     - 검색 성능 향상                              │
│                                                 │
│  2. 알림 시스템                                   │
│     - 티켓 생성 시 Slack 알림                     │
│     - 재고 부족 시 자동 알림                      │
│     - 정책 변경 시 팀 공지                        │
│                                                 │
│  3. 대시보드                                      │
│     - 감사 로그 시각화                            │
│     - 도구 사용 통계                              │
│     - 티켓 현황 대시보드                          │
│                                                 │
│  4. 인증/인가                                     │
│     - 사용자 인증 (OAuth, API Key)                │
│     - 역할 기반 접근 제어 (RBAC)                  │
│     - Tool별 권한 관리                            │
│                                                 │
│  5. 추가 Tool                                    │
│     - JIRA 연동                                  │
│     - GitHub Issue 연동                          │
│     - 캘린더/미팅 관리                            │
│     - 지식 베이스 검색                            │
│                                                 │
│  6. Sampling (LLM 호출)                          │
│     - 서버 측에서 LLM 호출                        │
│     - 자동 분류, 요약 기능                        │
│     - 티켓 자동 우선순위 결정                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 3. 라이브 데모 (10분)

### Step 1: 전체 테스트 스위트 실행

프로젝트의 모든 테스트를 한 번에 실행하여 최종 검증합니다.

macOS/Linux:
```bash
cd ~/mcp-course/acme-ops-assistant

# 전체 테스트 실행 (커버리지 포함)
uv run pytest --cov=src --cov-report=term-missing -v
```

Windows (PowerShell):
```powershell
cd $HOME\mcp-course\acme-ops-assistant

# 전체 테스트 실행 (커버리지 포함)
uv run pytest --cov=src --cov-report=term-missing -v
```

기대 결과:
```
tests/test_validation.py ............          [ 30%]
tests/test_security.py ...............         [ 60%]
tests/test_audit.py ......                     [ 75%]
tests/test_integration.py ..........           [100%]

---------- coverage ----------
TOTAL                         93%

==================== 35+ passed ====================
```

### Step 2: 감사 로그 분석

프로젝트 운영 중 생성된 감사 로그를 분석합니다.

macOS/Linux:
```bash
# 최근 로그 파일 확인
ls -la logs/

# 도구별 사용 통계
cat logs/audit_2026-*.jsonl | jq -r '.tool_name' | sort | uniq -c | sort -rn

# 실패한 요청 필터링
cat logs/audit_2026-*.jsonl | jq 'select(.success == false)'

# 평균 응답 시간
cat logs/audit_2026-*.jsonl | jq '[.duration_ms // 0] | add / length'
```

Windows (PowerShell):
```powershell
# 최근 로그 파일 확인
Get-ChildItem logs\

# 전체 로그 내용 확인
Get-Content logs\audit_2026-*.jsonl | ForEach-Object {
    $_ | ConvertFrom-Json
} | Format-Table tool_name, success, duration_ms
```

### Step 3: 프로젝트 구조 최종 확인

macOS/Linux:
```bash
# 프로젝트 트리 출력
find . -type f -not -path './.venv/*' -not -path './.git/*' -not -path './__pycache__/*' | sort
```

Windows (PowerShell):
```powershell
Get-ChildItem -Recurse -File | Where-Object {
    $_.FullName -notmatch '\.venv|\.git|__pycache__'
} | Select-Object -ExpandProperty FullName | Sort-Object
```

최종 프로젝트 구조:
```
acme-ops-assistant/
├── pyproject.toml
├── src/
│   ├── server.py              # 메인 서버 (FastMCP + lifespan)
│   ├── models.py              # 데이터 모델
│   ├── validation.py          # 입력 검증 함수
│   ├── audit.py               # AuditLogger
│   ├── tools/
│   │   ├── inventory_tool.py  # lookup_inventory
│   │   ├── policy_tool.py     # search_policy
│   │   └── ticket_tool.py     # create_ticket
│   ├── resources/
│   │   └── policy_resource.py # policy://index, policy://{doc_id}
│   └── prompts/
│       └── ops_prompts.py     # incident_report, policy_answer
├── data/
│   ├── inventory.csv          # 30+ IT 장비 목록
│   ├── policies/              # 5개 정책 마크다운
│   └── tickets.jsonl          # 티켓 저장소
├── logs/
│   └── audit_YYYY-MM-DD.jsonl # 감사 로그
├── tests/
│   ├── conftest.py            # 공유 fixture
│   ├── test_validation.py     # 입력 검증 테스트
│   ├── test_security.py       # 보안 테스트
│   ├── test_audit.py          # 감사 로깅 테스트
│   └── test_integration.py    # 통합 테스트
├── .github/
│   └── workflows/
│       └── test.yml           # CI 파이프라인
├── .cursor/
│   └── mcp.json               # Cursor MCP 설정
└── .vscode/
    └── mcp.json               # VS Code MCP 설정
```

### Step 4: 최종 동작 확인

세 가지 클라이언트에서 전체 플로우를 확인합니다:

**MCP Inspector** (개발자 도구):
macOS/Linux:
```bash
uv run mcp dev src/server.py
```

Windows (PowerShell):
```powershell
uv run mcp dev src\server.py
```

**Claude Desktop** (최종 사용자):
- claude_desktop_config.json 설정 확인
- "모니터 재고 검색해줘" → Tool 동작 확인
- "보안 정책 요약해줘" → Resource 동작 확인

**Cursor** (개발자):
- .cursor/mcp.json 설정 확인
- Chat에서 MCP 도구 사용 가능 확인

### Step 5: Core 트랙 수료 요약

```
┌─────────────────────────────────────────────────────────┐
│              MCP 실전 마스터 — Core 트랙 수료             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  배운 것:                                                │
│  ✅ MCP 프로토콜의 원리와 아키텍처                        │
│  ✅ FastMCP로 서버 구축 (Tool + Resource + Prompt)       │
│  ✅ 입력 검증, 보안, 에러 처리                           │
│  ✅ 감사 로깅                                           │
│  ✅ 테스트 전략 (단위 + 통합 + CI)                       │
│  ✅ Transport (stdio + Streamable HTTP)                  │
│  ✅ 클라이언트 연동 (Claude Desktop, Cursor, VS Code)    │
│                                                         │
│  만든 것:                                                │
│  ✅ Acme Corp Internal Ops Assistant                    │
│  ✅ 프로덕션 수준의 MCP 서버                              │
│  ✅ 완전한 테스트 스위트                                  │
│  ✅ CI/CD 파이프라인                                     │
│                                                         │
│  다음 단계:                                              │
│  → DB 연동, 인증/인가, 알림 시스템                       │
│  → 커스텀 Transport, Sampling 활용                       │
│  → 실제 팀/조직에 MCP 서버 도입                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- EP 1~21에서 MCP 프로토콜 이해부터 프로덕션 수준의 서버 구축까지 완료
- 3개 Tool, 2개 Resource, 2개 Prompt, 4종 검증, 감사 로깅, 테스트 스위트
- 2개 Transport (stdio, Streamable HTTP), 3개 클라이언트 연동
- 코드 리뷰 체크리스트로 보안, 에러 처리, 로깅, 테스트 품질 점검
- 확장 아이디어: DB, 알림, 대시보드, 인증, Sampling

### 퀴즈
1. MCP 서버의 세 가지 핵심 구성 요소는? → Tool (동작 수행), Resource (데이터 노출), Prompt (지시문 템플릿)
2. Defense in depth 원칙이 우리 프로젝트에서 적용된 곳은? → validate_doc_id()의 입력 형식 검증 + resolved path 검증 + OS 파일 시스템 권한의 다중 방어선
3. stdio에서 Streamable HTTP로 전환할 때 비즈니스 로직 변경이 필요 없는 이유는? → MCP 프로토콜이 transport를 추상화하여, 비즈니스 로직(Tool/Resource/Prompt)과 통신 레이어가 완전히 분리되어 있기 때문

### 수료 인사
"MCP 실전 마스터: 프로토콜 이해부터 운영까지" Core 트랙을 완료하셨습니다. 여러분은 이제 MCP 서버를 설계하고, 구현하고, 테스트하고, 배포할 수 있는 역량을 갖추었습니다. 실제 프로젝트에 MCP를 도입하여 AI 도구의 새로운 가능성을 열어가시기 바랍니다.
