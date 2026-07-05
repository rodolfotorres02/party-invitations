"""Template filters shared by the invitation themes."""
from __future__ import annotations

from typing import Any

from django import template

from invitations.themes import FAQ_MAX_ITEMS

register = template.Library()


@register.filter
def faq_pairs(content: Any) -> list[dict[str, str]]:
    """Collect populated FAQ question/answer pairs from a theme_content dict.

    Reads the discrete ``faq_q1``/``faq_a1`` … ``faq_q{FAQ_MAX_ITEMS}`` slots
    the wizard stores and returns ``[{"question", "answer"}]`` for every slot
    with a non-blank question (a blank answer is allowed but rare). Blank and
    missing slots are skipped, so the theme renders exactly the pairs the host
    filled in — in slot order.
    """
    if not hasattr(content, "get"):
        return []

    pairs: list[dict[str, str]] = []
    for i in range(1, FAQ_MAX_ITEMS + 1):
        question = str(content.get(f"faq_q{i}") or "").strip()
        if not question:
            continue
        answer = str(content.get(f"faq_a{i}") or "").strip()
        pairs.append({"question": question, "answer": answer})
    return pairs
