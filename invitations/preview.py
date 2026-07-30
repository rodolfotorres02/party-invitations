"""Template preview — render every invitation theme with dummy data.

This lets a host browse the available templates and see exactly how each one
looks, fully populated, without first creating a real party. Nothing here
touches the database: the Party / Invitation / Palette objects are built
unsaved, purely to feed the same rendering context the public guest view uses
(see ``InvitationPublicView``), so previews stay pixel-accurate to the real
thing.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from invitations.forms import RSVPForm
from invitations.models import Invitation, Palette, Party
from invitations.services import PaletteNotFoundError, PaletteService
from invitations.themes import Theme, all_themes, get_theme


# A fixed future date keeps previews deterministic (no "today" drift) and lands
# on a Saturday evening — the natural slot for the kind of events these
# templates are for.
_DUMMY_STARTS_AT = timezone.make_aware(datetime(2026, 9, 12, 16, 30))

# Every content field the catalog knows about, filled in. Each theme only reads
# the subset listed in its ``content_fields``, so one superset dict covers them
# all. Image URLs are left blank on purpose: the themes fall back to tasteful,
# palette-aware icon placeholders, which always render (no external requests,
# no broken images in the preview).
_DUMMY_CONTENT: dict[str, object] = {
    "hero_subtitle": "Together with their families, invite you to celebrate",
    "rsvp_deadline": "2026-08-15",
    "details_body": (
        "Join us for an evening of dinner, dancing, and celebration as we "
        "begin this next chapter. Cocktails at six, supper to follow."
    ),
    "our_story": (
        "We met one rainy afternoon in a little bookshop, both reaching for "
        "the same worn copy of the same novel. Three years, two cities, and "
        "countless adventures later, we can't wait to celebrate with the "
        "people we love most."
    ),
    "ceremony_time": "4:30 PM",
    "ceremony_venue": "The Rose Garden Chapel",
    "ceremony_address": "120 Lakeview Drive, San Francisco, CA",
    "reception_time": "6:00 PM",
    "reception_venue": "The Grand Ballroom",
    "reception_address": "500 Market Street, San Francisco, CA",
    "lodging_info": (
        "A block of rooms is reserved at The Clift Royal Sonesta under "
        "\"Evelyn & James\". Mention the wedding for the group rate through "
        "August 1st."
    ),
    "dress_code": "Garden formal — light suits and flowing dresses encouraged.",
    "faq_q1": "May we take photos during the ceremony?",
    "faq_a1": (
        "We'd love for you to be fully present, so we're keeping the ceremony "
        "unplugged. Our photographer will capture every moment and share them "
        "with everyone afterward."
    ),
    "faq_q2": "What is the RSVP deadline?",
    "faq_a2": (
        "Kindly reply by August 15th so we can finalize the seating and menu."
    ),
    "faq_q3": "Can I bring my children?",
    "faq_a3": (
        "As much as we adore your little ones, this will be an adults-only "
        "celebration so everyone can relax and enjoy the evening."
    ),
    "faq_q4": "Will parking be available?",
    "faq_a4": (
        "Yes — complimentary valet parking is available at the reception "
        "venue, and there is street parking nearby."
    ),
    "cover_intro": "For you",
    "invite_body": (
        "we have the honor of inviting you to celebrate the sacrament of "
        "marriage with us."
    ),
    "dress_code_intro": (
        "We want everyone to feel comfortable and elegant celebrating with us."
    ),
    "dress_code_ladies": (
        "A long or midi dress in a soft, garden-friendly fabric. Block heels "
        "or wedges are your friend — part of the evening is on the lawn."
    ),
    "dress_code_gentlemen": (
        "A light suit with a tie, in beige, sand, sage, or soft blue. A linen "
        "jacket works beautifully for an afternoon ceremony."
    ),
    "dress_code_note": (
        "Please avoid white, beige, cream, ivory, champagne, and pink — those "
        "shades are reserved for the bridal party. Everything else is fair "
        "game, and we can't wait to see you."
    ),
    # Left blank on purpose, like the other image fields — the gallery must not
    # hotlink photos that could 404. Unlike the other image fields there is no
    # icon placeholder to fall back to (a photo collage has no tasteful
    # equivalent), so the theme drops the whole collage, heading included, and
    # the preview simply doesn't exercise that block.
    "dress_code_inspiration_urls": "",
    "gift_intro": (
        "It fills us with joy to share this day with you, surrounded by your "
        "affection. If you would like to honor us with a gift, here are a few "
        "ways to do it."
    ),
    "gift_accounts": (
        "Bank: Scotiabank\n"
        "Beneficiary: James Whitfield\n"
        "Account Type: Savings\n"
        "Account Number: 1234567890\n"
        "\n"
        "Bank: Banco Popular\n"
        "Beneficiary: Evelyn Marsh\n"
        "Account Type: Checking\n"
        "Account Number: 0987654321\n"
        "\n"
        "Zelle: 929-503-8010"
    ),
    "gift_closing": "Your presence will always be our greatest gift.",
    "hero_image_url": "",
    "our_story_image_url": "",
    "details_image_url": "",
    "monogram_image_url": "",
}


# Each design-system family previews against the seed palette it was designed
# for. Families absent here fall back to Ethereal Union (index 0), so adding a
# family without a matching seed palette degrades gracefully.
_FAMILY_SEED_INDEX: dict[str, int] = {
    "ethereal": 0,
    "midnight": 1,
    "garden": 2,
}


def _dummy_palette(theme: Theme) -> Palette:
    """An unsaved palette matching the theme's design-system family.

    Mirrors the seed palettes so dark ("midnight") themes preview against the
    navy/gold set, "garden" themes against the olive/rose set, and everything
    else against the sage/cream set.
    """
    spec = Palette.SEED_PALETTES[_FAMILY_SEED_INDEX.get(theme.family, 0)]
    return Palette(**spec)


def _resolve_palette(request: HttpRequest, theme: Theme) -> Palette:
    """Use a real palette of the host's when ``?palette=<id>`` is given and
    valid; otherwise fall back to the theme family's seed palette."""
    palette_id = request.GET.get("palette")
    if palette_id:
        try:
            return PaletteService().get_for_host(int(palette_id), request.user)
        except (ValueError, PaletteNotFoundError):
            # Non-numeric id, or a palette that isn't this host's → fall back.
            pass
    return _dummy_palette(theme)


def _dummy_party(theme: Theme, palette: Palette) -> Party:
    return Party(
        name="Evelyn & James",
        description="We're getting married, and we'd love for you to be there.",
        location="The Grand Ballroom, San Francisco",
        starts_at=_DUMMY_STARTS_AT,
        template_choice=theme.slug,
        palette=palette,
        theme_content=dict(_DUMMY_CONTENT),
    )


def _dummy_invitation(party: Party) -> Invitation:
    # ``token`` defaults to a fresh uuid at construction, so ``{% url
    # 'rsvp_submit' invitation.token %}`` reverses cleanly inside the themes.
    return Invitation(
        party=party,
        label="The Smiths",
        num_guests=2,
        message=(
            "We're so happy to share this day with you — it wouldn't be the "
            "same without you there!"
        ),
        language="en",
        token=uuid.uuid4(),
    )


class TemplatePreviewView(LoginRequiredMixin, View):
    """Render a single theme, full-page, with dummy data.

    Output is byte-for-byte the theme a guest would see — no preview chrome is
    injected — so it doubles as a faithful "open in new tab" preview.
    """

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        theme = get_theme(slug)
        if theme.slug != slug:
            # get_theme falls back to Minimal for unknown slugs; reject those
            # so a bad URL 404s instead of silently previewing the wrong theme.
            raise Http404(f"Unknown template '{slug}'.")
        palette = _resolve_palette(request, theme)
        party = _dummy_party(theme, palette)
        invitation = _dummy_invitation(party)
        return render(
            request,
            theme.template_path,
            {
                "invitation": invitation,
                "party": party,
                "content": party.content_for_display(),
                "palette": palette,
                "theme": theme,
                "rsvp": None,
                # num_guests, or the seat dropdown previews with a single
                # option while the line under it offers the dummy's two.
                "form": RSVPForm(num_guests=invitation.num_guests),
                "is_preview": True,
            },
        )


class TemplateGalleryView(LoginRequiredMixin, View):
    """Grid of live, scaled-down previews — one card per template."""

    def get(self, request: HttpRequest) -> HttpResponse:
        palettes = PaletteService().list_for_host(request.user)
        selected_id = request.GET.get("palette") or ""
        # Preserve the chosen palette in each preview iframe's query string.
        query = f"?palette={selected_id}" if selected_id else ""
        return render(
            request,
            "invitations/template_gallery.html",
            {
                "themes": all_themes(),
                "palettes": palettes,
                "selected_palette_id": selected_id,
                "preview_query": query,
            },
        )
