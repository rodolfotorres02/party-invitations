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
        ("Common content", {"fields": ("hero_subtitle", "rsvp_deadline")}),
        ("Modern Minimal", {"fields": ("details_body",), "classes": ("collapse",)}),
        ("Classic & Floral", {
            "fields": (
                "our_story",
                "ceremony_time", "ceremony_venue", "ceremony_address",
                "reception_time", "reception_venue", "reception_address",
            ),
            "classes": ("collapse",),
        }),
        ("Floral only", {"fields": ("lodging_info",), "classes": ("collapse",)}),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("label", "party", "num_guests", "token", "created_at")
    list_filter = ("party",)
    search_fields = ("label", "party__name")
    readonly_fields = ("token",)


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ("invitation", "status", "responded_at")
    list_filter = ("status",)
