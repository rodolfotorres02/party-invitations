"""Business logic for RSVPs."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from invitations.models import RSVP
from invitations.repositories.rsvp_repository import RSVPRepository
from invitations.services.invitation_service import InvitationService


class RSVPService:
    def __init__(
        self,
        rsvp_repository: Optional[RSVPRepository] = None,
        invitation_service: Optional[InvitationService] = None,
    ) -> None:
        self._rsvps = rsvp_repository or RSVPRepository()
        self._invitations = invitation_service or InvitationService()

    def submit(
        self,
        token: UUID,
        *,
        status: str,
        message: str = "",
    ) -> RSVP:
        """Record (or update) a guest's response to an invitation by token.

        The headcount is fixed on the invitation by the organizer — the
        responder only chooses yes/no/maybe and an optional message.

        A non-empty `message` is written; an empty `message` is treated as
        "no change" so updating status later doesn't clobber an existing note.
        """
        if status not in RSVP.Status.values:
            raise ValueError(f"Invalid RSVP status: {status!r}.")
        invitation = self._invitations.get_by_token(token)
        fields: dict[str, Any] = {"status": status}
        if message:
            fields["message"] = message
        return self._rsvps.upsert_for_invitation(invitation, **fields)
