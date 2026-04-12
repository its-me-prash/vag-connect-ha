"""Base entity class for all VAG Connect entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VagConnectCoordinator


def _device_name(vehicle: dict, brand: str) -> str:
    """Return "{Brand} {Model}" or "{Brand} {VIN[-6:]}" as device name."""
    model = (vehicle.get("model") or "").strip()
    if model and model.lower() not in ("vag vehicle", "unknown", ""):
        return f"{brand.title()} {model}"
    vin = vehicle.get("vin", "")
    return f"{brand.title()} {vin[-6:]}" if vin else brand.title()


class VagConnectEntity(CoordinatorEntity[VagConnectCoordinator]):
    """Base entity shared by all VAG Connect platforms.

    parallel_updates=0: cloud_push — the CC background thread owns all API
    calls.  HA entities never initiate requests.
    """

    _attr_has_entity_name = True
    _attr_parallel_updates = 0  # cloud_push: CC thread owns all updates

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        key: str,
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator)
        self._vin = vin
        self._key = key

        self._attr_unique_id = f"{vin}_{key}"

    @property
    def _vehicle(self) -> dict:
        """Current vehicle data dict."""
        return (self.coordinator.data or {}).get(self._vin, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return HA DeviceInfo keyed by VIN."""
        vehicle = self._vehicle
        brand = self.coordinator.entry.data.get("brand", "vag")
        name = _device_name(vehicle, brand)

        return DeviceInfo(
            identifiers={(DOMAIN, self._vin)},
            name=name,
            model=vehicle.get("model") or "VAG Vehicle",
            manufacturer=brand.title(),
            serial_number=self._vin,
            hw_version=(
                str(vehicle.get("model_year"))
                if vehicle.get("model_year")
                else None
            ),
            sw_version=vehicle.get("firmware_version"),
        )
