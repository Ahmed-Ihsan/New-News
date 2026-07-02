"""
مصدر Medium — يجلب أحدث المقالات من وسوم التقنية عبر RSS.
Medium source: fetches latest articles from tech tags via RSS feeds.
"""

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
)


class MediumSource(NewsSource):
    name = "Medium"
    icon = "✍️"
    PER_TAG = 5

    TAGS = [
        "technology",
        "programming",
        "artificial-intelligence",
        "startup",
        "software-engineering",
    ]

    NS = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    def _fetch_tag(self, tag: str) -> list[dict]:
        """جلب أحدث المقالات من وسم Medium واحد عبر RSS."""
        url = f"https://medium.com/feed/tag/{tag}"
        try:
            xml = fetch_html(url)
            if not xml:
                return []
            root = ET.fromstring(xml)
            stories = []
            for item in root.findall(".//item")[: self.PER_TAG]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                author = item.findtext("dc:creator", "", self.NS) or item.findtext("author", "")
                published = item.findtext("pubDate", "")
                categories = [
                    cat.text for cat in item.findall("category") if cat.text
                ]
                stories.append({
                    "title": sanitize_text(title),
                    "url": link,
                    "author": sanitize_text(author or "مجهول"),
                    "published": published,
                    "tag": tag,
                    "categories": categories[:4],
                })
            return stories
        except Exception as e:
            logger.warning(f"  ⚠️ فشل جلب وسم Medium '{tag}': {e}")
            return []

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب مقالات {self.name}...")
        stories = []
        try:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self._fetch_tag, tag): tag
                    for tag in self.TAGS
                }
                for future in as_completed(futures):
                    tag = futures[future]
                    try:
                        tag_stories = future.result()
                        for story in tag_stories:
                            if len(stories) >= MAX_STORIES_PER_SOURCE:
                                break
                            stories.append(story)
                    except Exception as e:
                        logger.warning(f"  ⚠️ تخطي وسم Medium '{tag}': {e}")
            logger.info(f"  ✅ تم جلب {len(stories)} مقال من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
