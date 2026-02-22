"""
Input validation utilities.
TODO (Episode 8): Implement validation functions.
"""
from __future__ import annotations


def validate_priority(value: str) -> str:
    # TODO: Validate priority is one of low/medium/high/critical
    return value


def validate_text_length(text: str, field_name: str, max_len: int = 500) -> str:
    # TODO: Strip, check non-empty, check max length
    return text


def sanitize_query(query: str) -> str:
    # TODO: Strip, collapse spaces, lowercase, check non-empty
    return query


def validate_doc_id(doc_id: str) -> str:
    # TODO: Check alphanumeric + hyphens only
    return doc_id
