"""Data access for Palette."""
from __future__ import annotations

from typing import Any, Optional

from django.db.models import QuerySet

from invitations.models import Palette


class PaletteRepository:
    def list_for_host(self, host_id: int) -> QuerySet[Palette]:
        return Palette.objects.filter(host_id=host_id)

    def get_for_host(self, palette_id: int, host_id: int) -> Optional[Palette]:
        return Palette.objects.filter(pk=palette_id, host_id=host_id).first()

    def create(self, **fields: Any) -> Palette:
        return Palette.objects.create(**fields)

    def update(self, palette: Palette, **fields: Any) -> Palette:
        for key, value in fields.items():
            setattr(palette, key, value)
        palette.save(update_fields=list(fields.keys()) + ["updated_at"])
        return palette

    def delete(self, palette: Palette) -> None:
        palette.delete()

    def host_has_any(self, host_id: int) -> bool:
        return Palette.objects.filter(host_id=host_id).exists()
