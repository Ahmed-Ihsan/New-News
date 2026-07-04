"""
دوال مساعدة مشتركة.
Shared utility functions.
"""

import re
from datetime import datetime, timezone


def time_ago(timestamp: int | float) -> str:
    """تحويل الطابع الزمني إلى صيغة 'منذ X'."""
    now = datetime.now(timezone.utc)
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "الآن"
    elif seconds < 3600:
        mins = seconds // 60
        return f"منذ {mins} دقيقة" if mins == 1 else f"منذ {mins} دقائق"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
    else:
        days = seconds // 86400
        return f"منذ {days} يوم" if days == 1 else f"منذ {days} أيام"


def sanitize_text(text: str) -> str:
    """تنظيف النص من أحرف Markdown الخاصة."""
    if not text:
        return ""
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ").replace("\r", "")
    return text.strip()


def ddg_is_blocked(html: str) -> bool:
    """فحص ما إذا كانت DuckDuckGo تُعيد صفحة حظر (anomaly/botnet)."""
    return "anomaly" in html or "botnet" in html or (
        len(html) < 16000 and "result__a" not in html
    )


def ddg_extract_results(html: str) -> list[tuple[str, str, str]]:
    """
    استخراج نتائج DuckDuckGo HTML.
    يعيد قائمة من (link, title, snippet).
    يستخدم regex مرن — لا يتطلب snippet.
    """
    entries = re.findall(
        r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
        r'.*?<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    if entries:
        return entries

    entries_a = re.findall(
        r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )
    return [(link, title, "") for link, title in entries_a]


def ddg_clean_link(raw_link: str) -> str:
    """تنظيف رابط DuckDuckGo من redirect."""
    m = re.search(r'uddg=([^&]+)', raw_link)
    if m:
        from urllib.parse import unquote
        return unquote(m.group(1))
    return raw_link


def is_tool_launch(title: str, description: str = "") -> bool:
    """فحص ما إذا كان العنوان يتحدث عن إطلاق أداة أو تحديث."""
    from .config import TOOL_LAUNCH_KEYWORDS
    text = (title + " " + description).lower()
    return any(kw in text for kw in TOOL_LAUNCH_KEYWORDS)


def is_recent(date_str: str, max_days: int = 14) -> bool:
    """فحص ما إذا كان التاريخ ضمن آخر max_days يوماً."""
    if not date_str:
        return True
    now = datetime.now(timezone.utc)
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%a, %d %b %Y %H:%M:%S",
        "%a, %d %b %Y",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip()[:30], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = (now - dt).total_seconds() / 86400
            return age_days <= max_days
        except (ValueError, TypeError):
            continue
    return True


def normalize_title(title: str) -> str:
    """تطبيع العنوان لإزالة التكرار عبر المصادر."""
    normalized = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]', '', title.lower())[:60]
    return normalized
