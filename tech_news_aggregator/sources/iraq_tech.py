"""
مصدر التقنية العراقية — يجلب أخبار مجتمعات التقنية والفعاليات في العراق.
Iraq Tech source: aggregates news from Iraqi tech communities and events.

يجمع من ثلاثة مصادر:
1. Google News RSS — استعلامات بالعربية والإنجليزية عن التقنية في العراق
2. DuckDuckGo — بحث site: عن مجتمعات وفعاليات على Facebook/Meetup/LinkedIn
3. scraping مباشر — مواقع المجتمعات التقنية العراقية (Re:Coded, Five One Labs, etc.)
"""

import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text,
    ddg_is_blocked, ddg_extract_results, ddg_clean_link,
)


# ─────────────────────────────────────────────────────────────
# مجتمعات التقنية العراقية المعروفة
# ─────────────────────────────────────────────────────────────

IRAQ_COMMUNITIES = {
    "Re:Coded Iraq": {
        "url": "https://www.re-coded.com",
        "keywords": ["re:coded", "recoded", "re-coded iraq"],
    },
    "Five One Labs": {
        "url": "https://www.fiveonelabs.com",
        "keywords": ["five one labs", "fiveonelabs", "5one labs"],
    },
    "Iraq Tech": {
        "url": None,
        "keywords": ["iraq tech", "iraqi tech", "العراق تقني"],
    },
    "Baghdad Tech": {
        "url": None,
        "keywords": ["baghdad tech", "baghdad meetup", "بغداد التقنية"],
    },
    "Erbil Tech": {
        "url": None,
        "keywords": ["erbil tech", "erbil meetup", "أربيل التقنية"],
    },
    "Mosul Tech": {
        "url": None,
        "keywords": ["mosul tech", "mosul technology", "الموصل التقنية"],
    },
    "Basra Tech": {
        "url": None,
        "keywords": ["basra tech", "basra technology", "البصرة التقنية"],
    },
    "Iraq Developers": {
        "url": None,
        "keywords": ["iraqi developers", "iraq developers", "مطورو العراق"],
    },
    "Python Iraq": {
        "url": None,
        "keywords": ["python iraq", "بايثون العراق"],
    },
    "Tech Iraq Conference": {
        "url": None,
        "keywords": ["tech iraq conference", "tech iraq event", "مؤتمر التقنية العراق"],
    },
}

# ─────────────────────────────────────────────────────────────
# استعلامات Google News — عربية وإنجليزية
# ─────────────────────────────────────────────────────────────

GOOGLE_NEWS_QUERIES = [
    # English queries — must include "tech" or "technology" with Iraq
    '"Iraq" "tech" OR "technology" startup OR hackathon OR meetup OR developer 2026',
    '"Iraq" "developer" OR "programming" OR "coding" "community" OR "bootcamp"',
    '"Iraq" "tech conference" OR "tech event" OR "hackathon" OR "startup weekend"',
    '"Erbil" OR "Baghdad" OR "Basra" "tech" OR "startup" OR "developer"',
    '"Re:Coded" Iraq',
    '"Five One Labs" Iraq',
    '"Iraq" "tech hub" OR "innovation hub" OR "accelerator" OR "incubator"',
    # Arabic queries — must be tech-specific
    '"العراق" "تقني" OR "تقنية" "برمجة" OR "مطورين" OR "ناشئة" 2026',
    '"العراق" "مؤتمر تقني" OR "هاكاثون" OR "فعالية تقنية"',
    '"بغداد" OR "أربيل" "تقني" OR "برمجة" OR "مطورين"',
]

# ─────────────────────────────────────────────────────────────
# استعلامات DuckDuckGo — site: searches
# ─────────────────────────────────────────────────────────────

DDG_SITE_QUERIES = [
    'site:facebook.com "Iraq tech" OR "Iraqi developers" OR "Re:Coded Iraq"',
    'site:facebook.com "Five One Labs" OR "Python Iraq" OR "Baghdad tech"',
    'site:meetup.com Iraq tech OR developer OR programming',
    'site:linkedin.com "Iraq tech" OR "Iraqi developer" OR "tech community Iraq"',
    'site:eventbrite.com Iraq tech OR hackathon OR startup',
    'site:instagram.com "Iraq tech" OR "Iraqi developers" OR "Re:Coded"',
    '"العراق" تقني OR برمجة OR مطورين site:facebook.com',
    '"العراق" مؤتمر تقني OR هاكاثون site:facebook.com',
]

# ─────────────────────────────────────────────────────────────
# مواقع لها صفحات أخبار/مدونات
# ─────────────────────────────────────────────────────────────

COMMUNITY_SITES = {
    "Re:Coded": "https://www.re-coded.com/blog",
    "Five One Labs": "https://www.fiveonelabs.com/blog",
    "Iraq Tech Group": "https://iraqtech.com",
}

# ─────────────────────────────────────────────────────────────
# رؤوس HTTP
# ─────────────────────────────────────────────────────────────

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml,"
              "application/rss+xml",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


# كلمات مفتاحية يجب وجود واحدة على الأقل في العنوان/الوصف
TECH_KEYWORDS = [
    "tech", "technology", "developer", "programming", "coding", "code",
    "software", "startup", "hackathon", "meetup", "bootcamp", "python",
    "javascript", "react", "node", "ai", "artificial intelligence",
    "machine learning", "data science", "cybersecurity", "app",
    "innovation", "incubator", "accelerator", "digital", "cloud",
    "github", "open source", "web", "mobile", "firebase", "devops",
    # عربية
    "تقني", "تقنية", "برمجة", "مطور", "مطورين", "ناشئة", "حاضنة",
    "ابتكار", "رقمي", "ذكاء اصطناعي", "تعلم آلي", "أمن سيبراني",
    "تطبيق", "موقع", "كود", "سوفتوير", "هاكاثون", "بوت كامب",
]


def is_tech_related(title: str, description: str = "") -> bool:
    """فحص ما إذا كان النص يتحدث عن التقنية."""
    text = (title + " " + description).lower()
    return any(kw in text for kw in TECH_KEYWORDS)


class IraqTechSource(NewsSource):
    """
    مصدر مجتمعات التقنية العراقية والفعاليات.
    يجمع من Google News + DuckDuckGo + scraping مباشر.
    """

    name = "Iraq Tech"
    icon = "🇮🇶"
    BASE_NEWS_URL = "https://news.google.com/rss/search"
    DDG_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key

    # ─────────────────────────────────────────────────────────
    # 1. Google News RSS
    # ─────────────────────────────────────────────────────────

    def _fetch_google_news(self) -> list[dict]:
        """جلب أخبار العراق التقنية من Google News RSS."""
        stories = []

        if self.search_key:
            queries = [f'"Iraq" {self.search_key} tech']
        else:
            queries = GOOGLE_NEWS_QUERIES

        def fetch_query(query: str) -> list[dict]:
            items = []
            try:
                url = f"{self.BASE_NEWS_URL}?q={quote(query)}&hl=en&gl=IQ&ceid=IQ:en"
                xml = fetch_html(url, headers=BROWSER_HEADERS)
                if not xml:
                    return []
                root = ET.fromstring(xml)
                for item in root.findall(".//item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub = item.findtext("pubDate", "")
                    desc = item.findtext("description", "")
                    source_el = item.find("source")
                    source_name = (source_el.text if source_el is not None
                                   and source_el.text else "Google News")

                    # إزالة " - SourceName" من العنوان
                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0]

                    if not title:
                        continue

                    # تصفية: فقط الأخبار التقنية
                    if not is_tech_related(title, desc):
                        continue

                    # تحديد المجتمع المرتبط
                    community = self._detect_community(title + " " + desc)

                    items.append({
                        "title": sanitize_text(title),
                        "url": link,
                        "source": source_name,
                        "published": pub[:30] if pub else "",
                        "description": sanitize_text(
                            re.sub(r'<[^>]+>', '', desc)[:200]
                        ),
                        "community": community,
                    })
            except Exception as e:
                logger.warning(f"  ⚠️ فشل استعلام Google News العراق: {e}")
            return items

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_query, q): q for q in queries
            }
            for future in as_completed(futures):
                stories.extend(future.result())

        return stories

    # ─────────────────────────────────────────────────────────
    # 2. DuckDuckGo site: searches
    # ─────────────────────────────────────────────────────────

    def _fetch_ddg_searches(self) -> list[dict]:
        """جلب منشورات المجتمعات العراقية عبر DuckDuckGo."""
        stories = []
        seen_urls = set()

        for qi, query in enumerate(DDG_SITE_QUERIES):
            if len(stories) >= MAX_STORIES_PER_SOURCE:
                break
            for attempt in range(2):
                try:
                    ua = USER_AGENTS[(qi + attempt) % len(USER_AGENTS)]
                    url = f"{self.DDG_URL}?q={quote(query)}"
                    html = fetch_html(url, headers={
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                        "Referer": "https://duckduckgo.com/",
                    })

                    if ddg_is_blocked(html):
                        logger.debug("  DuckDuckGo حظرت الطلب (Iraq) — إعادة محاولة")
                        time.sleep(3 + attempt * 2)
                        continue

                    entries = ddg_extract_results(html)
                    if not entries:
                        time.sleep(1 + attempt)
                        continue

                    for raw_link, title_raw, snippet_raw in entries:
                        link = ddg_clean_link(raw_link)
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)

                        title = re.sub(r'<[^>]+>', '', title_raw).strip()
                        snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
                        title = (title.replace('&amp;', '&')
                                 .replace('&#39;', "'").replace('&quot;', '"'))
                        snippet = (snippet.replace('&amp;', '&')
                                   .replace('&#39;', "'").replace('&quot;', '"'))

                        if not title or len(title) < 3:
                            continue

                        # تصفية: فقط الأخبار التقنية
                        if not is_tech_related(title, snippet):
                            continue

                        community = self._detect_community(title + " " + snippet)

                        stories.append({
                            "title": sanitize_text(title),
                            "url": link,
                            "source": "DuckDuckGo",
                            "published": "",
                            "description": sanitize_text(snippet[:200]),
                            "community": community,
                        })

                        if len(stories) >= MAX_STORIES_PER_SOURCE:
                            break
                    break
                except Exception as e:
                    if attempt < 1:
                        time.sleep(2 + attempt * 2)
                    else:
                        logger.debug(f"  ⚠️ فشل DDG Iraq: {e}")

            if qi < len(DDG_SITE_QUERIES) - 1:
                time.sleep(1)

        return stories

    # ─────────────────────────────────────────────────────────
    # 3. Direct community website scraping
    # ─────────────────────────────────────────────────────────

    def _fetch_community_sites(self) -> list[dict]:
        """Scraping مباشر لمواقع المجتمعات التقنية العراقية."""
        stories = []

        def scrape_site(name: str, url: str) -> list[dict]:
            items = []
            try:
                html = fetch_html(url, headers=BROWSER_HEADERS)
                if not html:
                    return []

                # استخراج الروابط والعناوين من الصفحة
                # نمط 1: روابط مدونة/أخبار
                link_patterns = [
                    r'<a[^>]*href="([^"]*)"[^>]*>([^<]{10,200})</a>',
                    r'<h[1-3][^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                    r'<article[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                ]

                seen = set()
                for pattern in link_patterns:
                    matches = re.findall(pattern, html, re.DOTALL)
                    for link, title in matches:
                        # تحويل الروابط النسبية إلى مطلقة
                        if link.startswith("/"):
                            base = re.match(r'(https?://[^/]+)', url)
                            if base:
                                link = base.group(1) + link
                        elif not link.startswith("http"):
                            continue

                        title_clean = re.sub(r'<[^>]+>', '', title).strip()
                        if (not title_clean or len(title_clean) < 10
                                or link in seen
                                or link == url):
                            continue
                        seen.add(link)

                        # تصفية الروابط غير المهمة
                        skip = ["facebook.com", "twitter.com", "instagram.com",
                                "linkedin.com", "youtube.com", "mailto:",
                                "tel:", "#", "javascript:", "wp-content",
                                "wp-includes", ".css", ".js", ".png", ".jpg"]
                        if any(s in link.lower() for s in skip):
                            continue

                        items.append({
                            "title": sanitize_text(title_clean),
                            "url": link,
                            "source": name,
                            "published": "",
                            "description": "",
                            "community": name,
                        })
                        if len(items) >= 5:
                            break
                    if len(items) >= 5:
                        break

            except Exception as e:
                logger.debug(f"  ⚠️ فشل scraping {name}: {e}")
            return items

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(scrape_site, name, url): name
                for name, url in COMMUNITY_SITES.items()
            }
            for future in as_completed(futures):
                stories.extend(future.result())

        return stories

    # ─────────────────────────────────────────────────────────
    # كشف المجتمع المرتبط
    # ─────────────────────────────────────────────────────────

    def _detect_community(self, text: str) -> str:
        """تحديد أي مجتمع عراقي مرتبط بالنص."""
        text_lower = text.lower()
        for name, info in IRAQ_COMMUNITIES.items():
            for kw in info["keywords"]:
                if kw.lower() in text_lower:
                    return name
        return "Iraq Tech"

    # ─────────────────────────────────────────────────────────
    # fetch الرئيسي
    # ─────────────────────────────────────────────────────────

    def fetch(self) -> list[dict]:
        """جمع أخبار المجتمعات التقنية العراقية من جميع المصادر."""
        logger.info(f"{self.icon} جارٍ جلب أخبار المجتمعات التقنية العراقية...")

        all_stories = []
        seen_urls = set()

        # تشغيل المصادر الثلاثة بالتوازي
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._fetch_google_news): "google_news",
                executor.submit(self._fetch_ddg_searches): "ddg",
                executor.submit(self._fetch_community_sites): "sites",
            }
            for future in as_completed(futures):
                try:
                    source_stories = future.result()
                    for story in source_stories:
                        url = story.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_stories.append(story)
                except Exception as e:
                    logger.warning(f"  ⚠️ فشل مصدر Iraq Tech: {e}")

        # ترتيب: الأخبار ذات التاريخ أولاً
        all_stories.sort(
            key=lambda x: x.get("published", ""),
            reverse=True,
        )

        stories = all_stories[:MAX_STORIES_PER_SOURCE]
        logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name} "
                    f"({len(all_stories)} قبل التصفية)")
        return stories
