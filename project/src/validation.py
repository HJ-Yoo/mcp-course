"""
Input validation utilities for the Internal Ops Assistant.

Provides reusable validators that raise ToolError with appropriate
ErrorCode values when inputs are invalid.
"""

from __future__ import annotations

import re

from src.models import ErrorCode, ToolError

VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def validate_priority(value: str) -> str:
    """Ensure the priority value is one of: low, medium, high, critical.

    Args:
        value: The priority string to validate.

    Returns:
        The validated priority in lowercase.

    Raises:
        ToolError: If the value is not a valid priority.
    """
    normalized = value.strip().lower()
    if normalized not in VALID_PRIORITIES:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            f"Invalid priority '{value}'. Must be one of: {', '.join(sorted(VALID_PRIORITIES))}.",
        )
    return normalized


def validate_text_length(text: str, field_name: str, max_len: int = 500) -> str:
    """Strip whitespace and validate that text is non-empty and within max length.

    Args:
        text: The text to validate.
        field_name: Name of the field (used in error messages).
        max_len: Maximum allowed length after stripping.

    Returns:
        The stripped text.

    Raises:
        ToolError: If the text is empty or exceeds max_len.
    """
    stripped = text.strip()
    if not stripped:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            f"'{field_name}' must not be empty.",
        )
    if len(stripped) > max_len:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            f"'{field_name}' exceeds maximum length of {max_len} characters (got {len(stripped)}).",
        )
    return stripped


def sanitize_query(query: str) -> str:
    """Sanitize a search query: strip, collapse spaces, and lowercase.

    Args:
        query: The raw query string.

    Returns:
        The sanitized query.

    Raises:
        ToolError: If the query is empty after sanitization.
    """
    sanitized = re.sub(r"\s+", " ", query.strip()).lower()
    if not sanitized:
        raise ToolError(
            ErrorCode.INVALID_ARGUMENT,
            "Search query must not be empty.",
        )
    return sanitized


def validate_doc_id(doc_id: str) -> str:
    """Validate a document ID: only alphanumeric characters and hyphens allowed.

    Prevents path traversal attacks by rejecting dots, slashes, etc.

    Args:
        doc_id: The document ID to validate.

    Returns:
        The validated doc_id.

    Raises:
        ToolError: If the doc_id contains invalid characters.
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
