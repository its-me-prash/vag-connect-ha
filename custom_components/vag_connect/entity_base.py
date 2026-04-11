"""Base entity class for VAG Connect."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VagConnectCoordinator


class VagConnectEntity(CoordinatorEntity[VagConnectCoordinator]):
    """Base entity: shares coordinator + device info per VIN."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._vin = vin
        self._key = key
        self._attr_unique_id = f"{vin}_{key}"

    @property
    def _vehicle(self) -> dict:
        """Current vehicle data dict. Safe against None coordinator.data at startup."""
        return (self.coordinator.data or {}).get(self._vin, {})

    @property
    def device_info(self) -> DeviceInfo:
        """All entities of the same VIN share one HA device."""
        vehicle = self._vehicle
        return DeviceInfo(
            identifiers={(DOMAIN, self._vin)},
            name=vehicle.get("nickname") or self._vin,
            model=vehicle.get("model") or "VAG Vehicle",
            manufacturer=self.coordinator.entry.data.get("brand", "VAG").title(),
            serial_number=self._vin,
        )
