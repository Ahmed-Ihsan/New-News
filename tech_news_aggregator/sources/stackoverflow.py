"""
مصدر مدونة Stack Overflow — اتجاهات المطورين ومقالات تقنية.
Stack Overflow Blog source: developer trends and technical articles.
"""

import xml.etree.ElementTree as ET

from ..core import NewsSource, fetch_html, logger, MAX_STORIES_PER_SOURCE, sanitize_text

NS = {"dc": "http://purl.org/dc/elements/1.1/"}


class StackOverflowSource(NewsSource):
    name = "Stack Overflow Blog"
    icon = "💬"
    URL = "https://stackoverflow.blog/feed/"
    MAX_STORIES = 3
    EXCLUDED_CATEGORIES = {"podcast"}

    def __init__(self, search_key: str | None = None):
        pass

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب مقالات {self.name}...")
        stories = []
        try:
            xml = fetch_html(self.URL)
            if not xml:
                logger.warning(f"  ⚠️ لا يوجد محتوى من {self.name}")
                return stories
            root = ET.fromstring(xml)
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub = item.findtext("pubDate", "")
                desc = item.findtext("description", "")
                author = item.findtext("dc:creator", "", NS) or ""

                if not title:
                    continue

                categories = [
                    cat.text for cat in item.findall("category") if cat.text
                ]

                if any(cat.lower() in self.EXCLUDED_CATEGORIES for cat in categories):
                    continue

                stories.append({
                    "title": sanitize_text(title),
                    "url": link,
                    "author": sanitize_text(author or "مجهول"),
                    "published": pub[:30] if pub else "",
                    "description": sanitize_text(desc[:200] if desc else ""),
                    "categories": categories[:4],
                })

                if len(stories) >= self.MAX_STORIES:
                    break

            logger.info(f"  ✅ تم جلب {len(stories)} مقال من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
