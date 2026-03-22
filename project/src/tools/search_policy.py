"""
Tool: search_policy

Keyword search across policy markdown documents with weighted relevance
ranking. Parses YAML front-matter for metadata, scores matches across
title / tags / body, and returns ranked results with snippets.
"""

from __future__ import annotations

import json
import re

import yaml
from mcp.server.fastmcp import Context

from src.audit import AuditLogger
from src.models import AppContext
from src.validation import validate_query


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML front-matter와 본문을 분리합니다."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return meta, body
    return {}, content


def calculate_relevance(query: str, meta: dict, body: str) -> float:
    """검색 관련도 점수를 계산합니다."""
    q = query.lower()
    score = 0.0

    # 제목 매칭 (가중치 3)
    if q in meta.get("title", "").lower():
        score += 3.0

    # 태그 매칭 (가중치 2)
    tags = [t.lower() for t in meta.get("tags", [])]
    if q in tags:
        score += 2.0

    # 본문 매칭 (출현 횟수 기반, 최대 3점)
    occurrences = body.lower().count(q)
    score += min(occurrences * 0.5, 3.0)

    return score


def extract_snippet(body: str, query: str, context_chars: int = 150) -> str:
    """키워드 주변 텍스트를 스니펫으로 추출합니다."""
    idx = body.lower().find(query.lower())
    if idx == -1:
        return body[:context_chars * 2].strip() + "..."

    start = max(0, idx - context_chars)
    end = min(len(body), idx + len(query) + context_chars)

    snippet = body[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(body):
        snippet = snippet + "..."

    return snippet


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(mcp) -> None:
    """Register the search_policy tool on the MCP server."""

    @mcp.tool()
    async def search_policy(query: str, ctx: Context) -> str:
        """사내 정책 문서를 검색합니다.

        키워드를 기반으로 관련 정책 문서를 찾아 스니펫을 반환합니다.
        제목, 태그, 본문을 모두 검색하며, 관련도 순으로 정렬됩니다.

        Args:
            query: 검색 키워드 (예: "VPN", "재택근무", "비밀번호")
        """
        app: AppContext = ctx.request_context.lifespan_context["app"]
        logger = AuditLogger(app.audit_log_path)

        sanitized = validate_query(query)

        results: list[dict] = []
        for doc in app.policies:
            if not doc.path.exists():
                continue

            content = doc.path.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(content)
            score = calculate_relevance(sanitized, meta, body)

            if score > 0:
                results.append({
                    "slug": doc.doc_id,
                    "title": meta.get("title", doc.title),
                    "tags": meta.get("tags", []),
                    "last_updated": str(meta.get("last_updated", "")),
                    "relevance_score": round(score, 1),
                    "snippet": extract_snippet(body, sanitized),
                    "resource_uri": f"ops://policies/{doc.doc_id}",
                })

        # 관련도 순 정렬
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        response = {
            "query": sanitized,
            "total_results": len(results),
            "results": results,
        }

        if not results:
            response["suggestion"] = (
                "검색 결과가 없습니다. 다른 키워드를 시도해보세요."
            )

        result_json = json.dumps(response, ensure_ascii=False, indent=2)

        logger.log(
            action="search",
            tool_name="search_policy",
            input_summary=f"query={sanitized}",
            result_summary=f"Found {len(results)} matching policy/policies",
            success=True,
        )
        return result_json
