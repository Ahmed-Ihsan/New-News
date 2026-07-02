"""
المُجمّع الرئيسي — ينسق جميع المصادر ويُدير دورة الجمع.
TechNewsAggregator: orchestrates all sources, filtering, and output.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from .core.config import OUTPUT_DIR, logger
from .report import MarkdownReportGenerator
from .sources import (
    HackerNewsSource,
    RedditSource,
    GitHubTrendingSource,
    DevToSource,
    LobstersSource,
    ProductHuntSource,
    ArxivSource,
    XSource,
    YouTubeSource,
    MediumSource,
    CompanyBlogsSource,
    TechNewsSource,
    GoogleNewsSource,
    IraqTechSource,
)


class TechNewsAggregator:
    """المُجمّع الرئيسي للأخبار التقنية."""

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key.lower() if search_key else None
        self.sources = {
            "hacker_news": HackerNewsSource(),
            "reddit": RedditSource(),
            "github": GitHubTrendingSource(),
            "devto": DevToSource(),
            "lobsters": LobstersSource(),
            "product_hunt": ProductHuntSource(),
            "arxiv": ArxivSource(),
            "x": XSource(search_key=self.search_key),
            "youtube": YouTubeSource(),
            "medium": MediumSource(),
            "company_blogs": CompanyBlogsSource(),
            "tech_news": TechNewsSource(),
            "google_news": GoogleNewsSource(search_key=self.search_key),
            "iraq_tech": IraqTechSource(search_key=self.search_key),
        }
        self.results: dict[str, list[dict]] = {}
        self.stats: dict[str, int] = {}

    def collect_all(self) -> None:
        """جمع الأخبار من جميع المصادر."""
        logger.info("=" * 60)
        logger.info("🚀 بدء تجميع الأخبار التقنية...")
        logger.info("=" * 60)

        start_time = time.time()

        for key, source in self.sources.items():
            try:
                self.results[key] = source.fetch()
                self.stats[key] = len(self.results[key])
            except Exception as e:
                logger.error(f"❌ خطأ في مصدر {source.name}: {e}")
                self.results[key] = []
                self.stats[key] = 0

        # === إضافة التصفية (Filtering) هنا ===
        if self.search_key:
            logger.info(f"🔍 جاري تصفية النتائج للبحث عن: '{self.search_key}'")
            for key in self.results:
                filtered_stories = []
                for story in self.results[key]:
                    content_to_search = str(story.get('title', '')) + " " + \
                                        str(story.get('description', '')) + " " + \
                                        str(story.get('tags', '')) + " " + \
                                        str(story.get('tagline', ''))

                    if self.search_key in content_to_search.lower():
                        filtered_stories.append(story)

                self.results[key] = filtered_stories
                self.stats[key] = len(filtered_stories)

        duration = time.time() - start_time
        self.stats["_duration"] = duration

        total = sum(v for k, v in self.stats.items() if k != "_duration")
        logger.info("=" * 60)
        logger.info(f"✅ اكتمل التجميع: {total} خبر في {duration:.1f} ثانية")
        logger.info("=" * 60)

    def generate_report(self) -> Path:
        """إنشاء تقرير Markdown."""
        report = MarkdownReportGenerator(search_key=self.search_key)

        report.add_header()
        report.add_hacker_news(self.results.get("hacker_news", []))
        report.add_reddit(self.results.get("reddit", []))
        report.add_github_trending(self.results.get("github", []))
        report.add_devto(self.results.get("devto", []))
        report.add_lobsters(self.results.get("lobsters", []))
        report.add_product_hunt(self.results.get("product_hunt", []))
        report.add_arxiv(self.results.get("arxiv", []))
        report.add_x(self.results.get("x", []))
        report.add_youtube(self.results.get("youtube", []))
        report.add_medium(self.results.get("medium", []))
        report.add_company_blogs(self.results.get("company_blogs", []))
        report.add_tech_news(self.results.get("tech_news", []))
        report.add_google_news(self.results.get("google_news", []))
        report.add_iraq_tech(self.results.get("iraq_tech", []))
        report.add_footer(self.stats)

        filepath = report.save()
        logger.info(f"📄 تم حفظ التقرير: {filepath}")
        return filepath

    def save_raw_json(self) -> Path:
        """حفظ البيانات الخام في ملف JSON."""
        filename = f"tech_news_raw_{datetime.now().strftime('%Y-%m-%d_%H%M')}.json"
        filepath = OUTPUT_DIR / filename

        export_data = {
            "generated_at": datetime.now().isoformat(),
            "stats": {k: v for k, v in self.stats.items() if k != "_duration"},
            "sources": self.results,
        }

        filepath.write_text(
            json.dumps(export_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        logger.info(f"📦 تم حفظ البيانات الخام: {filepath}")
        return filepath
