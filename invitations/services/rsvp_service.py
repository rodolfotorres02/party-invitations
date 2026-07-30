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
        seats: Optional[int] = None,
        message: str = "",
    ) -> RSVP:
        """Record (or update) a guest's response to an invitation by token.

        The organizer fixes the ceiling on the invitation; the responder
        chooses yes/no/maybe, how many of those seats they will use, and an
        optional message.

        `seats` is clamped to 1..num_guests here as well as in the form, so a
        caller that skips the form cannot write a headcount the organizer never
        offered. Omitting it means the full allocation.

        A non-empty `message` is written; an empty `message` is treated as
        "no change" so updating status later doesn't clobber an existing note.
        """
        if status not in RSVP.Status.values:
            raise ValueError(f"Invalid RSVP status: {status!r}.")
        invitation = self._invitations.get_by_token(token)
        allocation = max(1, invitation.num_guests)
        fields: dict[str, Any] = {
            "status": status,
            "seats": allocation if seats is None else max(1, min(seats, allocation)),
        }
        if message:
            fields["message"] = message
        return self._rsvps.upsert_for_invitation(invitation, **fields)
