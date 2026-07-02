"""
حزمة مصادر الأخبار — كل مصدر في ملف مستقل.
Sources package: each news source is a separate adapter module.

المصادر المتاحة:
    HackerNewsSource, RedditSource, GitHubTrendingSource,
    DevToSource, LobstersSource, ProductHuntSource,
    ArxivSource, XSource, YouTubeSource, MediumSource,
    CompanyBlogsSource, TechNewsSource, GoogleNewsSource
"""

from .hacker_news import HackerNewsSource
from .reddit import RedditSource
from .github_trending import GitHubTrendingSource
from .devto import DevToSource
from .lobsters import LobstersSource
from .product_hunt import ProductHuntSource
from .arxiv import ArxivSource
from .x_twitter import XSource
from .youtube import YouTubeSource
from .medium import MediumSource
from .company_blogs import CompanyBlogsSource
from .tech_news_sites import TechNewsSource
from .google_news import GoogleNewsSource
from .iraq_tech import IraqTechSource

__all__ = [
    "HackerNewsSource",
    "RedditSource",
    "GitHubTrendingSource",
    "DevToSource",
    "LobstersSource",
    "ProductHuntSource",
    "ArxivSource",
    "XSource",
    "YouTubeSource",
    "MediumSource",
    "CompanyBlogsSource",
    "TechNewsSource",
    "GoogleNewsSource",
    "IraqTechSource",
]
