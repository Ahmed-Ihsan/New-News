"""
مُولّد تقرير Markdown.
Markdown report generator — renders collected news into a formatted .md file.
"""

from datetime import datetime
from pathlib import Path

from ..core.config import OUTPUT_DIR


class MarkdownReportGenerator:
    """إنشاء تقرير Markdown منسّق وجميل."""

    def __init__(self, search_key: str | None = None):
        self.now = datetime.now()
        self.search_key = search_key
        self.sections: list[str] = []

    def add_top_stories(self, all_results: dict[str, list[dict]]) -> None:
        """قسم أهم الأخبار — يختار أفضل 5 من جميع المصادر."""
        candidates = []

        for source_key, stories in all_results.items():
            for s in stories:
                score = 0
                if source_key == "hacker_news":
                    score = s.get("score", 0)
                elif source_key == "lobsters":
                    score = s.get("score", 0) * 3
                elif source_key == "github":
                    score = min(s.get("stars", 0) / 1000, 200)
                elif source_key == "cve_security":
                    score = s.get("cvss", 0) * 20
                elif source_key == "company_blogs":
                    score = 80
                elif source_key == "youtube_news":
                    score = 60
                elif source_key == "stackoverflow":
                    score = 40

                badge = ""
                if score >= 200 or (source_key == "cve_security" and s.get("cvss", 0) >= 9.0):
                    badge = "🔴"
                elif score >= 100:
                    badge = "🟠"
                else:
                    badge = "🟢"

                source_label = {
                    "hacker_news": "HN", "github": "GitHub",
                    "lobsters": "Lobsters", "company_blogs": "CoBlog",
                    "cve_security": "CVE", "stackoverflow": "SO",
                    "youtube_news": "YouTube",
                }.get(source_key, source_key)

                candidates.append({
                    "title": s.get("title", ""),
                    "url": s.get("url", ""),
                    "score": score,
                    "badge": badge,
                    "source": source_label,
                    "description": s.get("description", ""),
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        top = candidates[:5]

        if not top:
            return

        section = """
## 📌 Top Stories - أهم 5 أخبار اليوم

> أهم الأخبار من جميع المصادر — اقرأها أولاً

"""
        for i, s in enumerate(top, 1):
            desc = f"\n> {s['description'][:100]}..." if s["description"] else ""
            section += f"""### {i}. {s['badge']} [{s['title'][:80]}]({s['url']})
{desc}

`{s['source']}` | ⬆️ {int(s['score'])} نقطة

"""

        section += "\n---\n"
        self.sections.append(section)

    def add_header(self) -> None:
        """إضافة رأس التقرير."""
        date_str = self.now.strftime("%Y-%m-%d")
        time_str = self.now.strftime("%H:%M")
        day_names = {
            "Monday": "الإثنين", "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء", "Thursday": "الخميس",
            "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
        }
        day_en = self.now.strftime("%A")
        day_ar = day_names.get(day_en, day_en)

        search_text = f"\n\n### 🔍 نتائج البحث عن: `{self.search_key}`" if self.search_key else ""

        self.sections.append(f"""<div align="center">

# 🚀 التقرير اليومي للأخبار التقنية

### 📅 {day_ar} - {date_str} | ⏰ {time_str}{search_text}

---

> **مُجمّع تلقائي** من أفضل المصادر التقنية العالمية
> Hacker News • GitHub • Lobsters • Company Blogs • CVE Security • Stack Overflow • YouTube
> 🏢 Company Blogs (22 شركة) — تتبع إطلاقات الأدوات والتحديثات الرسمية (آخر 14 يوم)

---

</div>
""")

    def add_hacker_news(self, stories: list[dict]) -> None:
        """قسم Hacker News."""
        if not stories:
            return

        section = """
## 🟧 Hacker News - أهم الأخبار

> المصدر الأول للأخبار التقنية في وادي السيليكون

| # | العنوان | ⬆️ النقاط | 💬 التعليقات | ⏱️ الوقت |
|---|---------|-----------|-------------|----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title']}]({s['url']})"
            hn_link = f"[💬]({s['hn_link']})"
            section += f"| {i} | {title_link} | **{s['score']:,}** | {hn_link} {s['comments']:,} | {s['time_ago']} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_github_trending(self, stories: list[dict]) -> None:
        """قسم GitHub Trending."""
        if not stories:
            return

        section = """
## 🐙 GitHub - المشاريع الرائجة

> أكثر المشاريع مفتوحة المصدر رواجاً اليوم

"""
        for i, s in enumerate(stories, 1):
            topics = " ".join([f"`{t}`" for t in s.get("topics", [])[:3]])
            section += f"""### {i}. [{s['title']}]({s['url']})

> {s['description']}

⭐ **{s['stars']:,}** نجمة | 🍴 {s['forks']:,} fork | 💻 `{s['language']}` {topics}

"""

        section += "\n---\n"
        self.sections.append(section)

    def add_lobsters(self, stories: list[dict]) -> None:
        """قسم Lobsters."""
        if not stories:
            return

        section = """
## 🦞 Lobsters - أخبار تقنية عميقة

> محتوى تقني مُركّز وعالي الجودة

| # | العنوان | 🏷️ الوسوم | ⬆️ | 💬 |
|---|---------|-----------|-----|-----|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            tags = ", ".join([f"`{t}`" for t in s.get("tags", [])[:3]])
            comments_link = f"[{s['comments']}]({s['comments_url']})" if s.get("comments_url") else str(s["comments"])
            section += f"| {i} | {title_link} | {tags} | **{s['score']}** | {comments_link} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_company_blogs(self, stories: list[dict]) -> None:
        """قسم إعلانات الشركات الرسمية."""
        if not stories:
            return

        section = """
## 🏢 إعلانات الشركات - أحدث الأدوات والتحديثات

> إعلانات رسمية من 22 شركة: OpenAI, Google DeepMind, Google, NVIDIA, Microsoft, AWS, Cloudflare, GitHub, Apple, Netflix, Stripe, Docker, Kubernetes, Rust, Python, Node.js, JetBrains, PostgreSQL, HashiCorp, Meta, Google Security, GitHub Engineering

| # | العنوان | 🏢 الشركة | 📅 التاريخ |
|---|---------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('company', '')}` | {s.get('published', '')[:16]} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_cve_security(self, stories: list[dict]) -> None:
        """قسم ثغرات CVE الأمنية."""
        if not stories:
            return

        section = """
## �️ ثغرات أمنية حرجة - CVE

> ثغرات من NVD بـ CVSS >= 7.0 — قد تتطلب ترقية فورية

| # | العنوان | ⚠️ CVSS | 📅 التاريخ |
|---|---------|---------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:65]}{'...' if len(s['title']) > 65 else ''}]({s['url']})"
            cvss = s.get("cvss", 0.0)
            cvss_emoji = "🔴" if cvss >= 9.0 else "�" if cvss >= 7.0 else "🟡"
            section += f"| {i} | {title_link} | {cvss_emoji} **{cvss}** | {s.get('published', '')[:16]} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_stackoverflow(self, stories: list[dict]) -> None:
        """قسم مدونة Stack Overflow."""
        if not stories:
            return

        section = """
## 💬 Stack Overflow Blog - اتجاهات المطورين

> مقالات واتجاهات من أكبر مجتمع مطورين في العالم

"""
        for i, s in enumerate(stories, 1):
            cats = " ".join([f"`#{c}`" for c in s.get("categories", [])[:3]])
            section += f"""**{i}. [{s['title']}]({s['url']})**
- ✍️ {s.get('author', 'مجهول')} | 📅 {s.get('published', '')[:16]}
- {cats}

"""

        section += "\n---\n"
        self.sections.append(section)

    def add_youtube_news(self, stories: list[dict]) -> None:
        """قسم مقاطع يوتيوب الإخبارية."""
        if not stories:
            return

        section = """
## 📺 Tech Video Highlights - مقاطع إخبارية

> من قنوات مختارة: Fireship, TechLinked, AI Explained, Matthew Berman
> فلترة: عناوين إخبارية فقط (لا ترفيه، لا آراء، لا clickbait)

| # | العنوان | 🎥 القناة | 📅 التاريخ |
|---|---------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('channel', '')}` | {s.get('published', '')[:10]} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_footer(self, stats: dict) -> None:
        """إضافة تذييل التقرير."""
        total = sum(v for k, v in stats.items() if k != "_duration" and isinstance(v, int))
        duration = stats.get("_duration", 0)

        self.sections.append(f"""
<div align="center">

## 📊 إحصائيات التقرير

| المصدر | عدد الأخبار | الحالة |
|--------|-------------|--------|
| 🟧 Hacker News | {stats.get('hacker_news', 0)} | {'✅' if stats.get('hacker_news', 0) > 0 else '❌'} |
|  GitHub Trending | {stats.get('github', 0)} | {'✅' if stats.get('github', 0) > 0 else '❌'} |
| 🦞 Lobsters | {stats.get('lobsters', 0)} | {'✅' if stats.get('lobsters', 0) > 0 else '❌'} |
| 🏢 Company Blogs | {stats.get('company_blogs', 0)} | {'✅' if stats.get('company_blogs', 0) > 0 else '❌'} |
| �️ CVE Security | {stats.get('cve_security', 0)} | {'✅' if stats.get('cve_security', 0) > 0 else '❌'} |
| 💬 Stack Overflow | {stats.get('stackoverflow', 0)} | {'✅' if stats.get('stackoverflow', 0) > 0 else '❌'} |
| 📺 YouTube News | {stats.get('youtube_news', 0)} | {'✅' if stats.get('youtube_news', 0) > 0 else '❌'} |
| **الإجمالي** | **{total}** | ⏱️ {duration:.1f}s |

---

> 🤖 تم إنشاء هذا التقرير تلقائياً بواسطة **مُجمّع الأخبار التقنية v3.0**
>
> 📧 للمساهمة أو الإبلاغ عن مشاكل: [GitHub Issues](https://github.com)
>
> ⏰ آخر تحديث: {self.now.strftime('%Y-%m-%d %H:%M:%S')}

</div>
""")

    def generate(self) -> str:
        """إنشاء التقرير النهائي."""
        return "\n".join(self.sections)

    def save(self, filename: str | None = None) -> Path:
        """حفظ التقرير في ملف."""
        if not filename:
            filename = f"tech_news_{self.now.strftime('%Y-%m-%d_%H%M')}.md"

        filepath = OUTPUT_DIR / filename
        filepath.write_text(self.generate(), encoding="utf-8")
        return filepath
