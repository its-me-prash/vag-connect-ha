"""Sensors for VAG Connect — aligned to real CarConnectivity data model."""
from __future__ import annotations

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
    UnitOfLength,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagSensorDescription(SensorEntityDescription):
    """Extended description with coordinator data-key and optional condition."""
    data_key: str = ""
    condition: str | None = None  # "electric" | "combustion" | None


SENSOR_DESCRIPTIONS: tuple[VagSensorDescription, ...] = (
    # ── Fuel / Battery ──────────────────────────────────────────────
    VagSensorDescription(
        key="fuel_level",
        data_key="fuel_level",
        name="Tankfüllstand",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        condition="combustion",
    ),
    VagSensorDescription(
        key="battery_soc",
        data_key="battery_soc",
        name="Batterieladestand",
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
    # ── Odometer ────────────────────────────────────────────────────
    VagSensorDescription(
        key="odometer_km",
        data_key="odometer_km",
        name="Kilometerstand",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    # ── Charging ────────────────────────────────────────────────────
    VagSensorDescription(
        key="charging_state",
        data_key="charging_state",
        name="Ladestatus",
        icon="mdi:ev-plug-type2",
        condition="electric",
    ),
    VagSensorDescription(
        key="plug_state",
        data_key="plug_state",
        name="Steckerstatus",
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagSensorDescription(
        key="target_soc",
        data_key="target_soc",
        name="Ladziel",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-high",
        condition="electric",
    ),
    # ── Climatisation ───────────────────────────────────────────────
    VagSensorDescription(
        key="climatisation_state",
        data_key="climatisation_state",
        name="Klimatisierungsstatus",
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
    # ── Environment ─────────────────────────────────────────────────
    VagSensorDescription(
        key="outside_temp",
        data_key="outside_temp",
        name="Außentemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    # ── Maintenance ─────────────────────────────────────────────────
    VagSensorDescription(
        key="service_km",
        data_key="service_km",
        name="Inspektion fällig in",
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
    ),
    VagSensorDescription(
        key="oil_service_km",
        data_key="oil_service_km",
        name="Ölservice fällig in",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:oil",
        condition="combustion",
    ),
    VagSensorDescription(
        key="oil_service_at",
        data_key="oil_service_at",
        name="Ölservicedatum",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:oil",
        condition="combustion",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: VagConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[VagConnectSensor] = []

    for vin, vehicle in coordinator.vehicles.items():
        is_electric = vehicle.get("is_electric", False)
        for desc in SENSOR_DESCRIPTIONS:
            if desc.condition == "electric" and not is_electric:
                continue
            if desc.condition == "combustion" and is_electric:
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


# ── Issue #2: Ladeleistung + Ladegeschwindigkeit ──────────────────────────────
SENSOR_DESCRIPTIONS = SENSOR_DESCRIPTIONS + (
    VagSensorDescription(
        key="charging_power_kw",
        data_key="charging_power_kw",
        name="Ladeleistung",
        native_unit_of_measurement="kW",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:ev-plug-type2",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_rate_kmh",
        data_key="charging_rate_kmh",
        name="Ladegeschwindigkeit",
        native_unit_of_measurement="km/h",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        condition="electric",
    ),
)
