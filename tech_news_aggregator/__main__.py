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
    parser.add_argument("--gui", action="store_true",
                        help="تشغيل واجهة سطح المكتب (GUI)")
    parser.add_argument("--pdf", action="store_true",
                        help="تصدير التقرير إلى PDF")
    parser.add_argument("--post", action="store_true",
                        help="توليد بوست Telegram من الأخبار")
    parser.add_argument("--image", action="store_true",
                        help="توليد صورة بطاقة للبوست (بدلاً من نص)")
    args = parser.parse_args()

    # وضع GUI
    if args.gui:
        from .gui import TechNewsGUI
        app = TechNewsGUI(search_key=args.search)
        app.mainloop()
        return

    # وضع TUI
    if args.tui:
        from .tui import TechNewsApp
        app = TechNewsApp(search_key=args.search)
        app.run()
        return

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          🚀 مُجمّع الأخبار التقنية اليومي 🚀           ║
    ║          Tech News Daily Aggregator v3.0                ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📡 المصادر:                                            ║
    ║    🟧 Hacker News     GitHub       🦞 Lobsters         ║
    ║    🏢 Company Blogs  �️ CVE Security  💬 Stack Overflow   ║
    ║    📺 YouTube News   🐦 X (Twitter)                       ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    aggregator = TechNewsAggregator(search_key=args.search)

    # جمع الأخبار
    aggregator.collect_all()

    # إنشاء التقرير
    md_path = aggregator.generate_report()
    json_path = aggregator.save_raw_json()

    pdf_line = ""
    if args.pdf:
        try:
            pdf_path = aggregator.export_pdf(md_path)
            pdf_line = f"║  📕 تقرير PDF:      {str(pdf_path):<37s} ║\n"
        except Exception as e:
            print(f"  ⚠️ تعذر إنشاء PDF: {e}")

    post_line = ""
    if args.post:
        try:
            post_path = aggregator.export_social("telegram", image=args.image)
            label = "📸 صورة بطاقة" if args.image else "📱 بوست Telegram"
            post_line = f"║  {label}: {str(post_path):<37s} ║\n"
        except Exception as e:
            print(f"  ⚠️ تعذر إنشاء البوست: {e}")

    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✅ اكتمل التجميع بنجاح!                               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📄 تقرير Markdown: {str(md_path):<37s} ║
    ║  📦 بيانات JSON:    {str(json_path):<37s} ║
{pdf_line}{post_line}    ╚══════════════════════════════════════════════════════════╝
    """)

    return md_path


if __name__ == "__main__":
    main()
