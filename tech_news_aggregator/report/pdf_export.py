"""
تصدير التقرير إلى PDF.
PDF export: converts Markdown to styled HTML then uses Edge headless to render PDF.
Supports RTL Arabic text perfectly via browser engine.
"""

import re
import subprocess
from pathlib import Path

from ..core.config import OUTPUT_DIR, logger


CSS = """
@page {
    size: A4;
    margin: 15mm 18mm;
}

body {
    font-family: "Segoe UI", "Tahoma", "Arial", sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1a1a2e;
    direction: rtl;
    text-align: right;
}

h1 {
    font-size: 22pt;
    color: #0f3460;
    text-align: center;
    border-bottom: 3px solid #e94560;
    padding-bottom: 10px;
    margin-bottom: 5px;
}

h2 {
    font-size: 16pt;
    color: #16213e;
    border-right: 4px solid #e94560;
    padding-right: 10px;
    margin-top: 28px;
    page-break-after: avoid;
}

h3 {
    font-size: 13pt;
    color: #0f3460;
    margin-top: 18px;
    page-break-after: avoid;
}

a {
    color: #0f3460;
    text-decoration: none;
    word-break: break-all;
}

blockquote {
    border-right: 3px solid #e94560;
    background: #f8f9fa;
    padding: 8px 15px;
    margin: 10px 0;
    color: #555;
    font-size: 10pt;
}

code {
    background: #f0f0f0;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
    color: #c0392b;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 10pt;
}

th {
    background: #16213e;
    color: white;
    padding: 8px 10px;
    text-align: right;
    font-weight: bold;
}

td {
    border: 1px solid #ddd;
    padding: 6px 10px;
    text-align: right;
}

tr:nth-child(even) {
    background: #f8f9fa;
}

tr {
    page-break-inside: avoid;
}

hr {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 20px 0;
}

strong {
    color: #16213e;
}

em {
    color: #555;
}
"""


def _clean_md(md_text: str) -> str:
    """تنظيف Markdown من العناصر التي تسبب مشاكل."""
    md_text = md_text.replace('<div align="center">', "")
    md_text = md_text.replace("</div>", "")
    md_text = re.sub(r"\u200b|\u200c|\u200d|\ufeff", "", md_text)
    return md_text


def _build_html(md_path: Path) -> Path:
    """تحويل Markdown إلى HTML منسّق وحفظه كملف مؤقت."""
    import markdown as md_lib

    md_text = md_path.read_text(encoding="utf-8")
    md_text = _clean_md(md_text)

    html_body = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )

    full_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<style>
{CSS}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    html_path = OUTPUT_DIR / (md_path.stem + "_temp.html")
    html_path.write_text(full_html, encoding="utf-8")
    return html_path


def _find_edge() -> str | None:
    """البحث عن متصفح Edge على النظام."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    import os
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def export_to_pdf(md_path: Path) -> Path:
    """تحويل ملف Markdown إلى PDF عبر متصفح Edge headless."""
    logger.info(f"PDF: جارٍ تحويل {md_path.name} إلى PDF...")

    pdf_filename = md_path.stem + ".pdf"
    pdf_path = OUTPUT_DIR / pdf_filename

    html_path = _build_html(md_path)

    try:
        edge = _find_edge()
        if not edge:
            raise RuntimeError("لم يتم العثور على Edge أو Chrome")

        cmd = [
            edge,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--print-to-pdf=" + str(pdf_path),
            "--print-to-pdf-no-header",
            str(html_path),
        ]
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)

        if not pdf_path.exists():
            raise RuntimeError("لم يتم إنشاء ملف PDF")

        logger.info(f"PDF: تم حفظ الملف: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.error(f" PDF: فشل إنشاء PDF: {e}")
        raise
    finally:
        html_path.unlink(missing_ok=True)
