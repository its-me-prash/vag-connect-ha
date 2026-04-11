"""Sensors for VAG Connect — aligned to real CarConnectivity data model.

Conditions:
  "electric"    → Nur für Fahrzeuge mit Akku (EV + PHEV) — has_battery=True
  "combustion"  → Nur für Fahrzeuge mit Verbrennungsmotor (Verbrenner + PHEV) — has_combustion=True
  None          → Alle Fahrzeuge

Ladegeschwindigkeit (charging_rate_kmh):
  CarConnectivity gibt charging.rate als SpeedAttribute (Einheit: km/h) zurück.
  Bedeutung: Wie viele km Reichweite werden pro Stunde geladen.
  Beispiel: 50 kW Lader, 6 km/kWh Effizienz → 300 km/h Rate
  Einheit km/h ist korrekt (≠ Fahrzeuggeschwindigkeit).
  Kein SensorDeviceClass.SPEED — das wäre semantisch falsch.
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
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagSensorDescription(SensorEntityDescription):
    """Extended sensor description with coordinator data-key and condition."""
    data_key: str = ""
    condition: str | None = None  # "electric" | "combustion" | None


SENSOR_DESCRIPTIONS: tuple[VagSensorDescription, ...] = (
    # ── Antrieb: Verbrenner ──────────────────────────────────────────────────
    VagSensorDescription(
        key="fuel_level",
        data_key="fuel_level",
        name="Tankfüllstand",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        condition="combustion",  # Verbrenner + PHEV
    ),
    # ── Antrieb: Elektrisch (EV + PHEV) ─────────────────────────────────────
    VagSensorDescription(
        key="battery_soc",
        data_key="battery_soc",
        name="Batterieladestand",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        condition="electric",  # EV + PHEV
    ),
    # ── Reichweite: alle Fahrzeuge ───────────────────────────────────────────
    VagSensorDescription(
        key="range_km",
        data_key="range_km",
        name="Reichweite",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
    ),
    # ── Kilometerstand ───────────────────────────────────────────────────────
    VagSensorDescription(
        key="odometer_km",
        data_key="odometer_km",
        name="Kilometerstand",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    # ── Laden (nur EV + PHEV) ────────────────────────────────────────────────
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
    VagSensorDescription(
        key="charging_power_kw",
        data_key="charging_power_kw",
        name="Ladeleistung",
        # PowerAttribute von CarConnectivity — direkt in kW
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_rate_kmh",
        data_key="charging_rate_kmh",
        name="Lade-Reichweite/h",
        # SpeedAttribute von CarConnectivity — Einheit km/h
        # Bedeutung: km Reichweite die pro Stunde geladen werden
        # Beispiel: DC 50 kW bei 6 km/kWh → 300 km/h
        # NICHT DeviceClass.SPEED (das wäre Fahrzeuggeschwindigkeit)
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-outline",
        condition="electric",
    ),
    # ── Klimatisierung ───────────────────────────────────────────────────────
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
    # ── Umgebung ─────────────────────────────────────────────────────────────
    VagSensorDescription(
        key="outside_temp",
        data_key="outside_temp",
        name="Außentemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    # ── Wartung ──────────────────────────────────────────────────────────────
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
        condition="combustion",  # Verbrenner + PHEV
    ),
    VagSensorDescription(
        key="oil_service_at",
        data_key="oil_service_at",
        name="Ölservicedatum",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:oil",
        condition="combustion",  # Verbrenner + PHEV
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
        has_battery   = vehicle.get("has_battery", False)    # EV + PHEV
        has_combustion = vehicle.get("has_combustion", False)  # Verbrenner + PHEV

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


# ── Neue Sensoren — einzigartig in VAG Connect ───────────────────────────────
_NEW_SENSORS: tuple[VagSensorDescription, ...] = (

    # Fahrzeugstatus
    VagSensorDescription(
        key="vehicle_state",
        data_key="vehicle_state",
        name="Fahrzeugstatus",
        icon="mdi:car-info",
    ),
    VagSensorDescription(
        key="connection_state",
        data_key="connection_state",
        name="Verbindungsstatus",
        icon="mdi:car-wireless",
    ),

    # Position
    VagSensorDescription(
        key="parking_address",
        data_key="parking_address",
        name="Parkadresse",
        icon="mdi:map-marker",
    ),
    VagSensorDescription(
        key="parking_city",
        data_key="parking_city",
        name="Parkstadt",
        icon="mdi:city",
    ),
    VagSensorDescription(
        key="heading",
        data_key="heading",
        name="Fahrtrichtung",
        native_unit_of_measurement="°",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),

    # Akku (nur EV + PHEV)
    VagSensorDescription(
        key="battery_temp",
        data_key="battery_temp",
        name="Akkutemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        condition="electric",
    ),
    VagSensorDescription(
        key="battery_cap_kwh",
        data_key="battery_cap_kwh",
        name="Akkukapazität",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        condition="electric",
    ),

    # Laden (EV + PHEV)
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
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_station_operator",
        data_key="charging_station_operator",
        name="Ladesäule Betreiber",
        icon="mdi:domain",
        condition="electric",
    ),

    # Fahrzeugdaten
    VagSensorDescription(
        key="firmware_version",
        data_key="firmware_version",
        name="Firmware",
        icon="mdi:update",
    ),
    VagSensorDescription(
        key="license_plate",
        data_key="license_plate",
        name="Kennzeichen",
        icon="mdi:card-text",
    ),
)

SENSOR_DESCRIPTIONS = SENSOR_DESCRIPTIONS + _NEW_SENSORS
