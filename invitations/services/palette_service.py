"""Business logic for palettes."""
from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from invitations.models import Palette
from invitations.repositories.palette_repository import PaletteRepository


class PaletteNotFoundError(Exception):
    """Raised when a palette cannot be found, or the host isn't authorized."""


class PaletteService:
    def __init__(self, palette_repository: Optional[PaletteRepository] = None) -> None:
        self._palettes = palette_repository or PaletteRepository()

    def list_for_host(self, host: AbstractBaseUser) -> QuerySet[Palette]:
        """List a host's palettes, lazily seeding the defaults if they have none."""
        if not self._palettes.host_has_any(host.pk):
            for spec in Palette.SEED_PALETTES:
                self._palettes.create(host=host, **spec)
        return self._palettes.list_for_host(host.pk)

    def get_for_host(self, palette_id: int, host: AbstractBaseUser) -> Palette:
        palette = self._palettes.get_for_host(palette_id, host.pk)
        if palette is None:
            raise PaletteNotFoundError(
                f"Palette {palette_id} not found for host {host.pk}."
            )
        return palette

    def create(
        self,
        host: AbstractBaseUser,
        *,
        name: str,
        primary_color: str,
        secondary_color: str,
        surface_color: str,
        text_color: str,
    ) -> Palette:
        return self._palettes.create(
            host=host,
            name=name.strip(),
            primary_color=primary_color,
            secondary_color=secondary_color,
            surface_color=surface_color,
            text_color=text_color,
        )

    def update(
        self,
        palette_id: int,
        host: AbstractBaseUser,
        *,
        name: str,
        primary_color: str,
        secondary_color: str,
        surface_color: str,
        text_color: str,
    ) -> Palette:
        palette = self.get_for_host(palette_id, host)
        return self._palettes.update(
            palette,
            name=name.strip(),
            primary_color=primary_color,
            secondary_color=secondary_color,
            surface_color=surface_color,
            text_color=text_color,
        )

    def delete(self, palette_id: int, host: AbstractBaseUser) -> None:
        palette = self.get_for_host(palette_id, host)
        self._palettes.delete(palette)

    def default_for_host(self, host: AbstractBaseUser) -> Palette:
        """Return the host's first palette (auto-seeding if none exists).

        Used by the public invitation view when a Party has no palette FK set.
        """
        return self.list_for_host(host).first()
