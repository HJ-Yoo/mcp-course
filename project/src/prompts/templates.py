"""
Prompts: templates

Pre-built prompt templates for common operational workflows:
- incident_report: structured incident report generation
- policy_answer: answer questions based on policy documents
"""

from __future__ import annotations


def register(mcp) -> None:
    """Register prompt templates on the MCP server."""

    @mcp.prompt()
    async def incident_report(issue: str, affected_system: str) -> str:
        """Generate a structured incident report.

        Produces a prompt that guides the LLM to create a comprehensive
        incident report covering summary, impact, reproduction steps,
        and recommended actions.

        Args:
            issue: Description of the incident or issue.
            affected_system: The system or service affected by the incident.

        Returns:
            A structured prompt template for incident report generation.
        """
        return (
            f"Please generate a structured incident report based on the following details.\n"
            f"\n"
            f"**Issue:** {issue}\n"
            f"**Affected System:** {affected_system}\n"
            f"\n"
            f"Use the following format:\n"
            f"\n"
            f"## Summary\n"
            f"Provide a concise summary of the incident (2-3 sentences).\n"
            f"\n"
            f"## Affected System\n"
            f"Identify the affected system, its dependencies, and scope of impact.\n"
            f"\n"
            f"## Impact Assessment\n"
            f"Describe the business impact: severity level, number of users affected, "
            f"and any SLA implications.\n"
            f"\n"
            f"## Steps to Reproduce\n"
            f"List the steps that lead to the issue, if applicable.\n"
            f"\n"
            f"## Recommended Actions\n"
            f"Provide immediate mitigation steps and longer-term fixes.\n"
        )

    @mcp.prompt()
    async def policy_answer(question: str, doc_id: str) -> str:
        """Answer a question based on a specific policy document.

        Produces a prompt instructing the LLM to answer the question using
        only information from the referenced policy, citing relevant sections.

        Args:
            question: The user's question about the policy.
            doc_id: The identifier of the policy document to reference.

        Returns:
            A prompt template that instructs the LLM to answer from policy content.
        """
        return (
            f"Answer the following question based **only** on the content of "
            f"policy document `{doc_id}`. If the answer is not found in the policy, "
            f"say so explicitly.\n"
            f"\n"
            f"**Question:** {question}\n"
            f"\n"
            f"Instructions:\n"
            f"1. Read the policy document using resource `policy://{doc_id}`.\n"
            f"2. Find the relevant section(s) that address the question.\n"
            f"3. Provide a clear, concise answer.\n"
            f"4. Cite the specific section title or heading where you found the information.\n"
            f"5. If the policy does not cover this topic, state: "
            f"\"This topic is not covered in the referenced policy.\"\n"
        )
