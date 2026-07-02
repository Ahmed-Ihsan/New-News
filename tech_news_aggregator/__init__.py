"""
مُجمّع الأخبار التقنية — حزمة Python احترافية.
Tech News Aggregator — professional Python package.

الاستخدام:
    python -m tech_news_aggregator
    python -m tech_news_aggregator --search AI
"""

from .aggregator import TechNewsAggregator
from .core import NewsSource

__all__ = ["TechNewsAggregator", "NewsSource"]
__version__ = "2.0"
