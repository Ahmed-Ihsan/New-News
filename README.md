# Tech News Aggregator & Trend Analyzer

🚀 **مُجمّع الأخبار التقنية اليومي** — يجمع الأخبار من 14 مصدراً عالمياً ومحلياً، يحلل الاتجاهات، ويُولّد تقارير Markdown تلقائياً.

A daily automated tech news aggregator that collects from 14+ global and local sources, analyzes trends, and generates Markdown reports.

## Features

### News Aggregation (14 sources)
| Source | Icon | What it fetches |
|--------|------|----------------|
| Hacker News | 🟧 | Top stories from Silicon Valley's #1 news source |
| Reddit | 🟠 | Tech subreddits via DuckDuckGo |
| GitHub Trending | 🐙 | Most starred recent repositories |
| Dev.to | 👩‍💻 | Top articles from the dev community |
| Lobsters | 🦞 | Deep technical news |
| Product Hunt | 🐱 | Latest products and tools |
| arXiv | 🔬 | Latest CS/AI research papers |
| X (Twitter) | 🐦 | Tech posts discovered via DuckDuckGo |
| YouTube | 📺 | Latest videos from 67 tech channels |
| Medium | ✍️ | Articles from tech tags |
| Company Blogs | 🏢 | Tool launch announcements (Google, OpenAI, Meta, NVIDIA, etc.) |
| Tech News Sites | 📰 | TechCrunch, The Verge, Ars Technica, VentureBeat |
| Google News | 🌐 | Tool launch news from any company |
| **Iraq Tech** | 🇮🇶 | Iraqi tech communities & events (Re:Coded, Five One Labs, Baghdad/Erbil/Mosul/Basra Tech) |

### Trend Analyzer
- Tracks AI agent products and frameworks (OpenAI, Anthropic, Google, Meta, etc.)
- Auto-discovers new AI agents from context
- Generates trend reports with frequency analysis
- Console summary with colored output

## Installation

```bash
# No external dependencies required — uses Python standard library only
git clone https://github.com/Ahmed-Ihsan/New-News.git
cd New-News
```

**Requirements:** Python 3.10+ (uses `|` type union syntax)

## Usage

### News Aggregator

```bash
# Run the aggregator (collects from all 14 sources)
python -m tech_news_aggregator

# Search for specific topics
python -m tech_news_aggregator --search AI

# Or use the legacy entry point
python tech_news_aggregator.py
```

Output:
- `news_output/tech_news_YYYY-MM-DD_HHMM.md` — formatted Markdown report
- `news_output/tech_news_raw_YYYY-MM-DD_HHMM.json` — raw JSON data

### Trend Analyzer

```bash
# Run the trend analyzer on collected news
python trend_analyzer.py

# Analyze a specific JSON file
python trend_analyzer.py news_output/tech_news_raw_2026-07-02_1621.json
```

## Project Structure

```
New-News/
├── tech_news_aggregator.py          # Legacy entry point (thin wrapper)
├── trend_analyzer.py                # Trend analysis & AI agent tracking
├── tech_news_aggregator/            # Main package (adapter pattern)
│   ├── __init__.py                  # Package exports
│   ├── __main__.py                  # CLI entry point
│   ├── aggregator.py                # Orchestrator — coordinates all sources
│   ├── core/                        # Shared infrastructure
│   │   ├── base.py                  # NewsSource ABC
│   │   ├── config.py                # Logging, paths, constants
│   │   ├── http.py                  # fetch_json(), fetch_html()
│   │   └── utils.py                 # sanitize_text, time_ago, ddg_* helpers
│   ├── sources/                     # 14 source adapters (one per file)
│   │   ├── hacker_news.py
│   │   ├── reddit.py
│   │   ├── github_trending.py
│   │   ├── devto.py
│   │   ├── lobsters.py
│   │   ├── product_hunt.py
│   │   ├── arxiv.py
│   │   ├── x_twitter.py
│   │   ├── youtube.py               # 67 tech channels
│   │   ├── medium.py
│   │   ├── company_blogs.py
│   │   ├── tech_news_sites.py
│   │   ├── google_news.py
│   │   └── iraq_tech.py             # 🇮🇶 Iraqi tech communities
│   └── report/
│       └── markdown.py              # Markdown report generator
└── news_output/                     # Generated reports (gitignored)
```

## Architecture

### Adapter Pattern
Each news source is a `NewsSource` subclass that implements `fetch() -> list[dict]`. The `TechNewsAggregator` orchestrator registers all adapters, calls `fetch()` on each, filters by search key, and generates a Markdown report.

### Adding a New Source
1. Create `tech_news_aggregator/sources/my_source.py`
2. Implement `class MySource(NewsSource)` with `fetch()` method
3. Register in `sources/__init__.py` and `aggregator.py`
4. Add report section in `report/markdown.py`

### Iraq Tech Source
The `IraqTechSource` adapter aggregates from 3 parallel strategies:
- **Google News RSS** — 10 queries (Arabic + English) about Iraqi tech
- **DuckDuckGo scraping** — `site:` searches for Facebook/Meetup/LinkedIn
- **Direct scraping** — community websites (Re:Coded, Five One Labs)

## License

MIT License — see [LICENSE](LICENSE) file.

## Author

**Ahmed Ihsan** — [GitHub](https://github.com/Ahmed-Ihsan)
