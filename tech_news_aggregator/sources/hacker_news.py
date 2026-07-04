from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core import NewsSource, fetch_json, logger, MAX_STORIES_PER_SOURCE, sanitize_text, time_ago, MIN_HN_SCORE


class HackerNewsSource(NewsSource):
    name = "Hacker News"
    icon = "🟧"
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    MAX_STORIES = 7

    NON_TECH_PATTERNS = [
        "costco", "amazon is the anti", "factories are just",
        "oat supply", "my dad helped", "supply chain",
        "what are you doing this weekend",
    ]

    TECH_KEYWORDS = [
        "ai", "llm", "gpt", "claude", "gemini", "openai",
        "rust", "python", "javascript", "typescript", "go ",
        "java ", "kotlin", "swift", "c++", "c#",
        "api", "framework", "compiler", "runtime", "database",
        "sql", "postgres", "mysql", "redis", "mongodb",
        "docker", "kubernetes", "cloud", "aws", "gcp", "azure",
        "security", "vulnerability", "cve", "breach", "encryption",
        "open source", "open-source", "github", "gitlab",
        "release", "released", "launches", "announces",
        "bug", "fix", "patch", "update", "deprecat",
        "linux", "windows", "macos", "android", "ios",
        "react", "vue", "angular", "svelte", "node",
        "wasm", "webassembly", "browser", "http", "tcp",
        "programming", "coding", "developer", "software",
        "startup", "funding", "acquires", "acquired",
        "valve", "steam", "sqlite", "postgresql", "oom",
        "tla", "formal verification", "sandbox", "jit",
        "ssh", "tls", "dns", "cdn", "ssl",
    ]

    def _is_tech(self, title: str) -> bool:
        title_lower = title.lower()
        for pattern in self.NON_TECH_PATTERNS:
            if pattern in title_lower:
                return False
        for kw in self.TECH_KEYWORDS:
            if kw in title_lower:
                return True
        return True

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
                            title = sanitize_text(item.get("title", ""))
                            if not self._is_tech(title):
                                continue
                            stories.append({
                                "title": title,
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
            stories = [s for s in stories if s["score"] >= MIN_HN_SCORE]
            stories = stories[:self.MAX_STORIES]
            logger.info(f"  ✅ تم جلب {len(stories)} خبر من {self.name} (بعد فلترة النقاط >= {MIN_HN_SCORE})")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
