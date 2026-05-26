"""Thin view layer — delegates to services and renders templates."""
from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from invitations.forms import (
    InvitationForm,
    PaletteForm,
    PartyExtrasForm,
    PartyForm,
    RSVPForm,
)
from invitations.services import (
    InvitationNotFoundError,
    InvitationService,
    PaletteNotFoundError,
    PaletteService,
    PartyNotFoundError,
    PartyService,
    RSVPService,
)
from invitations.themes import get_theme


# --- Party views -------------------------------------------------------------


class PartyListView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        parties = PartyService().list_for_host(request.user)
        return render(request, "invitations/party_list.html", {"parties": parties})


class _PartyFormMixin:
    """Shared helpers for views that render the PartyForm."""

    def _resolve_palette(self, palette_id: str, host) -> object:
        return PaletteService().get_for_host(int(palette_id), host)


class PartyCreateView(LoginRequiredMixin, _PartyFormMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        # Touching the palette list lazily seeds the default palette.
        PaletteService().list_for_host(request.user)
        return render(
            request,
            "invitations/party_form.html",
            {"form": PartyForm(host=request.user)},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        PaletteService().list_for_host(request.user)
        form = PartyForm(request.POST, host=request.user)
        if not form.is_valid():
            return render(request, "invitations/party_form.html", {"form": form})

        data = form.cleaned_data
        try:
            palette = self._resolve_palette(data.pop("palette"), request.user)
        except PaletteNotFoundError as exc:
            form.add_error("palette", str(exc))
            return render(request, "invitations/party_form.html", {"form": form})

        party = PartyService().create(request.user, palette=palette, **data)
        messages.success(request, f"Created '{party.name}'. Now customize it.")
        return redirect("party_extras", party_id=party.pk)


class PartyDetailView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, party_id: int) -> HttpResponse:
        party_service = PartyService()
        invitation_service = InvitationService(party_service=party_service)
        try:
            party = party_service.get_for_host(party_id, request.user)
            invitations = invitation_service.list_for_party(party_id, request.user)
        except PartyNotFoundError as exc:
            raise Http404(str(exc)) from exc
        return render(
            request,
            "invitations/party_detail.html",
            {
                "party": party,
                "invitations": invitations,
                "theme": get_theme(party.template_choice),
            },
        )


class PartyUpdateView(LoginRequiredMixin, _PartyFormMixin, View):
    def get(self, request: HttpRequest, party_id: int) -> HttpResponse:
        try:
            party = PartyService().get_for_host(party_id, request.user)
        except PartyNotFoundError as exc:
            raise Http404(str(exc)) from exc
        PaletteService().list_for_host(request.user)
        form = PartyForm(
            host=request.user,
            initial={
                "name": party.name,
                "location": party.location,
                "starts_at": party.starts_at,
                "description": party.description,
                "template_choice": party.template_choice,
                "palette": party.palette_id and str(party.palette_id),
            },
        )
        return render(
            request, "invitations/party_form.html", {"form": form, "party": party}
        )

    def post(self, request: HttpRequest, party_id: int) -> HttpResponse:
        form = PartyForm(request.POST, host=request.user)
        if not form.is_valid():
            return render(request, "invitations/party_form.html", {"form": form})
        data = form.cleaned_data
        try:
            palette = self._resolve_palette(data.pop("palette"), request.user)
            PartyService().update(party_id, request.user, palette=palette, **data)
        except (PartyNotFoundError, PaletteNotFoundError) as exc:
            raise Http404(str(exc)) from exc
        messages.success(request, "Party updated.")
        return redirect("party_detail", party_id=party_id)


class PartyExtrasView(LoginRequiredMixin, View):
    """Wizard step 2 — collects template-specific content."""

    def _get_party(self, request: HttpRequest, party_id: int):
        try:
            return PartyService().get_for_host(party_id, request.user)
        except PartyNotFoundError as exc:
            raise Http404(str(exc)) from exc

    def get(self, request: HttpRequest, party_id: int) -> HttpResponse:
        party = self._get_party(request, party_id)
        theme = get_theme(party.template_choice)
        initial = {field: getattr(party, field) for field in theme.content_fields}
        form = PartyExtrasForm(template_slug=party.template_choice, initial=initial)
        return render(
            request,
            "invitations/party_extras.html",
            {"party": party, "theme": theme, "form": form},
        )

    def post(self, request: HttpRequest, party_id: int) -> HttpResponse:
        party = self._get_party(request, party_id)
        theme = get_theme(party.template_choice)
        form = PartyExtrasForm(request.POST, template_slug=party.template_choice)
        if not form.is_valid():
            return render(
                request,
                "invitations/party_extras.html",
                {"party": party, "theme": theme, "form": form},
            )
        PartyService().update_theme_content(party_id, request.user, **form.cleaned_data)
        messages.success(request, "Template content saved.")
        return redirect("party_detail", party_id=party_id)


class PartyDeleteView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, party_id: int) -> HttpResponse:
        try:
            PartyService().delete(party_id, request.user)
        except PartyNotFoundError as exc:
            raise Http404(str(exc)) from exc
        messages.success(request, "Party deleted.")
        return redirect("party_list")


# --- Palette views -----------------------------------------------------------


class PaletteListView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        palettes = PaletteService().list_for_host(request.user)
        return render(
            request, "invitations/palette_list.html", {"palettes": palettes}
        )


class PaletteCreateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request, "invitations/palette_form.html", {"form": PaletteForm()}
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PaletteForm(request.POST)
        if not form.is_valid():
            return render(request, "invitations/palette_form.html", {"form": form})
        PaletteService().create(request.user, **form.cleaned_data)
        messages.success(request, "Palette created.")
        return redirect("palette_list")


class PaletteUpdateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, palette_id: int) -> HttpResponse:
        try:
            palette = PaletteService().get_for_host(palette_id, request.user)
        except PaletteNotFoundError as exc:
            raise Http404(str(exc)) from exc
        form = PaletteForm(initial={
            "name": palette.name,
            "primary_color": palette.primary_color,
            "secondary_color": palette.secondary_color,
            "surface_color": palette.surface_color,
            "text_color": palette.text_color,
        })
        return render(
            request,
            "invitations/palette_form.html",
            {"form": form, "palette": palette},
        )

    def post(self, request: HttpRequest, palette_id: int) -> HttpResponse:
        form = PaletteForm(request.POST)
        if not form.is_valid():
            return render(request, "invitations/palette_form.html", {"form": form})
        try:
            PaletteService().update(palette_id, request.user, **form.cleaned_data)
        except PaletteNotFoundError as exc:
            raise Http404(str(exc)) from exc
        messages.success(request, "Palette updated.")
        return redirect("palette_list")


class PaletteDeleteView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, palette_id: int) -> HttpResponse:
        try:
            PaletteService().delete(palette_id, request.user)
        except PaletteNotFoundError as exc:
            raise Http404(str(exc)) from exc
        messages.success(request, "Palette deleted.")
        return redirect("palette_list")


# --- Invitation views --------------------------------------------------------


class InvitationCreateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, party_id: int) -> HttpResponse:
        try:
            party = PartyService().get_for_host(party_id, request.user)
        except PartyNotFoundError as exc:
            raise Http404(str(exc)) from exc
        return render(
            request,
            "invitations/invitation_form.html",
            {"form": InvitationForm(), "party": party},
        )

    def post(self, request: HttpRequest, party_id: int) -> HttpResponse:
        form = InvitationForm(request.POST)
        party_service = PartyService()
        try:
            party = party_service.get_for_host(party_id, request.user)
        except PartyNotFoundError as exc:
            raise Http404(str(exc)) from exc

        if not form.is_valid():
            return render(
                request,
                "invitations/invitation_form.html",
                {"form": form, "party": party},
            )

        invitation = InvitationService(party_service=party_service).create_link(
            party_id, request.user, **form.cleaned_data
        )
        return redirect(
            "invitation_link", party_id=party_id, invitation_id=invitation.pk
        )


class InvitationLinkView(LoginRequiredMixin, View):
    def get(
        self, request: HttpRequest, party_id: int, invitation_id: int
    ) -> HttpResponse:
        try:
            invitation = InvitationService().get_for_host(invitation_id, request.user)
        except InvitationNotFoundError as exc:
            raise Http404(str(exc)) from exc
        public_url = request.build_absolute_uri(
            reverse("invitation_public", args=[invitation.token])
        )
        return render(
            request,
            "invitations/invitation_link.html",
            {"invitation": invitation, "party": invitation.party, "public_url": public_url},
        )


class InvitationRevokeView(LoginRequiredMixin, View):
    def post(
        self, request: HttpRequest, party_id: int, invitation_id: int
    ) -> HttpResponse:
        try:
            InvitationService().revoke(invitation_id, request.user)
        except InvitationNotFoundError as exc:
            raise Http404(str(exc)) from exc
        messages.success(request, "Invitation revoked.")
        return redirect("party_detail", party_id=party_id)


# --- Public invitation + RSVP -----------------------------------------------


class InvitationPublicView(View):
    """Publicly accessible invitation page — dispatches to the party's theme."""

    def get(self, request: HttpRequest, token: UUID) -> HttpResponse:
        try:
            invitation = InvitationService().get_by_token(token)
        except InvitationNotFoundError as exc:
            raise Http404(str(exc)) from exc

        party = invitation.party
        theme = get_theme(party.template_choice)
        existing_rsvp = getattr(invitation, "rsvp", None)
        initial = (
            {"status": existing_rsvp.status, "message": existing_rsvp.message}
            if existing_rsvp is not None
            else None
        )
        # Fall back to the host's default palette if the party has none assigned.
        palette = party.palette or PaletteService().default_for_host(party.host)
        return render(
            request,
            theme.template_path,
            {
                "invitation": invitation,
                "party": party,
                "palette": palette,
                "rsvp": existing_rsvp,
                "form": RSVPForm(initial=initial),
            },
        )


class RSVPSubmitView(View):
    def post(self, request: HttpRequest, token: UUID) -> HttpResponse:
        form = RSVPForm(request.POST)
        invitation_service = InvitationService()
        try:
            invitation = invitation_service.get_by_token(token)
        except InvitationNotFoundError as exc:
            raise Http404(str(exc)) from exc

        if not form.is_valid():
            party = invitation.party
            theme = get_theme(party.template_choice)
            palette = party.palette or PaletteService().default_for_host(party.host)
            return render(
                request,
                theme.template_path,
                {
                    "invitation": invitation,
                    "party": party,
                    "palette": palette,
                    "rsvp": None,
                    "form": form,
                },
            )

        RSVPService(invitation_service=invitation_service).submit(
            token, **form.cleaned_data
        )
        return HttpResponseRedirect(reverse("invitation_public", args=[token]))
