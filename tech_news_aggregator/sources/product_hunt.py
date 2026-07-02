import re
from ..core import NewsSource, fetch_html, logger, MAX_STORIES_PER_SOURCE, sanitize_text


class ProductHuntSource(NewsSource):
    name = "Product Hunt"
    icon = "🐱"
    URL = "https://www.producthunt.com/"
    PATTERN = r'"name"\s*:\s*"([^"]+)".*?"tagline"\s*:\s*"([^"]+)"'

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            html = fetch_html(self.URL)
            if not html:
                logger.warning(f"  ⚠️ لا يوجد محتوى من {self.name}")
                return stories
            matches = re.findall(self.PATTERN, html, re.DOTALL)
            if not matches:
                logger.warning(f"  ⚠️ لا توجد منتجات من {self.name}")
                stories.append({
                    "title": "تعذر جلب منتجات Product Hunt",
                    "tagline": "حاول مرة أخرى لاحقاً",
                    "url": self.URL,
                    "rank": 1,
                })
                return stories
            for rank, (name, tagline) in enumerate(matches[:MAX_STORIES_PER_SOURCE], start=1):
                stories.append({
                    "title": sanitize_text(name),
                    "tagline": sanitize_text(tagline),
                    "url": self.URL,
                    "rank": rank,
                })
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
