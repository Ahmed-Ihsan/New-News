from ..core import NewsSource, fetch_json, logger, MAX_STORIES_PER_SOURCE, sanitize_text, EXCLUDED_REPOS


class GitHubTrendingSource(NewsSource):
    name = "GitHub Trending"
    icon = "🐙"
    API_URL = "https://api.github.com/search/repositories"
    MAX_STORIES = 5

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            url = (
                f"{self.API_URL}?q=stars:>50+pushed:>2026-06-28"
                f"&sort=stars&order=desc&per_page={MAX_STORIES_PER_SOURCE}"
            )
            headers = {"Accept": "application/vnd.github.v3+json"}
            data = fetch_json(url, headers=headers)
            if not data or "items" not in data:
                logger.warning(f"  ⚠️ لا توجد نتائج من {self.name}")
                return stories
            for repo in data["items"][:MAX_STORIES_PER_SOURCE * 3]:
                try:
                    full_name = repo.get("full_name", "")
                    if full_name in EXCLUDED_REPOS:
                        continue
                    description = repo.get("description") or ""
                    topics = repo.get("topics", []) or []
                    stories.append({
                        "title": sanitize_text(repo.get("full_name", "بدون اسم")),
                        "description": sanitize_text(description[:120]),
                        "url": repo.get("html_url", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language", "غير محدد"),
                        "today_stars": repo.get("watchers_count", 0),
                        "topics": topics[:5],
                    })
                except Exception as e:
                    logger.warning(f"تخطي مستودع: {e}")
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
            return stories[:self.MAX_STORIES]
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
