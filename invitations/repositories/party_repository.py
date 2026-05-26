"""Data access for Party."""
from __future__ import annotations

from typing import Any, Optional

from django.db.models import QuerySet

from invitations.models import Party


class PartyRepository:
    """All Party ORM queries live here. Services depend on this, not the ORM."""

    def list_for_host(self, host_id: int) -> QuerySet[Party]:
        return Party.objects.filter(host_id=host_id)

    def get(self, party_id: int) -> Optional[Party]:
        return Party.objects.filter(pk=party_id).first()

    def get_for_host(self, party_id: int, host_id: int) -> Optional[Party]:
        return Party.objects.filter(pk=party_id, host_id=host_id).first()

    def create(self, **fields: Any) -> Party:
        return Party.objects.create(**fields)

    def update(self, party: Party, **fields: Any) -> Party:
        for key, value in fields.items():
            setattr(party, key, value)
        party.save(update_fields=list(fields.keys()) + ["updated_at"])
        return party

    def delete(self, party: Party) -> None:
        party.delete()
