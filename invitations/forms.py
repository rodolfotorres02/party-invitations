"""Form definitions for the invitations app."""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from django import forms
from django.contrib.auth.models import AbstractBaseUser

from invitations.models import Invitation, RSVP, Palette, Party
from invitations.themes import (
    FAQ_CONTENT_FIELDS,
    FAQ_MAX_ITEMS,
    all_themes,
    get_theme,
)


# --- Field catalog for the wizard's extras step -----------------------------
#
# Maps the Party model's theme content fields to their form-field constructors.
# Each entry is "field_name → callable producing a forms.Field". The extras
# form picks a subset based on the selected theme's `content_fields`.

_EXTRAS_FIELD_CATALOG: dict[str, Any] = {
    "hero_subtitle": lambda: forms.CharField(
        max_length=300,
        required=False,
        label="Hero subtitle",
        help_text="Italic intro line under the hero title.",
    ),
    "rsvp_deadline": lambda: forms.DateField(
        required=False,
        label="RSVP deadline",
        widget=forms.DateInput(attrs={"type": "date"}),
    ),
    "details_body": lambda: forms.CharField(
        required=False,
        label="Details body",
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="The single block of details copy for this template.",
    ),
    "our_story": lambda: forms.CharField(
        required=False,
        label="Our Story",
        widget=forms.Textarea(attrs={"rows": 6}),
    ),
    "ceremony_time": lambda: forms.CharField(
        max_length=200, required=False, label="Ceremony time"
    ),
    "ceremony_venue": lambda: forms.CharField(
        max_length=200, required=False, label="Ceremony venue"
    ),
    "ceremony_address": lambda: forms.CharField(
        max_length=300, required=False, label="Ceremony address"
    ),
    "reception_time": lambda: forms.CharField(
        max_length=200, required=False, label="Reception time"
    ),
    "reception_venue": lambda: forms.CharField(
        max_length=200, required=False, label="Reception venue"
    ),
    "reception_address": lambda: forms.CharField(
        max_length=300, required=False, label="Reception address"
    ),
    "lodging_info": lambda: forms.CharField(
        required=False,
        label="Lodging info",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Hotel block, recommended accommodations, etc.",
    ),
    "dress_code": lambda: forms.CharField(
        max_length=200,
        required=False,
        label="Dress code",
        help_text="e.g. 'Black tie', 'Garden formal'.",
    ),
    "hero_image_url": lambda: forms.URLField(
        required=False,
        label="Hero image URL",
        help_text="Any public image URL (Imgur, Cloudinary, etc.). Blank = use a decorative icon.",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    ),
    "our_story_image_url": lambda: forms.URLField(
        required=False,
        label="Our Story image URL",
        help_text="Photo shown alongside the story text.",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    ),
    "details_image_url": lambda: forms.URLField(
        required=False,
        label="Details image URL",
        help_text="Side photo in the details block.",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    ),
    "cover_intro": lambda: forms.CharField(
        max_length=120,
        required=False,
        label="Cover intro",
        help_text="Tiny line above the guest's name on the cover, e.g. 'For you'.",
    ),
    # The three artwork slots below all ship with bundled defaults (the
    # watercolor set in invitations/static/invitations/wildflower/), so every
    # one of them is an override rather than a requirement — blank means "use
    # the artwork that comes with the template".
    "monogram_image_url": lambda: forms.URLField(
        required=False,
        label="Monogram / logo image URL",
        help_text="Your own monogram artwork, shown on the cover. "
        "Blank = the template's monogram.",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    ),
    "wreath_image_url": lambda: forms.URLField(
        required=False,
        label="Wreath image URL",
        help_text="The floral frame around the invitation. Use a PNG or WebP "
        "with a transparent middle. Blank = the template's wreath.",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    ),
    "sprig_image_url": lambda: forms.URLField(
        required=False,
        label="Corner sprig image URL",
        help_text="Replaces all four corner sprigs with one image of your own "
        "(the template otherwise varies three). Transparent background. "
        "Blank = the template's sprigs.",
        widget=forms.URLInput(attrs={"placeholder": "https://…"}),
    ),
    "invite_body": lambda: forms.CharField(
        required=False,
        label="Invitation body",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="The sentence that follows the names, e.g. 'we have the "
        "honor of inviting you…'.",
    ),
    "dress_code_intro": lambda: forms.CharField(
        required=False,
        label="Dress code intro",
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="One line setting the tone before the per-guest guidance.",
    ),
    "dress_code_ladies": lambda: forms.CharField(
        required=False,
        label="For the ladies",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Guidance for women — lengths, fabrics, shoes.",
    ),
    "dress_code_gentlemen": lambda: forms.CharField(
        required=False,
        label="For the gentlemen",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Guidance for men — suits, colors, ties.",
    ),
    "dress_code_note": lambda: forms.CharField(
        required=False,
        label="Dress code note",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Anything to avoid — reserved colors, footwear, etc.",
    ),
    "dress_code_inspiration_urls": lambda: forms.CharField(
        required=False,
        label="Inspiration photos",
        widget=forms.Textarea(
            attrs={"rows": 6, "placeholder": "https://…\nhttps://…"}
        ),
        help_text="One image URL per line. They fill the inspiration collage "
        "in order; blank = no collage.",
    ),
    "gift_intro": lambda: forms.CharField(
        required=False,
        label="Gift intro",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="How to phrase the ask before listing where to send a gift.",
    ),
    "gift_accounts": lambda: forms.CharField(
        required=False,
        label="Gift accounts",
        widget=forms.Textarea(attrs={"rows": 10}),
        help_text="One 'Label: Value' per line (e.g. 'Bank: Scotiabank'). "
        "Separate each account with a blank line to start a new block.",
    ),
    "gift_closing": lambda: forms.CharField(
        max_length=300,
        required=False,
        label="Gift closing",
        help_text="The reassuring last word, e.g. 'Your presence is our "
        "greatest gift.'",
    ),
}


# The FAQ is a fixed set of discrete question/answer slots — each its own plain
# field so it flows through the same catalog / grouped-form machinery as every
# other extra. Generated from FAQ_MAX_ITEMS (themes.py) so the count lives in
# one place. `n=n` binds the slot number into each no-arg factory.
def _faq_field_factories(n: int) -> tuple[Any, Any]:
    question = lambda n=n: forms.CharField(
        max_length=200,
        required=False,
        label=f"Question {n}",
        widget=forms.TextInput(
            attrs={"placeholder": "e.g. Can I bring my children?"}
        ),
    )
    answer = lambda n=n: forms.CharField(
        required=False,
        label=f"Answer {n}",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    return question, answer


for _i in range(1, FAQ_MAX_ITEMS + 1):
    _EXTRAS_FIELD_CATALOG[f"faq_q{_i}"], _EXTRAS_FIELD_CATALOG[f"faq_a{_i}"] = (
        _faq_field_factories(_i)
    )


def _palette_choices(host: AbstractBaseUser) -> Sequence[tuple[str, str]]:
    return [(str(p.pk), p.name) for p in Palette.objects.filter(host_id=host.pk)]


class PartyForm(forms.Form):
    """Step 1 of the create/edit wizard: basics + template + palette."""

    name = forms.CharField(
        max_length=200,
        label="Hero title",
        help_text="Displayed prominently on the invitation, e.g. 'Evelyn & James'.",
    )
    location = forms.CharField(max_length=300)
    starts_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )
    description = forms.CharField(widget=forms.Textarea, required=False)
    template_choice = forms.ChoiceField(
        choices=Party.TemplateChoice.choices,
        label="Invitation template",
        widget=forms.RadioSelect,
        initial=Party.TemplateChoice.MINIMAL.value,
    )
    palette = forms.ChoiceField(
        choices=(), label="Color palette", required=True
    )

    def __init__(self, *args: Any, host: AbstractBaseUser, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["palette"].choices = _palette_choices(host)


# Visual grouping of the extras form. The wizard renders one card per group
# that has at least one field present.
_EXTRAS_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Cover", "The first thing a guest sees, before the invitation itself.",
     ("cover_intro", "monogram_image_url")),
    ("Artwork", "Swap the template's illustrations for your own. Every field "
     "is optional — leave one blank to keep the bundled artwork.",
     ("wreath_image_url", "sprig_image_url")),
    ("Hero & timing", "Top of the invitation.",
     ("hero_subtitle", "invite_body", "hero_image_url", "rsvp_deadline")),
    ("Story", "A short paragraph about the occasion, with an optional photo.",
     ("our_story", "our_story_image_url", "details_body", "details_image_url")),
    ("Ceremony", "The main event.",
     ("ceremony_time", "ceremony_venue", "ceremony_address")),
    ("Reception", "Where the celebration continues.",
     ("reception_time", "reception_venue", "reception_address")),
    ("Lodging", "Hotels, accommodations, travel info.",
     ("lodging_info",)),
    ("Etiquette", "Optional notes for guests.",
     ("dress_code", "dress_code_intro", "dress_code_ladies",
      "dress_code_gentlemen", "dress_code_note",
      "dress_code_inspiration_urls")),
    ("Gifts", "Where to send a gift, if guests ask.",
     ("gift_intro", "gift_accounts", "gift_closing")),
    ("Questions & Answers",
     "Answer common guest questions — parking, kids, photos, dress code. "
     "Fill in as many pairs as you need; leave the rest blank.",
     FAQ_CONTENT_FIELDS),
)


class PartyExtrasForm(forms.Form):
    """Step 2 of the wizard: theme-specific content fields.

    Built dynamically from the chosen theme's `content_fields` list.
    """

    def __init__(
        self,
        *args: Any,
        template_slug: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._field_names: list[str] = []
        for field_name in get_theme(template_slug).content_fields:
            factory = _EXTRAS_FIELD_CATALOG.get(field_name)
            if factory is None:
                continue
            self.fields[field_name] = factory()
            self._field_names.append(field_name)

    @property
    def field_names(self) -> Iterable[str]:
        return iter(self._field_names)

    def grouped_fields(self) -> list[dict[str, Any]]:
        """Return [{title, subtitle, fields: [BoundField]}] for non-empty groups.

        Used by the wizard template to render fields in labelled sections.
        """
        result: list[dict[str, Any]] = []
        for title, subtitle, names in _EXTRAS_GROUPS:
            present = [self[name] for name in names if name in self.fields]
            if present:
                result.append({"title": title, "subtitle": subtitle, "fields": present})
        return result


class PaletteForm(forms.Form):
    name = forms.CharField(max_length=100)
    primary_color = forms.CharField(
        label="Primary (accents, buttons)",
        widget=forms.TextInput(attrs={"type": "color"}),
        initial=Palette.DEFAULT_PRIMARY,
    )
    secondary_color = forms.CharField(
        label="Secondary (highlights, CTAs)",
        widget=forms.TextInput(attrs={"type": "color"}),
        initial=Palette.DEFAULT_SECONDARY,
    )
    surface_color = forms.CharField(
        label="Surface (background)",
        widget=forms.TextInput(attrs={"type": "color"}),
        initial=Palette.DEFAULT_SURFACE,
    )
    text_color = forms.CharField(
        label="Text (body copy)",
        widget=forms.TextInput(attrs={"type": "color"}),
        initial=Palette.DEFAULT_TEXT,
    )


class InvitationForm(forms.Form):
    label = forms.CharField(
        max_length=200,
        label="Recipient label",
        help_text="A name to recognize the recipient(s), e.g. 'The Smiths'.",
    )
    num_guests = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Number of guests",
        help_text="How many people this link is good for.",
    )
    language = forms.ChoiceField(
        choices=Invitation.LANGUAGE_CHOICES,
        initial="en",
        label="Invitation language",
        help_text="The recipient will see chrome text (labels, dates) in this language.",
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Personal message (optional)",
    )


class RSVPForm(forms.Form):
    status = forms.ChoiceField(
        choices=RSVP.Status.choices,
        label="Will you attend?",
        widget=forms.RadioSelect,
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Message for the host",
    )
