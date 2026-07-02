import re
import time
from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
    ddg_is_blocked, ddg_extract_results, ddg_clean_link,
)


class XSource(NewsSource):
    name = "X (Twitter)"
    icon = "🐦"
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب منشورات {self.name}...")
        stories = []
        seen_urls = set()

        if self.search_key:
            queries = [f"site:x.com {self.search_key}"]
        else:
            queries = [
                "site:x.com tech OR AI",
                "site:x.com OpenAI OR Anthropic OR Google",
                "site:x.com programming OR developer",
            ]

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]

        for qi, query in enumerate(queries):
            if len(stories) >= MAX_STORIES_PER_SOURCE:
                break
            for attempt in range(3):
                if len(stories) >= MAX_STORIES_PER_SOURCE:
                    break
                try:
                    ua = user_agents[(qi + attempt) % len(user_agents)]
                    url = f"{self.SEARCH_URL}?q={query.replace(' ', '+')}"
                    html = fetch_html(url, headers={
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://duckduckgo.com/",
                    })
                    if ddg_is_blocked(html):
                        logger.debug(f"  DuckDuckGo حظرت الطلب (anomaly) — إعادة محاولة")
                        time.sleep(3 + attempt * 2)
                        continue
                    entries = ddg_extract_results(html)
                    if not entries:
                        time.sleep(2 + attempt)
                        continue
                    for raw_link, title_raw, snippet_raw in entries:
                        link = ddg_clean_link(raw_link)
                        if "x.com" not in link and "twitter.com" not in link:
                            continue
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)
                        title = re.sub(r'<[^>]+>', '', title_raw).strip()
                        snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
                        title = title.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')
                        snippet = snippet.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')
                        if not title or len(title) < 3:
                            continue
                        handle = "مجهول"
                        hm = re.search(r'x\.com/([^/?#]+)/?', link)
                        if hm and hm.group(1) not in ("home", "search", "explore", "i"):
                            handle = f"@{hm.group(1)}"
                        stories.append({
                            "title": sanitize_text(title),
                            "url": link,
                            "snippet": sanitize_text(snippet[:200]),
                            "author": handle,
                            "source": "X",
                        })
                        if len(stories) >= MAX_STORIES_PER_SOURCE:
                            break
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.debug(f"  إعادة محاولة X (محاولة {attempt+1}/3): {e}")
                        time.sleep(3 + attempt * 2)
                    else:
                        logger.warning(f"  ⚠️ فشل جلب {self.name} بعد 3 محاولات: {e}")
            if qi < len(queries) - 1 and len(stories) < MAX_STORIES_PER_SOURCE:
                time.sleep(1)
        logger.info(f"  ✅ تم جلب {len(stories)} منشور من {self.name}")
        return stories
