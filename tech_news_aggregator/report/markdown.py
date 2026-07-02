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
> Hacker News • Reddit • GitHub • Dev.to • Lobsters • Product Hunt • arXiv • X • YouTube • Medium
> 🏢 Company Blogs • 📰 TechCrunch/Verge/ArsTechnica • 🌐 Google News — تتبع إطلاقات الأدوات

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

    def add_reddit(self, stories: list[dict]) -> None:
        """قسم Reddit."""
        if not stories:
            return

        section = """
## 🟠 Reddit - أبرز المنشورات التقنية

> من أكبر مجتمعات التقنية على الإنترنت

| # | العنوان | المجتمع |
|---|---------|---------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:80]}{'...' if len(s['title']) > 80 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s['subreddit']}` |\n"

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

    def add_devto(self, stories: list[dict]) -> None:
        """قسم Dev.to."""
        if not stories:
            return

        section = """
## 👩‍💻 Dev.to - أفضل المقالات

> مقالات من مجتمع المطورين العالمي

"""
        for i, s in enumerate(stories, 1):
            tags = " ".join([f"`#{t}`" for t in s.get("tags", [])])
            section += f"""**{i}. [{s['title']}]({s['url']})**
- ✍️ {s['author']} | ❤️ {s['reactions']} | 💬 {s['comments']} | ⏱️ {s['reading_time']} دقائق قراءة
- {tags}
- {s.get('description', '')}

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

    def add_product_hunt(self, stories: list[dict]) -> None:
        """قسم Product Hunt."""
        if not stories:
            return

        section = """
## 🐱 Product Hunt - أحدث المنتجات

> اكتشف أحدث المنتجات والأدوات التقنية

"""
        for i, s in enumerate(stories, 1):
            section += f"**{i}. [{s['title']}]({s['url']})** — {s.get('tagline', '')}\n\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_arxiv(self, stories: list[dict]) -> None:
        """قسم arXiv للأبحاث."""
        if not stories:
            return

        section = """
## 🔬 arXiv - أحدث الأبحاث العلمية 

> أبحاث وأوراق علمية حديثة في علوم الحاسب والذكاء الاصطناعي

"""
        for i, s in enumerate(stories, 1):
            section += f"**{i}. [{s['title']}]({s['url']})**\n> 📄 *{s['description']}*\n\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_x(self, stories: list[dict]) -> None:
        """قسم X (Twitter)."""
        if not stories:
            return

        section = """
## 🐦 X (Twitter) - منشورات مُكتشفة

> منشورات من X تم العثور عليها عبر DuckDuckGo (site:x.com)

| # | العنوان | 👤 الحساب |
|---|---------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:75]}{'...' if len(s['title']) > 75 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('author', 'مجهول')}` |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_youtube(self, stories: list[dict]) -> None:
        """قسم YouTube."""
        if not stories:
            return

        section = """
## 📺 YouTube - أحدث الفيديوهات التقنية

> أحدث الفيديوهات من قنوات تقنية و AI مختارة

| # | العنوان | 🎥 القناة | 📅 التاريخ |
|---|---------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('channel', '')}` | {s.get('published', '')} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_medium(self, stories: list[dict]) -> None:
        """قسم Medium."""
        if not stories:
            return

        section = """
## ✍️ Medium - مقالات مختارة

> مقالات من Medium عبر وسوم: technology, programming, AI, startup

"""
        for i, s in enumerate(stories, 1):
            cats = " ".join([f"`#{c}`" for c in s.get("categories", [])[:3]])
            section += f"""**{i}. [{s['title']}]({s['url']})**
- ✍️ {s.get('author', 'مجهول')} | 🏷️ `{s.get('tag', '')}` | 📅 {s.get('published', '')}
- {cats}

"""

        section += "\n---\n"
        self.sections.append(section)

    def add_company_blogs(self, stories: list[dict]) -> None:
        """قسم إعلانات الشركات الرسمية."""
        if not stories:
            return

        section = """
## 🏢 إعلانات الشركات - أحدث الأدوات والتحديثات

> إعلانات رسمية من مدونات: Google, OpenAI, Meta, NVIDIA, Microsoft, AWS, GitHub, DeepMind

| # | العنوان | 🏢 الشركة | 📅 التاريخ |
|---|---------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('company', '')}` | {s.get('published', '')[:16]} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_tech_news(self, stories: list[dict]) -> None:
        """قسم المواقع التقنية."""
        if not stories:
            return

        section = """
## 📰 مواقع تقنية - إطلاقات الأدوات

> من TechCrunch, The Verge, Ars Technica, VentureBeat — تغطية إطلاقات الأدوات

| # | العنوان | 📡 المصدر | 📅 التاريخ |
|---|---------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('site', '')}` | {s.get('published', '')[:16]} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_google_news(self, stories: list[dict]) -> None:
        """قسم Google News."""
        if not stories:
            return

        section = """
## 🌐 Google News - أحدث إطلاقات الأدوات التقنية

> أخبار من Google News عن إطلاقات أدوات وتحديثات من أي شركة (حتى الجديدة)

| # | العنوان | 📡 المصدر | 📅 التاريخ |
|---|---------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:70]}{'...' if len(s['title']) > 70 else ''}]({s['url']})"
            section += f"| {i} | {title_link} | `{s.get('source', '')}` | {s.get('published', '')[:16]} |\n"

        section += "\n---\n"
        self.sections.append(section)

    def add_iraq_tech(self, stories: list[dict]) -> None:
        """قسم المجتمعات التقنية العراقية."""
        if not stories:
            return

        section = """
## 🇮🇶 المجتمعات التقنية العراقية - أخبار وفعاليات

> أخبار من مجتمعات التقنية العراقية: Re:Coded, Five One Labs, Baghdad/Erbil/Mosul/Basra Tech
> مصادر: Google News + DuckDuckGo + scraping مباشر

| # | العنوان | 🏢 المجتمع | 📡 المصدر | 📅 التاريخ |
|---|---------|-----------|-----------|-----------|
"""
        for i, s in enumerate(stories, 1):
            title_link = f"[{s['title'][:65]}{'...' if len(s['title']) > 65 else ''}]({s['url']})"
            section += (f"| {i} | {title_link} | "
                        f"`{s.get('community', 'Iraq Tech')}` | "
                        f"`{s.get('source', '')}` | "
                        f"{s.get('published', '')[:16]} |\n")

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
| 🟠 Reddit | {stats.get('reddit', 0)} | {'✅' if stats.get('reddit', 0) > 0 else '❌'} |
| 🐙 GitHub Trending | {stats.get('github', 0)} | {'✅' if stats.get('github', 0) > 0 else '❌'} |
| 👩‍💻 Dev.to | {stats.get('devto', 0)} | {'✅' if stats.get('devto', 0) > 0 else '❌'} |
| 🦞 Lobsters | {stats.get('lobsters', 0)} | {'✅' if stats.get('lobsters', 0) > 0 else '❌'} |
| 🐱 Product Hunt | {stats.get('product_hunt', 0)} | {'✅' if stats.get('product_hunt', 0) > 0 else '❌'} |
| 🔬 arXiv | {stats.get('arxiv', 0)} | {'✅' if stats.get('arxiv', 0) > 0 else '❌'} |
| 🐦 X (Twitter) | {stats.get('x', 0)} | {'✅' if stats.get('x', 0) > 0 else '❌'} |
| 📺 YouTube | {stats.get('youtube', 0)} | {'✅' if stats.get('youtube', 0) > 0 else '❌'} |
| ✍️ Medium | {stats.get('medium', 0)} | {'✅' if stats.get('medium', 0) > 0 else '❌'} |
| 🏢 Company Blogs | {stats.get('company_blogs', 0)} | {'✅' if stats.get('company_blogs', 0) > 0 else '❌'} |
| 📰 Tech News Sites | {stats.get('tech_news', 0)} | {'✅' if stats.get('tech_news', 0) > 0 else '❌'} |
| 🌐 Google News | {stats.get('google_news', 0)} | {'✅' if stats.get('google_news', 0) > 0 else '❌'} |
| 🇮🇶 Iraq Tech | {stats.get('iraq_tech', 0)} | {'✅' if stats.get('iraq_tech', 0) > 0 else '❌'} |
| **الإجمالي** | **{total}** | ⏱️ {duration:.1f}s |

---

> 🤖 تم إنشاء هذا التقرير تلقائياً بواسطة **مُجمّع الأخبار التقنية v2.0**
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
