"""Base entity class for all VAG Connect entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VagConnectCoordinator


def _device_name(vehicle: dict, brand: str) -> str:
    """Build device name from brand + model.

    Result: 'Audi Q4 e-tron' → entity_id prefix sensor.audi_q4_e_tron_*
    Fallback when model is unknown: '<Brand> <last 6 of VIN>'
    so two unknown vehicles still get different names.
    """
    model = (vehicle.get("model") or "").strip()
    if model and model.lower() not in ("vag vehicle", "unknown", ""):
        return f"{brand.title()} {model}"
    vin = vehicle.get("vin", "")
    return f"{brand.title()} {vin[-6:]}" if vin else brand.title()


class VagConnectEntity(CoordinatorEntity[VagConnectCoordinator]):
    """Base entity for all VAG Connect platforms.

    Entity-ID schema with has_entity_name=True:
        sensor.{brand}_{model}_{translation_key}
    Examples:
        sensor.audi_q4_e_tron_akkustand
        sensor.skoda_enyaq_iv_reichweite
        binary_sensor.volkswagen_id_4_turen_offen

    Multiple vehicles of same model:
        sensor.audi_q4_e_tron_akkustand    ← first vehicle
        sensor.audi_q4_e_tron_2_akkustand  ← second vehicle (HA adds _2)

    Each vehicle = one HA device (identified by VIN, stable across renames).
    Multiple brands = multiple config entries = separate coordinators.

    parallel_updates=0: cloud_push integration — CC background thread handles
    all API calls. HA entities never call the API directly, so parallel
    entity updates are safe and unlimited within the coordinator.
    """

    _attr_has_entity_name = True
    _attr_parallel_updates = 0  # cloud_push: CC thread owns all updates

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        key: str,
    ) -> None:
        """Initialise entity with coordinator, VIN and entity key."""
        super().__init__(coordinator)
        self._vin = vin
        self._key = key
        # VIN-based unique_id stays stable even when vehicle model is renamed
        self._attr_unique_id = f"{vin}_{key}"

    @property
    def _vehicle(self) -> dict:
        """Current vehicle data dict — safe against None at startup."""
        return (self.coordinator.data or {}).get(self._vin, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Device info shared by all entities of the same vehicle.

        The device name determines the entity_id prefix.
        Using VIN as identifier ensures stability across renames.
        """
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
