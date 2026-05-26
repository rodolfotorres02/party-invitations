"""Form definitions for the invitations app."""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from django import forms
from django.contrib.auth.models import AbstractBaseUser

from invitations.models import Invitation, RSVP, Palette, Party
from invitations.themes import all_themes, get_theme


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
}


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
    ("Hero & timing", "Top of the invitation.",
     ("hero_subtitle", "hero_image_url", "rsvp_deadline")),
    ("Story", "A short paragraph about the occasion, with an optional photo.",
     ("our_story", "our_story_image_url", "details_body", "details_image_url")),
    ("Ceremony", "The main event.",
     ("ceremony_time", "ceremony_venue", "ceremony_address")),
    ("Reception", "Where the celebration continues.",
     ("reception_time", "reception_venue", "reception_address")),
    ("Lodging", "Hotels, accommodations, travel info.",
     ("lodging_info",)),
    ("Etiquette", "Optional notes for guests.",
     ("dress_code",)),
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
