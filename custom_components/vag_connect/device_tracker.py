"""Device tracker (GPS) for VAG Connect."""

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities = []
    for vin, vehicle in coordinator.vehicles.items():
        if vehicle.get("latitude") is not None:
            entities.append(VagConnectTracker(coordinator, vin))
    async_add_entities(entities)


class VagConnectTracker(VagConnectEntity, TrackerEntity):
    """GPS tracker entity — shows car on HA map."""

    _attr_icon = "mdi:car"
    _attr_name = "Position"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "position")

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        return self._vehicle.get("latitude")

    @property
    def longitude(self) -> float | None:
        return self._vehicle.get("longitude")

    @property
    def location_accuracy(self) -> int:
        return 10  # metres
