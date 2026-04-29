# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Binary sensors for VAG Connect — correct data keys from coordinator."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagBinarySensorDescription(BinarySensorEntityDescription):
    data_key: str = ""
    condition: str | None = None


BINARY_DESCRIPTIONS: tuple[VagBinarySensorDescription, ...] = (
    VagBinarySensorDescription(
        key="doors_locked",
        translation_key="doors_locked",
        data_key="doors_locked",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:car-door-lock",
    ),
    VagBinarySensorDescription(
        key="doors_open",
        translation_key="doors_open",
        data_key="doors_open",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    VagBinarySensorDescription(
        key="windows_open",
        translation_key="windows_open",
        data_key="windows_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-windshield-outline",
    ),
    VagBinarySensorDescription(
        key="plug_connected",
        translation_key="plug_connected",
        data_key="plug_connected",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="is_charging",
        translation_key="is_charging",
        data_key="is_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="climatisation_active",
        translation_key="climatisation_active",
        data_key="climatisation_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:thermometer",
    ),
    VagBinarySensorDescription(
        key="warning_active",
        translation_key="warning_active",
        data_key="warning_active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="warning_engine",
        translation_key="warning_engine",
        data_key="warning_engine",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:engine",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="warning_oil",
        translation_key="warning_oil",
        data_key="warning_oil",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:oil",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="warning_tyre",
        translation_key="warning_tyre",
        data_key="warning_tyre",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:tire",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="warning_brakes",
        translation_key="warning_brakes",
        data_key="warning_brakes",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:car-brake-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

_NEW_BINARY: tuple[VagBinarySensorDescription, ...] = (
    VagBinarySensorDescription(
        key="is_driving",
        translation_key="is_driving",
        data_key="is_driving",
        device_class=BinarySensorDeviceClass.MOTION,
        icon="mdi:car-speed-limiter",
    ),
    VagBinarySensorDescription(
        key="is_online",
        translation_key="is_online",
        data_key="is_online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:car-wireless",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="connector_locked",
        translation_key="connector_locked",
        data_key="connector_locked",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:ev-plug-ccs2",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="window_heating_front",
        translation_key="window_heating_front",
        data_key="window_heating_front",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:car-windshield",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="window_heating_back",
        translation_key="window_heating_back",
        data_key="window_heating_back",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:car-windshield",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)
BINARY_DESCRIPTIONS = BINARY_DESCRIPTIONS + _NEW_BINARY


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[VagConnectBinarySensor] = []

    for vin, vehicle in coordinator.vehicles.items():
        has_battery = vehicle.get("has_battery", False)  # EV + PHEV
        for desc in BINARY_DESCRIPTIONS:
            if desc.condition == "electric" and not has_battery:
                continue
            entities.append(VagConnectBinarySensor(coordinator, vin, desc))

    for vin, vehicle in coordinator.vehicles.items():
        await _async_setup_door_sensors(coordinator, vin, vehicle, entities)

    # v1.8.9 (Session 3C) — per-window binary sensors. Currently only
    # populated for SEAT/CUPRA via the corrected OLA status paths;
    # other brands leave ``windows_individual`` empty so no entities
    # are created for them.
    for vin, vehicle in coordinator.vehicles.items():
        await _async_setup_window_sensors(coordinator, vin, vehicle, entities)

    async_add_entities(entities)


class VagConnectBinarySensor(VagConnectEntity, BinarySensorEntity):
    entity_description: VagBinarySensorDescription

    def __init__(self, coordinator: VagConnectCoordinator, vin: str, description: VagBinarySensorDescription) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        val = self._vehicle.get(self.entity_description.data_key)
        if val is None:
            return None
        return bool(val)


# Per-door binary sensors.

_DOOR_NAMES = {
    "frontLeft":  "Door Front Left",
    "frontRight": "Door Front Right",
    "rearLeft":   "Door Rear Left",
    "rearRight":  "Door Rear Right",
    "trunk":      "Trunk",
    "bonnet":     "Motorhaube",
}


class VagDoorSensor(VagConnectEntity, BinarySensorEntity):
    """Binary Sensor für eine einzelne Tür/Kofferraum/Motorhaube."""

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        door_id: str,
    ) -> None:
        super().__init__(coordinator, vin, f"door_{door_id}")
        self._door_id = door_id
        self._attr_name = _DOOR_NAMES.get(door_id, door_id)
        self._attr_icon = "mdi:car-door" if "door" in door_id.lower() or "rear" in door_id.lower() or "front" in door_id.lower() else "mdi:car-door-lock"

    @property
    def is_on(self) -> bool | None:
        doors = self._vehicle.get("doors_individual", {})
        val = doors.get(self._door_id)
        return bool(val) if val is not None else None


async def _async_setup_door_sensors(
    coordinator: VagConnectCoordinator,
    vin: str,
    vehicle: dict,
    entities: list,
) -> None:
    """Legt individuelle Tür-Sensoren an basierend auf Fahrzeug-Doors-Dict."""
    doors = vehicle.get("doors_individual", {})
    for door_id in doors:
        entities.append(VagDoorSensor(coordinator, vin, door_id))


# v1.8.9 (Session 3C) — per-window binary sensors.
# Layout mirrors ``_DOOR_NAMES``; populated by SEAT/CUPRA OLA paths
# (``status.windows.{position}``). State convention: ``True`` means
# *open* (BinarySensorDeviceClass.WINDOW reports True for "the
# detected event", i.e. open). Internally we store ``True`` for
# *closed* in ``windows_individual`` (consistent with
# ``doors_individual``), so ``is_on`` inverts that.

_WINDOW_NAMES = {
    "frontLeft":  "Window Front Left",
    "frontRight": "Window Front Right",
    "rearLeft":   "Window Rear Left",
    "rearRight":  "Window Rear Right",
}


class VagWindowSensor(VagConnectEntity, BinarySensorEntity):
    """Binary Sensor für ein einzelnes Fenster (CUPRA/SEAT initial)."""

    _attr_device_class = BinarySensorDeviceClass.WINDOW

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        window_id: str,
    ) -> None:
        super().__init__(coordinator, vin, f"window_{window_id}")
        self._window_id = window_id
        self._attr_name = _WINDOW_NAMES.get(window_id, window_id)
        self._attr_icon = "mdi:car-door"

    @property
    def is_on(self) -> bool | None:
        windows = self._vehicle.get("windows_individual", {})
        val = windows.get(self._window_id)
        # Stored value: True == closed. is_on for WINDOW device_class
        # means "open detected" — invert.
        return (not val) if val is not None else None


async def _async_setup_window_sensors(
    coordinator: VagConnectCoordinator,
    vin: str,
    vehicle: dict,
    entities: list,
) -> None:
    """Legt individuelle Fenster-Sensoren an, wenn die Fahrzeug-Antwort
    sie liefert. Heute: SEAT/CUPRA OLA. Andere Marken: leer → keine Entities."""
    windows = vehicle.get("windows_individual", {})
    for window_id in windows:
        entities.append(VagWindowSensor(coordinator, vin, window_id))
