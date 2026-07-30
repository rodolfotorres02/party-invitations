"""Admin registrations."""
from django.contrib import admin

from invitations.models import Invitation, Palette, Party, RSVP


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
    search_fields = ("invitation__label", "message")
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
