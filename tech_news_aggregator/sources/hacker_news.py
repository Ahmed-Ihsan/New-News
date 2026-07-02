from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core import NewsSource, fetch_json, logger, MAX_STORIES_PER_SOURCE, sanitize_text, time_ago


class HackerNewsSource(NewsSource):
    name = "Hacker News"
    icon = "🟧"
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب أخبار {self.name}...")
        stories = []
        try:
            top_ids = fetch_json(f"{self.BASE_URL}/topstories.json")
            story_ids = top_ids[:MAX_STORIES_PER_SOURCE]
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    executor.submit(fetch_json, f"{self.BASE_URL}/item/{sid}.json"): sid
                    for sid in story_ids
                }
                for future in as_completed(futures):
                    try:
                        item = future.result()
                        if item and item.get("type") == "story":
                            stories.append({
                                "title": sanitize_text(item.get("title", "بدون عنوان")),
                                "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                                "score": item.get("score", 0),
                                "comments": item.get("descendants", 0),
                                "author": item.get("by", "مجهول"),
                                "time": item.get("time", 0),
                                "time_ago": time_ago(item.get("time", 0)),
                                "hn_link": f"https://news.ycombinator.com/item?id={item['id']}",
                            })
                    except Exception as e:
                        logger.warning(f"تخطي قصة HN: {e}")
            stories.sort(key=lambda x: x["score"], reverse=True)
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
