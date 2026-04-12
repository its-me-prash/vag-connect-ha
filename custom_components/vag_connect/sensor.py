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
    UnitOfEnergy,
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


SENSOR_DESCRIPTIONS: tuple[VagSensorDescription, ...] = (

    VagSensorDescription(
        key="fuel_level",
        data_key="fuel_level",
        name="Tankstand",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        condition="combustion",
    ),
    VagSensorDescription(
        key="battery_soc",
        data_key="battery_soc",
        name="Akkustand",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        condition="electric",
    ),
    VagSensorDescription(
        key="range_km",
        data_key="range_km",
        name="Reichweite",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
    ),
    VagSensorDescription(
        key="range_estimated_full_km",
        data_key="range_estimated_full_km",
        name="Reichweite bei 100%",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        condition="electric",
    ),
    VagSensorDescription(
        key="range_wltp_km",
        data_key="range_wltp_km",
        name="WLTP-Reichweite",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),

    VagSensorDescription(
        key="odometer_km",
        data_key="odometer_km",
        name="Kilometerstand",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),

    VagSensorDescription(
        key="charging_state",
        data_key="charging_state",
        name="Ladevorgang",
        icon="mdi:ev-plug-type2",
        condition="electric",
    ),
    VagSensorDescription(
        key="plug_state",
        data_key="plug_state",
        name="Ladestecker",
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagSensorDescription(
        key="target_soc",
        data_key="target_soc",
        name="Ladeziel",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-high",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_power_kw",
        data_key="charging_power_kw",
        name="Ladeleistung",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_rate_kmh",
        data_key="charging_rate_kmh",
        name="Ladegeschwindigkeit",
        # km/h = km Reichweite pro Stunde → device_class=SPEED → HA rechnet km/h ↔ mph
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="charge_complete_eta",
        data_key="charge_complete_eta",
        name="Ladeende",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-end",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_type",
        data_key="charging_type",
        name="Ladetyp",
        icon="mdi:ev-plug-type2",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),

    VagSensorDescription(
        key="charging_station_name",
        data_key="charging_station_name",
        name="Ladesäule",
        icon="mdi:ev-station",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_station_address",
        data_key="charging_station_address",
        name="Ladesäule Adresse",
        icon="mdi:map-marker-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_station_kw",
        data_key="charging_station_kw",
        name="Ladesäule Max-Leistung",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_station_operator",
        data_key="charging_station_operator",
        name="Ladesäule Betreiber",
        icon="mdi:domain",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),

    VagSensorDescription(
        key="climatisation_state",
        data_key="climatisation_state",
        name="Klimatisierung",
        icon="mdi:thermometer",
    ),
    VagSensorDescription(
        key="target_temperature",
        data_key="target_temperature",
        name="Zieltemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer-auto",
    ),

    VagSensorDescription(
        key="outside_temp",
        data_key="outside_temp",
        name="Außentemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),

    VagSensorDescription(
        key="service_km",
        data_key="service_km",
        name="Nächste Inspektion",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wrench-clock",
    ),
    VagSensorDescription(
        key="service_due_at",
        data_key="service_due_at",
        name="Inspektionsdatum",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VagSensorDescription(
        key="oil_service_km",
        data_key="oil_service_km",
        name="Nächster Ölwechsel",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:oil",
        condition="combustion",
    ),
    VagSensorDescription(
        key="oil_service_at",
        data_key="oil_service_at",
        name="Ölwechseldatum",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:oil",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="combustion",
    ),

    VagSensorDescription(
        key="vehicle_state",
        data_key="vehicle_state",
        name="Fahrzeugzustand",
        icon="mdi:car-info",
    ),
    VagSensorDescription(
        key="connection_state",
        data_key="connection_state",
        name="Verbindung",
        icon="mdi:car-wireless",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),

    VagSensorDescription(
        key="parking_address",
        data_key="parking_address",
        name="Standort",
        icon="mdi:map-marker",
    ),
    VagSensorDescription(
        key="parking_city",
        data_key="parking_city",
        name="Standort Stadt",
        icon="mdi:city",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VagSensorDescription(
        key="heading",
        data_key="heading",
        name="Fahrtrichtung",
        native_unit_of_measurement="°",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),

    VagSensorDescription(
        key="battery_temp",
        data_key="battery_temp",
        name="Akkutemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),
    VagSensorDescription(
        key="battery_cap_kwh",
        data_key="battery_cap_kwh",
        name="Akkukapazität (gesamt)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        condition="electric",
    ),
    VagSensorDescription(
        key="battery_available_kwh",
        data_key="battery_available_kwh",
        name="Akkuenergie verfügbar",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        condition="electric",
    ),

    VagSensorDescription(
        key="firmware_version",
        data_key="firmware_version",
        name="Firmware-Version",
        icon="mdi:update",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VagSensorDescription(
        key="license_plate",
        data_key="license_plate",
        name="Kennzeichen",
        icon="mdi:card-text",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VagSensorDescription(
        key="last_updated_at",
        data_key="last_updated_at",
        name="Zuletzt aktualisiert",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),

    VagSensorDescription(
        key="departure_timer_1_time",
        data_key="departure_timer_1_time",
        name="Abfahrtstimer 1",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="departure_timer_2_time",
        data_key="departure_timer_2_time",
        name="Abfahrtstimer 2",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="departure_timer_3_time",
        data_key="departure_timer_3_time",
        name="Abfahrtstimer 3",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-time-eight-outline",
        condition="electric",
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

    @property
    def native_value(self) -> Any:
        return self._vehicle.get(self.entity_description.data_key)
