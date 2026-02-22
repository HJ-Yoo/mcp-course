---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 21 — 캡스톤 리뷰: 전체 시스템 점검"
---

# EP 21 — 캡스톤 리뷰: 전체 시스템 점검
## Module D · MCP 실전 마스터

---

## 학습 목표

1. 프로젝트 전체 아키텍처 리뷰
2. 코드 품질 체크리스트로 점검
3. 향후 확장 포인트 식별

---

## 전체 아키텍처

```
┌─────────────────────────────────────────┐
│         Acme Internal Ops Assistant       │
│                                         │
│  Transport: stdio / Streamable HTTP     │
│                                         │
│  ┌────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Tools  │ │Resources │ │ Prompts  │  │
│  │ (3개)  │ │ (2개)    │ │ (2개)    │  │
│  └────────┘ └──────────┘ └──────────┘  │
│                                         │
│  Validation │ AuditLogger │ AppContext  │
│                                         │
│  Data: CSV + Markdown + JSONL           │
└─────────────────────────────────────────┘
         ↑         ↑         ↑
    Claude Desktop  Cursor   VS Code
```

---

## 모듈별 학습 여정

| Module | 주제 | EP |
|--------|------|-----|
| **A** | 기초: 프로토콜, FastMCP, Inspector | 1-4 |
| **B** | 핵심: lifespan, Tool, 검증, 에러 | 5-9 |
| **C** | 품질: Resource, Prompt, 로깅, 테스트 | 10-16 |
| **D** | 배포: Transport, 클라이언트, 마이그레이션 | 17-21 |

---

## 구현 현황 요약

| 카테고리 | 항목 | 수량 |
|---------|------|------|
| Tools | lookup_inventory, search_policy, create_ticket | **3** |
| Resources | policy://index, policy://{doc_id} | **2** |
| Prompts | incident_report, policy_answer | **2** |
| Validation | priority, text_length, query, doc_id | **4** |
| Models | InventoryItem, PolicyDoc, Ticket, AppContext, ToolError, ErrorCode | **6** |
| Transports | stdio, Streamable HTTP | **2** |
| Clients | Claude Desktop, Cursor, VS Code | **3** |

---

## 코드 리뷰 체크리스트: 보안

```
□ validate_doc_id() — path traversal 방어
□ sanitize_query() — 입력 새니타이징
□ validate_priority() — 우선순위 검증
□ validate_text_length() — 텍스트 길이 제한
□ 민감 데이터가 로그에 미포함 확인
□ Defense in depth 적용
```

---

## 코드 리뷰 체크리스트: 에러 & 로깅

**에러 처리:**
```
□ 모든 Tool에 try/except
□ ToolError로 구조화된 에러 반환
□ ErrorCode로 에러 유형 분류
□ 존재하지 않는 Resource 적절한 에러
```

**로깅:**
```
□ AuditLogger가 모든 Tool 호출 기록
□ 성공/실패 모두 기록
□ duration_ms 기록
□ 로그 rotation 고려 (프로덕션)
```

---

## 코드 리뷰 체크리스트: 테스트 & 배포

**테스트:**
```
□ 입력 검증 단위 테스트
□ 보안 테스트 (공격 패턴)
□ 감사 로깅 테스트
□ 통합 테스트 (전체 플로우)
□ CI 파이프라인 (GitHub Actions)
```

**배포:**
```
□ stdio / HTTP 모두 동작 확인
□ Claude Desktop 설정 검증
□ Cursor / VS Code 설정 검증
□ 환경별 설정 분리 (dev/prod)
```

---

## 프로젝트 최종 구조

```
acme-ops-assistant/
├── src/
│   ├── server.py          # 메인 서버
│   ├── models.py          # 데이터 모델
│   ├── validation.py      # 입력 검증
│   ├── audit.py           # AuditLogger
│   ├── tools/             # 3개 Tool
│   ├── resources/         # 2개 Resource
│   └── prompts/           # 2개 Prompt
├── data/                  # CSV + MD + JSONL
├── logs/                  # 감사 로그
├── tests/                 # 단위 + 통합 테스트
├── .github/workflows/     # CI
├── .cursor/mcp.json       # Cursor 설정
└── .vscode/mcp.json       # VS Code 설정
```

---

## 전체 테스트 실행

```bash
# macOS/Linux
uv run pytest --cov=src --cov-report=term-missing -v

# Windows
uv run pytest --cov=src --cov-report=term-missing -v
```

```
test_validation.py ............   [ 30%]
test_security.py ...............  [ 60%]
test_audit.py ......              [ 75%]
test_integration.py ..........    [100%]

TOTAL coverage: 93%
==================== 35+ passed ====================
```

---

## 확장 아이디어

| 확장 | 설명 |
|------|------|
| **DB 연동** | CSV → SQLite/PostgreSQL |
| **알림 시스템** | 티켓 생성 시 Slack 알림 |
| **대시보드** | 감사 로그 시각화 |
| **인증/인가** | OAuth, API Key, RBAC |
| **추가 Tool** | JIRA, GitHub Issue, 캘린더 |
| **Sampling** | 서버 측 LLM 호출 (자동 분류) |

---

## MCP 생태계에서의 위치

```
┌──────────────────────────────────────┐
│           MCP Ecosystem              │
│                                      │
│  우리가 만든 것:                       │
│  ✅ 프로토콜 이해                     │
│  ✅ 서버 설계/구현                    │
│  ✅ 보안/테스트/배포                  │
│                                      │
│  다음 단계:                           │
│  → 커스텀 Transport                  │
│  → 분산 MCP 아키텍처                 │
│  → MCP Gateway                      │
│  → 프로덕션 운영                     │
└──────────────────────────────────────┘
```

---

## Core 트랙 수료 요약

```
배운 것:
  ✅ MCP 프로토콜의 원리와 아키텍처
  ✅ FastMCP로 서버 구축 (Tool + Resource + Prompt)
  ✅ 입력 검증, 보안, 에러 처리
  ✅ 감사 로깅
  ✅ 테스트 전략 (단위 + 통합 + CI)
  ✅ Transport (stdio + Streamable HTTP)
  ✅ 클라이언트 연동 (3개)

만든 것:
  ✅ Acme Corp Internal Ops Assistant
  ✅ 프로덕션 수준의 MCP 서버
```

---

## 최종 퀴즈

1. **MCP 서버의 3대 구성 요소는?**
   → Tool, Resource, Prompt

2. **Defense in depth가 적용된 곳은?**
   → validate_doc_id() + 경로 resolve + OS 권한

3. **Transport 전환 시 코드 변경이 불필요한 이유는?**
   → MCP가 transport를 추상화, 비즈니스 로직과 분리

---

## 수료를 축하합니다!

### MCP 실전 마스터: 프로토콜 이해부터 운영까지

Core 트랙 완료

여러분은 이제 MCP 서버를 **설계하고, 구현하고, 테스트하고, 배포**할 수 있습니다.

실제 프로젝트에 MCP를 도입하여 AI 도구의 새로운 가능성을 열어가세요.
