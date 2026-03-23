"""TODO (Episode 11-12): Implement policy resources."""
from __future__ import annotations

def register(mcp):
    # TODO: @mcp.resource("policy://index", mime_type="application/json")
    #       AppContext에서 policies 목록 가져오기
    #       JSON 반환: [{"doc_id", "title", "tags"}, ...]

    # TODO: @mcp.resource("policy://{doc_id}", mime_type="application/json")
    #       validate_doc_id로 보안 검증 (Episode 12)
    #       JSON 반환: {"doc_id", "title", "content"}
    pass
