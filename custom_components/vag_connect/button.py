# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Button entities for VAG Connect (flash lights, force refresh, wake)."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity

# OLA capability IDs (per pycupra) used to gate flash + wake buttons on
# SEAT/CUPRA. Other brands have no capabilities cache yet, so the helper
# returns None for them and the buttons are created unconditionally —
# matching pre-Session-2B behaviour.
_CAP_HONK_AND_FLASH = "honkAndFlash"
_CAP_VEHICLE_WAKEUP = "vehicleWakeUpTrigger"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[VagConnectEntity] = []
    for vin in coordinator.vehicles:
        # Refresh button never gates — it's a coordinator-level operation,
        # not a vehicle command.
        entities.append(VagRefreshButton(coordinator, vin))

        # Capability gating: only skip if we have an explicit ``False`` from
        # the cache. ``None`` (unknown / no capabilities endpoint) keeps the
        # button so other brands behave as before.
        if coordinator.vehicle_supports_capability(vin, _CAP_HONK_AND_FLASH) is not False:
            entities.append(VagFlashButton(coordinator, vin))
        if coordinator.vehicle_supports_capability(vin, _CAP_VEHICLE_WAKEUP) is not False:
            entities.append(VagWakeButton(coordinator, vin))
    async_add_entities(entities)


class VagFlashButton(VagConnectEntity, ButtonEntity):
    """Trigger a honk-and-flash sequence."""

    _attr_translation_key = "flash_button"
    _attr_icon = "mdi:car-light-high"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "flash_button")

    async def async_press(self) -> None:
        await self.coordinator.async_flash_lights(self._vin)


class VagRefreshButton(VagConnectEntity, ButtonEntity):
    """Force an immediate data refresh from the cloud."""

    _attr_translation_key = "refresh_button"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "refresh_button")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()


class VagWakeButton(VagConnectEntity, ButtonEntity):
    """Wake the vehicle from sleep."""

    _attr_translation_key = "wake_button"
    _attr_icon = "mdi:car-connected"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "wake_button")

    async def async_press(self) -> None:
        await self.coordinator.async_wake_vehicle(self._vin)
