# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Select entities for VAG Connect — Lademodus."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity

# CARIAD charge modes — values as returned by API
_CHARGE_MODES: dict[str, str] = {
    "MANUAL":                    "Manuell",
    "TIMER":                     "Timer",
    "PREFERRED_CHARGING_TIMES":  "Bevorzugte Ladezeiten",
    "ONLY_OWN_CURRENT":          "Nur Eigenstrom",
    "IMMEDIATE_DISCHARGING":     "Sofort entladen",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up charge-mode selects."""
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[SelectEntity] = []

    for vin, vehicle in coordinator.vehicles.items():
        if vehicle.get("has_battery"):  # EV + PHEV
            entities.append(VagChargeModeSelect(coordinator, vin))

    async_add_entities(entities)


class VagChargeModeSelect(VagConnectEntity, SelectEntity):
    """Select entity for charging mode (MANUAL / TIMER / PREFERRED_CHARGING_TIMES)."""

    _attr_translation_key = "charge_mode_select"
    _attr_icon = "mdi:ev-plug-type2"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(_CHARGE_MODES.values())  # HA shows translated labels

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "charge_mode_select")

    @property
    def current_option(self) -> str | None:
        """Return the current charge mode as a human-readable label."""
        raw = self._vehicle.get("charge_mode")
        if raw is None:
            return None
        result = _CHARGE_MODES.get(str(raw).upper(), str(raw))
        return str(result) if result else None

    async def async_select_option(self, option: str) -> None:
        """Set the charging mode — translates label back to API key."""
        # Reverse lookup: label → API key
        reverse = {v: k for k, v in _CHARGE_MODES.items()}
        api_key = reverse.get(option, option.upper())
        await self.coordinator.async_set_charge_mode(self._vin, api_key)
