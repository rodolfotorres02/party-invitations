"""Template filters shared by the invitation themes."""
from __future__ import annotations

import re
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


# The hero title is one free-text field ("Gabriela & Jairo"), but the wreath
# theme stacks the two halves as separate script lines with the joiner set in
# its own color. Alternation order is irrelevant here — `re.search` returns the
# leftmost match, which is exactly the "first separator" rule we want. The word
# forms are wrapped in \s+ so a name like "Yara" or "Andrea" can't be split.
_COUPLE_SEPARATOR = re.compile(r"\s*&\s*|\s+y\s+|\s+and\s+", re.IGNORECASE)


@register.filter
def couple_names(value: Any) -> dict[str, str]:
    """Split a hero title into its two halves for the stacked script layout.

    Splits on the first ``&``, `` y `` or `` and `` and returns
    ``{"first", "second", "separator"}``. When there is no separator (a solo
    host, a birthday, a party name) ``second`` and ``separator`` come back
    empty so the theme can fall back to rendering one line.
    """
    text = str(value or "").strip()
    if not text:
        return {"first": "", "second": "", "separator": ""}

    match = _COUPLE_SEPARATOR.search(text)
    if match is None:
        return {"first": text, "second": "", "separator": ""}

    return {
        "first": text[: match.start()].strip(),
        "second": text[match.end():].strip(),
        "separator": match.group(0).strip(),
    }


@register.filter
def url_list(value: Any) -> list[str]:
    """Split newline- and/or comma-separated text into a list of image URLs.

    SECURITY: the ``http://`` / ``https://`` allow-list is a control, not a
    convenience. These values are host-supplied and land straight in an
    ``<img src>``, so anything else — ``javascript:``, ``data:``, a bare
    fragment — is dropped rather than rendered. Order is preserved so the
    collage matches what the host typed.
    """
    text = str(value or "")
    if not text.strip():
        return []

    urls: list[str] = []
    for chunk in re.split(r"[\r\n,]+", text):
        candidate = chunk.strip()
        # URL schemes are case-insensitive, so a host who typed "HTTPS://…"
        # should not have their image silently dropped. Match on a lowercased
        # copy but keep the original casing — the path may be case-sensitive.
        if candidate.lower().startswith(("http://", "https://")):
            urls.append(candidate)
    return urls


@register.filter
def detail_blocks(value: Any) -> list[list[dict[str, str]]]:
    """Parse blank-line-separated blocks of ``Label: Value`` lines.

    Used for the gift/registry accounts, where each bank is its own block of
    labelled lines. Returns one inner list per block, each item being
    ``{"label", "value"}``; a line without a colon becomes a label-less value
    so free-form lines ("Zelle: …" vs. a bare phone number) still render.
    Empty blocks are skipped.
    """
    text = str(value or "")
    if not text.strip():
        return []

    blocks: list[list[dict[str, str]]] = []
    # A "blank" separator line may still carry stray spaces, so tolerate them.
    for raw_block in re.split(r"(?:\r?\n[ \t]*){2,}", text):
        rows: list[dict[str, str]] = []
        for raw_line in raw_block.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            label, sep, detail = line.partition(":")
            if sep:
                rows.append({"label": label.strip(), "value": detail.strip()})
            else:
                rows.append({"label": "", "value": line})
        if rows:
            blocks.append(rows)
    return blocks
