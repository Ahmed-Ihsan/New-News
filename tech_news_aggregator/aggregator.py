"""
المُجمّع الرئيسي — ينسق جميع المصادر ويُدير دورة الجمع.
TechNewsAggregator: orchestrates all sources, filtering, and output.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from .core.config import OUTPUT_DIR, logger
from .report import MarkdownReportGenerator, export_to_pdf, SocialMediaAdapter
from .sources import (
    HackerNewsSource,
    GitHubTrendingSource,
    LobstersSource,
    CompanyBlogsSource,
    CVESecuritySource,
    StackOverflowSource,
    YouTubeNewsSource,
    XSource,
)


class TechNewsAggregator:
    """المُجمّع الرئيسي للأخبار التقنية."""

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key.lower() if search_key else None
        self.sources = {
            "hacker_news": HackerNewsSource(),
            "github": GitHubTrendingSource(),
            "lobsters": LobstersSource(),
            "company_blogs": CompanyBlogsSource(),
            "cve_security": CVESecuritySource(),
            "stackoverflow": StackOverflowSource(),
            "youtube_news": YouTubeNewsSource(),
            "x": XSource(search_key=search_key),
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

        self._deduplicate()

        duration = time.time() - start_time
        self.stats["_duration"] = duration

        total = sum(v for k, v in self.stats.items() if k != "_duration")
        logger.info("=" * 60)
        logger.info(f"✅ اكتمل التجميع: {total} خبر في {duration:.1f} ثانية")
        logger.info("=" * 60)

    def _deduplicate(self) -> None:
        """إزالة الأخبار المكررة عبر المصادر."""
        from .core.utils import normalize_title
        seen: set[str] = set()
        for key in self.results:
            filtered = []
            for story in self.results[key]:
                norm = normalize_title(story.get("title", ""))
                if norm and norm not in seen:
                    seen.add(norm)
                    filtered.append(story)
            self.results[key] = filtered
            self.stats[key] = len(filtered)

    def generate_report(self) -> Path:
        """إنشاء تقرير Markdown."""
        report = MarkdownReportGenerator(search_key=self.search_key)

        report.add_header()
        report.add_top_stories(self.results)
        report.add_hacker_news(self.results.get("hacker_news", []))
        report.add_github_trending(self.results.get("github", []))
        report.add_lobsters(self.results.get("lobsters", []))
        report.add_company_blogs(self.results.get("company_blogs", []))
        report.add_cve_security(self.results.get("cve_security", []))
        report.add_stackoverflow(self.results.get("stackoverflow", []))
        report.add_youtube_news(self.results.get("youtube_news", []))
        report.add_x(self.results.get("x", []))
        report.add_footer(self.stats)

        filepath = report.save()
        logger.info(f"📄 تم حفظ التقرير: {filepath}")
        return filepath

    def export_pdf(self, md_path: Path) -> Path:
        """تصدير التقرير إلى PDF."""
        return export_to_pdf(md_path)

    def export_social(self, platform: str = "telegram", image: bool = False) -> Path:
        """تصدير البوست الاجتماعي."""
        adapter = SocialMediaAdapter(self.results, self.stats)
        return adapter.save(platform, image=image)

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
