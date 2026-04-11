"""Button entities for VAG Connect (flash lights, force refresh)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for vin in coordinator.vehicles:
        entities.append(VagFlashButton(coordinator, vin))
        entities.append(VagRefreshButton(coordinator, vin))
        entities.append(VagWakeButton(coordinator, vin))
    async_add_entities(entities)


class VagFlashButton(VagConnectEntity, ButtonEntity):
    """Flash lights (honk & flash)."""

    _attr_name = "Lichtsignal"
    _attr_icon = "mdi:car-light-high"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "flash_button")

    async def async_press(self) -> None:
        await self.coordinator.async_flash_lights(self._vin)


class VagRefreshButton(VagConnectEntity, ButtonEntity):
    """Force a data refresh from the cloud."""

    _attr_name = "Daten aktualisieren"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "refresh_button")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()


class VagWakeButton(VagConnectEntity, ButtonEntity):
    """Fahrzeug aufwecken (wake-sleep)."""

    _attr_name = "Fahrzeug aufwecken"
    _attr_icon = "mdi:car-connected"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "wake_button")

    async def async_press(self) -> None:
        await self.coordinator.async_wake_vehicle(self._vin)
