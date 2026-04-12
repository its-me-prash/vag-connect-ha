# Copyright 2026 Prash Nair (@its-me-prash) — Apache License 2.0
"""Number entities for VAG Connect (target SOC, climatisation temperature)."""

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagNumberDescription(NumberEntityDescription):
    data_key: str = ""
    condition: str | None = None  # "electric" | None


NUMBER_DESCRIPTIONS: tuple[VagNumberDescription, ...] = (
    VagNumberDescription(
        key="target_soc",
        data_key="target_soc",
        name="Ladeziel",
        native_unit_of_measurement=PERCENTAGE,
        device_class=NumberDeviceClass.BATTERY,
        native_min_value=10,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-charging-high",
        entity_category=EntityCategory.CONFIG,
        condition="electric",
    ),
    VagNumberDescription(
        key="target_temperature",
        data_key="target_temperature",
        name="Klimatisierungstemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=16,
        native_max_value=30,
        native_step=0.5,
        mode=NumberMode.SLIDER,
        icon="mdi:thermometer",
        entity_category=EntityCategory.CONFIG,
    ),
    VagNumberDescription(
        key="max_charge_current",
        data_key="max_charge_current",
        name="Max. Ladestrom",
        native_unit_of_measurement="A",
        native_min_value=6,
        native_max_value=32,
        native_step=1,
        mode=NumberMode.SLIDER,
        icon="mdi:current-ac",
        entity_category=EntityCategory.CONFIG,
        condition="electric",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[VagConnectNumber] = []

    for vin, vehicle in coordinator.vehicles.items():
        has_battery = vehicle.get("has_battery", False)  # EV + PHEV
        for desc in NUMBER_DESCRIPTIONS:
            if desc.condition == "electric" and not has_battery:
                continue
            entities.append(VagConnectNumber(coordinator, vin, desc))

    async_add_entities(entities)


class VagConnectNumber(VagConnectEntity, NumberEntity):
    entity_description: VagNumberDescription

    def __init__(self, coordinator, vin, description):
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        val = self._vehicle.get(self.entity_description.data_key)
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set slider value — dispatches to the appropriate coordinator action."""
        key = self.entity_description.key
        if key == "target_soc":
            await self.coordinator.async_set_target_soc(self._vin, int(value))
        elif key == "target_temperature":
            await self.coordinator.async_set_climatisation_temperature(self._vin, value)
        elif key == "max_charge_current":
            await self.coordinator.async_set_max_charge_current(self._vin, int(value))
