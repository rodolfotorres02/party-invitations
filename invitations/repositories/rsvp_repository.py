"""Data access for RSVP."""
from __future__ import annotations

from typing import Any, Optional

from invitations.models import RSVP, Invitation


class RSVPRepository:
    def get_for_invitation(self, invitation: Invitation) -> Optional[RSVP]:
        return RSVP.objects.filter(invitation=invitation).first()

    def upsert_for_invitation(self, invitation: Invitation, **fields: Any) -> RSVP:
        rsvp, _ = RSVP.objects.update_or_create(
            invitation=invitation, defaults=fields
        )
        return rsvp
