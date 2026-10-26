"""Extract one SQL query from a raw model completion.

Extraction is lenient so that execution accuracy measures the query rather than
formatting: the first fenced block or the first line starting with SELECT/WITH
is taken, a trailing semicolon or closing tag is dropped, and trailing prose is
cut off. ``format_ok`` records whether the completion was nothing but the query
(optionally inside a single fence), which is reported separately.
"""

from __future__ import annotations

import re

from sqlglot import parse_one
from sqlglot.errors import SqlglotError

_FENCE_RE = re.compile(r"```[ \t]*(?:sql|googlesql|bigquery)?[ \t]*\n(?P<body>[\s\S]*?)```", re.I)
_START_RE = re.compile(r"(?im)^[ \t]*(?:select|with)\b")
_TRAILER_RE = re.compile(r"(?:\s*</?google_sql>\s*|\s*;\s*)+$", re.I)


def _parses(sql: str) -> bool:
    try:
        return parse_one(sql, read="bigquery") is not None
    except SqlglotError:
        return False


def _trim(candidate: str) -> str:
    candidate = _TRAILER_RE.sub("", candidate.strip())
    paragraphs = candidate.split("\n\n")
    for size in range(len(paragraphs), 0, -1):
        prefix = _TRAILER_RE.sub("", "\n\n".join(paragraphs[:size]).strip())
        if _parses(prefix):
            return prefix
    return candidate


def extract_sql(raw: str) -> tuple[str | None, bool]:
    """Return (sql or None, format_ok)."""
    text = raw.replace("\r\n", "\n").strip()
    if not text:
        return None, False
    fences = list(_FENCE_RE.finditer(text))
    if fences:
        body = fences[0].group("body").strip()
        if not _START_RE.match(body):
            return None, False
        sql = _trim(body)
        whole_fence = len(fences) == 1 and fences[0].start() == 0 and fences[0].end() == len(text)
        return sql or None, whole_fence and sql == body
    start = _START_RE.search(text)
    if start is None:
        return None, False
    sql = _trim(text[start.start() :])
    return sql or None, sql == text
