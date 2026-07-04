"""
مصدر أخبار يوتيوب التقنية — يجلب مقاطع إخبارية من قنوات مختارة.
YouTube News source: fetches news-oriented videos from curated tech channels.
"""

import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import NewsSource, fetch_html, logger, sanitize_text, is_recent


class YouTubeNewsSource(NewsSource):
    name = "Tech Video Highlights"
    icon = "📺"
    PER_CHANNEL = 3
    MAX_STORIES = 3
    MAX_AGE_DAYS = 7

    CHANNELS = {
        "Fireship": "UCsBjURrPoezykLs9EqgamOA",
        "TechLinked": "UCeeFfhMcJa1kjtfZAGskOCA",
        "AI Explained": "UCNJ1Ymd5yFuUPtn21xtRbbw",
        "Matthew Berman": "UCawZsQWqfGSbCI5yjkdVkTA",
    }

    NEWS_KEYWORDS = [
        "announces", "announced", "released", "launches", "launched",
        "updates", "updated", "discontinues", "acquires", "acquired",
        "open sources", "open-sourced", "deprecates", "deprecated",
        "introduces", "introduced", "unveils", "unveiled",
        "rolls out", "shuts down", "shutting down",
        "security", "vulnerability", "breach", "cve",
        "api", "framework", "language", "compiler", "runtime",
        "new ", "now ", "finally", "breaking",
        "gpt", "claude", "gemini", "llm", "ai ",
        "rust", "python", "javascript", "typescript", "go ",
        "kubernetes", "docker", "react", "vue", "angular",
        "github", "gitlab", "vscode", "neovim",
    ]

    CLICKBAIT_PATTERNS = [
        "you won't believe", "changes everything", "game changer",
        "the truth about", "nobody is talking about",
        "this is insane", "mind blowing", "must watch",
        "i tried", "i switched", "i tested", "my honest",
        "reaction", "reviewing", "roasting", "i built",
        "i coded", "100 days", "30 days", "i quit",
        "i left", "i moved", "day in the life",
    ]

    def __init__(self, search_key: str | None = None):
        pass

    def _is_news(self, title: str) -> bool:
        title_lower = title.lower()
        for pattern in self.CLICKBAIT_PATTERNS:
            if pattern in title_lower:
                return False
        for kw in self.NEWS_KEYWORDS:
            if kw in title_lower:
                return True
        return False

    def _fetch_channel(self, channel_name: str, channel_id: str) -> list[dict]:
        stories = []
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            xml = fetch_html(url)
            if not xml:
                return stories
            root = ET.fromstring(xml)
            count = 0
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext(
                    "{http://www.w3.org/2005/Atom}title", ""
                )
                link_elem = entry.find(
                    "{http://www.w3.org/2005/Atom}link"
                )
                link = link_elem.get("href", "") if link_elem is not None else ""
                published = entry.findtext(
                    "{http://www.w3.org/2005/Atom}published", ""
                )

                if not title:
                    continue
                if not self._is_news(title):
                    continue
                if not is_recent(published, self.MAX_AGE_DAYS):
                    continue

                stories.append({
                    "title": sanitize_text(title),
                    "url": link,
                    "channel": channel_name,
                    "published": published[:30] if published else "",
                })
                count += 1
                if count >= self.PER_CHANNEL:
                    break
        except Exception as e:
            logger.warning(f"  ⚠️ فشل جلب قناة {channel_name}: {e}")
        return stories

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب مقاطع {self.name}...")
        stories = []
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(self._fetch_channel, name, cid): name
                    for name, cid in self.CHANNELS.items()
                }
                for future in as_completed(futures):
                    channel_stories = future.result()
                    for story in channel_stories:
                        if len(stories) >= self.MAX_STORIES:
                            break
                        stories.append(story)
            logger.info(f"  ✅ تم جلب {len(stories)} مقطع إخباري من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
