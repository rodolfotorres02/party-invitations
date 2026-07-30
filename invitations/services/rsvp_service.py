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
        message: Optional[str] = None,
    ) -> RSVP:
        """Record (or update) a guest's response to an invitation by token.

        The organizer fixes the ceiling on the invitation; the responder
        chooses yes/no/maybe, how many of those seats they will use, and an
        optional message.

        `seats` is clamped to 1..num_guests here as well as in the form, so a
        caller that skips the form cannot write a headcount the organizer never
        offered. Omitting it means the full allocation.

        `message` distinguishes absent from empty, which the RSVP form relies
        on to let a guest rewrite a note they have already sent:

        - ``None`` (omitted) leaves the stored message untouched. This is what
          protects a caller that only means to change the status — the form
          always sends the field, but nothing else has to.
        - ``""`` clears it. The form renders the textarea pre-filled with the
          current message, so an empty box coming back is a guest deleting
          their note on purpose, not an update that forgot to include it.
        - Any other value replaces it, and is appended to the RSVP's message
          history unless it is what the message already said.

        Clearing appends nothing: the history is the messages a guest sent, and
        an erasure is not one. The trail of what they did say survives it.
        """
        if status not in RSVP.Status.values:
            raise ValueError(f"Invalid RSVP status: {status!r}.")
        invitation = self._invitations.get_by_token(token)
        allocation = max(1, invitation.num_guests)
        fields: dict[str, Any] = {
            "status": status,
            "seats": allocation if seats is None else max(1, min(seats, allocation)),
        }
        if message is not None:
            fields["message"] = message
        rsvp = self._rsvps.upsert_for_invitation(invitation, **fields)
        if message:
            self._record_message_version(rsvp, message)
        return rsvp

    def _record_message_version(self, rsvp: RSVP, message: str) -> None:
        """Append `message` to the RSVP's history unless it is already current.

        Every submission posts the message back, because the textarea is
        pre-filled with it — so most updates carry a message the host has
        already seen. Recording those would bury the versions that actually
        changed under a pile of identical rows, one per time the guest amended
        their headcount.
        """
        latest = self._rsvps.latest_message(rsvp)
        if latest is not None and latest.body == message:
            return
        self._rsvps.add_message(rsvp, message)
