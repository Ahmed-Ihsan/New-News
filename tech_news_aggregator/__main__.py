"""
نقطة الدخول — تشغيل المُجمّع من سطر الأوامر.
Entry point: python -m tech_news_aggregator
"""

import argparse

from .aggregator import TechNewsAggregator


def main():
    """الدالة الرئيسية."""
    parser = argparse.ArgumentParser(description="مُجمّع الأخبار التقنية")
    parser.add_argument("--search", "-s", type=str, default=None,
                        help="كلمة مفتاحية للبحث في الأخبار")
    parser.add_argument("--tui", action="store_true",
                        help="تشغيل واجهة المستخدم الطرفية (TUI)")
    args = parser.parse_args()

    # وضع TUI
    if args.tui:
        from .tui import TechNewsApp
        app = TechNewsApp(search_key=args.search)
        app.run()
        return

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          🚀 مُجمّع الأخبار التقنية اليومي 🚀           ║
    ║          Tech News Daily Aggregator v2.0                ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📡 المصادر:                                            ║
    ║    🟧 Hacker News    🟠 Reddit      🐙 GitHub           ║
    ║    👩‍💻 Dev.to         🦞 Lobsters    🐱 Product Hunt     ║
    ║    🔬 arXiv          🐦 X (Twitter)  📺 YouTube          ║
    ║    ✍️ Medium          🏢 Company Blogs  📰 Tech News      ║
    ║    🌐 Google News    🇮🇶 Iraq Tech                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    aggregator = TechNewsAggregator(search_key=args.search)

    # جمع الأخبار
    aggregator.collect_all()

    # إنشاء التقرير
    md_path = aggregator.generate_report()
    json_path = aggregator.save_raw_json()

    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✅ اكتمل التجميع بنجاح!                               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📄 تقرير Markdown: {str(md_path):<37s} ║
    ║  📦 بيانات JSON:    {str(json_path):<37s} ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    return md_path


if __name__ == "__main__":
    main()
