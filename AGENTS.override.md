# New-News — Agent Collaboration Guide

> This file gives AI agents (Devin, Codex, Claude) the context they need to work effectively in this repo.

## Project overview

**New-News** is a tech news aggregator that collects from 14 sources, filters by keyword, and generates Markdown reports. Built with Python 3.10+ standard library only — no pip dependencies.

## Tech stack

- **Language:** Python 3.10+ (uses `str | None` union syntax)
- **Dependencies:** None (stdlib only: urllib, json, xml, concurrent.futures, logging)
- **Architecture:** Adapter pattern — each source is a `NewsSource` subclass

## First-run commands

```bash
# Run the aggregator
python -m tech_news_aggregator

# Search for specific topics
python -m tech_news_aggregator --search AI

# Run trend analyzer on collected data
python trend_analyzer.py

# Verify imports work
python -c "from tech_news_aggregator import TechNewsAggregator; print('OK')"
```

## Non-negotiable constraints

1. **No external dependencies** — stdlib only. Do not add `pip install` requirements.
2. **Python 3.10+** — use `str | None` not `Optional[str]`.
3. **Adapter pattern** — each source is a separate file in `sources/`, inheriting `NewsSource`.
4. **Bilingual comments** — Arabic + English in docstrings (existing convention).
5. **Never modify `core/` without reason** — all sources depend on it.

## How to add a new source adapter

1. Create `tech_news_aggregator/sources/my_source.py`
2. Implement `class MySource(NewsSource)` with `name`, `icon`, and `fetch() -> list[dict]`
3. Register in `sources/__init__.py` (import + `__all__`)
4. Register in `aggregator.py` (add to `self.sources` dict)
5. Add report section in `report/markdown.py` (new method + call in `generate_report`)

## Story dict format

Every `fetch()` must return a list of dicts with at minimum:

```python
{
    "title": str,        # sanitized title
    "url": str,          # canonical URL
    "source": str,       # source name (e.g., "Hacker News")
    "published": str,    # date string (format varies by source)
    "description": str,  # short description (optional but recommended)
}
```

Some sources add extra fields (`community`, `tags`, `tagline`, `site`) — these are optional.

## File ownership

| Directory | Purpose | Who can edit |
|-----------|---------|-------------|
| `core/` | Shared infrastructure | Only for cross-cutting changes |
| `sources/` | One adapter per file | Anyone — add new files freely |
| `report/` | Markdown generation | Only when adding/removing source sections |
| `aggregator.py` | Orchestration | Only when registering new sources |
| `trend_analyzer.py` | Trend analysis | Standalone script |

## Verification

After any change:
```bash
# 1. Check imports
python -c "from tech_news_aggregator import TechNewsAggregator; print('OK')"

# 2. Run the aggregator (quick test with one source)
python -c "from tech_news_aggregator.sources import HackerNewsSource; print(len(HackerNewsSource().fetch()))"

# 3. Full run
python -m tech_news_aggregator
```
