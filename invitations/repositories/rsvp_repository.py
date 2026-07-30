"""Data access for RSVP."""
from __future__ import annotations

from typing import Any, Optional

from invitations.models import RSVP, Invitation, RSVPMessage


class RSVPRepository:
    def get_for_invitation(self, invitation: Invitation) -> Optional[RSVP]:
        return RSVP.objects.filter(invitation=invitation).first()

    def upsert_for_invitation(self, invitation: Invitation, **fields: Any) -> RSVP:
        rsvp, _ = RSVP.objects.update_or_create(
            invitation=invitation, defaults=fields
        )
        return rsvp

    def latest_message(self, rsvp: RSVP) -> Optional[RSVPMessage]:
        """The most recently written version of this RSVP's message."""
        return rsvp.message_history.last()

    def add_message(self, rsvp: RSVP, body: str) -> RSVPMessage:
        """Append a version to the RSVP's message history."""
        return RSVPMessage.objects.create(rsvp=rsvp, body=body)
