# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Lock platform for VAG Connect — proper HA LockEntity for door lock/unlock."""

from __future__ import annotations

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[LockEntity] = []

    for vin in coordinator.vehicles:
        entities.append(VagDoorLock(coordinator, vin))

    async_add_entities(entities)


class VagDoorLock(VagConnectEntity, LockEntity):
    """Vehicle door lock — uses HA's native LockEntity."""

    _attr_translation_key = "door_lock"
    # v1.9.1 — Phase 2 gating. If a previous lock/unlock attempt was
    # rejected as missing-capability or not-entitled, the entity goes
    # unavailable instead of throwing 403/400 on every press.
    _command_id = "command_lock"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "door_lock")

    @property
    def is_locked(self) -> bool | None:
        return self._vehicle.get("doors_locked")

    async def async_lock(self, **kwargs: object) -> None:
        await self.coordinator.async_lock(self._vin)

    async def async_unlock(self, **kwargs: object) -> None:
        await self.coordinator.async_unlock(self._vin)
