# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Button entities for VAG Connect (flash lights, force refresh, wake)."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BRAND
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity

# Capability IDs vary by backend. The OLA documentation (pycupra) uses
# camelCase strings like below for SEAT/CUPRA. CARIAD BFF (Audi/VW EU)
# uses a different vocabulary that we have not yet verified against
# real vehicles, so gating is currently scoped to brands whose IDs we
# trust — see ``_BRANDS_WITH_CAPABILITY_GATING`` below.
_CAP_HONK_AND_FLASH = "honkAndFlash"
_CAP_VEHICLE_WAKEUP = "vehicleWakeUpTrigger"

# Brands whose capability vocabulary we've verified end-to-end. Other
# brands fetch capabilities (cache populated) but the IDs may not match
# what we look up below, so we skip gating for them to avoid hiding
# entities by mistake.
_BRANDS_WITH_CAPABILITY_GATING = frozenset({"seat", "cupra"})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    brand = str(entry.data.get(CONF_BRAND, "")).lower()
    gating_active = brand in _BRANDS_WITH_CAPABILITY_GATING

    entities: list[VagConnectEntity] = []
    for vin in coordinator.vehicles:
        # Refresh button never gates — it's a coordinator-level operation,
        # not a vehicle command.
        entities.append(VagRefreshButton(coordinator, vin))

        # Capability gating: only skip if we have an explicit ``False`` from
        # the cache AND the brand uses the OLA capability vocabulary.
        # ``None`` (unknown) keeps the button so other brands behave as before.
        flash_supported = (
            coordinator.vehicle_supports_capability(vin, _CAP_HONK_AND_FLASH)
            if gating_active
            else None
        )
        wake_supported = (
            coordinator.vehicle_supports_capability(vin, _CAP_VEHICLE_WAKEUP)
            if gating_active
            else None
        )
        if flash_supported is not False:
            entities.append(VagFlashButton(coordinator, vin))
        if wake_supported is not False:
            entities.append(VagWakeButton(coordinator, vin))
    async_add_entities(entities)


class VagFlashButton(VagConnectEntity, ButtonEntity):
    """Trigger a honk-and-flash sequence."""

    _attr_translation_key = "flash_button"
    _attr_icon = "mdi:car-light-high"
    # v1.9.1 — Phase 2 gating: hide once a 403/missing-capability is seen.
    _command_id = "command_flash"

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
    # v1.9.1 — Phase 2 gating.
    _command_id = "command_wake"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "wake_button")

    async def async_press(self) -> None:
        await self.coordinator.async_wake_vehicle(self._vin)
