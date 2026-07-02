"""
مصدر YouTube — يجلب أحدث الفيديوهات من قنوات التقنية عبر RSS.
YouTube source: fetches latest videos from tech channels via RSS feeds.
"""

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
)


class YouTubeSource(NewsSource):
    name = "YouTube"
    icon = "📺"
    PER_CHANNEL = 3

    CHANNELS = {
        "The Verge": "UCddiUEpeqJcYeBxX1IVBKvQ",
        "Engadget": "UC-6OW5aJYBFM33zXQlBKPNA",
        "9to5Google": "UCzIO0iX4yKW2P4NkmmKq1PA",
        "Linus Tech Tips": "UCXuqSBlHAE6Xw-yeJA0Tunw",
        "Marques Brownlee": "UCBJycsmduvYEL83R_U4JriQ",
        "Mrwhosetheboss": "UCMiJRAwDNSNzuYeN2uWa0pA",
        "Fireship": "UCsBjURrPoezykLs9EqgamOA",
        "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg",
        "Unbox Therapy": "UC-YwYEpH91JDzWwSepHOtkw",
        "Lex Fridman": "UCSHZKyawb77ixDdsGog4iWA",
    }

    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    def _fetch_channel(self, channel_name: str, channel_id: str) -> list[dict]:
        """جلب أحدث الفيديوهات من قناة واحدة عبر RSS."""
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            xml = fetch_html(url)
            if not xml:
                return []
            root = ET.fromstring(xml)
            videos = []
            for entry in root.findall("atom:entry", self.NS)[: self.PER_CHANNEL]:
                video_id = entry.findtext("yt:videoId", "", self.NS)
                title = entry.findtext("atom:title", "", self.NS)
                link_elem = entry.find("atom:link", self.NS)
                link = link_elem.get("href", "") if link_elem is not None else ""
                author_elem = entry.find("atom:author", self.NS)
                channel = (
                    author_elem.findtext("atom:name", channel_name, self.NS)
                    if author_elem is not None
                    else channel_name
                )
                published = entry.findtext("atom:published", "", self.NS)
                if video_id:
                    videos.append({
                        "title": sanitize_text(title),
                        "url": link or f"https://www.youtube.com/watch?v={video_id}",
                        "channel": sanitize_text(channel),
                        "published": published[:10],
                        "video_id": video_id,
                    })
            return videos
        except Exception as e:
            logger.warning(f"  ⚠️ فشل جلب قناة {channel_name}: {e}")
            return []

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب فيديوهات {self.name}...")
        stories = []
        try:
            per_channel: dict[str, list[dict]] = {}
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(self._fetch_channel, name, cid): name
                    for name, cid in self.CHANNELS.items()
                }
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        videos = future.result()
                        if videos:
                            per_channel[name] = videos
                    except Exception as e:
                        logger.warning(f"  ⚠️ تخطي قناة {name}: {e}")

            # Round-robin: كل قناة تحصل على فيديو واحد قبل أي قناة أخرى تحصل على الثاني
            for i in range(self.PER_CHANNEL):
                if len(stories) >= MAX_STORIES_PER_SOURCE:
                    break
                for name in self.CHANNELS:
                    if name not in per_channel:
                        continue
                    if i >= len(per_channel[name]):
                        continue
                    if len(stories) >= MAX_STORIES_PER_SOURCE:
                        break
                    stories.append(per_channel[name][i])

            logger.info(f"  ✅ تم جلب {len(stories)} فيديو من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
