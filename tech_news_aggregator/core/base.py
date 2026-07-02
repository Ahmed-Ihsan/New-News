"""
الفئة الأساسية لمصادر الأخبار — Abstract Base Class.
NewsSource ABC: all source adapters inherit from this.
"""

from abc import ABC, abstractmethod


class NewsSource(ABC):
    """
    الفئة الأساسية المجردة لمصادر الأخبار.
    كل مصدر يجب أن يُورّث هذه الفئة ويُنفّذ fetch().

    Attributes:
        name: اسم المصدر للعرض في السجلات والتقارير.
        icon: أيقونة emoji للمصدر.
    """

    name: str = "Unknown"
    icon: str = "📰"

    @abstractmethod
    def fetch(self) -> list[dict]:
        """
        جلب الأخبار من المصدر.
        يعيد قائمة من القواميس (dict) — كل قاموس يمثل خبراً واحداً.
        """
        ...
