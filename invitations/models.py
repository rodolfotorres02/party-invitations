"""Domain models for parties, invitation links, RSVPs, and visual palettes."""
import uuid
from datetime import date
from typing import Any

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


HEX_COLOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Color must be a 7-character hex value, e.g. '#768970'.",
)


class TimestampedModel(models.Model):
    """Abstract base providing created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Palette(TimestampedModel):
    """A reusable 4-color palette belonging to a host.

    Maps to a Stitch design system's four override slots:
    primary, secondary, surface, text.
    The full Material-style tonal scale is derived from these at render time.
    """

    # Defaults are still here so a single-palette `Palette()` keeps working,
    # but new hosts get seeded with all SEED_PALETTES at first sign-in.
    DEFAULT_NAME = "Ethereal Union"
    DEFAULT_PRIMARY = "#768970"
    DEFAULT_SECONDARY = "#d4af37"
    DEFAULT_SURFACE = "#f9f7f2"
    DEFAULT_TEXT = "#2d2926"

    # Palettes auto-created on a host's first visit. Keep in sync with the
    # `family` values in invitations/themes.py — the public theme picks
    # tonal-scale fallbacks based on its family, but the user can still pair
    # any palette with any template.
    SEED_PALETTES: tuple[dict[str, str], ...] = (
        {  # Ethereal Union — light, sage/gold/cream
            "name": "Ethereal Union",
            "primary_color": "#768970",
            "secondary_color": "#d4af37",
            "surface_color": "#f9f7f2",
            "text_color": "#2d2926",
        },
        {  # Midnight Garden — navy/gold/white, designed for the Midnight themes
            "name": "Midnight Garden",
            "primary_color": "#1a2b3c",
            "secondary_color": "#c5a059",
            "surface_color": "#ffffff",
            "text_color": "#1a1c1c",
        },
        {  # Wildflower Wreath — olive/rose/white, designed for the garden family
            "name": "Wildflower Wreath",
            "primary_color": "#546524",
            "secondary_color": "#be688c",
            "surface_color": "#ffffff",
            "text_color": "#3b393c",
        },
    )

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="palettes",
    )
    name = models.CharField(max_length=100)
    primary_color = models.CharField(
        max_length=7, default=DEFAULT_PRIMARY, validators=[HEX_COLOR]
    )
    secondary_color = models.CharField(
        max_length=7, default=DEFAULT_SECONDARY, validators=[HEX_COLOR]
    )
    surface_color = models.CharField(
        max_length=7, default=DEFAULT_SURFACE, validators=[HEX_COLOR]
    )
    text_color = models.CharField(
        max_length=7, default=DEFAULT_TEXT, validators=[HEX_COLOR]
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Party(TimestampedModel):
    class TemplateChoice(models.TextChoices):
        MINIMAL = "minimal", "Modern Minimal"
        CLASSIC = "classic", "Classic Elegance"
        FLORAL = "floral", "Romantic Floral"
        MIDNIGHT_MINIMAL = "midnight_minimal", "Midnight Minimal"
        MIDNIGHT_ELEGANCE = "midnight_elegance", "Midnight Elegance"
        MIDNIGHT_FLORAL = "midnight_floral", "Midnight Floral"
        SECRET_GARDEN = "secret_garden", "Secret Garden"
        WILDFLOWER_WREATH = "wildflower_wreath", "Wildflower Wreath"

    # --- Core fields (used by every template) ------------------------------
    name = models.CharField(
        max_length=200,
        help_text="Hero title — e.g. 'Evelyn & James' or 'Rodolfo's 30th'.",
    )
    description = models.TextField(blank=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parties",
    )
    location = models.CharField(max_length=300)
    starts_at = models.DateTimeField()

    # --- Theme selection ---------------------------------------------------
    template_choice = models.CharField(
        max_length=32,
        choices=TemplateChoice.choices,
        default=TemplateChoice.MINIMAL,
    )
    palette = models.ForeignKey(
        Palette,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parties",
    )

    # --- Theme content ------------------------------------------------------
    # All template-customizable fields live here as a JSON dict. The keys
    # are defined in invitations/forms.py::_EXTRAS_FIELD_CATALOG and selected
    # per-template by invitations/themes.py::Theme.content_fields. Adding a
    # new field is purely a code change — no migration required.
    theme_content = models.JSONField(default=dict, blank=True)

    # Field names whose values are stored as ISO date strings in JSON.
    # `content_for_display` parses these back into `datetime.date` objects so
    # Django's `|date` template filter can format them. Add new date-typed
    # fields here when they're introduced in the form catalog.
    _DATE_CONTENT_FIELDS: tuple[str, ...] = ("rsvp_deadline",)

    class Meta:
        ordering = ["-starts_at"]
        verbose_name_plural = "parties"

    def __str__(self) -> str:
        return self.name

    def content_for_display(self) -> dict[str, Any]:
        """Return `theme_content` with typed values parsed for template use.

        JSON has no date type, so date fields round-trip as ISO strings;
        Django's `|date` filter only works on `date`/`datetime` objects, so
        we parse them back here before rendering. Other values pass through.
        """
        result = dict(self.theme_content)
        for key in self._DATE_CONTENT_FIELDS:
            raw = result.get(key)
            if isinstance(raw, str) and raw:
                try:
                    result[key] = date.fromisoformat(raw)
                except ValueError:
                    result[key] = None
        return result


class Invitation(TimestampedModel):
    """A shareable link created by the organizer for a group of guests."""

    LANGUAGE_CHOICES = (
        ("en", "English"),
        ("es", "Español"),
    )

    party = models.ForeignKey(
        Party, on_delete=models.CASCADE, related_name="invitations"
    )
    label = models.CharField(
        max_length=200,
        help_text="A name to recognize the recipient(s), e.g. 'The Smiths'.",
    )
    num_guests = models.PositiveSmallIntegerField(
        default=1,
        help_text="How many people this invitation is for.",
    )
    message = models.TextField(blank=True)
    language = models.CharField(
        max_length=8,
        choices=LANGUAGE_CHOICES,
        default="en",
        help_text="Language used for chrome text on the public invitation page.",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation for {self.label} — {self.party}"


class RSVP(TimestampedModel):
    class Status(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        MAYBE = "maybe", _("Maybe")

    invitation = models.OneToOneField(
        Invitation, on_delete=models.CASCADE, related_name="rsvp"
    )
    status = models.CharField(max_length=8, choices=Status.choices)
    # How many of the invitation's seats the guest is actually taking up. The
    # organizer still fixes the ceiling (Invitation.num_guests); this is the
    # guest narrowing it — "we're a table of two, only one of us can make it".
    #
    # NULL, not 0, is the "never asked" value: the field is newer than the
    # RSVPs already in the table, and a row that predates the question has not
    # answered it rather than answered it with zero. Read it through
    # `seats_confirmed`, which resolves both cases.
    seats = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Seats the guest confirmed, up to the invitation's num_guests.",
    )
    # The message as it stands right now. Every version it has ever had —
    # including this one — is kept in `message_history`; this field is the
    # denormalized "current", which is what the guest sees and what the host
    # reads first.
    message = models.TextField(blank=True)
    responded_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "RSVP"
        verbose_name_plural = "RSVPs"

    def __str__(self) -> str:
        return f"{self.invitation.label} → {self.get_status_display()}"

    @property
    def seats_confirmed(self) -> int:
        """Seats to count for this RSVP, safe to sum across a whole party.

        A declined invitation takes no seats. An RSVP answered before the
        question existed falls back to the full allocation, which is what the
        headcount silently assumed for those rows all along.
        """
        if self.status == self.Status.NO:
            return 0
        if self.seats is None:
            return self.invitation.num_guests
        return self.seats

    @property
    def message_sent_at(self) -> Any:
        """When the current message was written.

        Deliberately not `responded_at`: that field is `auto_now`, so it moves
        every time any part of the RSVP is saved. A guest who flips maybe→yes
        without touching their note would otherwise be told the note was sent
        just now. Falls back to `responded_at` only for a message with no
        history row — a value written outside the service, e.g. in the admin.
        """
        latest = self.message_history.last()
        return latest.created_at if latest else self.responded_at

    @property
    def previous_messages(self) -> list["RSVPMessage"]:
        """Superseded versions of the message, newest first.

        The current message is displayed on its own, so the row holding it is
        dropped rather than repeated at the top of the trail. Matching on the
        body rather than assuming "the last row is the current one" keeps this
        honest when `message` was edited directly in the admin, which appends
        no history: there the newest row is genuinely superseded and belongs
        in the trail.
        """
        history = list(self.message_history.all())
        if history and history[-1].body == self.message:
            history = history[:-1]
        return list(reversed(history))


class RSVPMessage(TimestampedModel):
    """One version of the note a guest sent along with their RSVP.

    Guests may rewrite their message as often as they like, and only ever see
    the current one. This table is what makes that safe for the host: every
    version ever sent is kept, so a note the host already read cannot be
    quietly replaced.

    Rows are append-only — an edit adds a version, it never rewrites one.
    """

    rsvp = models.ForeignKey(
        RSVP, on_delete=models.CASCADE, related_name="message_history"
    )
    body = models.TextField()

    class Meta:
        # `created_at` alone is not a total order — two versions written in the
        # same instant would sort arbitrarily — and "the current version" is
        # defined here as the last row. `id` breaks ties in insertion order so
        # that definition always resolves to one row.
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"Message from {self.rsvp.invitation.label} at {self.created_at}"
