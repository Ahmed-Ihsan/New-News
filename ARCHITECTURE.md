# New-News Architecture

## System intent

New-News is a daily automated tech news aggregator that collects from 14+ global and local sources (Hacker News, Reddit, GitHub, Dev.to, YouTube, Google News, Iraq Tech communities, etc.), analyzes trends, and generates Markdown reports. It serves developers and tech enthusiasts who want a consolidated daily briefing. The adapter pattern must stay stable — new sources are added as new adapter files without touching existing code.

## Boundary model

- **Core layer** (`tech_news_aggregator/core/`) — shared infrastructure: `NewsSource` ABC, HTTP helpers (`fetch_json`, `fetch_html`), config (logging, paths, constants), and utilities (`sanitize_text`, `time_ago`, DuckDuckGo helpers). No source-specific logic here.
- **Sources layer** (`tech_news_aggregator/sources/`) — 14 source adapters, each a `NewsSource` subclass in its own file. Each adapter implements `fetch() -> list[dict]` independently. No cross-source dependencies.
- **Report layer** (`tech_news_aggregator/report/`) — `MarkdownReportGenerator` renders collected stories into formatted Markdown. One method per source section.
- **Orchestration** (`tech_news_aggregator/aggregator.py`) — `TechNewsAggregator` registers all sources, calls `fetch()` on each, filters by search key, and generates the report.
- **Trend analysis** (`trend_analyzer.py`) — standalone script that analyzes collected JSON data for AI agent product trends.

## Module map

```
tech_news_aggregator/
├── core/
│   ├── base.py          → NewsSource ABC (abstract fetch())
│   ├── config.py        → logger, OUTPUT_DIR, MAX_STORIES_PER_SOURCE, SSL_CONTEXT
│   ├── http.py          → fetch_json(), fetch_html()
│   └── utils.py         → sanitize_text(), time_ago(), ddg_is_blocked(), ddg_extract_results(), is_tool_launch()
├── sources/
│   ├── hacker_news.py   → HackerNewsSource (Firebase API)
│   ├── reddit.py        → RedditSource (DuckDuckGo site: search)
│   ├── github_trending.py → GitHubTrendingSource (GitHub API)
│   ├── devto.py         → DevToSource (Dev.to API)
│   ├── lobsters.py      → LobstersSource (lobste.rs JSON API)
│   ├── product_hunt.py  → ProductHuntSource (HTML scraping)
│   ├── arxiv.py         → ArxivSource (arXiv Atom API)
│   ├── x_twitter.py     → XSource (DuckDuckGo site: search)
│   ├── youtube.py       → YouTubeSource (67 channels via RSS)
│   ├── medium.py        → MediumSource (RSS per tag)
│   ├── company_blogs.py → CompanyBlogsSource (8 company blogs via RSS)
│   ├── tech_news_sites.py → TechNewsSource (TechCrunch/Verge/Ars/VentureBeat RSS)
│   ├── google_news.py   → GoogleNewsSource (Google News RSS search)
│   └── iraq_tech.py     → IraqTechSource (Google News + DuckDuckGo + direct scraping)
├── report/
│   └── markdown.py      → MarkdownReportGenerator
├── aggregator.py        → TechNewsAggregator (orchestrator)
├── __main__.py          → CLI entry point (argparse)
└── __init__.py          → Package exports
```

## Data flow

```
User runs: python -m tech_news_aggregator --search AI
    ↓
TechNewsAggregator.__init__() registers 14 sources
    ↓
collect_all() → for each source: source.fetch() → list[dict]
    ↓
Filter by search_key (title + description + tags + tagline)
    ↓
generate_report() → MarkdownReportGenerator
    ↓
save() → news_output/tech_news_YYYY-MM-DD_HHMM.md
save_raw_json() → news_output/tech_news_raw_YYYY-MM-DD_HHMM.json
```

## Dependency rules

1. Sources depend on `core/` only — never on each other.
2. Report layer depends on story dict format — never on source internals.
3. Orchestrator depends on both sources and report — it's the only glue.
4. No external pip dependencies — Python standard library only.
5. Python 3.10+ required (PEP 604 union type syntax: `str | None`).

## Change checklist

- Adding a new source? Create `sources/new_source.py`, register in `sources/__init__.py` and `aggregator.py`, add report section in `report/markdown.py`.
- Changing HTTP behavior? Edit `core/http.py` — all sources use it.
- Changing report format? Edit `report/markdown.py` — no source changes needed.
- Changing how sources are registered? Edit `aggregator.py` only.
