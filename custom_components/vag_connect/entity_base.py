# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Base entity class for all VAG Connect entities."""

from __future__ import annotations
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .cariad.api.graphql import VehicleImageFetcher
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

    parallel_updates=0: the coordinator's background poll loop owns all API
    calls.  HA entities never initiate requests directly.

    available: per-VIN — entity is unavailable when its vehicle's last poll
    failed, even if other vehicles in the same account succeeded.

    v1.9.1 (Capability-Filter Phase 2, #56) — command-bound entities can
    set ``_command_id`` on subclass init. When set, the ``available``
    property additionally consults
    ``coordinator.is_command_known_unsupported(vin, command)`` and returns
    ``False`` once the backend has explicitly rejected the command (missing
    capability, subscription expired, not entitled). Entities without a
    command (sensors, binary sensors) leave ``_command_id`` as ``None``
    and behave exactly as before.
    """

    _attr_has_entity_name = True
    _attr_parallel_updates = 0  # coordinator owns all API requests
    # v1.9.1 — set on subclasses that map 1:1 to a coordinator command.
    # ``None`` means "not a command-bound entity, never use Phase-2 gating".
    _command_id: str | None = None

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
    def _vehicle(self) -> dict[str, Any]:
        """Current vehicle data dict."""
        data: dict[str, Any] = self.coordinator.data or {}
        result: dict[str, Any] = data.get(self._vin, {})
        return result

    @property
    def available(self) -> bool:
        """Per-VIN availability — falls back to coordinator default if unknown.

        Reflects the success of the last per-vehicle poll, so that a single
        failing vehicle does not affect entities for other vehicles in the
        same account.

        v1.9.1 (Capability-Filter Phase 2): for command-bound entities,
        also returns False if the coordinator's ``FeatureState`` records a
        definitive "command not supported" outcome from a previous attempt.
        """
        if not super().available:
            return False
        if not self.coordinator.is_vehicle_available(self._vin):
            return False
        if self._command_id is not None:
            try:
                if self.coordinator.is_command_known_unsupported(
                    self._vin, self._command_id
                ):
                    return False
            except Exception:  # noqa: BLE001
                # Bookkeeping must never affect availability negatively
                pass
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return HA DeviceInfo keyed by VIN.

        Sets entity_picture to the vehicle render image (side_large preferred)
        so the car photo appears on the device page in HA.
        """
        vehicle = self._vehicle
        brand = self.coordinator.entry.data.get("brand", "vag")
        name = _device_name(vehicle, brand)

        # Use vehicle render image as device picture
        image_urls: dict = vehicle.get("image_urls") or {}
        picture = VehicleImageFetcher.best_url(image_urls) if image_urls else None

        info = DeviceInfo(
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
        if picture:
            info["entity_picture"] = picture  # type: ignore[typeddict-unknown-key]
        return info

    @property
    def entity_picture(self) -> str | None:
        """Return vehicle render image URL as entity picture.

        Shows the car photo on the entity detail page and in dashboards
        that display entity pictures (e.g. mushroom cards).
        Falls back to None so HA uses the entity's icon instead.
        """
        vehicle = self._vehicle
        image_urls: dict = vehicle.get("image_urls") or {}
        return VehicleImageFetcher.best_url(image_urls) if image_urls else None
