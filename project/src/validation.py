"""
Input validation utilities for the Internal Ops Assistant.

Provides reusable validators that raise ToolError with appropriate
ErrorCode values when inputs are invalid.

4 core functions:
- sanitize_string(): 문자열 정리 (XSS, 제어 문자)
- validate_path(): 경로 검증 (Path Traversal)
- validate_ticket_input(): 티켓 입력 검증 (Injection)
- validate_query(): 검색어 검증 (Injection, DoS)
"""

from __future__ import annotations

import re
from pathlib import Path

from src.models import ErrorCode, ToolError

VALID_PRIORITIES = {"low", "medium", "high", "critical"}

# 제어 문자 패턴
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# 위험한 패턴 블랙리스트
DANGEROUS_PATTERNS = [
    # SQL Injection
    re.compile(r"['\";].*(?:DROP|DELETE|UPDATE|INSERT|UNION|SELECT)", re.I),
    # NoSQL (MongoDB) Injection
    re.compile(r"\$(?:gt|gte|lt|lte|ne|in|nin|regex|where|expr)", re.I),
    # Prototype Pollution
    re.compile(r"__proto__", re.I),
    re.compile(r"constructor\[", re.I),
    # XSS (Cross-Site Scripting)
    re.compile(r"<script", re.I),
    re.compile(r"javascript:", re.I),
]


def sanitize_string(value: str, max_length: int = 500) -> str:
    """문자열을 정리하고 보안 검증을 수행합니다.

    5단계 파이프라인:
    1. 타입 체크
    2. 공백 제거
    3. 제어 문자 제거
    4. 길이 제한
    5. 위험 패턴 탐지

    Args:
        value: 검증할 문자열.
        max_length: 최대 허용 길이.

    Returns:
        정리된 문자열.

    Raises:
        ToolError: 타입이 올바르지 않거나 위험 패턴이 감지된 경우.
    """
    if not isinstance(value, str):
        raise ToolError(ErrorCode.INVALID_ARGUMENT, "문자열이 아닙니다")

    cleaned = value.strip()
    cleaned = CONTROL_CHARS.sub("", cleaned)

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(cleaned):
            raise ToolError(ErrorCode.INVALID_ARGUMENT, "보안 위험 감지")

    return cleaned


def validate_path(user_path: str, base_dir: str) -> Path:
    """사용자 경로가 base_dir 내부에 있는지 검증합니다.

    Path Traversal 공격을 방어합니다.

    Args:
        user_path: 사용자가 입력한 경로.
        base_dir: 허용된 기본 디렉토리.

    Returns:
        검증된 Path 객체.

    Raises:
        ToolError: 경로가 허용 범위를 벗어나는 경우.
    """
    if ".." in user_path:
        raise ToolError(ErrorCode.INVALID_ARGUMENT, "'..'을 포함할 수 없습니다")
    if "\x00" in user_path:
        raise ToolError(ErrorCode.INVALID_ARGUMENT, "null 바이트 불가")

    resolved = Path(base_dir, user_path).resolve()
    base_resolved = Path(base_dir).resolve()

    if not str(resolved).startswith(str(base_resolved)):
        raise ToolError(ErrorCode.INVALID_ARGUMENT, "허용 범위 밖의 경로")
    return resolved


def validate_ticket_input(
    title: str,
    description: str,
    priority: str = "medium",
) -> dict:
    """티켓 생성 입력을 검증합니다.

    Args:
        title: 티켓 제목 (5~200자).
        description: 티켓 설명 (10~2000자).
        priority: 우선순위 (low, medium, high, critical).

    Returns:
        검증된 입력 딕셔너리 {"title", "description", "priority"}.

    Raises:
        ToolError: 입력이 유효하지 않은 경우.
    """
    title = sanitize_string(title, 200)
    if len(title) < 5:
        raise ToolError(ErrorCode.INVALID_ARGUMENT, "제목은 5자 이상이어야 합니다")

    desc = sanitize_string(description, 2000)
    if len(desc) < 10:
        raise ToolError(ErrorCode.INVALID_ARGUMENT, "설명은 10자 이상이어야 합니다")

    if priority.lower() not in VALID_PRIORITIES:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            f"유효하지 않은 우선순위: {priority}. Must be one of: {', '.join(sorted(VALID_PRIORITIES))}.",
        )

    return {
        "title": title,
        "description": desc,
        "priority": priority.lower(),
    }


def validate_query(
    query: str,
    min_length: int = 1,
    max_length: int = 100,
) -> str:
    """검색 쿼리를 검증합니다.

    Args:
        query: 검색어.
        min_length: 최소 길이.
        max_length: 최대 길이.

    Returns:
        검증된 쿼리 문자열.

    Raises:
        ToolError: 쿼리가 유효하지 않은 경우.
    """
    query = sanitize_string(query, max_length)
    if len(query) < min_length:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            f"검색어는 {min_length}자 이상이어야 합니다",
        )
    return query


def validate_doc_id(doc_id: str) -> str:
    """문서 ID를 검증합니다: 영숫자와 하이픈만 허용.

    Path traversal 공격을 방지합니다.

    Args:
        doc_id: 검증할 문서 ID.

    Returns:
        검증된 doc_id.

    Raises:
        ToolError: doc_id에 유효하지 않은 문자가 포함된 경우.
    """
    stripped = doc_id.strip()
    if not stripped:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            "Document ID must not be empty.",
        )
    if not re.match(r"^[a-zA-Z0-9-]+$", stripped):
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            f"Invalid document ID '{doc_id}'. Only alphanumeric characters and hyphens are allowed.",
        )
    return stripped
