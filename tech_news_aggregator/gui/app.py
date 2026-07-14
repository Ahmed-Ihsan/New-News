"""
واجهة سطح المكتب — تطبيق مُجمّع الأخبار التقنية (pywebview).
Desktop GUI built with pywebview: a polished web-based single-page UI
(HTML/CSS/JS) bridged to the Python aggregator backend.

Public API is identical to the previous customtkinter implementation:
    from .gui import TechNewsGUI
    TechNewsGUI(search_key=...).mainloop()

Layout:
  ┌──────────────────────────────────────────────────────┐
  │  Topbar: Title + Search + Refresh                    │
  ├──────────────────────────────────────────────────────┤
  │  Source Tabs (All, HN, GitHub, Lobsters, ...)        │
  ├────────────────────────┬─────────────────────────────┤
  │  News List (cards)     │  Detail Panel               │
  │                        │  + Action Buttons           │
  ├────────────────────────┴─────────────────────────────┤
  │  Status Bar + Progress                               │
  └──────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

import webview

from ..aggregator import TechNewsAggregator
from ..sources import (
    HackerNewsSource, GitHubTrendingSource,
    LobstersSource, CompanyBlogsSource,
    CVESecuritySource, StackOverflowSource,
    YouTubeNewsSource, XSource,
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
    ("x", "🐦 X", XSource),
]

SOURCE_LABELS = {
    "hacker_news": "Hacker News",
    "github": "GitHub",
    "lobsters": "Lobsters",
    "company_blogs": "Company Blog",
    "cve_security": "CVE Security",
    "stackoverflow": "Stack Overflow",
    "youtube_news": "YouTube",
    "x": "X (Twitter)",
}

SOURCE_ICONS = {
    "hacker_news": "🟧",
    "github": "🐙",
    "lobsters": "🦞",
    "company_blogs": "🏢",
    "cve_security": "🛡️",
    "stackoverflow": "💬",
    "youtube_news": "📺",
    "x": "🐦",
}

# Source accent colors (used by the frontend badges).
SOURCE_COLORS = {
    "hacker_news": "#ff6600",
    "github": "#ffffff",
    "lobsters": "#ac130d",
    "company_blogs": "#3b82f6",
    "cve_security": "#ef4444",
    "stackoverflow": "#f48024",
    "youtube_news": "#ff0000",
    "x": "#1d9bf0",
}


# ──────────────────────────────────────────────────────────────────────────
# Frontend (single-file HTML/CSS/JS)
# ──────────────────────────────────────────────────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Tech News Aggregator</title>
<style>
  :root {
    --bg:        #0f1117;
    --bg-soft:   #161922;
    --bg-card:   #1b1f2a;
    --bg-card-h: #232838;
    --border:    #2a2f3d;
    --border-s:  #353b4d;
    --text:      #e6e9ef;
    --text-dim:  #9aa3b2;
    --text-mute: #6b7280;
    --accent:    #3b82f6;
    --accent-2:  #60a5fa;
    --accent-d:  #2563eb;
    --ok:        #22c55e;
    --warn:      #f59e0b;
    --err:       #ef4444;
    --radius:    12px;
    --radius-s:  8px;
    --shadow:    0 6px 24px rgba(0,0,0,.35);
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji", sans-serif;
    --mono: "SF Mono", "Cascadia Code", Consolas, "Liberation Mono", monospace;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    font-size: 14px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }
  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #2f3547; border-radius: 8px; border: 2px solid transparent; background-clip: padding-box; }
  ::-webkit-scrollbar-thumb:hover { background: #3d445a; background-clip: padding-box; }

  /* Topbar */
  .topbar {
    flex: 0 0 auto;
    height: 56px;
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0 18px;
    background: linear-gradient(180deg, #14171f 0%, #0f1117 100%);
    border-bottom: 1px solid var(--border);
  }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 17px; letter-spacing: .2px; white-space: nowrap; }
  .brand .logo {
    width: 30px; height: 30px; border-radius: 8px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    display: grid; place-items: center; font-size: 16px;
    box-shadow: 0 2px 10px rgba(59,130,246,.4);
  }
  .brand .ver { color: var(--text-mute); font-weight: 500; font-size: 12px; }
  .spacer { flex: 1 1 auto; }
  .search {
    position: relative; width: 320px; max-width: 40vw;
  }
  .search input {
    width: 100%; height: 36px; padding: 0 12px 0 34px;
    background: var(--bg-soft); color: var(--text);
    border: 1px solid var(--border); border-radius: 10px;
    font-size: 13px; outline: none; transition: .15s;
  }
  .search input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(59,130,246,.18); }
  .search input::placeholder { color: var(--text-mute); }
  .search .ico { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--text-mute); font-size: 14px; }
  .btn {
    height: 36px; padding: 0 14px; border: 1px solid var(--border);
    background: var(--bg-soft); color: var(--text);
    border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer;
    display: inline-flex; align-items: center; gap: 7px; transition: .15s; user-select: none;
  }
  .btn:hover { background: var(--bg-card-h); border-color: var(--border-s); }
  .btn:active { transform: translateY(1px); }
  .btn.primary { background: linear-gradient(135deg, var(--accent), var(--accent-d)); border-color: transparent; color: #fff; }
  .btn.primary:hover { filter: brightness(1.08); }
  .btn:disabled { opacity: .5; cursor: not-allowed; }
  .btn.sm { height: 32px; padding: 0 12px; font-size: 12.5px; }

  /* Tabs */
  .tabs {
    flex: 0 0 auto;
    display: flex; align-items: center; gap: 6px;
    padding: 8px 14px; overflow-x: auto;
    background: var(--bg-soft); border-bottom: 1px solid var(--border);
  }
  .tabs::-webkit-scrollbar { height: 6px; }
  .tab {
    flex: 0 0 auto; height: 32px; padding: 0 13px;
    display: inline-flex; align-items: center; gap: 6px;
    background: transparent; color: var(--text-dim);
    border: 1px solid transparent; border-radius: 8px;
    font-size: 12.5px; font-weight: 600; cursor: pointer; transition: .15s; white-space: nowrap;
  }
  .tab:hover { background: var(--bg-card); color: var(--text); }
  .tab.active { background: var(--bg-card-h); color: var(--text); border-color: var(--border-s); box-shadow: inset 0 -2px 0 var(--accent); }
  .tab .count { font-size: 11px; color: var(--text-mute); background: var(--bg); padding: 1px 7px; border-radius: 10px; }
  .tab.active .count { color: var(--accent-2); }

  /* Main panes */
  .main { flex: 1 1 auto; display: flex; min-height: 0; }
  .pane-list { flex: 3 1 0; min-width: 0; display: flex; flex-direction: column; border-right: 1px solid var(--border); }
  .pane-detail { flex: 2 1 0; min-width: 0; display: flex; flex-direction: column; background: var(--bg); }

  .list-head {
    flex: 0 0 auto; height: 38px; padding: 0 16px;
    display: flex; align-items: center; justify-content: space-between;
    color: var(--text-dim); font-size: 12px; font-weight: 600;
    border-bottom: 1px solid var(--border); text-transform: uppercase; letter-spacing: .6px;
  }
  .list-scroll { flex: 1 1 auto; overflow-y: auto; padding: 10px; }

  .card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius-s); padding: 11px 13px; margin-bottom: 8px;
    cursor: pointer; transition: .12s; position: relative;
  }
  .card:hover { background: var(--bg-card-h); border-color: var(--border-s); transform: translateY(-1px); }
  .card.selected { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), 0 6px 18px rgba(59,130,246,.18); }
  .card .ct { display: flex; align-items: flex-start; gap: 9px; }
  .card .badge {
    flex: 0 0 auto; width: 26px; height: 26px; border-radius: 7px;
    display: grid; place-items: center; font-size: 13px;
    background: var(--bg-soft); border: 1px solid var(--border);
  }
  .card .body { min-width: 0; flex: 1 1 auto; }
  .card .title { font-size: 13.5px; font-weight: 600; line-height: 1.35; color: var(--text); margin: 0; }
  .card .meta { margin-top: 5px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 11.5px; color: var(--text-mute); }
  .card .meta .src { color: var(--text-dim); font-weight: 600; }
  .card .meta .pill { background: var(--bg-soft); border: 1px solid var(--border); padding: 1px 7px; border-radius: 10px; }

  .empty { text-align: center; color: var(--text-mute); padding: 60px 20px; font-size: 15px; }
  .empty .big { font-size: 40px; display: block; margin-bottom: 10px; opacity: .6; }

  /* Detail */
  .detail-scroll { flex: 1 1 auto; overflow-y: auto; padding: 22px 24px; }
  .detail-empty { height: 100%; display: grid; place-items: center; color: var(--text-mute); text-align: center; }
  .detail-empty .big { font-size: 44px; opacity: .5; margin-bottom: 12px; }
  .detail h1 { font-size: 20px; line-height: 1.3; margin: 0 0 12px; font-weight: 700; }
  .detail .dmeta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
  .detail .chip { font-size: 11.5px; padding: 3px 10px; border-radius: 12px; background: var(--bg-soft); border: 1px solid var(--border); color: var(--text-dim); display: inline-flex; align-items: center; gap: 5px; }
  .detail .chip.accent { color: var(--accent-2); border-color: rgba(59,130,246,.4); background: rgba(59,130,246,.08); }
  .detail .chip.danger { color: #fca5a5; border-color: rgba(239,68,68,.4); background: rgba(239,68,68,.08); }
  .detail .desc { color: var(--text-dim); line-height: 1.6; font-size: 13.5px; margin: 0 0 18px; }
  .detail .url { font-family: var(--mono); font-size: 11.5px; color: var(--accent-2); word-break: break-all; background: var(--bg-soft); border: 1px solid var(--border); padding: 8px 10px; border-radius: 8px; margin-bottom: 18px; }
  .detail .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .detail .actions .btn { width: 100%; justify-content: center; }

  /* Status bar */
  .statusbar {
    flex: 0 0 auto; height: 34px; display: flex; align-items: center; gap: 14px;
    padding: 0 16px; background: var(--bg-soft); border-top: 1px solid var(--border);
    font-size: 12px; color: var(--text-dim);
  }
  .statusbar .st { flex: 1 1 auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .progress { flex: 0 0 auto; width: 200px; height: 6px; background: var(--bg); border-radius: 6px; overflow: hidden; }
  .progress .bar { height: 100%; width: 0%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); transition: width .25s ease; }
  .progress.done .bar { background: linear-gradient(90deg, var(--ok), #4ade80); }

  /* Loading overlay for exports */
  .toast {
    position: fixed; bottom: 50px; left: 50%; transform: translateX(-50%) translateY(20px);
    background: var(--bg-card); border: 1px solid var(--border-s); color: var(--text);
    padding: 10px 18px; border-radius: 10px; box-shadow: var(--shadow); font-size: 13px;
    opacity: 0; pointer-events: none; transition: .25s; z-index: 50; display: flex; align-items: center; gap: 9px;
  }
  .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
  .toast.ok { border-color: rgba(34,197,94,.5); }
  .toast.err { border-color: rgba(239,68,68,.5); }

  .skel { background: linear-gradient(90deg, var(--bg-card) 25%, var(--bg-card-h) 37%, var(--bg-card) 63%); background-size: 400% 100%; animation: sk 1.3s infinite; border-radius: 8px; }
  @keyframes sk { 0%{background-position:100% 50%} 100%{background-position:0 50%} }
  .skel-card { height: 62px; margin-bottom: 8px; }
</style>
</head>
<body>
  <div class="topbar">
    <div class="brand">
      <div class="logo">🚀</div>
      <span>Tech News Aggregator <span class="ver">v3.1</span></span>
    </div>
    <div class="spacer"></div>
    <div class="search">
      <span class="ico">🔍</span>
      <input id="search" type="text" placeholder="Search stories..." />
    </div>
    <button class="btn primary" id="refresh">🔄 Refresh</button>
  </div>

  <div class="tabs" id="tabs"></div>

  <div class="main">
    <div class="pane-list">
      <div class="list-head">
        <span id="list-title">All Stories</span>
        <span id="list-count">0</span>
      </div>
      <div class="list-scroll" id="list"></div>
    </div>
    <div class="pane-detail">
      <div class="detail-scroll" id="detail">
        <div class="detail-empty">
          <div>
            <div class="big">👈</div>
            <div>Select a story to view details</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="statusbar">
    <div class="st" id="status">⏳ Initializing...</div>
    <div class="progress" id="progress"><div class="bar" id="bar"></div></div>
  </div>

  <div class="toast" id="toast"></div>

<script>
  // ---- Source metadata (mirrors Python SOURCE_ORDER) ----
  const SOURCES = [
    {key:"all",            label:"All",          icon:"📌"},
    {key:"hacker_news",    label:"Hacker News",  icon:"🟧", color:"#ff6600"},
    {key:"github",         label:"GitHub",       icon:"🐙", color:"#ffffff"},
    {key:"lobsters",       label:"Lobsters",     icon:"🦞", color:"#ac130d"},
    {key:"company_blogs",  label:"Company Blog", icon:"🏢", color:"#3b82f6"},
    {key:"cve_security",   label:"CVE Security", icon:"🛡️", color:"#ef4444"},
    {key:"stackoverflow",  label:"Stack Overflow",icon:"💬", color:"#f48024"},
    {key:"youtube_news",   label:"YouTube",      icon:"📺", color:"#ff0000"},
    {key:"x",              label:"X (Twitter)",  icon:"🐦", color:"#1d9bf0"},
  ];
  const SRC_MAP = Object.fromEntries(SOURCES.map(s => [s.key, s]));

  const state = {
    all: [],            // every story, each tagged with _source_key
    bySrc: {},          // key -> [stories]
    counts: {},         // key -> count
    filter: "all",
    query: "",
    selected: null,
    fetching: false,
  };

  // ---- DOM ----
  const $ = id => document.getElementById(id);
  const tabsEl = $("tabs"), listEl = $("list"), detailEl = $("detail");
  const statusEl = $("status"), barEl = $("bar"), progressEl = $("progress");
  const searchEl = $("search"), refreshEl = $("refresh");
  const listTitleEl = $("list-title"), listCountEl = $("list-count");
  const toastEl = $("toast");

  // ---- Tabs ----
  function renderTabs() {
    tabsEl.innerHTML = "";
    SOURCES.forEach(s => {
      const t = document.createElement("button");
      t.className = "tab" + (s.key === state.filter ? " active" : "");
      const cnt = s.key === "all" ? state.all.length : (state.counts[s.key] || 0);
      t.innerHTML = `<span>${s.icon} ${s.label}</span>` +
        (cnt > 0 ? `<span class="count">${cnt}</span>` : "");
      t.onclick = () => { state.filter = s.key; renderTabs(); renderList(); };
      tabsEl.appendChild(t);
    });
  }

  // ---- Helpers ----
  function metaFor(story) {
    const k = story._source_key;
    switch (k) {
      case "hacker_news": return {main: `⬆️ ${story.score||0}`, sub: `💬 ${story.comments||0}`};
      case "lobsters":    return {main: `⬆️ ${story.score||0}`, sub: ""};
      case "github":      return {main: `⭐ ${(story.stars||0).toLocaleString()}`, sub: story.language ? `💻 ${story.language}` : ""};
      case "cve_security":return {main: `⚠️ CVSS ${story.cvss||"-"}`, sub: story.cve_id || ""};
      case "company_blogs":return {main: story.company || "", sub: ""};
      case "youtube_news":return {main: story.channel || "", sub: ""};
      case "x":           return {main: story.author ? `👤 ${story.author}` : "", sub: ""};
      default:            return {main: "", sub: ""};
    }
  }
  function filtered() {
    let arr = state.filter === "all"
      ? state.all
      : state.all.filter(s => s._source_key === state.filter);
    const q = state.query;
    if (q) {
      arr = arr.filter(s =>
        (s.title||"").toLowerCase().includes(q) ||
        (s.description||"").toLowerCase().includes(q) ||
        (s.snippet||"").toLowerCase().includes(q));
    }
    return arr;
  }

  // ---- List ----
  function renderList() {
    const src = SOURCES.find(s => s.key === state.filter);
    listTitleEl.textContent = src ? `${src.icon} ${src.label}` : "Stories";
    const arr = filtered();
    listCountEl.textContent = arr.length;

    if (state.fetching && state.all.length === 0) {
      listEl.innerHTML = Array.from({length: 6})
        .map(() => `<div class="skel skel-card"></div>`).join("");
      return;
    }
    if (arr.length === 0) {
      listEl.innerHTML = `<div class="empty"><span class="big">📭</span>No stories found</div>`;
      return;
    }
    listEl.innerHTML = "";
    arr.forEach(story => {
      const s = SRC_MAP[story._source_key] || {icon:"📰", color:"#888"};
      const m = metaFor(story);
      const card = document.createElement("div");
      card.className = "card" + (state.selected === story ? " selected" : "");
      card.innerHTML = `
        <div class="ct">
          <div class="badge" style="color:${s.color}">${s.icon}</div>
          <div class="body">
            <div class="title">${escapeHtml((story.title||"Untitled").slice(0,120))}</div>
            <div class="meta">
              <span class="src">${s.label}</span>
              ${m.main ? `<span class="pill">${escapeHtml(m.main)}</span>` : ""}
              ${m.sub  ? `<span class="pill">${escapeHtml(m.sub)}</span>`  : ""}
              ${story.time_ago ? `<span>${escapeHtml(story.time_ago)}</span>` : ""}
            </div>
          </div>
        </div>`;
      card.onclick = () => { state.selected = story; renderList(); renderDetail(story); };
      listEl.appendChild(card);
    });
  }

  // ---- Detail ----
  function renderDetail(story) {
    const s = SRC_MAP[story._source_key] || {icon:"📰", color:"#888", label:story._source_key};
    const m = metaFor(story);
    const desc = story.description || story.snippet || "";
    const url = story.url || "";
    const chips = [`<span class="chip accent">${s.icon} ${s.label}</span>`];
    if (story.time_ago) chips.push(`<span class="chip">📅 ${escapeHtml(story.time_ago)}</span>`);
    if (story.published) chips.push(`<span class="chip">📅 ${escapeHtml(String(story.published).slice(0,16))}</span>`);
    if (m.main) chips.push(`<span class="chip">${escapeHtml(m.main)}</span>`);
    if (m.sub)  chips.push(`<span class="chip">${escapeHtml(m.sub)}</span>`);
    if (s.key === "cve_security") chips.push(`<span class="chip danger">⚠️ Security</span>`);

    detailEl.innerHTML = `
      <h1>${escapeHtml(story.title || "Untitled")}</h1>
      <div class="dmeta">${chips.join("")}</div>
      ${desc ? `<p class="desc">${escapeHtml(desc)}</p>` : ""}
      ${url ? `<div class="url">🔗 ${escapeHtml(url)}</div>` : ""}
      <div class="actions">
        ${url ? `<button class="btn primary" id="act-open">🔗 Open Link</button>` : `<span></span>`}
        <button class="btn" id="act-pdf">📄 Export PDF</button>
        <button class="btn" id="act-post">📱 Telegram Post</button>
        <button class="btn" id="act-image">📸 Card Image</button>
      </div>`;
    const ob = $("act-open"); if (ob) ob.onclick = () => pywebview.api.open_url(url);
    $("act-pdf").onclick   = () => pywebview.api.export_pdf();
    $("act-post").onclick  = () => pywebview.api.export_social(false);
    $("act-image").onclick = () => pywebview.api.export_social(true);
  }

  // ---- Status / progress / toast ----
  function setStatus(txt) { statusEl.textContent = txt; }
  function setProgress(p, done) {
    barEl.style.width = Math.round(p*100) + "%";
    progressEl.classList.toggle("done", !!done);
  }
  let toastTimer = null;
  function toast(msg, kind) {
    toastEl.className = "toast show" + (kind ? " " + kind : "");
    toastEl.textContent = msg;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.className = "toast"; }, 3500);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }

  // ---- Events ----
  let searchTimer = null;
  searchEl.oninput = () => {
    state.query = searchEl.value.trim().toLowerCase();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(renderList, 120);
  };
  refreshEl.onclick = () => { if (!state.fetching) pywebview.api.fetch_news(); };

  // ---- Callbacks from Python ----
  window.js_on_source_done = function(key, count, completed, total) {
    state.counts[key] = count;
    setProgress(completed / total, false);
    setStatus(`⏳ Fetched ${SRC_MAP[key]?.label || key}... (${completed}/${total})`);
    renderTabs();
  };
  window.js_on_all_done = function(payload) {
    state.fetching = false;
    state.all = payload.stories || [];
    state.counts = payload.counts || {};
    setProgress(1, true);
    const total = state.all.length;
    const parts = SOURCES.filter(s => s.key !== "all")
      .filter(s => state.counts[s.key] > 0)
      .map(s => `${s.label}:${state.counts[s.key]}`);
    setStatus(`✅ ${total} stories | ${parts.join(" | ")}`);
    renderTabs(); renderList();
    refreshEl.disabled = false;
  };
  window.js_status = function(msg, kind) {
    setStatus(msg);
    toast(msg, kind);
  };

  // ---- Boot ----
  function start() {
    state.fetching = true;
    refreshEl.disabled = true;
    setStatus("⏳ Fetching news from all sources...");
    setProgress(0, false);
    renderTabs(); renderList();
    pywebview.api.fetch_news();
  }
  window.addEventListener("pywebviewready", start);
</script>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────────
# Python <-> JS bridge
# ──────────────────────────────────────────────────────────────────────────

class _Api:
    """JS-exposed API. Methods are callable from the frontend as
    `pywebview.api.<method>(...)` and may return JSON-serialisable values."""

    def __init__(self, search_key: str | None):
        # NOTE: pywebview's JS bridge (webview/util.py:get_functions) walks every
        # public attribute of the js_api object via dir()/getattr and recurses
        # into non-callable members. If `window` (whose `.native` is the WinForms
        # Form, a .NET object) is exposed publicly, pythonnet recurses infinitely
        # through `native.AccessibilityObject.Bounds.Empty.Empty.Empty...`
        # (System.Drawing.Rectangle.Empty returns a Rectangle with its own .Empty).
        # The introspector skips any attribute whose name starts with '_', so all
        # non-API members here are underscore-prefixed.
        self.search_key = search_key
        self._aggregator = TechNewsAggregator(search_key=search_key)
        self._window = None  # set before webview.start()
        self._results: dict[str, list[dict]] = {}
        self._counts: dict[str, int] = {}

    # ── helpers ────────────────────────────────────────────────────────────
    def _js(self, expr: str) -> None:
        if self._window:
            try:
                self._window.evaluate_js(expr)
            except Exception as e:  # pragma: no cover - defensive
                from ..core.config import logger
                logger.error(f"GUI: evaluate_js failed: {e}")

    def _status(self, msg: str, kind: str = "") -> None:
        kind_js = json.dumps(kind)
        msg_js = json.dumps(msg)
        self._js(f"window.js_status({msg_js}, {kind_js});")

    # ── exposed to JS ──────────────────────────────────────────────────────
    def fetch_news(self) -> None:
        """Fetch from all sources in a background thread, streaming progress
        back to the frontend via callbacks."""
        self._results = {}
        self._counts = {}
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

        total = len(SOURCE_ORDER) - 1  # exclude "all"
        completed = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_source, key, cls, self.search_key): key
                for key, _, cls in SOURCE_ORDER if cls is not None
            }
            for future in as_completed(futures):
                key, stories = future.result()
                self._results[key] = stories
                self._counts[key] = len(stories)
                completed += 1
                self._js(
                    f"window.js_on_source_done({json.dumps(key)},"
                    f"{len(stories)},{completed},{total});"
                )

        # Flatten + tag stories for the frontend.
        flat: list[dict] = []
        for key, _, _ in SOURCE_ORDER:
            if key == "all":
                continue
            for s in self._results.get(key, []):
                s["_source_key"] = key
                flat.append(s)

        payload = json.dumps({"stories": flat, "counts": self._counts},
                             ensure_ascii=False)
        self._js(f"window.js_on_all_done({payload});")

    def open_url(self, url: str) -> None:
        if url:
            webbrowser.open(url)

    def export_pdf(self) -> None:
        self._status("📄 Generating PDF...", "")
        threading.Thread(target=self._export_pdf_worker, daemon=True).start()

    def _export_pdf_worker(self) -> None:
        try:
            self._aggregator.results = self._results
            self._aggregator.stats = dict(self._counts)
            self._aggregator.stats["_duration"] = 0.0
            md_path = self._aggregator.generate_report()
            pdf_path = self._aggregator.export_pdf(md_path)
            self._status(f"✅ PDF saved: {pdf_path.name}", "ok")
        except Exception as e:
            self._status(f"❌ PDF error: {e}", "err")

    def export_social(self, image: bool) -> None:
        label = "📸 Generating image..." if image else "📱 Generating post..."
        self._status(label, "")
        threading.Thread(
            target=self._export_social_worker, args=(image,), daemon=True
        ).start()

    def _export_social_worker(self, image: bool) -> None:
        try:
            self._aggregator.results = self._results
            self._aggregator.stats = dict(self._counts)
            self._aggregator.stats["_duration"] = 0.0
            path = self._aggregator.export_social("telegram", image=image)
            kind = "Image" if image else "Post"
            self._status(f"✅ {kind} saved: {path.name}", "ok")
        except Exception as e:
            self._status(f"❌ Export error: {e}", "err")


# ──────────────────────────────────────────────────────────────────────────
# Public window class (same API as the old customtkinter GUI)
# ──────────────────────────────────────────────────────────────────────────

class TechNewsGUI:
    """pywebview-based desktop window for the Tech News Aggregator.

    Mirrors the previous customtkinter API:
        app = TechNewsGUI(search_key=...)
        app.mainloop()
    """

    def __init__(self, search_key: str | None = None):
        self.search_key = search_key
        self.api = _Api(search_key=search_key)
        self._window = None

    def mainloop(self) -> None:
        """Create the window and start the pywebview event loop (blocking)."""
        self._window = webview.create_window(
            title="🚀 Tech News Aggregator",
            html=_HTML,
            js_api=self.api,
            width=1280,
            height=820,
            min_size=(960, 640),
            text_select=True,
        )
        self.api._window = self._window
        webview.start(debug=False)
