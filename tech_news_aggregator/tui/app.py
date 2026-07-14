"""
تطبيق واجهة المستخدم الطرفية الرئيسي — TUI لتجميع وعرض الأخبار التقنية.
Main TUI application: collect and display tech news in an interactive terminal UI.

الميزات:
  - تبويبات لكل مصدر (Hacker News, Reddit, Iraq Tech, ...)
  - شريط بحث فلتر مباشر
  - شريط تقدم أثناء الجلب
  - فتح الرابط في المتصفح بالضغط على Enter
  - توليد تقرير Markdown
  - لوحة إحصائيات
"""

import webbrowser

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    DataTable,
    Input,
    Label,
    ProgressBar,
    TabbedContent,
    TabPane,
    Button,
    Footer,
    Header,
)

from ..aggregator import TechNewsAggregator
from ..sources import (
    HackerNewsSource, GitHubTrendingSource,
    LobstersSource, CompanyBlogsSource,
    CVESecuritySource, StackOverflowSource,
    YouTubeNewsSource, XSource,
)

# ترتيب المصادر للألسنة (tabs)
SOURCE_ORDER = [
    ("hacker_news", "HN", HackerNewsSource),
    ("github", "GitHub", GitHubTrendingSource),
    ("lobsters", "Lobsters", LobstersSource),
    ("company_blogs", "CoBlogs", CompanyBlogsSource),
    ("cve_security", "CVE", CVESecuritySource),
    ("stackoverflow", "SO Blog", StackOverflowSource),
    ("youtube_news", "YouTube", YouTubeNewsSource),
    ("x", "X", XSource),
]


class TechNewsApp(App):
    """تطبيق TUI لمُجمّع الأخبار التقنية."""

    CSS = """
    #toolbar { dock: top; height: 3; padding: 0 1; }
    #search-input { width: 1fr; margin: 0 1; }
    #generate-btn { width: 20; margin: 0 1; }
    #refresh-btn { width: 12; margin: 0 1; }
    #stats-bar { dock: top; height: 1; padding: 0 2; background: $boost; }
    #progress-bar { dock: top; height: 1; }
    #source-tabs { height: 1fr; }
    #footer { dock: bottom; height: 1; padding: 0 2; background: $boost; color: $text-muted; }
    """

    TITLE = "Tech News Aggregator"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("g", "generate_report", "Gen Report"),
        Binding("slash", "focus_search", "Search"),
    ]

    def __init__(self, search_key: str | None = None):
        super().__init__()
        self.search_key = search_key
        self.aggregator = TechNewsAggregator(search_key=search_key)
        self._all_stories: dict[str, list[dict]] = {}
        self._stats: dict[str, int] = {}
        self._url_map: dict[str, list[str]] = {}  # key -> list of urls by row

    # ─────────────────────────────────────────────────────────
    # التخطيط (Layout)
    # ─────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal(id="toolbar"):
                yield Input(placeholder="Search stories... (type to filter)", id="search-input")
                yield Button("Gen Report", id="generate-btn", variant="primary")
                yield Button("Refresh", id="refresh-btn", variant="default")
            yield Label("Stats: Loading...", id="stats-bar")
            yield ProgressBar(id="progress-bar", total=len(SOURCE_ORDER), show_eta=False)
            with TabbedContent(id="source-tabs"):
                for key, label, _ in SOURCE_ORDER:
                    with TabPane(label, id=f"tab-{key}"):
                        yield DataTable(id=f"table-{key}", cursor_type="row")
            yield Label(
                "Enter: open link | /: search | R: refresh | G: report | Q: quit",
                id="footer",
            )
        yield Footer()

    def on_mount(self) -> None:
        """تهيئة الجداول عند بدء التطبيق."""
        for key, _, _ in SOURCE_ORDER:
            table = self.query_one(f"#table-{key}", DataTable)
            table.add_column("#", width=4)
            table.add_column("Title", width=55)
            table.add_column("Source", width=18)
            table.add_column("Date", width=14)
        # بدء الجلب تلقائياً
        self.run_worker(self._fetch_all_sources, exclusive=True, thread=True)

    # ─────────────────────────────────────────────────────────
    # جلب البيانات (Fetching) — يعمل في thread منفصل
    # ─────────────────────────────────────────────────────────

    def _fetch_all_sources(self) -> None:
        """جلب الأخبار من جميع المصادر بالتوازي."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        self._all_stories = {}
        self._stats = {}

        # تصفير شريط التقدم من الـ thread
        self.app.call_from_thread(self._reset_progress)

        def fetch_source(key: str, source_cls, search_key):
            try:
                source = source_cls(search_key=search_key)
                return key, source.fetch()
            except Exception:
                return key, []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_source, key, cls, self.search_key): key
                for key, _, cls in SOURCE_ORDER
            }
            for future in as_completed(futures):
                key, stories = future.result()
                self._all_stories[key] = stories
                self._stats[key] = len(stories)
                # تحديث الواجهة من الـ thread الرئيسي
                self.app.call_from_thread(self._on_source_done, key, stories)

        self.app.call_from_thread(self._on_all_done)

    def _reset_progress(self) -> None:
        """تصفير شريط التقدم — يعمل في الـ thread الرئيسي."""
        progress = self.query_one("#progress-bar", ProgressBar)
        progress.update(total=len(SOURCE_ORDER))
        progress.progress = 0

    def _on_source_done(self, key: str, stories: list[dict]) -> None:
        """تحديث الجدول والإحصائيات بعد اكتمال مصدر — يعمل في الـ thread الرئيسي."""
        progress = self.query_one("#progress-bar", ProgressBar)
        progress.advance(1)
        self._populate_table(key, stories)
        self._update_stats()

    def _on_all_done(self) -> None:
        """تحديث الشريط عند اكتمال جميع المصادر."""
        total = sum(self._stats.values())
        label = self.query_one("#stats-bar", Label)
        label.update(f"Done! {total} stories from {len(SOURCE_ORDER)} sources")

    def _populate_table(self, key: str, stories: list[dict]) -> None:
        """ملء جدول مصدر معين بالقصص."""
        table = self.query_one(f"#table-{key}", DataTable)
        table.clear()
        urls = []
        for i, story in enumerate(stories, 1):
            title = story.get("title", "")[:55]
            source = story.get("source", "")[:18]
            published = story.get("published", "")[:14]
            url = story.get("url", "")
            urls.append(url)
            table.add_row(str(i), title, source, published)
        self._url_map[key] = urls

    def _update_stats(self) -> None:
        """تحديث شريط الإحصائيات."""
        parts = []
        for key, label, _ in SOURCE_ORDER:
            count = self._stats.get(key, 0)
            if count > 0:
                parts.append(f"{label}:{count}")
        total = sum(self._stats.values())
        label = self.query_one("#stats-bar", Label)
        label.update(f"{total} stories | {' | '.join(parts[:10])}")

    # ─────────────────────────────────────────────────────────
    # البحث (Search Filter)
    # ─────────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        """فلترة الجداول عند تغيير نص البحث."""
        if event.input.id != "search-input":
            return
        query = event.value.lower().strip()
        for key, _, _ in SOURCE_ORDER:
            stories = self._all_stories.get(key, [])
            if query:
                filtered = [
                    s for s in stories
                    if query in (s.get("title", "") +
                                 s.get("description", "") +
                                 s.get("snippet", "")).lower()
                ]
            else:
                filtered = stories
            self._populate_table(key, filtered)

    # ─────────────────────────────────────────────────────────
    # فتح الرابط (Open Link)
    # ─────────────────────────────────────────────────────────

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """فتح رابط القصة في المتصفح عند الضغط على Enter."""
        if not event.data_table.id or not event.data_table.id.startswith("table-"):
            return
        key = event.data_table.id.replace("table-", "")
        urls = self._url_map.get(key, [])
        row_idx = event.cursor_row
        if 0 <= row_idx < len(urls):
            url = urls[row_idx]
            if url and url.startswith("http"):
                webbrowser.open(url)
                self.notify(f"Opened: {url[:50]}...")

    # ─────────────────────────────────────────────────────────
    # الأزرار (Buttons)
    # ─────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """معالجة ضغطات الأزرار."""
        if event.button.id == "generate-btn":
            self.run_worker(self._generate_report, exclusive=True, thread=True)
        elif event.button.id == "refresh-btn":
            self.run_worker(self._fetch_all_sources, exclusive=True, thread=True)

    def _generate_report(self) -> None:
        """توليد تقرير Markdown من البيانات المجمعة."""
        if not self._all_stories:
            self.app.call_from_thread(self.notify,
                                      "No data! Fetch first (press R)",
                                      severity="warning")
            return

        self.aggregator.results = self._all_stories
        self.aggregator.stats = dict(self._stats)
        self.aggregator.stats["_duration"] = 0.0

        try:
            filepath = self.aggregator.generate_report()
            self.app.call_from_thread(self.notify,
                                      f"Report saved: {filepath}",
                                      title="Report Generated")
        except Exception as e:
            self.app.call_from_thread(self.notify,
                                      f"Error: {e}", severity="error")

    # ─────────────────────────────────────────────────────────
    # اختصارات لوحة المفاتيح (Key Bindings)
    # ─────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        """تحديث جميع المصادر."""
        self.run_worker(self._fetch_all_sources, exclusive=True, thread=True)

    def action_generate_report(self) -> None:
        """توليد التقرير."""
        self.run_worker(self._generate_report, exclusive=True, thread=True)

    def action_focus_search(self) -> None:
        """التركيز على حقل البحث."""
        self.query_one("#search-input", Input).focus()
