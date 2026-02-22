# EP 13 — Prompt Template 이해와 활용

> Module C · 약 20분

## 학습 목표
1. MCP Prompt의 역할과 Tool/Resource와의 차이를 이해한다
2. `@mcp.prompt()` 데코레이터로 파라미터화된 프롬프트를 구현한다
3. Resource + Prompt를 조합한 실전 워크플로우를 설계한다

---

## 1. 인트로 (2분)

지금까지 우리는 MCP의 세 가지 구성 요소 중 두 가지를 구현했습니다:
- **Tool**: 동작을 수행 (EP 5~9)
- **Resource**: 데이터를 노출 (EP 10~12)

이번에는 세 번째이자 마지막 구성 요소인 **Prompt**를 배웁니다.

Prompt는 "재사용 가능한 LLM 지시문 템플릿"입니다. 매번 같은 지시를 타이핑하는 대신, 잘 설계된 프롬프트를 템플릿화하여 파라미터만 바꿔가며 사용합니다. 마치 함수처럼요.

"인시던트 리포트를 작성해줘" — 매번 포맷을 설명하는 대신, `incident_report` Prompt를 호출하면 됩니다.

---

## 2. 핵심 개념 (6분)

### 2.1 MCP의 세 구성 요소 완성

```
┌─────────────────────────────────────────────────────────┐
│                    MCP 서버                              │
│                                                         │
│  ┌─────────┐    ┌──────────┐    ┌─────────────┐        │
│  │  Tools  │    │Resources │    │   Prompts   │        │
│  │         │    │          │    │             │        │
│  │ 동작    │    │ 데이터    │    │ 지시문 템플릿│        │
│  │ 수행    │    │ 노출     │    │ 재사용      │        │
│  └────┬────┘    └────┬─────┘    └──────┬──────┘        │
│       │              │                 │                │
│       └──────────────┼─────────────────┘                │
│                      │                                  │
│              LLM이 조합하여 사용                          │
└─────────────────────────────────────────────────────────┘
```

각 요소의 역할:
- **Tool**: "이 작업을 수행해" (재고 검색, 티켓 생성)
- **Resource**: "이 데이터를 참고해" (정책 문서, 서버 정보)
- **Prompt**: "이 방식으로 답변해" (인시던트 리포트 양식, 정책 기반 QA)

### 2.2 Prompt의 핵심 가치

왜 프롬프트를 서버 측에서 관리해야 할까요?

1. **일관성**: 모든 사용자가 동일한 고품질 프롬프트 사용
2. **재사용성**: 한 번 설계하면 반복 사용
3. **중앙 관리**: 프롬프트 업데이트가 모든 클라이언트에 즉시 반영
4. **전문성 캡처**: 프롬프트 엔지니어링 노하우를 코드로 보존
5. **파라미터화**: 동적 값을 주입하여 유연하게 활용

### 2.3 @mcp.prompt() 데코레이터

```python
@mcp.prompt()
async def incident_report(issue: str, affected_system: str) -> str:
    """IT 인시던트 리포트를 생성하는 프롬프트입니다."""
    return f"""You are an IT incident response specialist at Acme Corp.

Create a structured incident report for the following:
- Issue: {issue}
- Affected System: {affected_system}

Include these sections:
1. Summary (한 줄 요약)
2. Impact Assessment (영향 범위)
3. Steps to Reproduce (재현 절차)
4. Recommended Actions (권장 조치)
5. Priority Level (P1~P4)

Use professional tone. Write in Korean."""
```

**구조 분석**:
- `@mcp.prompt()`: 이 함수를 MCP Prompt로 등록
- 함수 파라미터: 클라이언트가 제공하는 동적 값
- 반환값: LLM에게 전달될 완성된 프롬프트 문자열
- Docstring: 클라이언트에 표시되는 설명

### 2.4 Prompt + Resource 협업 패턴

Prompt가 Resource 데이터를 참조하도록 설계하면 강력한 워크플로우가 됩니다:

```python
@mcp.prompt()
async def policy_answer(question: str, doc_id: str) -> str:
    """정책 문서를 참고하여 질문에 답변하는 프롬프트입니다."""
    return f"""Answer the following question based strictly on
the policy document (policy://{doc_id}).

Question: {question}

Rules:
- Only use information from the policy document
- Cite specific sections when possible
- If the answer is not in the document, clearly state so
- Write in Korean"""
```

이 프롬프트는 `policy://{doc_id}` Resource를 참조합니다. LLM은:
1. 프롬프트의 지시를 읽고
2. 참조된 Resource 데이터를 로드하고
3. 지시에 따라 정책 기반 답변을 생성합니다

### 2.5 프롬프트 엔지니어링 팁

좋은 MCP Prompt를 설계하기 위한 원칙:

```
┌─────────────────────────────────────────┐
│  1. 역할 부여                            │
│     "You are an IT specialist..."       │
├─────────────────────────────────────────┤
│  2. 구조화된 출력 포맷                    │
│     "Include these sections: ..."       │
├─────────────────────────────────────────┤
│  3. 제약 조건 명시                       │
│     "Only use information from..."      │
├─────────────────────────────────────────┤
│  4. 언어 지정                            │
│     "Write in Korean"                   │
├─────────────────────────────────────────┤
│  5. 톤 설정                             │
│     "Use professional tone"             │
└─────────────────────────────────────────┘
```

---

## 3. 라이브 데모 (10분)

### Step 1: Prompt 모듈 생성

`src/prompts/ops_prompts.py` 파일을 생성합니다:

```python
"""Acme Corp Internal Ops Prompt Templates"""


def register(mcp):
    """MCP 서버에 Prompt 템플릿을 등록합니다."""

    @mcp.prompt()
    async def incident_report(issue: str, affected_system: str) -> str:
        """IT 인시던트 리포트를 생성합니다.

        Args:
            issue: 발생한 문제에 대한 설명
            affected_system: 영향을 받는 시스템 이름
        """
        return f"""You are an IT incident response specialist at Acme Corp.

Create a structured incident report for the following issue:

- Issue: {issue}
- Affected System: {affected_system}

Please include these sections in your report:

## 1. Summary
Provide a one-line summary of the incident.

## 2. Impact Assessment
- Severity: (Critical / High / Medium / Low)
- Affected Users: (estimated count or scope)
- Business Impact: (description)

## 3. Timeline
- Reported: (when the issue was first reported)
- Current Status: (ongoing / investigating / resolved)

## 4. Steps to Reproduce
List the steps to reproduce this issue, if applicable.

## 5. Recommended Actions
- Immediate: (actions to take now)
- Short-term: (actions within 24 hours)
- Long-term: (preventive measures)

## 6. Priority Level
Assign a priority level (P1-P4) with justification.

Write the report in Korean (한국어). Use professional tone."""

    @mcp.prompt()
    async def policy_answer(question: str, doc_id: str) -> str:
        """정책 문서를 기반으로 질문에 답변합니다.

        Args:
            question: 사용자의 질문
            doc_id: 참고할 정책 문서 ID (예: remote-work, security)
        """
        return f"""You are a policy compliance advisor at Acme Corp.

Answer the following question based **strictly** on the policy document.

**Reference Document**: policy://{doc_id}
**Question**: {question}

Rules:
1. ONLY use information found in the referenced policy document
2. Cite specific sections or clauses when possible (e.g., "제3조 2항에 따르면...")
3. If the answer is NOT in the document, clearly state:
   "해당 정책 문서에서 이 질문에 대한 내용을 찾을 수 없습CCCCCCl."
4. If the question is partially covered, answer what you can and note the gaps
5. Do NOT make assumptions beyond what the document states

Write your answer in Korean (한국어).
Structure your response as:
- 답변 요약 (1-2줄)
- 상세 설명 (관련 조항 인용 포함)
- 참고사항 (있는 경우)"""

    @mcp.prompt()
    async def ticket_summary(ticket_type: str) -> str:
        """티켓 생성을 위한 정보 수집 가이드입니다.

        Args:
            ticket_type: 티켓 유형 (incident, request, change)
        """
        guides = {
            "incident": """You are helping a user create an IT incident ticket.

Gather the following information through conversation:

1. **문제 설명**: What is happening? Error messages?
2. **영향 범위**: How many users are affected?
3. **시작 시점**: When did it start?
4. **재현 방법**: Can it be reproduced?
5. **우선순위**: How urgent is this? (P1-P4)

Once you have all information, use the create_ticket tool to submit it.
Communicate in Korean.""",

            "request": """You are helping a user create an IT service request ticket.

Gather the following information:

1. **요청 내용**: What do you need?
2. **사유**: Why do you need it?
3. **희망 일정**: When do you need it by?
4. **승인**: Does this need manager approval?

Once ready, use the create_ticket tool to submit.
Communicate in Korean.""",

            "change": """You are helping a user create a change request ticket.

Gather the following information:

1. **변경 내용**: What will be changed?
2. **변경 사유**: Why is this change needed?
3. **영향 분석**: What systems will be affected?
4. **롤백 계획**: How to revert if something goes wrong?
5. **희망 일정**: When should this change be applied?

Once ready, use the create_ticket tool to submit.
Communicate in Korean.""",
        }

        template = guides.get(ticket_type)
        if template is None:
            valid_types = ", ".join(guides.keys())
            return f"Unknown ticket type: '{ticket_type}'. Valid types: {valid_types}"

        return template
```

### Step 2: 서버에 등록

`src/server.py`:

```python
from prompts import ops_prompts

# ... 기존 등록 코드 아래에 추가 ...
ops_prompts.register(mcp)
```

### Step 3: MCP Inspector에서 테스트

macOS/Linux:
```bash
uv run mcp dev src/server.py
```

Windows (PowerShell):
```powershell
uv run mcp dev src\server.py
```

Inspector에서:
1. **Prompts** 탭 클릭 → 3개 프롬프트가 목록에 표시됨
2. `incident_report` 선택:
   - `issue`: "사내 프린터가 작동하지 않음"
   - `affected_system`: "3층 복합기"
   - → 생성된 프롬프트 내용 확인
3. `policy_answer` 선택:
   - `question`: "재택근무 시 VPN 필수인가요?"
   - `doc_id`: "remote-work"
   - → `policy://remote-work` 참조가 포함된 프롬프트 확인

### Step 4: Claude Desktop에서 실전 사용

Claude Desktop에서 프롬프트를 사용하는 방법:

1. 대화창에서 `/` 입력 → MCP 프롬프트 목록 표시
2. `incident_report` 선택
3. 파라미터 입력:
   - issue: "이메일 서버 접속 불가"
   - affected_system: "Microsoft Exchange"
4. Claude가 구조화된 인시던트 리포트를 생성

**Resource + Prompt 조합 시나리오**:
1. `policy_answer` 프롬프트 선택
2. question: "해외 출장 시 장비 반출 절차는?"
3. doc_id: "equipment-management"
4. Claude가 `policy://equipment-management` Resource를 읽고, 정책 기반으로 답변

### Step 5: 세 요소의 조합 시나리오

모든 MCP 요소가 함께 작동하는 시나리오:

```
사용자: "3층 프린터가 고장났어. 관련 정책 확인하고 티켓 만들어줘."

LLM의 동작:
1. [Prompt] incident_report 템플릿 활용
2. [Resource] policy://equipment-management 참조
3. [Tool] lookup_inventory로 프린터 재고 확인
4. [Tool] create_ticket으로 수리 티켓 생성
5. 구조화된 응답 생성
```

이것이 MCP의 진정한 힘입니다 — Tool, Resource, Prompt가 유기적으로 협업합니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- Prompt는 재사용 가능한 LLM 지시문 템플릿으로, MCP의 세 번째 구성 요소
- `@mcp.prompt()`로 등록하며, 함수 파라미터로 동적 값을 주입
- Prompt + Resource 조합으로 "정책 기반 답변" 같은 강력한 워크플로우 구현
- 좋은 프롬프트는 역할 부여, 구조화된 출력, 제약 조건을 포함
- Tool + Resource + Prompt를 조합하면 복잡한 업무 자동화가 가능

### 퀴즈
1. Prompt가 Resource 데이터를 참조하려면 어떻게 해야 하는가? → 프롬프트 텍스트 내에 `policy://{doc_id}` 같은 Resource URI를 포함시키면 LLM이 해당 Resource를 로드하여 컨텍스트로 사용한다
2. `policy_answer` Prompt에서 "ONLY use information from the policy document"라는 제약이 중요한 이유는? → LLM이 학습 데이터에서 추측하지 않고, 실제 정책 문서 내용만 기반으로 답변하도록 하여 정확성을 보장하기 위함 (hallucination 방지)
3. 프롬프트를 서버 측에서 관리하는 장점은? → 일관성 보장, 중앙 관리로 업데이트 즉시 반영, 프롬프트 엔지니어링 전문성 보존

### 다음 편 예고
EP 14에서는 **감사 로깅(Audit Logging)** 을 구현합니다. AI 도구가 어떤 작업을 수행했는지 추적하는 것은 규정 준수와 디버깅에 필수입니다. JSONL 포맷의 AuditLogger를 만들고 모든 Tool에 통합합니다.
