# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Image entities for VAG Connect — vehicle render images.

Provides one ImageEntity per vehicle using the best available render image
(side profile ~309KB). All images have transparent PNG backgrounds and are
publicly accessible without authentication.

Data flow:
  VWEUClient.get_vehicles() → VehicleImageFetcher.fetch_image_urls()
  → GraphQL vgql → mediaservice.{brand}.com (public URL)
  → ImageEntity._attr_image_url → HA fetches + caches bytes

Supported brands: Audi, VW EU, Škoda, SEAT, CUPRA (all via vgql)
VW US/CA + Porsche: separate API, images not yet supported.
"""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cariad.api.graphql import VehicleImageFetcher
from .const import DOMAIN
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up image entities — one per vehicle that has render images."""
    coordinator: VagConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for vin, vehicle in coordinator.vehicles.items():
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        best_url = VehicleImageFetcher.best_url(image_urls)
        if best_url:
            entities.append(VagVehicleImage(hass, coordinator, vin, best_url))

    if entities:
        async_add_entities(entities)


class VagVehicleImage(VagConnectEntity, ImageEntity):
    """Vehicle render image entity.

    Uses the best available mediaType (side profile MYAPN8NB preferred).
    Image URL is stable until vehicle config (color, equipment) changes.
    """

    _attr_name = "Fahrzeugbild"
    _attr_content_type = "image/png"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VagConnectCoordinator,
        vin: str,
        image_url: str,
    ) -> None:
        VagConnectEntity.__init__(self, coordinator, vin, "vehicle_image")
        ImageEntity.__init__(self, hass, verify_ssl=True)
        self._attr_image_url = image_url
        self._attr_image_last_updated = datetime.now(tz=timezone.utc)

    @property
    def image_url(self) -> str | None:
        """Return the current best render image URL.

        Re-checks coordinator data in case the URL changed after a vehicle
        config update (e.g. new colour coded after workshop visit).
        """
        vehicle = self._vehicle
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        fresh_url = VehicleImageFetcher.best_url(image_urls)
        if fresh_url and fresh_url != self._attr_image_url:
            # URL changed (vehicle colour/config update) — invalidate cache
            self._attr_image_url = fresh_url
            self._attr_image_last_updated = datetime.now(tz=timezone.utc)
            self._cached_image = None  # type: ignore[assignment]
        url = self._attr_image_url
        # Cast away UndefinedType — we always set a concrete str in __init__
        return url if isinstance(url, str) else None

    @property
    def extra_state_attributes(self) -> dict:
        """Expose all available image URLs as attributes for advanced use."""
        vehicle = self._vehicle
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        attrs: dict = {}
        for media_type, url in image_urls.items():
            attrs[f"url_{media_type.lower()}"] = url
        return attrs
