"""
طبقة HTTP — دوال جلب البيانات من الإنترنت.
HTTP layer: fetch_json, fetch_html.
"""

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import HEADERS, REQUEST_TIMEOUT, SSL_CONTEXT, logger


def fetch_json(url: str, headers: dict | None = None, timeout: int = REQUEST_TIMEOUT) -> Any:
    """جلب بيانات JSON من URL مع معالجة الأخطاء."""
    req_headers = {**HEADERS, **(headers or {})}
    req = Request(url, headers=req_headers)
    try:
        with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except HTTPError as e:
        logger.error(f"خطأ HTTP {e.code} عند جلب: {url}")
        raise
    except URLError as e:
        logger.error(f"خطأ اتصال عند جلب: {url} - {e.reason}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"خطأ في تحليل JSON من: {url} - {e}")
        raise


def fetch_html(url: str, headers: dict | None = None, timeout: int = REQUEST_TIMEOUT) -> str:
    """جلب محتوى HTML من URL."""
    req_headers = {**HEADERS, **(headers or {})}
    req_headers["Accept"] = "text/html"
    req = Request(url, headers=req_headers)
    try:
        with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as e:
        logger.error(f"خطأ عند جلب HTML من: {url} - {e}")
        raise
