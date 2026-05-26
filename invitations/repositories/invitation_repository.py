"""Data access for Invitation."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from django.db.models import QuerySet

from invitations.models import Invitation


class InvitationRepository:
    def list_for_party(self, party_id: int) -> QuerySet[Invitation]:
        return (
            Invitation.objects.filter(party_id=party_id)
            .select_related("party")
            .prefetch_related("rsvp")
        )

    def get(self, invitation_id: int) -> Optional[Invitation]:
        return Invitation.objects.filter(pk=invitation_id).first()

    def get_by_token(self, token: UUID) -> Optional[Invitation]:
        return (
            Invitation.objects.filter(token=token)
            .select_related("party")
            .first()
        )

    def create(self, **fields: Any) -> Invitation:
        return Invitation.objects.create(**fields)

    def delete(self, invitation: Invitation) -> None:
        invitation.delete()
