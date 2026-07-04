"""
Social Media Adapter — يحوّل الأخبار المجمعة إلى بوستات Telegram وصور بطاقات.
SocialMediaAdapter: converts aggregated news into platform-ready social posts and card images.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from ..core.config import OUTPUT_DIR, logger


class SocialMediaAdapter:
    """تحويل الأخبار إلى بوستات جاهزة للنشر على منصات التواصل الاجتماعي."""

    MAX_POSTS = 5
    MAX_TG_CHARS = 4096
    IMG_WIDTH = 1080

    SOURCE_LABELS = {
        "hacker_news": "Hacker News",
        "github": "GitHub",
        "lobsters": "Lobsters",
        "company_blogs": "Company Blog",
        "cve_security": "CVE Security",
        "stackoverflow": "Stack Overflow",
        "youtube_news": "YouTube",
    }

    SOURCE_ICONS = {
        "hacker_news": "🟧",
        "github": "🐙",
        "lobsters": "🦞",
        "company_blogs": "🏢",
        "cve_security": "🛡️",
        "stackoverflow": "💬",
        "youtube_news": "📺",
    }

    def __init__(self, results: dict[str, list[dict]], stats: dict):
        self.results = results
        self.stats = stats
        self.now = datetime.now()

    def _select_top(self) -> list[dict]:
        """اختيار أهم 5 أخبار من جميع المصادر."""
        candidates = []

        for source_key, stories in self.results.items():
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

                candidates.append({
                    "title": s.get("title", ""),
                    "url": s.get("url", ""),
                    "score": score,
                    "source": self.SOURCE_LABELS.get(source_key, source_key),
                    "source_key": source_key,
                    "description": s.get("description", ""),
                    "cvss": s.get("cvss", 0),
                    "cve_id": s.get("cve_id", ""),
                    "company": s.get("company", ""),
                    "stars": s.get("stars", 0),
                    "language": s.get("language", ""),
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[: self.MAX_POSTS]

    def _format_item(self, item: dict, index: int) -> str:
        """تنسيق خبر واحد بصيغة Telegram."""
        source_key = item["source_key"]

        if source_key == "cve_security":
            cvss = item["cvss"]
            severity = "🔴 حرج" if cvss >= 9.0 else "🟠 عالي"
            return (
                f"🚨 *ثغرة أمنية {severity}*\n\n"
                f"`{item['cve_id']}` — {item['description'][:120]}\n\n"
                f"⚠️ CVSS: *{cvss}*\n"
                f"🔗 [التفاصيل]({item['url']})"
            )

        if source_key == "github":
            stars = item["stars"]
            lang = item["language"]
            return (
                f"🐙 *مشروع رائج على GitHub*\n\n"
                f"[{item['title'][:80]}]({item['url']})\n\n"
                f"⭐ {stars:,} نجمة | 💻 `{lang}`\n"
                f"📋 {item['description'][:120]}"
            )

        if source_key == "company_blogs":
            company = item["company"]
            return (
                f"🏢 *{company} تعلن عن تحديث*\n\n"
                f"[{item['title'][:80]}]({item['url']})\n\n"
                f"📋 {item['description'][:150]}"
            )

        if source_key == "youtube_news":
            return (
                f"📺 *فيديو تقني جديد*\n\n"
                f"[{item['title'][:80]}]({item['url']})\n"
                f"🎬 {item['source']}"
            )

        score_display = int(item["score"])
        return (
            f"📰 *{item['title'][:90]}*\n\n"
            f"📋 {item['description'][:150]}\n\n"
            f"🔗 [اقرأ المزيد]({item['url']})\n"
            f"📊 {item['source']} | ⬆️ {score_display}"
        )

    def generate_telegram(self) -> str:
        """توليد بوست Telegram كامل."""
        top = self._select_top()
        if not top:
            return ""

        date_str = self.now.strftime("%Y-%m-%d")
        day_names = {
            "Monday": "الإثنين", "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء", "Thursday": "الخميس",
            "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد",
        }
        day_ar = day_names.get(self.now.strftime("%A"), self.now.strftime("%A"))

        header = (
            f"🚀 *التقرير التقني اليومي*\n"
            f"📅 {day_ar} — {date_str}\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
        )

        body_parts = []
        for i, item in enumerate(top, 1):
            formatted = self._format_item(item, i)
            body_parts.append(f"{i}️⃣ {formatted}\n\n━━━━━━━━━━━━━━━\n")

        total = sum(
            v for k, v in self.stats.items()
            if k != "_duration" and isinstance(v, int)
        )
        footer = (
            f"\n📊 *ملخص اليوم:* {total} خبر من {len(self.results)} مصدر\n"
            f"🤖 تم التجميع تلقائياً بواسطة Tech News Aggregator"
        )

        post = header + "".join(body_parts) + footer

        if len(post) > self.MAX_TG_CHARS:
            post = post[: self.MAX_TG_CHARS - 50] + "\n\n... (مقتطع)\n" + footer
            logger.warning(
                f"Social: البوست تجاوز {self.MAX_TG_CHARS} حرف — تم اقتطاعه"
            )

        return post

    def _find_edge(self) -> str | None:
        """البحث عن متصفح Edge على النظام."""
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def _build_card_html(self) -> Path:
        """بناء HTML بطاقة أنيقة للتصدير كصورة."""
        top = self._select_top()
        date_str = self.now.strftime("%Y-%m-%d")
        day_names = {
            "Monday": "الإثنين", "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء", "Thursday": "الخميس",
            "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد",
        }
        day_ar = day_names.get(self.now.strftime("%A"), self.now.strftime("%A"))

        items_html = ""
        for i, item in enumerate(top, 1):
            icon = self.SOURCE_ICONS.get(item["source_key"], "📰")
            title = item["title"][:90]
            desc = item["description"][:120] if item["description"] else ""
            source = item["source"]
            score = int(item["score"])

            desc_html = f'<p class="desc">{desc}</p>' if desc else ""

            if item["source_key"] == "cve_security":
                cvss = item["cvss"]
                badge_color = "#e74c3c" if cvss >= 9.0 else "#e67e22"
                items_html += f'''
                <div class="card-item cve">
                    <div class="item-header">
                        <span class="num">{i}</span>
                        <span class="icon">🚨</span>
                        <span class="badge" style="background:{badge_color}">CVSS {cvss}</span>
                    </div>
                    <h3>{title}</h3>
                    {desc_html}
                    <div class="meta">🛡️ {source} · {item['cve_id']}</div>
                </div>'''
            elif item["source_key"] == "github":
                stars = item["stars"]
                lang = item["language"]
                items_html += f'''
                <div class="card-item github">
                    <div class="item-header">
                        <span class="num">{i}</span>
                        <span class="icon">🐙</span>
                        <span class="badge" style="background:#24292e">⭐ {stars:,}</span>
                    </div>
                    <h3>{title}</h3>
                    {desc_html}
                    <div class="meta">💻 {lang} · GitHub Trending</div>
                </div>'''
            elif item["source_key"] == "company_blogs":
                company = item["company"]
                items_html += f'''
                <div class="card-item company">
                    <div class="item-header">
                        <span class="num">{i}</span>
                        <span class="icon">🏢</span>
                        <span class="badge" style="background:#0f3460">{company}</span>
                    </div>
                    <h3>{title}</h3>
                    {desc_html}
                    <div class="meta">📢 {source}</div>
                </div>'''
            else:
                items_html += f'''
                <div class="card-item">
                    <div class="item-header">
                        <span class="num">{i}</span>
                        <span class="icon">{icon}</span>
                        <span class="badge">⬆️ {score}</span>
                    </div>
                    <h3>{title}</h3>
                    {desc_html}
                    <div class="meta">{icon} {source}</div>
                </div>'''

        total = sum(
            v for k, v in self.stats.items()
            if k != "_duration" and isinstance(v, int)
        )

        html = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: {self.IMG_WIDTH}px;
    background: #0f0f1a;
    font-family: "Segoe UI", "Tahoma", "Arial", sans-serif;
    padding: 40px;
    color: #fff;
}}

.container {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 24px;
    padding: 40px;
    border: 1px solid rgba(255,255,255,0.08);
}}

.header {{
    text-align: center;
    margin-bottom: 35px;
    padding-bottom: 25px;
    border-bottom: 2px solid #e94560;
}}

.header h1 {{
    font-size: 32px;
    color: #fff;
    margin-bottom: 8px;
}}

.header .date {{
    font-size: 18px;
    color: #a0a0b0;
}}

.header .stats {{
    font-size: 14px;
    color: #e94560;
    margin-top: 10px;
}}

.card-item {{
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border-right: 4px solid #e94560;
}}

.card-item.cve {{ border-right-color: #e74c3c; }}
.card-item.github {{ border-right-color: #6e5494; }}
.card-item.company {{ border-right-color: #0f3460; }}

.item-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}}

.num {{
    background: #e94560;
    color: #fff;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
}}

.icon {{
    font-size: 22px;
}}

.badge {{
    background: rgba(255,255,255,0.1);
    color: #fff;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    margin-right: auto;
}}

.card-item h3 {{
    font-size: 17px;
    color: #fff;
    line-height: 1.5;
    margin-bottom: 6px;
}}

.desc {{
    font-size: 14px;
    color: #b0b0c0;
    line-height: 1.5;
    margin-bottom: 8px;
}}

.meta {{
    font-size: 13px;
    color: #7878a0;
}}

.footer {{
    text-align: center;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.08);
    font-size: 14px;
    color: #7878a0;
}}

.footer .total {{
    color: #e94560;
    font-weight: bold;
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🚀 التقرير التقني اليومي</h1>
        <div class="date">📅 {day_ar} — {date_str}</div>
        <div class="stats">📌 أهم {len(top)} أخبار · {total} خبر من {len(self.results)} مصدر</div>
    </div>
    {items_html}
    <div class="footer">
        <span class="total">Tech News Aggregator</span> · 🤖 تم التجميع تلقائياً
    </div>
</div>
</body>
</html>'''

        html_path = OUTPUT_DIR / f"social_card_{self.now.strftime('%Y-%m-%d_%H%M')}.html"
        html_path.write_text(html, encoding="utf-8")
        return html_path

    def generate_image(self) -> Path:
        """توليد صورة بطاقة من البوست عبر Edge headless screenshot."""
        logger.info("📱 Social: جارٍ توليد صورة البوست...")

        html_path = self._build_card_html()
        img_filename = f"social_card_{self.now.strftime('%Y-%m-%d_%H%M')}.png"
        img_path = OUTPUT_DIR / img_filename

        try:
            edge = self._find_edge()
            if not edge:
                raise RuntimeError("لم يتم العثور على Edge أو Chrome")

            cmd = [
                edge,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--screenshot={img_path}",
                f"--window-size={self.IMG_WIDTH},1920",
                str(html_path),
            ]
            subprocess.run(cmd, capture_output=True, timeout=60, check=True)

            if not img_path.exists():
                raise RuntimeError("لم يتم إنشاء الصورة")

            logger.info(f"📱 Social: تم حفظ الصورة: {img_path}")
            return img_path
        except Exception as e:
            logger.error(f"📱 Social: فشل إنشاء الصورة: {e}")
            raise
        finally:
            html_path.unlink(missing_ok=True)

    def save(self, platform: str = "telegram", image: bool = False) -> Path:
        """حفظ البوست في ملف نصي و/أو صورة."""
        if image:
            return self.generate_image()

        if platform == "telegram":
            content = self.generate_telegram()
        else:
            raise ValueError(f"منصة غير مدعومة: {platform}")

        if not content:
            logger.warning("Social: لا يوجد محتوى للتصدير")
            return Path()

        filename = (
            f"social_post_{platform}_"
            f"{self.now.strftime('%Y-%m-%d_%H%M')}.txt"
        )
        filepath = OUTPUT_DIR / filename
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"📱 Social: تم حفظ بوست {platform}: {filepath}")
        return filepath
