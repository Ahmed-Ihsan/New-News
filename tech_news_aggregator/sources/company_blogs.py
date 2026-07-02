"""
مصدر مدونات الشركات — يجلب أحدث المنشورات من مدونات شركات التقنية.
Company Blogs source: fetches latest posts from tech company blogs via RSS/Atom.
"""

import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core import (
    NewsSource, fetch_html, logger,
    MAX_STORIES_PER_SOURCE, sanitize_text, is_tool_launch,
)


def _local_name(tag: str) -> str:
    """استخراج الاسم المحلي من وسم XML مع أو بدون namespace."""
    return tag.split("}")[-1].lower() if "}" in tag else tag.lower()


def _findtext_local(parent, name: str) -> str:
    """البحث عن نص أول عنصر فرعي بالاسم المحلي بغض النظر عن namespace."""
    for child in parent:
        if _local_name(child.tag) == name.lower():
            return child.text or ""
    return ""


def _find_local(parent, name: str):
    """البحث عن أول عنصر فرعي بالاسم المحلي بغض النظر عن namespace."""
    for child in parent:
        if _local_name(child.tag) == name.lower():
            return child
    return None


class CompanyBlogsSource(NewsSource):
    name = "Company Blogs"
    icon = "🏢"
    PER_BLOG = 5

    BLOGS = {
        "Google": "https://blog.google/rss/",
        "OpenAI": "https://openai.com/blog/rss.xml",
        "Meta": "https://about.fb.com/feed/",
        "NVIDIA": "https://blogs.nvidia.com/feed/",
        "Microsoft": "https://blogs.microsoft.com/feed/",
        "AWS": "https://aws.amazon.com/blogs/aws/feed/",
        "GitHub": "https://github.blog/feed/",
        "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    }

    def _parse_feed(self, xml: str, company: str) -> list[dict]:
        """تحليل RSS أو Atom واستخراج المنشورات المتعلقة بإطلاق الأدوات."""
        stories = []
        try:
            root = ET.fromstring(xml)
            root_tag = _local_name(root.tag)

            if root_tag == "rss":
                # RSS 2.0
                for item in root.iter():
                    if _local_name(item.tag) != "item":
                        continue
                    title = _findtext_local(item, "title")
                    link = _findtext_local(item, "link")
                    published = _findtext_local(item, "pubdate") or _findtext_local(item, "published")
                    description = _findtext_local(item, "description")
                    if not title:
                        continue
                    if is_tool_launch(title, description):
                        stories.append({
                            "title": sanitize_text(title),
                            "url": link,
                            "company": company,
                            "published": published[:30],
                            "description": sanitize_text(description[:200]),
                        })
                        if len(stories) >= self.PER_BLOG:
                            break

            elif root_tag == "feed":
                # Atom
                for entry in root.iter():
                    if _local_name(entry.tag) != "entry":
                        continue
                    title = _findtext_local(entry, "title")
                    link_elem = _find_local(entry, "link")
                    link = link_elem.get("href", "") if link_elem is not None else ""
                    published = _findtext_local(entry, "published") or _findtext_local(entry, "updated")
                    description = _findtext_local(entry, "summary") or _findtext_local(entry, "content")
                    if not title:
                        continue
                    if is_tool_launch(title, description):
                        stories.append({
                            "title": sanitize_text(title),
                            "url": link,
                            "company": company,
                            "published": published[:30],
                            "description": sanitize_text(description[:200]),
                        })
                        if len(stories) >= self.PER_BLOG:
                            break
        except Exception as e:
            logger.warning(f"  ⚠️ فشل تحليل feed مدونة {company}: {e}")
        return stories

    def _fetch_blog(self, company: str, feed_url: str) -> list[dict]:
        """جلب وتحليل مدونة شركة واحدة."""
        try:
            xml = fetch_html(feed_url)
            if not xml:
                return []
            return self._parse_feed(xml, company)
        except Exception as e:
            logger.warning(f"  ⚠️ فشل جلب مدونة {company}: {e}")
            return []

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب مدونات {self.name}...")
        stories = []
        try:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    executor.submit(self._fetch_blog, company, url): company
                    for company, url in self.BLOGS.items()
                }
                for future in as_completed(futures):
                    company = futures[future]
                    try:
                        blog_stories = future.result()
                        for story in blog_stories:
                            if len(stories) >= MAX_STORIES_PER_SOURCE:
                                break
                            stories.append(story)
                    except Exception as e:
                        logger.warning(f"  ⚠️ تخطي مدونة {company}: {e}")
            logger.info(f"  ✅ تم جلب {len(stories)} منشور من {self.name}")
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
