"""
الإعدادات العامة للمُجمّع
Central configuration for the Tech News Aggregator.
"""

import logging
import os
import ssl
import sys
import io
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# إصلاح ترميز Windows
# ─────────────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────
# إعداد التسجيل (Logging)
# ─────────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "aggregator.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("TechNewsAggregator")

# ─────────────────────────────────────────────────────────────
# الإعدادات العامة
# ─────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent.parent.parent / "news_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# عدد الأخبار من كل مصدر
MAX_STORIES_PER_SOURCE = 10

# مهلة الاتصال (ثواني)
REQUEST_TIMEOUT = 15

# رؤوس HTTP المشتركة
HEADERS = {
    "User-Agent": "TechNewsAggregator/2.0 (Educational Bot)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

# إنشاء SSL context (لحل مشكلة الشهادات على بعض الأنظمة مثل MSYS2)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# كلمات مفتاحية للكشف عن إطلاقات الأدوات والتحديثات
TOOL_LAUNCH_KEYWORDS = [
    "launch", "announc", "introduc", "unveil", "release",
    "new tool", "new feature", "now available", "rolling out",
    "debut", "open source", "preview", "beta", "generally available",
    "updates", "upgrades", "new model", "new api", "new platform",
]

# ─────────────────────────────────────────────────────────────
# معايير الفلترة الصارمة
# ─────────────────────────────────────────────────────────────

# الحد الأدنى لنقاط Hacker News
MIN_HN_SCORE = 50

# الحد الأدنى لنقاط Lobsters
MIN_LOBSTERS_SCORE = 5

# أقصى عمر خبر (أيام)
MAX_NEWS_AGE_DAYS = 14

# مشاريع GitHub مستثناة (تظهر كل يوم، ليست "جديدة")
EXCLUDED_REPOS = {
    "sindresorhus/awesome",
    "freeCodeCamp/freeCodeCamp",
    "public-apis/public-apis",
    "EbookFoundation/free-programming-books",
    "awesome-selfhosted/awesome-selfhosted",
    "vinta/awesome-python",
    "kamranahmedse/developer-roadmap",
}
