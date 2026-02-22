---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 01 — MCP란 무엇인가?"
---

# EP 01 — MCP란 무엇인가?
## Module A: MCP 기초 · MCP 실전 마스터

---

## 학습 목표

1. MCP의 탄생 배경과 해결하려는 문제를 설명할 수 있다
2. 기존 방식(커스텀 플러그인)과 MCP의 차이를 비교할 수 있다
3. MCP의 3대 프리미티브(Tools, Resources, Prompts)를 구분할 수 있다

---

## LLM의 딜레마

> "LLM은 똑똑하지만, 혼자서는 아무것도 할 수 없다"

- 이메일 전송 → 이메일 API 필요
- 데이터 조회 → DB 연결 필요
- 파일 읽기 → 파일 시스템 접근 필요

**통일된 연결 표준이 없다!**

---

## N x M 문제

```
ChatGPT  ──┬── Slack 전용 플러그인
            ├── GitHub 전용 플러그인
            └── Jira 전용 플러그인

Claude   ──┬── Slack 전용 플러그인
            ├── GitHub 전용 플러그인
            └── Jira 전용 플러그인

Gemini   ──┬── Slack 전용 플러그인
            ├── ...
```

**N개 LLM x M개 서비스 = N x M 커스텀 통합**

---

## MCP의 해답: 1 x (N+M)

```
ChatGPT ──┐
Claude  ──┤── [MCP 프로토콜] ──┬── Slack MCP 서버
Gemini  ──┘                    ├── GitHub MCP 서버
                               └── Jira MCP 서버
```

- 각 LLM: MCP 클라이언트 **1번** 구현
- 각 서비스: MCP 서버 **1번** 구현
- **N + M개 구현으로 전부 연결!**

---

## USB-C 비유

| 과거 | 현재 |
|------|------|
| Lightning, Micro USB, 전용 충전기... | USB-C 하나로 통일 |
| LLM마다 전용 플러그인 | **MCP 하나로 통일** |

MCP = LLM 생태계의 USB-C

---

## MCP 3대 프리미티브

| 프리미티브 | 역할 | 비유 | 예시 |
|-----------|------|------|------|
| **Tools** | 실행 (행동) | 손 | 티켓 생성, 이메일 전송 |
| **Resources** | 읽기 (데이터) | 눈 | 정책 문서, 재고 현황 |
| **Prompts** | 템플릿 (대본) | 대본 | 티켓 분류, 요약 |

---

## MCP vs REST API vs GraphQL

| 기준 | REST API | GraphQL | MCP |
|------|----------|---------|-----|
| 대상 | 개발자 | 개발자 | **LLM** |
| 스키마 | OpenAPI | 필수 | **자동 생성** |
| 실행 주체 | 개발자 | 개발자 | **LLM이 자율 판단** |

핵심 차이: **LLM이 스스로 도구를 선택하고 호출**

---

## 데모: uv 설치

macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
uv --version
# uv 0.5.x
```

---

## 데모: 프로젝트 세팅

```bash
git clone https://github.com/HJ-Yoo/mcp-course.git
cd mcp-course/starter-kit
uv sync
```

`uv sync` = 의존성 설치 + 가상환경 자동 생성

---

## 캡스톤 프로젝트: Internal Ops Assistant

| 시나리오 | 프리미티브 | Tool/Resource |
|----------|-----------|--------------|
| "노트북 재고 몇 대?" | Tool | `lookup_inventory` |
| "VPN 설정 방법?" | Tool + Resource | `search_policy` + `ops://policies/{slug}` |
| "키보드 수리 접수" | Tool + Prompt | `create_ticket` + `triage-ticket` |

MCP 서버 하나로 Claude, Cursor, VS Code 어디서든 사용!

---

## 핵심 정리

- MCP = LLM과 외부 시스템을 연결하는 **표준 프로토콜**
- N x M 문제 → **1 x (N+M)**으로 비용 절감
- 3대 프리미티브: **Tools**(행동), **Resources**(데이터), **Prompts**(템플릿)
- REST API와의 핵심 차이: **LLM이 자율적으로 활용**

---

## 퀴즈

1. MCP가 해결하는 N x M 문제란?
   → N개 LLM x M개 서비스의 커스텀 통합. MCP로 N+M으로 줄임

2. MCP의 3가지 프리미티브와 각각의 역할은?
   → Tools(행동), Resources(데이터), Prompts(템플릿)

---

## 다음 편 예고

### EP 02: MCP 아키텍처 한눈에 보기

- Host / Client / Server 3-tier 구조
- JSON-RPC 2.0 메시지 흐름
- Transport 레이어: stdio vs HTTP
