"""Template registry.

A single source of truth declaring each invitation template, the Django
template path that renders it, and which Party content fields it uses.

Used by:
- the Party creation wizard (to decide which extras to show in step 2)
- the public invitation view (to dispatch to the right theme)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from invitations.models import Party


@dataclass(frozen=True)
class Theme:
    slug: str
    display_name: str
    description: str
    template_path: str
    # Field names on Party that this theme uses for content (beyond the
    # always-required name/starts_at/location). The wizard collects these
    # in step 2.
    content_fields: Sequence[str] = field(default_factory=tuple)


_THEMES: dict[str, Theme] = {
    Party.TemplateChoice.MINIMAL.value: Theme(
        slug=Party.TemplateChoice.MINIMAL.value,
        display_name="Modern Minimal",
        description="Airy, editorial layout with a single details block. "
        "Best when you want elegance with low text overhead.",
        template_path="invitations/themes/minimal.html",
        content_fields=(
            "hero_subtitle",
            "details_body",
            "rsvp_deadline",
        ),
    ),
    Party.TemplateChoice.CLASSIC.value: Theme(
        slug=Party.TemplateChoice.CLASSIC.value,
        display_name="Classic Elegance",
        description="Traditional structure with 'Our Story' plus separate "
        "ceremony and reception cards.",
        template_path="invitations/themes/classic.html",
        content_fields=(
            "hero_subtitle",
            "our_story",
            "ceremony_time",
            "ceremony_venue",
            "ceremony_address",
            "reception_time",
            "reception_venue",
            "reception_address",
            "rsvp_deadline",
        ),
    ),
    Party.TemplateChoice.FLORAL.value: Theme(
        slug=Party.TemplateChoice.FLORAL.value,
        display_name="Romantic Floral",
        description="Ornate floral hero with 'Our Story' and three detail "
        "cards including lodging info.",
        template_path="invitations/themes/floral.html",
        content_fields=(
            "hero_subtitle",
            "our_story",
            "ceremony_time",
            "ceremony_venue",
            "ceremony_address",
            "reception_time",
            "reception_venue",
            "reception_address",
            "lodging_info",
            "rsvp_deadline",
        ),
    ),
}


def get_theme(slug: str) -> Theme:
    """Return the Theme for a slug, falling back to Modern Minimal."""
    return _THEMES.get(slug, _THEMES[Party.TemplateChoice.MINIMAL.value])


def all_themes() -> tuple[Theme, ...]:
    return tuple(_THEMES.values())
