import xml.etree.ElementTree as ET
from ..core import NewsSource, fetch_html, logger, MAX_STORIES_PER_SOURCE, sanitize_text


class ArxivSource(NewsSource):
    name = "arXiv Research"
    icon = "🔬"
    URL = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10"
    NS = {"atom": "http://www.w3.org/2005/Atom"}

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            xml_text = fetch_html(self.URL)
            if not xml_text:
                logger.warning(f"  ⚠️ لا يوجد محتوى من {self.name}")
                return stories
            root = ET.fromstring(xml_text)
            entries = root.findall("atom:entry", self.NS)
            for entry in entries[:MAX_STORIES_PER_SOURCE]:
                try:
                    title_el = entry.find("atom:title", self.NS)
                    summary_el = entry.find("atom:summary", self.NS)
                    id_el = entry.find("atom:id", self.NS)
                    title = title_el.text.strip() if title_el is not None and title_el.text else "بدون عنوان"
                    summary = summary_el.text.strip() if summary_el is not None and summary_el.text else ""
                    url = id_el.text.strip() if id_el is not None and id_el.text else ""
                    stories.append({
                        "title": sanitize_text(title),
                        "description": sanitize_text(summary[:150]) + "...",
                        "url": url,
                        "author": "arXiv",
                        "tagline": "ورقة بحثية علمية",
                    })
                except Exception as e:
                    logger.warning(f"تخطي ورقة arXiv: {e}")
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
