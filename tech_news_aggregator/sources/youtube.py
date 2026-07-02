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
        "Google": "UCK8sQmJBp8GCxrOtXWBpyEA",
        "Amazon": "UCxGq825hl0AHP18I9-JGKgg",
        "Meta": "UCcr9tciZbuvJrEVAgIXCp8Q",
        "OpenAI": "UCXZCJLdBC09xxGZ6gcdrc6A",
        "NVIDIA": "UCL-g3eGJi1omSDSz48AML-g",
        "Microsoft": "UCnba_sSOe_umiHCpYYvRCqQ",
        "Apple": "UCYFQ33UIPERYx8-ZHucZbDA",
        "Anthropic": "UCOIji0UklfggVrY7Ym-IfDQ",
        "Google DeepMind": "UCP7jMXSY2xbc3KCAE0MHQ-A",
        "Intel": "UC9G8DcGtPfHsVEfUTM_TjEw",
        "AMD": "UC3IHCD51zFpt28TkSBOKJpA",
        "IBM": "UCKWaEZ-_VweaEx1j62do_vQ",
        "Tesla": "UCr7nsg_hE_t06057x51g_Fg",
        "GitHub": "UC7c3Kb6jYCRj4JOHHZTxKsQ",
        "AWS": "UCdoadna9HFHsxXWhafhNvKw",
        "Oracle": "UCHCThmyZ-2yWkv0UVeBDdnQ",
        "SAP": "UC3We5qK8jkxH8yBc0SugKEQ",
        "VMware": "UCTr3zah69bISSVdBcHiKhpA",
        "Red Hat": "UCZKMj3YI0wP-kq4QYpaKdEA",
        "Adobe": "UCL0iAkpqV5YaIVG7xkDtS4Q",
        "Salesforce": "UC_1fwuGhZL5_a6Q-4Rpsl8w",
        "ServiceNow": "UCdXorgCT87YlFRN9n8oJ7_A",
        "Workday": "UCuXDjlKjGUDdtcqbt97gUqQ",
        "Google Cloud": "UCJS9pqu9BzkAMNTmzNMNhvg",
        "Microsoft Developer": "UCV_6HOhwxYLXAGd-JOqKPoQ",
        "Hugging Face": "UCHlNU7kIZhRgSbhHvFoy72w",
        "Mistral AI": "UCRaz_dquopKtb4ptswKcxTA",
        "Perplexity": "UCj593rprmaby5DxBXl4fYvQ",
        "Snowflake": "UCxgY7r-o_ql8ADIdyiQr3Zw",
        "Databricks": "UC3q8O3Bh2Le8Rj1-Q-_UUbA",
        "TensorFlow": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
        "PyTorch": "UCWXI5YeOsh03QvJ59PMaXFw",
        "Cloudflare": "UCgv3xMy6kECn0boYP9d2o-g",
        "GitLab": "UCnMGQ8QHMAnVIsI3xJrihhg",
        "HashiCorp": "UC-AdvAxaagE9W2f0webyNUQ",
        "MongoDB": "UCK_m2976Yvbx-TyDLw7n1WA",
        "Elastic": "UC7z5VlhDHnorjUm6oW5dXcw",
        "Confluent": "UCmTK4CrCaDXpuZ-Evl5-b5Q",
        "Datadog": "UC3lHO0HAZHxPOCYw2edsdPg",
        "Docker Official": "UCW_rmuloTXSIGV1jQG9kEgQ",
        "Kubernetes": "UCZ2bu0qutTOM0tHYa_jkIwg",
        "Firebase": "UCP4bf6IHJJQehibu6ai__cg",
        "Android": "UCrRK02By-e-HD6uotM5nlA",
        "Samsung": "UCWwgaK7x0_FR1goeSRazfsQ",
        "Qualcomm": "UCZRYEa3YILhcdYd7MHkFGzg",
        "ARM": "UCHUAckhCfRom2EHDGxwhfOg",
        "TSMC": "UCtb_F21By-e-HD6uotM5nlA",
        "ASUS": "UCBK_MzhanH8HamrFbABbe8Q",
        "Dell": "UCQmE9qgzRd2eGqJ1Z2ACl5A",
        "HP": "UCYo7yoKhSrj0D618ROH0ccw",
        "Lenovo": "UCJkBIeTewoQGgtviUe5LH_g",
        "Stripe": "UCM1guA1E-RHLO2OyfQPOkEQ",
        "Shopify": "UC7geKfz2-IH0rsgRBtHTm0g",
        "Square": "UC8XWdXApGfNHTHSm1P9hLEQ",
        "PayPal": "UCXe1qKfGweMKTnmRrMw9yOg",
        "Twilio": "UCWh3G9LZmZ3q_xWOyPpn8ag",
        "Notion": "UCoSvlWS5XcwaSzIcbuJ-Ysg",
        "Slack": "UCY3YECgeBcLCzIrFLP4gblw",
        "Atlassian": "UCmM5yxBJKu-JMJ3Js2wE6vw",
        "Zoom": "UC2SxmE4C-KAQuHaEfHVymgQ",
        "LinkedIn": "UCikzJG7RbnNZhKLqqaXRM6A",
        "Spotify": "UCRMqQWxCWE0VMvtUElm-rEA",
        "Netflix": "UCGie8GMlUo3kBKIopdvumVQ",
        "TikTok": "UCLhU6Ror2kjx3_SKqiHfcug",
        "Airbnb": "UCCww-R0oM_CQWXerBcNyKKw",
        "Uber": "UC1xnncYc7586km_rIYQLtLQ",
        "X Corp": "UC0K4Q4pHVZS4OeXVGFYoMaA",
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
