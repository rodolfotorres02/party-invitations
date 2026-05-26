"""URL config for the invitations app."""
from django.urls import path

from invitations import views


urlpatterns = [
    path("", views.PartyListView.as_view(), name="party_list"),

    # Parties
    path("parties/new/", views.PartyCreateView.as_view(), name="party_create"),
    path("parties/<int:party_id>/", views.PartyDetailView.as_view(), name="party_detail"),
    path(
        "parties/<int:party_id>/customize/",
        views.PartyExtrasView.as_view(),
        name="party_extras",
    ),
    path("parties/<int:party_id>/edit/", views.PartyUpdateView.as_view(), name="party_edit"),
    path("parties/<int:party_id>/delete/", views.PartyDeleteView.as_view(), name="party_delete"),

    # Invitation links
    path(
        "parties/<int:party_id>/invitations/new/",
        views.InvitationCreateView.as_view(),
        name="invitation_create",
    ),
    path(
        "parties/<int:party_id>/invitations/<int:invitation_id>/link/",
        views.InvitationLinkView.as_view(),
        name="invitation_link",
    ),
    path(
        "parties/<int:party_id>/invitations/<int:invitation_id>/revoke/",
        views.InvitationRevokeView.as_view(),
        name="invitation_revoke",
    ),

    # Palettes
    path("palettes/", views.PaletteListView.as_view(), name="palette_list"),
    path("palettes/new/", views.PaletteCreateView.as_view(), name="palette_create"),
    path(
        "palettes/<int:palette_id>/edit/",
        views.PaletteUpdateView.as_view(),
        name="palette_edit",
    ),
    path(
        "palettes/<int:palette_id>/delete/",
        views.PaletteDeleteView.as_view(),
        name="palette_delete",
    ),

    # Public guest-facing pages
    path(
        "i/<uuid:token>/",
        views.InvitationPublicView.as_view(),
        name="invitation_public",
    ),
    path(
        "i/<uuid:token>/rsvp/",
        views.RSVPSubmitView.as_view(),
        name="rsvp_submit",
    ),
]
