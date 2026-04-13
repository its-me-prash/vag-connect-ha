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
    def _vehicle(self) -> dict[str, Any]:
        """Current vehicle data dict."""
        data: dict[str, Any] = self.coordinator.data or {}
        result: dict[str, Any] = data.get(self._vin, {})
        return result

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
