"""
Input validation utilities.
TODO (Episode 9): Implement validation functions.

4 core functions:
- sanitize_string(): 문자열 정리 (XSS, 제어 문자)
- validate_path(): 경로 검증 (Path Traversal)
- validate_ticket_input(): 티켓 입력 검증 (Injection)
- validate_query(): 검색어 검증 (Injection, DoS)
"""
from __future__ import annotations


def sanitize_string(value: str, max_length: int = 500) -> str:
    # TODO: 1. 타입 체크
    # TODO: 2. 공백 제거 (strip)
    # TODO: 3. 제어 문자 제거 (CONTROL_CHARS)
    # TODO: 4. 길이 제한 (max_length)
    # TODO: 5. 위험 패턴 탐지 (DANGEROUS_PATTERNS)
    return value


def validate_path(user_path: str, base_dir: str):
    # TODO: '..' 포함 여부 검사
    # TODO: null 바이트 검사
    # TODO: Path.resolve()로 정규화
    # TODO: base_dir 내부인지 확인
    pass


def validate_ticket_input(
    title: str,
    description: str,
    priority: str = "medium",
) -> dict:
    # TODO: sanitize_string으로 title 검증 (max 200, min 5)
    # TODO: sanitize_string으로 description 검증 (max 2000, min 10)
    # TODO: priority 화이트리스트 검증 (low/medium/high/critical)
    # TODO: 검증된 dict 반환 {"title", "description", "priority"}
    return {"title": title, "description": description, "priority": priority}


def validate_query(
    query: str,
    min_length: int = 1,
    max_length: int = 100,
) -> str:
    # TODO: sanitize_string으로 검증
    # TODO: min_length 이상인지 확인
    return query


def validate_doc_id(doc_id: str) -> str:
    # TODO: 빈 값 검사
    # TODO: 소문자 알파벳, 숫자, 하이픈만 허용 (1~50자)
    # TODO: regex pattern: r'^[a-z0-9]([a-z0-9\-]{0,48}[a-z0-9])?$'
    return doc_id


def safe_resolve_policy_path(doc_id: str, policy_dir):
    # TODO: validate_doc_id로 입력 형식 검증 (Layer 1)
    # TODO: (policy_dir / f"{doc_id}.md").resolve() 경로 생성
    # TODO: resolved 경로가 policy_dir 내부인지 확인 (Layer 2)
    pass
