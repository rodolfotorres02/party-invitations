"""Business logic for parties."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from invitations.models import Palette, Party
from invitations.repositories.party_repository import PartyRepository


class PartyNotFoundError(Exception):
    """Raised when a party cannot be found, or the user isn't authorized to see it."""


class PartyService:
    def __init__(self, party_repository: Optional[PartyRepository] = None) -> None:
        self._parties = party_repository or PartyRepository()

    def list_for_host(self, host: AbstractBaseUser) -> QuerySet[Party]:
        return self._parties.list_for_host(host.pk)

    def get_for_host(self, party_id: int, host: AbstractBaseUser) -> Party:
        party = self._parties.get_for_host(party_id, host.pk)
        if party is None:
            raise PartyNotFoundError(f"Party {party_id} not found for host {host.pk}.")
        return party

    def create(
        self,
        host: AbstractBaseUser,
        *,
        name: str,
        location: str,
        starts_at: datetime,
        description: str = "",
        template_choice: str = Party.TemplateChoice.MINIMAL.value,
        palette: Optional[Palette] = None,
    ) -> Party:
        return self._parties.create(
            host=host,
            name=name,
            location=location,
            starts_at=starts_at,
            description=description,
            template_choice=template_choice,
            palette=palette,
        )

    def update(
        self,
        party_id: int,
        host: AbstractBaseUser,
        *,
        name: str,
        location: str,
        starts_at: datetime,
        description: str = "",
        template_choice: str = Party.TemplateChoice.MINIMAL.value,
        palette: Optional[Palette] = None,
    ) -> Party:
        party = self.get_for_host(party_id, host)
        return self._parties.update(
            party,
            name=name,
            location=location,
            starts_at=starts_at,
            description=description,
            template_choice=template_choice,
            palette=palette,
        )

    def update_theme_content(
        self,
        party_id: int,
        host: AbstractBaseUser,
        **fields: Any,
    ) -> Party:
        """Merge the wizard step-2 'extras' into the party's theme_content JSON.

        Empty values prune their key from the dict (keeps storage tidy); date
        values serialize to ISO strings so JSONField can store them.

        Field validity is enforced upstream by `PartyExtrasForm` — the form is
        built dynamically from the chosen theme's `content_fields`, so only
        valid keys reach `cleaned_data`.
        """
        party = self.get_for_host(party_id, host)
        content = dict(party.theme_content)
        for key, value in fields.items():
            if value in (None, ""):
                content.pop(key, None)
            elif hasattr(value, "isoformat"):  # date / datetime
                content[key] = value.isoformat()
            else:
                content[key] = value
        return self._parties.update(party, theme_content=content)

    def delete(self, party_id: int, host: AbstractBaseUser) -> None:
        party = self.get_for_host(party_id, host)
        self._parties.delete(party)
