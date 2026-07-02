from ..core import NewsSource, fetch_json, logger, MAX_STORIES_PER_SOURCE, sanitize_text


class DevToSource(NewsSource):
    name = "Dev.to"
    icon = "👩‍💻"
    API_URL = "https://dev.to/api/articles"

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            url = f"{self.API_URL}?per_page={MAX_STORIES_PER_SOURCE}&top=1"
            articles = fetch_json(url)
            if not articles or not isinstance(articles, list):
                logger.warning(f"  ⚠️ لا توجد مقالات من {self.name}")
                return stories
            for article in articles[:MAX_STORIES_PER_SOURCE]:
                try:
                    description = article.get("description") or ""
                    tag_list = article.get("tag_list", []) or []
                    user = article.get("user", {}) or {}
                    stories.append({
                        "title": sanitize_text(article.get("title", "بدون عنوان")),
                        "url": article.get("url", ""),
                        "reactions": article.get("positive_reactions_count", 0),
                        "comments": article.get("comments_count", 0),
                        "author": sanitize_text(user.get("name", "مجهول")),
                        "reading_time": article.get("reading_time_minutes", 0),
                        "tags": tag_list[:4] if isinstance(tag_list, list) else [],
                        "published": article.get("readable_publish_date", ""),
                        "description": sanitize_text(description[:120]),
                    })
                except Exception as e:
                    logger.warning(f"تخطي مقال Dev.to: {e}")
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
