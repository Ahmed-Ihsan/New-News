"""
مصدر Reddit — يستخدم DuckDuckGo مع site:reddit.com للالتفاف حول حظر Reddit.
Reddit source: uses DuckDuckGo with site:reddit.com to bypass Reddit's bot blocking.
"""

import re
import time

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
    ddg_is_blocked, ddg_extract_results, ddg_clean_link,
)


class RedditSource(NewsSource):
    """
    Reddit - Subreddits تقنية
    Reddit يحظر RSS و JSON API للبوتات (HTTP 429/403).
    نستخدم DuckDuckGo مع site:reddit.com/r/{subreddit} للعثور على
    منشورات Reddit حقيقية — نفس آلية X (Twitter).
    """

    name = "Reddit Tech"
    icon = "�"
    SUBREDDITS = [
        "technology",
        "programming",
        "artificial",
        "MachineLearning",
        "webdev",
    ]
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        seen_urls = set()

        for sub in self.SUBREDDITS:
            try:
                query = f"site:reddit.com/r/{sub}"
                url = f"{self.SEARCH_URL}?q={query.replace(' ', '+')}"
                html = fetch_html(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://duckduckgo.com/",
                })

                # فحص إذا كانت DuckDuckGo تحظرنا
                if ddg_is_blocked(html):
                    logger.warning(f"  ⚠️ DuckDuckGo حظرت الطلب (anomaly/botnet) لـ r/{sub}")
                    time.sleep(3)
                    continue

                # استخراج النتائج باستخدام الدالة المساعدة المرنة
                entries = ddg_extract_results(html)

                for raw_link, title_raw, snippet_raw in entries[:3]:
                    link = ddg_clean_link(raw_link)

                    if "reddit.com" not in link or link in seen_urls:
                        continue
                    seen_urls.add(link)

                    title = re.sub(r'<[^>]+>', '', title_raw).strip()
                    snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
                    title = title.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')

                    if not title or len(title) < 3:
                        continue

                    stories.append({
                        "title": sanitize_text(title),
                        "url": link,
                        "score": 0,
                        "comments": 0,
                        "author": "Reddit",
                        "subreddit": f"r/{sub}",
                        "time": 0,
                        "time_ago": "اليوم",
                        "reddit_link": link,
                        "snippet": sanitize_text(snippet[:200]),
                    })

                    if len(stories) >= MAX_STORIES_PER_SOURCE:
                        break

                time.sleep(1)

            except Exception as e:
                logger.warning(f"  ⚠️ فشل جلب r/{sub}: {e}")

        logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        return stories
