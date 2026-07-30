"""Admin registrations."""
from typing import Optional

from django.contrib import admin
from django.http import HttpRequest

from invitations.models import Invitation, Palette, Party, RSVP, RSVPMessage


@admin.register(Palette)
class PaletteAdmin(admin.ModelAdmin):
    list_display = ("name", "host", "primary_color", "secondary_color",
                    "surface_color", "text_color")
    list_filter = ("host",)
    search_fields = ("name",)


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("name", "host", "template_choice", "starts_at", "location")
    list_filter = ("host", "template_choice")
    search_fields = ("name", "location")
    date_hierarchy = "starts_at"
    fieldsets = (
        (None, {"fields": ("name", "host", "description", "location", "starts_at")}),
        ("Theme", {"fields": ("template_choice", "palette")}),
        ("Template content (JSON)", {
            "fields": ("theme_content",),
            "description": (
                "Template-customizable copy/URLs. Edited via the host wizard; "
                "shape is per-template (see invitations/themes.py)."
            ),
        }),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("label", "party", "num_guests", "token", "created_at")
    list_filter = ("party",)
    search_fields = ("label", "party__name")
    readonly_fields = ("token",)


class RSVPMessageInline(admin.TabularInline):
    """The message trail, read-only.

    A guest can rewrite their message freely; this is the record of what they
    wrote before. An audit trail that can be edited in place is not one, so
    nothing here is writable — the current message stays editable on the RSVP
    itself, which is the field the guest is actually changing.
    """

    model = RSVPMessage
    extra = 0
    fields = ("body", "created_at")
    readonly_fields = ("body", "created_at")
    can_delete = False
    verbose_name_plural = "Message history"

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[RSVP] = None
    ) -> bool:
        return False


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = (
        "invitation",
        "status",
        "seats_confirmed",
        "seats_offered",
        "message",
        "responded_at",
    )
    list_filter = ("status",)
    # Searching the trail too, not just the current text: a host looking for
    # "allergy" should still find the RSVP whose note said it last week.
    search_fields = ("invitation__label", "message", "message_history__body")
    inlines = (RSVPMessageInline,)
    # `seats_confirmed` and `seats_offered` both read through to the
    # invitation, so without this the changelist runs a query per row.
    list_select_related = ("invitation",)

    @admin.display(description="Seats offered", ordering="invitation__num_guests")
    def seats_offered(self, obj: RSVP) -> int:
        """The allocation `seats_confirmed` is a fraction of.

        Confirmed seats mean nothing on their own — 2 is good news on an
        invitation for 2 and bad news on one for 6 — so the ceiling is shown
        next to it.
        """
        return obj.invitation.num_guests
