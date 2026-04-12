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
        data_key="doors_locked",
        name="Türen verriegelt",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:car-door-lock",
    ),
    VagBinarySensorDescription(
        key="doors_open",
        data_key="doors_open",
        name="Türen offen",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    VagBinarySensorDescription(
        key="windows_open",
        data_key="windows_open",
        name="Fenster offen",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-windshield-outline",
    ),
    VagBinarySensorDescription(
        key="plug_connected",
        data_key="plug_connected",
        name="Ladekabel verbunden",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="is_charging",
        data_key="is_charging",
        name="Lädt",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="climatisation_active",
        data_key="climatisation_active",
        name="Klimatisierung aktiv",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:thermometer",
    ),
)

_NEW_BINARY: tuple[VagBinarySensorDescription, ...] = (
    VagBinarySensorDescription(
        key="is_driving",
        data_key="is_driving",
        name="In Fahrt",
        device_class=BinarySensorDeviceClass.MOTION,
        icon="mdi:car-speed-limiter",
    ),
    VagBinarySensorDescription(
        key="is_online",
        data_key="is_online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:car-wireless",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VagBinarySensorDescription(
        key="connector_locked",
        data_key="connector_locked",
        name="Stecker verriegelt",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:ev-plug-ccs2",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="electric",
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

    async_add_entities(entities)


class VagConnectBinarySensor(VagConnectEntity, BinarySensorEntity):
    entity_description: VagBinarySensorDescription

    def __init__(self, coordinator, vin, description):
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
    "frontLeft":  "Tür vorne links",
    "frontRight": "Tür vorne rechts",
    "rearLeft":   "Tür hinten links",
    "rearRight":  "Tür hinten rechts",
    "trunk":      "Kofferraum",
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
        return doors.get(self._door_id)


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
