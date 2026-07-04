"""
الحزمة الأساسية — تصدير كل ما يحتاجه المصادر والمُجمّع.
Core package: exports config, http, utils, and base.
"""

from .config import (
    logger,
    OUTPUT_DIR,
    MAX_STORIES_PER_SOURCE,
    REQUEST_TIMEOUT,
    HEADERS,
    SSL_CONTEXT,
    TOOL_LAUNCH_KEYWORDS,
    MIN_HN_SCORE,
    MIN_LOBSTERS_SCORE,
    MAX_NEWS_AGE_DAYS,
    EXCLUDED_REPOS,
)
from .http import fetch_json, fetch_html
from .utils import (
    time_ago,
    sanitize_text,
    ddg_is_blocked,
    ddg_extract_results,
    ddg_clean_link,
    is_tool_launch,
    is_recent,
    normalize_title,
)
from .base import NewsSource

__all__ = [
    "logger",
    "OUTPUT_DIR",
    "MAX_STORIES_PER_SOURCE",
    "REQUEST_TIMEOUT",
    "HEADERS",
    "SSL_CONTEXT",
    "TOOL_LAUNCH_KEYWORDS",
    "MIN_HN_SCORE",
    "MIN_LOBSTERS_SCORE",
    "MAX_NEWS_AGE_DAYS",
    "EXCLUDED_REPOS",
    "fetch_json",
    "fetch_html",
    "time_ago",
    "sanitize_text",
    "ddg_is_blocked",
    "ddg_extract_results",
    "ddg_clean_link",
    "is_tool_launch",
    "is_recent",
    "normalize_title",
    "NewsSource",
]
