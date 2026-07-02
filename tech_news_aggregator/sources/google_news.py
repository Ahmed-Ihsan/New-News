"""
مصدر Google News — يجلب أحدث الأخبار التقنية عبر استعلامات بحث متعددة.
Google News source: fetches latest tech news via RSS search queries.
"""

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
)


class GoogleNewsSource(NewsSource):
    name = "Google News"
    icon = "🌐"
    BASE_URL = "https://news.google.com/rss/search"
    QUERIES = [
        '"launches new" tool OR platform OR feature tech',
        '"announces" "new" AI OR tool OR model 2026',
        '"introduces" "new" technology OR software OR API',
    ]

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key

    def _fetch_query(self, query: str) -> list[dict]:
        """جلب وتحليل نتائج استعلام واحد من Google News RSS."""
        url = f"{self.BASE_URL}?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        stories = []
        try:
            xml = fetch_html(url)
            if not xml:
                return []
            root = ET.fromstring(xml)
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                published = item.findtext("pubDate", "")
                description = item.findtext("description", "")
                source_elem = item.find("source")
                source_name = source_elem.text if source_elem is not None and source_elem.text else ""

                # إزالة " - SourceName" من العنوان
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0]

                if not title:
                    continue

                stories.append({
                    "title": sanitize_text(title),
                    "url": link,
                    "source": source_name or "Google News",
                    "published": published[:30],
                    "description": sanitize_text(description[:200]),
                })
        except Exception as e:
            logger.warning(f"  ⚠️ فشل جلب استعلام Google News: {e}")
        return stories

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            if self.search_key:
                queries = [f"{self.search_key} tech"]
            else:
                queries = self.QUERIES

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._fetch_query, query): query
                    for query in queries
                }
                for future in as_completed(futures):
                    try:
                        query_stories = future.result()
                        for story in query_stories:
                            if len(stories) >= MAX_STORIES_PER_SOURCE:
                                break
                            stories.append(story)
                    except Exception as e:
                        logger.warning(f"  ⚠️ تخطي استعلام Google News: {e}")

            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
