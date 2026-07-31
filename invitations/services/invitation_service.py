"""Business logic for invitations."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from invitations.models import Invitation
from invitations.repositories.invitation_repository import InvitationRepository
from invitations.repositories.rsvp_repository import RSVPRepository
from invitations.services.party_service import PartyService


class InvitationNotFoundError(Exception):
    """Raised when an invitation cannot be located by id or token, or the
    requesting host isn't authorized to act on it."""


class InvitationService:
    def __init__(
        self,
        invitation_repository: Optional[InvitationRepository] = None,
        party_service: Optional[PartyService] = None,
        rsvp_repository: Optional[RSVPRepository] = None,
    ) -> None:
        self._invitations = invitation_repository or InvitationRepository()
        self._parties = party_service or PartyService()
        self._rsvps = rsvp_repository or RSVPRepository()

    def list_for_party(
        self, party_id: int, host: AbstractBaseUser
    ) -> QuerySet[Invitation]:
        # Authorize first: this raises if the host doesn't own the party.
        self._parties.get_for_host(party_id, host)
        return self._invitations.list_for_party(party_id)

    def get_for_host(self, invitation_id: int, host: AbstractBaseUser) -> Invitation:
        invitation = self._invitations.get(invitation_id)
        if invitation is None or invitation.party.host_id != host.pk:
            raise InvitationNotFoundError(
                f"No invitation {invitation_id} owned by host {host.pk}."
            )
        return invitation

    def get_by_token(self, token: UUID) -> Invitation:
        invitation = self._invitations.get_by_token(token)
        if invitation is None:
            raise InvitationNotFoundError(f"No invitation with token {token}.")
        return invitation

    def create_link(
        self,
        party_id: int,
        host: AbstractBaseUser,
        *,
        label: str,
        num_guests: int = 1,
        message: str = "",
        language: str = "en",
    ) -> Invitation:
        if num_guests < 1:
            raise ValueError("num_guests must be at least 1.")
        party = self._parties.get_for_host(party_id, host)
        return self._invitations.create(
            party=party,
            label=label.strip(),
            num_guests=num_guests,
            message=message,
            language=language,
        )

    def update_link(
        self,
        invitation_id: int,
        host: AbstractBaseUser,
        *,
        label: str,
        num_guests: int = 1,
        message: str = "",
        language: str = "en",
    ) -> Invitation:
        """Rewrite the settings the host chose when the link was created.

        The token is left alone, so a link already in a guest's hands keeps
        working and the RSVP they may have already sent stays attached to it.
        """
        if num_guests < 1:
            raise ValueError("num_guests must be at least 1.")
        invitation = self.get_for_host(invitation_id, host)
        invitation = self._invitations.update(
            invitation,
            label=label.strip(),
            num_guests=num_guests,
            message=message,
            language=language,
        )
        self._trim_confirmed_seats(invitation)
        return invitation

    def _trim_confirmed_seats(self, invitation: Invitation) -> None:
        """Bring an existing RSVP back under a lowered allocation.

        `RSVP.seats` is only ever written within the ceiling the host offered —
        `RSVPService.submit` clamps it — but the host moving that ceiling down
        afterwards would strand an answer above it, and every headcount reads
        `seats_confirmed`, so the party would over-count. The host owns the
        allocation, so the answer is trimmed to fit rather than the other way
        around. An RSVP that never answered the seat question is left NULL:
        it already tracks the allocation on its own.
        """
        rsvp = self._rsvps.get_for_invitation(invitation)
        if rsvp is None or rsvp.seats is None:
            return
        if rsvp.seats > invitation.num_guests:
            self._rsvps.update(rsvp, seats=invitation.num_guests)

    def revoke(self, invitation_id: int, host: AbstractBaseUser) -> None:
        invitation = self.get_for_host(invitation_id, host)
        self._invitations.delete(invitation)
