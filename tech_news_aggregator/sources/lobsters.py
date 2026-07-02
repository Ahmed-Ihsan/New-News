from ..core import NewsSource, fetch_json, logger, MAX_STORIES_PER_SOURCE, sanitize_text


class LobstersSource(NewsSource):
    name = "Lobsters"
    icon = "🦞"
    URL = "https://lobste.rs/hottest.json"

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            data = fetch_json(self.URL)
            if not data or not isinstance(data, list):
                logger.warning(f"  ⚠️ لا توجد نتائج من {self.name}")
                return stories
            for item in data[:MAX_STORIES_PER_SOURCE]:
                try:
                    submitter = item.get("submitter_user", "مجهول")
                    if isinstance(submitter, dict):
                        author = submitter.get("username", "مجهول")
                    else:
                        author = submitter
                    stories.append({
                        "title": sanitize_text(item.get("title", "بدون عنوان")),
                        "url": item.get("url") or item.get("comments_url", ""),
                        "score": item.get("score", 0),
                        "comments": item.get("comment_count", 0),
                        "author": sanitize_text(author),
                        "tags": item.get("tags", []) or [],
                        "comments_url": item.get("comments_url", ""),
                        "created_at": item.get("created_at", ""),
                    })
                except Exception as e:
                    logger.warning(f"تخطي قصة Lobsters: {e}")
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
