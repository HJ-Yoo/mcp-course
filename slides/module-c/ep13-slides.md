---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 13 — Prompt Template 이해와 활용"
---

# EP 13 — Prompt Template 이해와 활용
## Module C · MCP 실전 마스터

---

## 학습 목표

1. MCP Prompt의 역할과 Tool/Resource와의 차이
2. `@mcp.prompt()` 데코레이터 사용법
3. Resource + Prompt 조합 워크플로우

---

## MCP의 세 구성 요소 완성

| 구분 | 역할 | 비유 |
|------|------|------|
| **Tool** | 동작 수행 | "이 작업을 수행해" |
| **Resource** | 데이터 노출 | "이 데이터를 참고해" |
| **Prompt** | 지시문 템플릿 | "이 방식으로 답변해" |

세 요소가 조합되어 강력한 워크플로우를 구성

---

## Prompt의 핵심 가치

1. **일관성** — 모든 사용자가 동일한 고품질 프롬프트
2. **재사용성** — 한 번 설계, 반복 사용
3. **중앙 관리** — 업데이트가 모든 클라이언트에 반영
4. **전문성 캡처** — 프롬프트 엔지니어링 노하우 보존
5. **파라미터화** — 동적 값을 주입하여 유연하게 활용

---

## @mcp.prompt() 기본 사용법

```python
@mcp.prompt()
async def incident_report(
    issue: str,
    affected_system: str
) -> str:
    """IT 인시던트 리포트를 생성합니다."""
    return f"""You are an IT incident response specialist.

Create a structured incident report:
- Issue: {issue}
- Affected System: {affected_system}

Include: Summary, Impact, Steps to Reproduce,
Recommended Actions, Priority Level.

Write in Korean."""
```

---

## Prompt + Resource 협업

```python
@mcp.prompt()
async def policy_answer(
    question: str, doc_id: str
) -> str:
    """정책 문서 기반 질문 답변"""
    return f"""Answer based strictly on
the policy document (policy://{doc_id}).

Question: {question}

Rules:
- Only use information from the policy document
- Cite specific sections
- If not in document, say so"""
```

프롬프트가 `policy://{doc_id}` Resource를 참조!

---

## 프롬프트 엔지니어링 원칙

```
1. 역할 부여
   "You are an IT specialist..."

2. 구조화된 출력 포맷
   "Include these sections: ..."

3. 제약 조건 명시
   "Only use information from..."

4. 언어 지정
   "Write in Korean"

5. 톤 설정
   "Use professional tone"
```

---

## 티켓 유형별 가이드 Prompt

```python
@mcp.prompt()
async def ticket_summary(ticket_type: str) -> str:
    guides = {
        "incident": """인시던트 티켓 작성 가이드:
          1. 문제 설명, 2. 영향 범위, 3. 시작 시점,
          4. 재현 방법, 5. 우선순위""",
        "request": """서비스 요청 작성 가이드:
          1. 요청 내용, 2. 사유, 3. 희망 일정,
          4. 승인 필요 여부""",
        "change": """변경 요청 작성 가이드:
          1. 변경 내용, 2. 변경 사유, 3. 영향 분석,
          4. 롤백 계획, 5. 희망 일정""",
    }
    return guides.get(ticket_type, "Unknown type")
```

---

## Claude Desktop에서 Prompt 사용

1. 대화창에서 `/` 입력 → 프롬프트 목록
2. `incident_report` 선택
3. 파라미터 입력:
   - issue: "이메일 서버 접속 불가"
   - affected_system: "Exchange"
4. Claude가 구조화된 리포트 생성

---

## 세 요소의 조합 시나리오

```
사용자: "3층 프린터 고장. 관련 정책 확인하고 티켓 만들어줘."

LLM 동작:
  1. [Prompt]   incident_report 템플릿 활용
  2. [Resource] policy://equipment-management 참조
  3. [Tool]     lookup_inventory → 프린터 재고 확인
  4. [Tool]     create_ticket → 수리 티켓 생성
  5. 구조화된 응답 생성
```

**Tool + Resource + Prompt = MCP의 진정한 힘**

---

## 데모: Inspector에서 테스트

```bash
uv run mcp dev src/server.py
```

1. **Prompts** 탭 → 3개 프롬프트 확인
2. `incident_report` 선택 → 파라미터 입력 → 생성된 프롬프트 확인
3. `policy_answer` 선택 → Resource URI 참조 확인

---

## 핵심 정리

- Prompt = 재사용 가능한 LLM 지시문 템플릿
- `@mcp.prompt()` 데코레이터로 등록
- Resource + Prompt → "정책 기반 답변" 워크플로우
- 프롬프트 설계: 역할 부여, 구조화, 제약 조건
- Tool + Resource + Prompt 조합 → 복잡한 업무 자동화

---

## 다음 편 예고

### EP 14: 감사 로깅 (Audit Logging)

- JSONL 포맷 AuditLogger 구현
- Tool 호출 기록 추적
- 로그 분석 (jq 활용)
