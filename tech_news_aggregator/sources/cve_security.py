"""
مصدر ثغرات NVD — يجلب الثغرات الأمنية الحرجة (CVSS >= 7.0).
CVE Security source: fetches critical vulnerabilities from NVD JSON API 2.0.
"""

from ..core import NewsSource, fetch_json, logger, sanitize_text


class CVESecuritySource(NewsSource):
    name = "CVE Security"
    icon = "🛡️"
    API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    MIN_CVSS = 7.0
    MAX_STORIES = 5
    MIN_YEAR = 2025
    FETCH_BATCH = 20

    def __init__(self, search_key: str | None = None):
        pass

    def fetch(self) -> list[dict]:
        logger.info(f"{self.icon} جارٍ جلب ثغرات {self.name}...")
        stories = []
        try:
            count_url = f"{self.API_URL}?resultsPerPage=1&cvssV3Severity=HIGH"
            count_data = fetch_json(count_url)
            if not count_data or "totalResults" not in count_data:
                logger.warning(f"  ⚠️ لا توجد نتائج من {self.name}")
                return stories

            total = count_data["totalResults"]
            start_index = max(0, total - self.FETCH_BATCH)
            url = (
                f"{self.API_URL}?resultsPerPage={self.FETCH_BATCH}"
                f"&cvssV3Severity=HIGH"
                f"&startIndex={start_index}"
            )
            data = fetch_json(url)
            if not data or "vulnerabilities" not in data:
                logger.warning(f"  ⚠️ لا توجد نتائج من {self.name}")
                return stories

            for vuln in data["vulnerabilities"]:
                cve = vuln.get("cve", {})
                cve_id = cve.get("id", "")
                if not cve_id:
                    continue

                published = cve.get("published", "")
                if published and published[:4] < str(self.MIN_YEAR):
                    continue

                descriptions = cve.get("descriptions", [])
                desc_text = ""
                for d in descriptions:
                    if d.get("lang") == "en":
                        desc_text = d.get("value", "")
                        break

                last_modified = cve.get("lastModified", "")

                references = cve.get("references", [])
                url_ref = ""
                if references:
                    url_ref = references[0].get("url", "")

                cvss_score = 0.0
                metrics = cve.get("metrics", {})
                for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                    if key in metrics and metrics[key]:
                        cvss_data = metrics[key][0].get("cvssData", {})
                        cvss_score = cvss_data.get("baseScore", 0.0)
                        break

                if 0.0 < cvss_score < self.MIN_CVSS:
                    continue

                stories.append({
                    "title": sanitize_text(f"{cve_id}: {desc_text[:80]}"),
                    "url": url_ref or f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    "description": sanitize_text(desc_text[:200]),
                    "cvss": cvss_score,
                    "cve_id": cve_id,
                    "published": published[:30] if published else "",
                })

                if len(stories) >= self.MAX_STORIES:
                    break

            stories.sort(key=lambda x: x.get("published", ""), reverse=True)
            logger.info(
                f"  ✅ تم جلب {len(stories)} ثغرة حرجة من {self.name} "
                f"(CVSS >= {self.MIN_CVSS}, بعد {self.MIN_YEAR})"
            )
        except Exception as e:
            logger.error(f"  ❌ فشل جلب {self.name}: {e}")
        return stories
