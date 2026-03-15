"""TODO (Episode 7): Implement policy search tool with weighted relevance ranking."""
from __future__ import annotations


def register(mcp):
    @mcp.tool()
    async def search_policy(query: str, ctx) -> str:
        """사내 정책 문서를 검색합니다.

        키워드를 기반으로 관련 정책 문서를 찾아 스니펫을 반환합니다.
        제목, 태그, 본문을 모두 검색하며, 관련도 순으로 정렬됩니다.

        Args:
            query: 검색 키워드 (예: "VPN", "재택근무", "비밀번호")
        """
        # TODO: Get AppContext from ctx
        # TODO: sanitize_query로 입력 검증
        # TODO: parse_frontmatter()로 YAML 메타데이터/본문 분리
        # TODO: calculate_relevance()로 가중치 점수 계산
        #       - 제목 매칭: x3
        #       - 태그 매칭: x2
        #       - 본문 매칭: 출현 횟수 x0.5 (최대 3점)
        # TODO: extract_snippet()으로 키워드 주변 텍스트 추출
        # TODO: 관련도 순 정렬 후 JSON 반환
        #       결과 필드: slug, title, tags, last_updated,
        #                  relevance_score, snippet, resource_uri
        # TODO: Add audit logging (Episode 14)
        return "Not implemented yet"
