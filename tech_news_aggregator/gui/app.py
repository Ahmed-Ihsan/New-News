"""
واجهة سطح المكتب — تطبيق مُجمّع الأخبار التقنية.
Desktop GUI: Two-pane layout with source tabs, dark mode, and export actions.

Layout:
  ┌──────────────────────────────────────────────────┐
  │  Topbar: Title + Search                          │
  ├──────────────────────────────────────────────────┤
  │  Source Tabs (All, HN, GitHub, Lobsters, ...)    │
  ├──────────────────────┬───────────────────────────┤
  │  News List (cards)   │  Detail Panel             │
  │                      │  + Action Buttons         │
  ├──────────────────────┴───────────────────────────┤
  │  Status Bar + Progress                           │
  └──────────────────────────────────────────────────┘
"""

import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

import customtkinter as ctk

from ..aggregator import TechNewsAggregator
from ..sources import (
    HackerNewsSource, GitHubTrendingSource,
    LobstersSource, CompanyBlogsSource,
    CVESecuritySource, StackOverflowSource,
    YouTubeNewsSource,
)

SOURCE_ORDER = [
    ("all", "📌 All", None),
    ("hacker_news", "🟧 HN", HackerNewsSource),
    ("github", "🐙 GitHub", GitHubTrendingSource),
    ("lobsters", "🦞 Lobsters", LobstersSource),
    ("company_blogs", "🏢 CoBlogs", CompanyBlogsSource),
    ("cve_security", "🛡️ CVE", CVESecuritySource),
    ("stackoverflow", "💬 SO Blog", StackOverflowSource),
    ("youtube_news", "📺 YouTube", YouTubeNewsSource),
]

SOURCE_LABELS = {
    "hacker_news": "Hacker News",
    "github": "GitHub",
    "lobsters": "Lobsters",
    "company_blogs": "Company Blog",
    "cve_security": "CVE Security",
    "stackoverflow": "Stack Overflow",
    "youtube_news": "YouTube",
}

SOURCE_ICONS = {
    "hacker_news": "🟧",
    "github": "🐙",
    "lobsters": "🦞",
    "company_blogs": "🏢",
    "cve_security": "🛡️",
    "stackoverflow": "💬",
    "youtube_news": "📺",
}


class TechNewsGUI(ctk.CTk):
    """النافذة الرئيسية لتطبيق مُجمّع الأخبار التقنية."""

    def __init__(self, search_key: str | None = None):
        super().__init__()

        self.search_key = search_key
        self.aggregator = TechNewsAggregator(search_key=search_key)
        self.all_stories: dict[str, list[dict]] = {}
        self.stats: dict[str, int] = {}
        self.current_filter = "all"
        self.current_selection: dict | None = None

        self._setup_window()
        self._build_ui()
        self.after(100, self._start_fetch)

    # ─────────────────────────────────────────────────────────
    # إعداد النافذة
    # ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.title("🚀 Tech News Aggregator")
        self.geometry("1200x750")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_topbar()
        self._build_source_tabs()
        self._build_main_panes()
        self._build_statusbar()

    # ─────────────────────────────────────────────────────────
    # شريط الأدوات العلوي
    # ─────────────────────────────────────────────────────────

    def _build_topbar(self) -> None:
        topbar = ctk.CTkFrame(self, height=50, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            topbar, text="🚀 Tech News Aggregator",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        search_entry = ctk.CTkEntry(
            topbar, textvariable=self.search_var,
            placeholder_text="🔍 Search stories...",
            width=300, height=32,
        )
        search_entry.grid(row=0, column=1, padx=10, pady=8, sticky="e")

        refresh_btn = ctk.CTkButton(
            topbar, text="🔄 Refresh", width=100, height=32,
            command=self._start_fetch,
        )
        refresh_btn.grid(row=0, column=2, padx=(0, 15), pady=8)

    # ─────────────────────────────────────────────────────────
    # تبويبات المصادر
    # ─────────────────────────────────────────────────────────

    def _build_source_tabs(self) -> None:
        tabbar = ctk.CTkFrame(self, height=42, corner_radius=0)
        tabbar.grid(row=1, column=0, sticky="ew")

        self.tab_buttons: dict[str, ctk.CTkButton] = {}
        for i, (key, label, _) in enumerate(SOURCE_ORDER):
            btn = ctk.CTkButton(
                tabbar, text=label, width=90, height=30,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self._on_tab_clicked(k),
            )
            btn.grid(row=0, column=i, padx=4, pady=6)
            self.tab_buttons[key] = btn

        self._highlight_tab("all")

    def _highlight_tab(self, key: str) -> None:
        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(fg_color=("#3b8ed0", "#1f6aa5"))
            else:
                btn.configure(fg_color=("gray75", "gray30"))

    def _on_tab_clicked(self, key: str) -> None:
        self.current_filter = key
        self._highlight_tab(key)
        self._populate_news_list()

    # ─────────────────────────────────────────────────────────
    # اللوحات الرئيسية (Two-pane)
    # ─────────────────────────────────────────────────────────

    def _build_main_panes(self) -> None:
        panes = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        panes.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        panes.grid_columnconfigure(0, weight=3, uniform="pane")
        panes.grid_columnconfigure(1, weight=2, uniform="pane")
        panes.grid_rowconfigure(0, weight=1)

        self._build_news_list(panes)
        self._build_detail_panel(panes)

    # ─────────────────────────────────────────────────────────
    # قائمة الأخبار (Left pane)
    # ─────────────────────────────────────────────────────────

    def _build_news_list(self, parent) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.news_scroll = ctk.CTkScrollableFrame(frame, corner_radius=0)
        self.news_scroll.grid(row=0, column=0, sticky="nsew")
        self.news_scroll.grid_columnconfigure(0, weight=1)

        self.news_cards: list[ctk.CTkFrame] = []

    def _populate_news_list(self) -> None:
        for card in self.news_cards:
            card.destroy()
        self.news_cards.clear()

        stories = self._get_filtered_stories()

        for i, story in enumerate(stories):
            card = self._create_news_card(self.news_scroll, story, i)
            card.grid(row=i, column=0, padx=4, pady=3, sticky="ew")
            self.news_cards.append(card)

        if not stories:
            empty = ctk.CTkLabel(
                self.news_scroll, text="📭 لا توجد أخبار",
                font=ctk.CTkFont(size=16),
            )
            empty.grid(row=0, column=0, pady=50)
            self.news_cards.append(empty)

    def _create_news_card(self, parent, story: dict, index: int) -> ctk.CTkFrame:
        source_key = story.get("_source_key", "")
        icon = SOURCE_ICONS.get(source_key, "📰")
        title = story.get("title", "Untitled")[:80]
        source_label = SOURCE_LABELS.get(source_key, source_key)

        score_text = ""
        if source_key == "hacker_news":
            score_text = f"⬆️ {story.get('score', 0)}"
        elif source_key == "github":
            score_text = f"⭐ {story.get('stars', 0):,}"
        elif source_key == "lobsters":
            score_text = f"⬆️ {story.get('score', 0)}"
        elif source_key == "cve_security":
            cvss = story.get("cvss", 0)
            score_text = f"⚠️ CVSS {cvss}"
        elif source_key == "company_blogs":
            score_text = story.get("company", "")
        elif source_key == "youtube_news":
            score_text = story.get("channel", "")

        card = ctk.CTkFrame(parent, corner_radius=8, height=60,
                            border_width=1, border_color=("gray60", "gray30"))
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            card, text=f"{icon} {title}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", justify="left",
        )
        title_label.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="ew")

        meta_label = ctk.CTkLabel(
            card, text=f"{source_label}  |  {score_text}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w",
        )
        meta_label.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

        card.bind("<Button-1>", lambda e, s=story: self._on_card_clicked(s))
        title_label.bind("<Button-1>", lambda e, s=story: self._on_card_clicked(s))
        meta_label.bind("<Button-1>", lambda e, s=story: self._on_card_clicked(s))

        return card

    def _on_card_clicked(self, story: dict) -> None:
        self.current_selection = story
        self._update_detail_panel(story)

    # ─────────────────────────────────────────────────────────
    # لوحة التفاصيل (Right pane)
    # ─────────────────────────────────────────────────────────

    def _build_detail_panel(self, parent) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.detail_scroll = ctk.CTkScrollableFrame(frame, corner_radius=0)
        self.detail_scroll.grid(row=0, column=0, sticky="nsew")
        self.detail_scroll.grid_columnconfigure(0, weight=1)

        self.detail_content = ctk.CTkFrame(self.detail_scroll, fg_color="transparent")
        self.detail_content.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.detail_content.grid_columnconfigure(0, weight=1)

        placeholder = ctk.CTkLabel(
            self.detail_content,
            text="👈 اختر خبراً لعرض التفاصيل",
            font=ctk.CTkFont(size=16),
            text_color=("gray50", "gray60"),
        )
        placeholder.grid(row=0, column=0, pady=60)

    def _update_detail_panel(self, story: dict) -> None:
        for widget in self.detail_content.winfo_children():
            widget.destroy()

        source_key = story.get("_source_key", "")
        icon = SOURCE_ICONS.get(source_key, "📰")
        title = story.get("title", "Untitled")
        source_label = SOURCE_LABELS.get(source_key, source_key)
        url = story.get("url", "")
        desc = story.get("description", "")
        published = story.get("published", "")

        row = 0

        ctk.CTkLabel(
            self.detail_content, text=f"{icon} {title}",
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=350, justify="left", anchor="w",
        ).grid(row=row, column=0, padx=10, pady=(10, 5), sticky="ew")
        row += 1

        meta_parts = [source_label]
        if published:
            meta_parts.append(f"📅 {published[:16]}")
        if source_key == "hacker_news":
            meta_parts.append(f"⬆️ {story.get('score', 0)}")
            meta_parts.append(f"💬 {story.get('comments', 0)}")
        elif source_key == "github":
            meta_parts.append(f"⭐ {story.get('stars', 0):,}")
            meta_parts.append(f"💻 {story.get('language', '')}")
        elif source_key == "cve_security":
            meta_parts.append(f"⚠️ CVSS {story.get('cvss', 0)}")
            if story.get("cve_id"):
                meta_parts.append(story["cve_id"])

        ctk.CTkLabel(
            self.detail_content, text="  |  ".join(meta_parts),
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"), anchor="w",
        ).grid(row=row, column=0, padx=10, pady=(0, 10), sticky="w")
        row += 1

        if desc:
            ctk.CTkLabel(
                self.detail_content, text=desc,
                font=ctk.CTkFont(size=13), wraplength=350,
                justify="left", anchor="w",
            ).grid(row=row, column=0, padx=10, pady=(0, 15), sticky="ew")
            row += 1

        if url:
            ctk.CTkLabel(
                self.detail_content, text=f"🔗 {url[:80]}",
                font=ctk.CTkFont(size=11),
                text_color=("#3b8ed0", "#1f6aa5"), anchor="w",
                wraplength=350,
            ).grid(row=row, column=0, padx=10, pady=(0, 15), sticky="w")
            row += 1

        btn_frame = ctk.CTkFrame(self.detail_content, fg_color="transparent")
        btn_frame.grid(row=row, column=0, padx=10, pady=(5, 10), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        row += 1

        if url:
            ctk.CTkButton(
                btn_frame, text="🔗 Open Link", height=32,
                command=lambda u=url: webbrowser.open(u),
            ).grid(row=0, column=0, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="📄 Export PDF", height=32,
            command=self._export_pdf,
        ).grid(row=0, column=1, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="📱 Telegram Post", height=32,
            command=lambda: self._export_social(image=False),
        ).grid(row=1, column=0, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="📸 Card Image", height=32,
            command=lambda: self._export_social(image=True),
        ).grid(row=1, column=1, padx=3, pady=3, sticky="ew")

    # ─────────────────────────────────────────────────────────
    # شريط الحالة + التقدم
    # ─────────────────────────────────────────────────────────

    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(self, height=36, corner_radius=0)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            bar, text="⏳ Loading...", font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(bar, width=200, height=14)
        self.progress_bar.grid(row=0, column=1, padx=15, pady=8, sticky="e")
        self.progress_bar.set(0)

    # ─────────────────────────────────────────────────────────
    # جلب البيانات (Threading)
    # ─────────────────────────────────────────────────────────

    def _start_fetch(self) -> None:
        self.status_label.configure(text="⏳ Fetching news from all sources...")
        self.progress_bar.set(0)
        self.all_stories = {}
        self.stats = {}

        thread = threading.Thread(target=self._fetch_worker, daemon=True)
        thread.start()

    def _fetch_worker(self) -> None:
        from ..core.config import logger

        def fetch_source(key: str, source_cls, search_key):
            try:
                try:
                    source = source_cls(search_key=search_key)
                except TypeError:
                    source = source_cls()
                return key, source.fetch()
            except Exception as e:
                logger.error(f"GUI: فشل مصدر {key}: {e}")
                return key, []

        total = len(SOURCE_ORDER) - 1
        completed = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_source, key, cls, self.search_key): key
                for key, _, cls in SOURCE_ORDER if cls is not None
            }
            for future in as_completed(futures):
                key, stories = future.result()
                self.all_stories[key] = stories
                self.stats[key] = len(stories)
                completed += 1
                self.after(0, lambda c=completed, t=total, k=key: self._on_source_done(c, t, k))

        self.after(0, self._on_all_done)

    def _on_source_done(self, completed: int, total: int, key: str) -> None:
        self.progress_bar.set(completed / total)
        label = next((lbl for k, lbl, _ in SOURCE_ORDER if k == key), key)
        self.status_label.configure(
            text=f"⏳ Fetched {label}... ({completed}/{total})"
        )
        self._populate_news_list()

    def _on_all_done(self) -> None:
        total = sum(self.stats.values())
        self.progress_bar.set(1.0)
        parts = []
        for key, label, _ in SOURCE_ORDER:
            if key == "all":
                continue
            count = self.stats.get(key, 0)
            if count > 0:
                parts.append(f"{label}:{count}")
        self.status_label.configure(
            text=f"✅ {total} stories | {' | '.join(parts)}"
        )

    # ─────────────────────────────────────────────────────────
    # فلترة وبحث
    # ─────────────────────────────────────────────────────────

    def _get_filtered_stories(self) -> list[dict]:
        query = self.search_var.get().lower().strip() if hasattr(self, "search_var") else ""

        if self.current_filter == "all":
            stories = []
            for key, _, _ in SOURCE_ORDER:
                if key == "all":
                    continue
                for s in self.all_stories.get(key, []):
                    s["_source_key"] = key
                    stories.append(s)
        else:
            stories = []
            for s in self.all_stories.get(self.current_filter, []):
                s["_source_key"] = self.current_filter
                stories.append(s)

        if query:
            stories = [
                s for s in stories
                if query in (s.get("title", "") + s.get("description", "")).lower()
            ]

        return stories

    def _on_search_changed(self, *args) -> None:
        self._populate_news_list()

    # ─────────────────────────────────────────────────────────
    # تصدير
    # ─────────────────────────────────────────────────────────

    def _export_pdf(self) -> None:
        self.status_label.configure(text="📄 Generating PDF...")
        thread = threading.Thread(target=self._export_pdf_worker, daemon=True)
        thread.start()

    def _export_pdf_worker(self) -> None:
        try:
            self.aggregator.results = self.all_stories
            self.aggregator.stats = dict(self.stats)
            self.aggregator.stats["_duration"] = 0.0
            md_path = self.aggregator.generate_report()
            pdf_path = self.aggregator.export_pdf(md_path)
            self.after(0, lambda: self.status_label.configure(
                text=f"✅ PDF saved: {pdf_path.name}"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(
                text=f"❌ PDF error: {e}"))

    def _export_social(self, image: bool = False) -> None:
        label = "📸 Generating image..." if image else "📱 Generating post..."
        self.status_label.configure(text=label)
        thread = threading.Thread(
            target=self._export_social_worker, args=(image,), daemon=True)
        thread.start()

    def _export_social_worker(self, image: bool) -> None:
        try:
            self.aggregator.results = self.all_stories
            self.aggregator.stats = dict(self.stats)
            self.aggregator.stats["_duration"] = 0.0
            path = self.aggregator.export_social("telegram", image=image)
            kind = "Image" if image else "Post"
            self.after(0, lambda: self.status_label.configure(
                text=f"✅ {kind} saved: {path.name}"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(
                text=f"❌ Export error: {e}"))
