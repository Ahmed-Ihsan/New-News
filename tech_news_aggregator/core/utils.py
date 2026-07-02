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
