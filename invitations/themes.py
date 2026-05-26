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
    # Design-system family. Drives the tonal-scale fallbacks in
    # _theme_head.html — the user's 4-color palette still overrides
    # the primary slots, but derived shades (surface-container-*, outline,
    # etc.) come from the family's design tokens so a Midnight template
    # rendered with a custom palette still feels coherent.
    family: str = "ethereal"


_THEMES: dict[str, Theme] = {
    Party.TemplateChoice.MINIMAL.value: Theme(
        slug=Party.TemplateChoice.MINIMAL.value,
        display_name="Modern Minimal",
        description="Airy, editorial layout with a single details block. "
        "Best when you want elegance with low text overhead.",
        template_path="invitations/themes/minimal.html",
        content_fields=(
            "hero_subtitle",
            "hero_image_url",
            "details_body",
            "details_image_url",
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
            "our_story_image_url",
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
            "hero_image_url",
            "our_story",
            "our_story_image_url",
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
    Party.TemplateChoice.MIDNIGHT_MINIMAL.value: Theme(
        slug=Party.TemplateChoice.MIDNIGHT_MINIMAL.value,
        display_name="Midnight Minimal",
        description="Editorial dark layout with navy hero and gold accents. "
        "Pairs naturally with the Midnight Garden palette.",
        template_path="invitations/themes/midnight_minimal.html",
        family="midnight",
        content_fields=(
            "hero_subtitle",
            "hero_image_url",
            "details_body",
            "details_image_url",
            "rsvp_deadline",
        ),
    ),
    Party.TemplateChoice.MIDNIGHT_ELEGANCE.value: Theme(
        slug=Party.TemplateChoice.MIDNIGHT_ELEGANCE.value,
        display_name="Midnight Elegance",
        description="Ornate dark theme with botanical hero, story panel, "
        "and structured ceremony / reception cards.",
        template_path="invitations/themes/midnight_elegance.html",
        family="midnight",
        content_fields=(
            "hero_subtitle",
            "hero_image_url",
            "our_story",
            "our_story_image_url",
            "ceremony_time",
            "ceremony_venue",
            "ceremony_address",
            "reception_time",
            "reception_venue",
            "reception_address",
            "rsvp_deadline",
        ),
    ),
    Party.TemplateChoice.MIDNIGHT_FLORAL.value: Theme(
        slug=Party.TemplateChoice.MIDNIGHT_FLORAL.value,
        display_name="Midnight Floral",
        description="Light hero with botanical motifs, deep navy details, "
        "and a gold-accented RSVP card.",
        template_path="invitations/themes/midnight_floral.html",
        family="midnight",
        content_fields=(
            "hero_subtitle",
            "hero_image_url",
            "our_story",
            "our_story_image_url",
            "ceremony_time",
            "ceremony_venue",
            "ceremony_address",
            "reception_time",
            "reception_venue",
            "reception_address",
            "lodging_info",
            "dress_code",
            "rsvp_deadline",
        ),
    ),
}


def get_theme(slug: str) -> Theme:
    """Return the Theme for a slug, falling back to Modern Minimal."""
    return _THEMES.get(slug, _THEMES[Party.TemplateChoice.MINIMAL.value])


def all_themes() -> tuple[Theme, ...]:
    return tuple(_THEMES.values())
