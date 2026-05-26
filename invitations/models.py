"""Domain models for parties, invitation links, RSVPs, and visual palettes."""
import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


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

    Maps to the 'Ethereal Union' Stitch design system's four override slots:
    primary (sage), secondary (gold), surface (cream), text (charcoal).
    The full Material-style tonal scale is derived from these at render time.
    """

    DEFAULT_NAME = "Ethereal Union"
    DEFAULT_PRIMARY = "#768970"
    DEFAULT_SECONDARY = "#d4af37"
    DEFAULT_SURFACE = "#f9f7f2"
    DEFAULT_TEXT = "#2d2926"

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
        max_length=16,
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

    # --- Theme content (all templates) -------------------------------------
    hero_subtitle = models.CharField(
        max_length=300,
        blank=True,
        help_text="Italic intro under the hero title.",
    )
    rsvp_deadline = models.DateField(null=True, blank=True)

    # --- Theme content (Modern Minimal) -----------------------------------
    details_body = models.TextField(
        blank=True,
        help_text="Single block of details copy (Modern Minimal template).",
    )

    # --- Theme content (Classic & Floral) ----------------------------------
    our_story = models.TextField(blank=True)
    ceremony_time = models.CharField(max_length=200, blank=True)
    ceremony_venue = models.CharField(max_length=200, blank=True)
    ceremony_address = models.CharField(max_length=300, blank=True)
    reception_time = models.CharField(max_length=200, blank=True)
    reception_venue = models.CharField(max_length=200, blank=True)
    reception_address = models.CharField(max_length=300, blank=True)

    # --- Theme content (Floral only) ---------------------------------------
    lodging_info = models.TextField(blank=True)

    class Meta:
        ordering = ["-starts_at"]
        verbose_name_plural = "parties"

    def __str__(self) -> str:
        return self.name


class Invitation(TimestampedModel):
    """A shareable link created by the organizer for a group of guests."""

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
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation for {self.label} — {self.party}"


class RSVP(TimestampedModel):
    class Status(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        MAYBE = "maybe", "Maybe"

    invitation = models.OneToOneField(
        Invitation, on_delete=models.CASCADE, related_name="rsvp"
    )
    status = models.CharField(max_length=8, choices=Status.choices)
    message = models.TextField(blank=True)
    responded_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "RSVP"
        verbose_name_plural = "RSVPs"

    def __str__(self) -> str:
        return f"{self.invitation.label} → {self.get_status_display()}"
