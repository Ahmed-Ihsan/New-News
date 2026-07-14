"""
مصدر X (تويتر سابقاً) — يجلب أحدث المنشورات من حسابات تقنية مختارة.
X (Twitter) source: aggregates recent posts from selected tech accounts.

القناة الأساسية: Nitter RSS (تغريدات حقيقية، بدون API أو تسجيل دخول) عبر عدة مرايا.
القناة الاحتياطية: DuckDuckGo `site:x.com/<handle>` (تُستخدم فقط إذا فشلت كل مرايا Nitter).
Primary: Nitter RSS (real tweets, multi-instance failover). Fallback: DuckDuckGo site: search.

سبب التصميم: الاعتماد الكامل على DuckDuckGo يؤدي إلى حظر عنوان IP (anomaly page)
فيعيد المصدر 0 منشور. Nitter RSS أكثر موثوقية ويعطي التغريدات الفعلية.
"""

import re
import time
import xml.etree.ElementTree as ET

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
    ddg_is_blocked, ddg_extract_results, ddg_clean_link,
)


# ─────────────────────────────────────────────────────────────
# حسابات تقنية مختارة على X — mix of companies + news outlets
# ─────────────────────────────────────────────────────────────

TECH_ACCOUNTS = [
    "OpenAI",
    "GoogleDeepMind",
    "AnthropicAI",
    "nvidia",
    "github",
    "vercel",
    "TechCrunch",
    "verge",
    "arstechnica",
    "ycombinator",
]

# مرايا Nitter — تُجرَّب بالترتيب حتى تنجح واحدة (للمرونة عند تعطّل مرآة)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com",
    "https://xcancel.com",
    "https://nitter.tiekoetter.com",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# أقصى عدد منشورات لكل حساب — لضمان التنوع عبر الحسابات
MAX_PER_ACCOUNT = 2


def _clean_html(text: str) -> str:
    """إزالة وسوم HTML وفك ترميز الكيانات الشائعة."""
    text = re.sub(r'<[^>]+>', '', text or '').strip()
    return (text.replace('&amp;', '&')
                .replace('&#39;', "'")
                .replace('&quot;', '"')
                .replace('&lt;', '<')
                .replace('&gt;', '>'))


def _nitter_link_to_x(link: str) -> str:
    """تحويل رابط Nitter إلى رابط x.com الأصلي (وإزالة #m)."""
    m = re.search(r'https?://[^/]+/([^/?#]+/status/\d+)', link or '')
    if m:
        return f"https://x.com/{m.group(1)}"
    return link


class XSource(NewsSource):
    name = "X (Twitter)"
    icon = "🐦"
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب منشورات {self.name} من {len(TECH_ACCOUNTS)} حساب...")

        # اجمع حتى MAX_PER_ACCOUNT لكل حساب، ثم وزّع بالتناوب لتغطية كل الحسابات
        per_account: dict[str, list[dict]] = {}
        nitter_ok = 0
        for hi, handle in enumerate(TECH_ACCOUNTS):
            posts = self._fetch_nitter(handle)
            if posts:
                nitter_ok += 1
            else:
                posts = self._fetch_ddg(handle)
            per_account[handle] = posts[:MAX_PER_ACCOUNT]
            if hi < len(TECH_ACCOUNTS) - 1:
                time.sleep(0.6)

        # دمج بالتناوب (round-robin): منشور واحد من كل حساب أولاً، ثم الثاني...
        stories: list[dict] = []
        seen_urls: set[str] = set()
        for rank in range(MAX_PER_ACCOUNT):
            for handle in TECH_ACCOUNTS:
                lst = per_account.get(handle, [])
                if rank < len(lst):
                    s = lst[rank]
                    if s["url"] in seen_urls:
                        continue
                    seen_urls.add(s["url"])
                    stories.append(s)
                    if len(stories) >= MAX_STORIES_PER_SOURCE:
                        break
            if len(stories) >= MAX_STORIES_PER_SOURCE:
                break

        logger.info(
            f"  ✅ تم جلب {len(stories)} منشور من {self.name} "
            f"(Nitter: {nitter_ok}/{len(TECH_ACCOUNTS)} حساب)"
        )
        return stories

    # ─────────────────────────────────────────────────────────
    # القناة الأساسية: Nitter RSS
    # ─────────────────────────────────────────────────────────

    def _fetch_nitter(self, handle: str) -> list[dict]:
        """جلب تغريدات الحساب عبر Nitter RSS مع تجربة عدة مرايا."""
        for base in NITTER_INSTANCES:
            url = f"{base}/{handle}/rss"
            try:
                xml_text = fetch_html(url, headers={
                    "User-Agent": USER_AGENTS[0],
                    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                })
            except Exception as e:
                logger.debug(f"  Nitter فشل ({base} @{handle}): {e}")
                continue

            try:
                root = ET.fromstring(xml_text)
            except ET.ParseError:
                # صفحة تحقق/حظر وليست RSS — جرّب المرآة التالية
                continue

            channel = root.find("channel")
            items = channel.findall("item") if channel is not None else []
            if not items:
                continue

            posts: list[dict] = []
            for it in items:
                title = _clean_html(it.findtext("title") or "")
                raw_link = (it.findtext("link") or "").strip()
                pub = (it.findtext("pubDate") or "").strip()
                if not title or len(title) < 3 or not raw_link:
                    continue
                if self.search_key and self.search_key.lower() not in title.lower():
                    continue
                link = _nitter_link_to_x(raw_link)
                posts.append({
                    "title": sanitize_text(title),
                    "url": link,
                    "snippet": sanitize_text(title[:200]),
                    "author": f"@{handle}",
                    "handle": handle,
                    "source": "X",
                    "published": pub,
                })
                if len(posts) >= MAX_PER_ACCOUNT:
                    break
            if posts:
                return posts
        return []

    # ─────────────────────────────────────────────────────────
    # القناة الاحتياطية: DuckDuckGo site:x.com/<handle>
    # ─────────────────────────────────────────────────────────

    def _fetch_ddg(self, handle: str) -> list[dict]:
        """جلب منشورات الحساب عبر DuckDuckGo (يُستخدم فقط عند فشل Nitter)."""
        query = f"site:x.com/{handle}"
        if self.search_key:
            query = f"{query} {self.search_key}"

        posts: list[dict] = []
        for attempt in range(2):
            try:
                ua = USER_AGENTS[attempt % len(USER_AGENTS)]
                url = f"{self.SEARCH_URL}?q={query.replace(' ', '+')}"
                html = fetch_html(url, headers={
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://duckduckgo.com/",
                })
                if ddg_is_blocked(html):
                    logger.debug(f"  DuckDuckGo محظورة (@{handle}) — تخطّي الاحتياطي")
                    time.sleep(2 + attempt * 2)
                    continue
                entries = ddg_extract_results(html)
                if not entries:
                    continue
                for raw_link, title_raw, snippet_raw in entries:
                    link = ddg_clean_link(raw_link)
                    link_l = link.lower()
                    if (f"x.com/{handle.lower()}" not in link_l
                            and f"twitter.com/{handle.lower()}" not in link_l):
                        continue
                    title = _clean_html(title_raw)
                    snippet = _clean_html(snippet_raw)
                    if not title or len(title) < 3:
                        continue
                    posts.append({
                        "title": sanitize_text(title),
                        "url": link,
                        "snippet": sanitize_text(snippet[:200]),
                        "author": f"@{handle}",
                        "handle": handle,
                        "source": "X",
                    })
                    if len(posts) >= MAX_PER_ACCOUNT:
                        break
                break
            except Exception as e:
                logger.debug(f"  إعادة محاولة DDG @{handle} ({attempt+1}/2): {e}")
                time.sleep(2 + attempt * 2)
        return posts
