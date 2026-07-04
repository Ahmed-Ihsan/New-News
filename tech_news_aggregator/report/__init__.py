"""
حزمة التقارير — تصدير مُولّد Markdown و PDF و Social.
Report package: exports MarkdownReportGenerator, export_to_pdf, SocialMediaAdapter.
"""

from .markdown import MarkdownReportGenerator
from .pdf_export import export_to_pdf
from .social_adapter import SocialMediaAdapter

__all__ = ["MarkdownReportGenerator", "export_to_pdf", "SocialMediaAdapter"]
