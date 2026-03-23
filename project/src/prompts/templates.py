"""
Prompts: templates

Pre-built prompt templates for common operational workflows:
- incident_report: structured incident report generation
- policy_answer: answer questions based on policy documents
- ticket_summary: ticket type-specific writing guide
"""

from __future__ import annotations


def register(mcp) -> None:
    """Register prompt templates on the MCP server."""

    @mcp.prompt()
    async def incident_report(issue: str, affected_system: str) -> str:
        """IT 인시던트 리포트를 생성합니다."""
        return f"""You are an IT incident response specialist.

Create a structured incident report:
- Issue: {issue}
- Affected System: {affected_system}

Include: Summary, Impact, Steps to Reproduce,
Recommended Actions, Priority Level.

Write in Korean."""

    @mcp.prompt()
    async def policy_answer(question: str, doc_id: str) -> str:
        """정책 문서 기반 질문 답변"""
        return f"""Answer based strictly on
the policy document (policy://{doc_id}).

Question: {question}

Rules:
- Only use information from the policy document
- Cite specific sections
- If not in document, say so"""

    @mcp.prompt()
    async def ticket_summary(ticket_type: str) -> str:
        """티켓 유형별 작성 가이드를 제공합니다."""
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
