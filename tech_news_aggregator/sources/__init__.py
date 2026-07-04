"""
حزمة مصادر الأخبار — كل مصدر في ملف مستقل.
Sources package: each news source is a separate adapter module.

المصادر المتاحة:
    HackerNewsSource, GitHubTrendingSource,
    LobstersSource, CompanyBlogsSource,
    CVESecuritySource, StackOverflowSource,
    YouTubeNewsSource
"""

from .hacker_news import HackerNewsSource
from .github_trending import GitHubTrendingSource
from .lobsters import LobstersSource
from .company_blogs import CompanyBlogsSource
from .cve_security import CVESecuritySource
from .stackoverflow import StackOverflowSource
from .youtube_news import YouTubeNewsSource

__all__ = [
    "HackerNewsSource",
    "GitHubTrendingSource",
    "LobstersSource",
    "CompanyBlogsSource",
    "CVESecuritySource",
    "StackOverflowSource",
    "YouTubeNewsSource",
]
