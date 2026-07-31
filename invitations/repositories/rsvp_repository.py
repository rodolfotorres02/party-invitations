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

    def update(self, rsvp: RSVP, **fields: Any) -> RSVP:
        """Write `fields` to an existing RSVP.

        `responded_at` is deliberately left out of `update_fields`: it is
        `auto_now`, and the callers of this method are host-side edits to the
        invitation, not the guest answering it again. Leaving it out is what
        keeps it still: `auto_now` only fires for the fields being saved.
        """
        for key, value in fields.items():
            setattr(rsvp, key, value)
        rsvp.save(update_fields=list(fields.keys()) + ["updated_at"])
        return rsvp

    def latest_message(self, rsvp: RSVP) -> Optional[RSVPMessage]:
        """The most recently written version of this RSVP's message."""
        return rsvp.message_history.last()

    def add_message(self, rsvp: RSVP, body: str) -> RSVPMessage:
        """Append a version to the RSVP's message history."""
        return RSVPMessage.objects.create(rsvp=rsvp, body=body)
