# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Sensor platform for VAG Connect.

The VagSensorDescription.condition field gates sensor creation:
  "electric"  — EV and PHEV only (has_battery=True)
  "combustion" — combustion and PHEV only (has_combustion=True)
  None        — all vehicles

charging_rate_kmh uses SensorDeviceClass.SPEED so HA auto-converts km/h ↔ mph
based on the user's unit system preference.
"""
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagSensorDescription(SensorEntityDescription):
    """Sensor description with coordinator data key, condition, and optional default-disabled flag."""

    data_key: str = ""
    condition: str | None = None  # "electric" | "combustion" | None
    suggested_display_precision: int | None = None


SENSOR_DESCRIPTIONS: tuple[VagSensorDescription, ...] = (

    VagSensorDescription(
        key="fuel_level",
        data_key="fuel_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        condition="combustion",
    ),
    VagSensorDescription(
        key="battery_soc",
        data_key="battery_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        condition="electric",
    ),
    VagSensorDescription(
        key="range_km",
        data_key="range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        suggested_display_precision=0,
    ),

    VagSensorDescription(
        key="odometer_km",
        data_key="odometer_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        suggested_display_precision=0,
    ),

    VagSensorDescription(
        key="charging_state",
        data_key="charging_state",
        icon="mdi:ev-plug-type2",
        condition="electric",
    ),
    VagSensorDescription(
        key="plug_state",
        data_key="plug_state",
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagSensorDescription(
        key="target_soc",
        data_key="target_soc",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-high",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_power_kw",
        data_key="charging_power_kw",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_rate_kmh",
        data_key="charging_rate_kmh",
        # km/h = km Reichweite pro Stunde → device_class=SPEED → HA rechnet km/h ↔ mph
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-outline",
        condition="electric",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="charge_complete_eta",
        data_key="charge_complete_eta",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-end",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_type",
        data_key="charging_type",
        icon="mdi:ev-plug-type2",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="electric",
    ),


    VagSensorDescription(
        key="climatisation_state",
        data_key="climatisation_state",
        icon="mdi:thermometer",
    ),
    VagSensorDescription(
        key="target_temperature",
        data_key="target_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer-auto",
    ),

    VagSensorDescription(
        key="outside_temp",
        data_key="outside_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),

    VagSensorDescription(
        key="service_km",
        data_key="service_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wrench-clock",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="service_due_at",
        data_key="service_due_at",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagSensorDescription(
        key="oil_service_km",
        data_key="oil_service_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:oil",
        condition="combustion",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="oil_service_at",
        data_key="oil_service_at",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:oil",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="combustion",
    ),

    VagSensorDescription(
        key="vehicle_state",
        data_key="vehicle_state",
        icon="mdi:car-info",
    ),

    VagSensorDescription(
        key="parking_address",
        data_key="parking_address",
        icon="mdi:map-marker",
    ),
    VagSensorDescription(
        key="parking_city",
        data_key="parking_city",
        icon="mdi:city",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    VagSensorDescription(
        key="battery_temp",
        data_key="battery_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="electric",
    ),

    VagSensorDescription(
        key="last_updated_at",
        data_key="last_updated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    VagSensorDescription(
        key="departure_timer_1_time",
        data_key="departure_timer_1_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="departure_timer_2_time",
        data_key="departure_timer_2_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="departure_timer_3_time",
        data_key="departure_timer_3_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),

    # ── AdBlue (Diesel) ──────────────────────────────────────────────────────
    VagSensorDescription(
        key="adblue_range_km",
        data_key="adblue_range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-check",
        condition="combustion",
        suggested_display_precision=0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor-Entities einrichten."""
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[VagConnectSensor] = []

    for vin, vehicle in coordinator.vehicles.items():
        has_battery    = vehicle.get("has_battery", False)
        has_combustion = vehicle.get("has_combustion", False)

        for desc in SENSOR_DESCRIPTIONS:
            if desc.condition == "electric" and not has_battery:
                continue
            if desc.condition == "combustion" and not has_combustion:
                continue
            entities.append(VagConnectSensor(coordinator, vin, desc))

    async_add_entities(entities)


# Keys that return 0 instead of None when not charging/driving
# This prevents the sensor showing "unavailable" while connected but idle
_ZERO_WHEN_IDLE: frozenset[str] = frozenset({
    "charging_power_kw",
    "charging_rate_kmh",
})


class VagConnectSensor(VagConnectEntity, SensorEntity):
    entity_description: VagSensorDescription

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        description: VagSensorDescription,
    ) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description
        if description.suggested_display_precision is not None:
            self._attr_suggested_display_precision = description.suggested_display_precision

    @property
    def native_value(self) -> Any:
        val = self._vehicle.get(self.entity_description.data_key)
        # charging_power_kw + charging_rate_kmh: API omits these when not charging.
        # Return 0 so the entity shows "0 kW / 0 km/h" instead of "unavailable".
        if val is None and self.entity_description.key in _ZERO_WHEN_IDLE:
            # Only return 0 if plug is connected (makes sense to show 0 kW)
            if self._vehicle.get("plug_connected"):
                return 0

        # DATE sensors: API may return int (days until event) or a date string.
        # HA SensorDeviceClass.DATE requires datetime.date — convert if needed.
        if (
            self.entity_description.device_class == SensorDeviceClass.DATE
            and val is not None
        ):
            if isinstance(val, int):
                from datetime import date, timedelta  # noqa: PLC0415
                return date.today() + timedelta(days=val)
            if isinstance(val, str):
                try:
                    from datetime import date as _date  # noqa: PLC0415
                    return _date.fromisoformat(val[:10])
                except ValueError:
                    return None

        return val
