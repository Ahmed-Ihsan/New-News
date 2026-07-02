#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           🚀 مُجمّع الأخبار التقنية اليومي 🚀                ║
║   Tech News Aggregator - Daily Automated News Collector      ║
║                                                              ║
║   تم إعادة الهيكلة إلى حزمة احترافية (adapter pattern)       ║
║   هذا الملف نقطة دخول متوافقة مع الإصدار السابق             ║
║                                                              ║
║   الاستخدام الجديد:                                          ║
║     python -m tech_news_aggregator                           ║
║     python -m tech_news_aggregator --search AI               ║
║                                                              ║
║   الاستخدام القديم (ما زال يعمل):                            ║
║     python tech_news_aggregator.py                           ║
║     python tech_news_aggregator.py --search AI               ║
╚══════════════════════════════════════════════════════════════╝

المؤلف: Tech News Bot
الإصدار: 2.0 (refactored to package)
التاريخ: 2026-07-02
"""

# هذا الملف مجرد نقطة دخول — كل المنطق في الحزمة tech_news_aggregator/
from tech_news_aggregator.__main__ import main

if __name__ == "__main__":
    main()
