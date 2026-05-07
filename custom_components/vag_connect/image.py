# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Image entities for VAG Connect — 7 vehicle render images per vehicle.

Creates one ImageEntity per MediaType per vehicle:
  image.{vehicle}_render_icon       (MS_MYP3,   76 KB)
  image.{vehicle}_render_small      (MS_MYP4,  117 KB)
  image.{vehicle}_render_medium     (MS_MYP5,  196 KB)
  image.{vehicle}_render_side_sm    (MYAPN3NB, 158 KB)
  image.{vehicle}_render_side_lg    (MYAPN8NB, 309 KB) ← recommended
  image.{vehicle}_render_angle_hd   (MYAAN3NB, 1.7 MB)
  image.{vehicle}_render_angle_lg   (MYAAN8NB, 879 KB)

All images are cached locally under /config/www/vehicles/{vin}_{tag}.png
for offline use and fast Lovelace card loading.
"""

from __future__ import annotations

import logging

import asyncio
import os
from datetime import datetime, timezone

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cariad._util import mask_vin
from .cariad.api.graphql import RENDER_IMAGE_TYPES
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity

_LOGGER = logging.getLogger(__name__)

# Local cache directory under HA's /config/www/
_CACHE_SUBDIR = "vehicles"


def _local_path(hass: HomeAssistant, vin: str, tag: str) -> str:
    """Return absolute path to local cached PNG file."""
    www_dir = hass.config.path("www", _CACHE_SUBDIR)
    return os.path.join(www_dir, f"{vin}_{tag}.png")


def _local_url(vin: str, tag: str) -> str:
    """Return HA /local/ URL for the cached image (for Lovelace use)."""
    return f"/local/{_CACHE_SUBDIR}/{vin}_{tag}.png"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up image entities — 7 per vehicle that has render images.

    If image_urls are not yet available at setup time (GraphQL fetch pending
    or failed), a coordinator listener will retry once data arrives.
    """
    coordinator: VagConnectCoordinator = entry.runtime_data
    added_vins: set[str] = set()

    # Ensure cache dir exists
    www_dir = hass.config.path("www", _CACHE_SUBDIR)
    await hass.async_add_executor_job(os.makedirs, www_dir, 0o755, True)

    def _add_entities_for_vin(vin: str, vehicle: dict) -> list:
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        entities = []
        for meta in RENDER_IMAGE_TYPES:
            url = image_urls.get(meta["media_type"])
            if url:
                entities.append(VagRenderImageEntity(hass, coordinator, vin, meta, url))
        # v1.22.0 (Bundle 2 Phase B) — Skoda render via widget endpoint.
        # Skoda's Cariad-BFF doesn't have the GraphQL media endpoint
        # that Audi/VW use; instead the v1.20.0 widget endpoint
        # (myskoda PR #557) carries a single ``vehicle.renderUrl``
        # already populated to ``data["render_url"]``. Expose as one
        # ImageEntity per Skoda VIN — separate class because it
        # doesn't fit the 7-MediaType pattern of Audi/VW.
        skoda_render = vehicle.get("render_url")
        if isinstance(skoda_render, str) and skoda_render.startswith("http"):
            entities.append(VagSkodaWidgetImageEntity(
                hass, coordinator, vin, skoda_render,
            ))
        return entities

    # Initial setup — add entities for vehicles that already have image_urls
    entities = []
    for vin, vehicle in coordinator.vehicles.items():
        if vehicle.get("image_urls"):
            new = _add_entities_for_vin(vin, vehicle)
            if new:
                entities.extend(new)
                added_vins.add(vin)
                _LOGGER.debug("Image entities created for %s (%d entities)", mask_vin(vin), len(new))
        else:
            _LOGGER.debug(
                "No image_urls for %s at setup — will retry on next coordinator update", mask_vin(vin)
            )

    if entities:
        async_add_entities(entities)
        asyncio.ensure_future(_cache_all_images(hass, coordinator))

    # Listener: create entities if image_urls arrive on a subsequent poll
    def _on_coordinator_update() -> None:
        new_entities = []
        for vin, vehicle in coordinator.vehicles.items():
            if vin in added_vins:
                continue
            if vehicle.get("image_urls"):
                new = _add_entities_for_vin(vin, vehicle)
                if new:
                    new_entities.extend(new)
                    added_vins.add(vin)
                    _LOGGER.info(
                        "Image entities created for %s on coordinator update (%d entities)",
                        vin, len(new),
                    )
        if new_entities:
            async_add_entities(new_entities)
            asyncio.ensure_future(_cache_all_images(hass, coordinator))

    entry.async_on_unload(coordinator.async_add_listener(_on_coordinator_update))


async def _cache_all_images(
    hass: HomeAssistant,
    coordinator: VagConnectCoordinator,
) -> None:
    """Download and cache all render images locally (background task)."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession  # noqa: PLC0415
    session = async_get_clientsession(hass)

    for vin, vehicle in coordinator.vehicles.items():
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        for meta in RENDER_IMAGE_TYPES:
            url = image_urls.get(meta["media_type"])
            if not url:
                continue
            local = _local_path(hass, vin, meta["tag"])
            if await hass.async_add_executor_job(os.path.exists, local):
                continue  # Already cached
            try:
                async with session.get(url, timeout=None) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        await hass.async_add_executor_job(
                            _write_file, local, content
                        )
                        _LOGGER.debug(  # type: ignore[name-defined]
                            "Cached %s → %s (%d KB)",
                            meta["tag"], local, len(content) // 1024,
                        )
            except Exception:  # noqa: BLE001
                pass  # Cache failure is non-critical
        # v1.22.0 (Bundle 2 Phase B) — cache Skoda widget render too
        skoda_url = vehicle.get("render_url")
        if isinstance(skoda_url, str) and skoda_url.startswith("http"):
            local = _local_path(hass, vin, "widget")
            if not await hass.async_add_executor_job(os.path.exists, local):
                try:
                    async with session.get(skoda_url, timeout=None) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            await hass.async_add_executor_job(
                                _write_file, local, content
                            )
                            _LOGGER.debug(
                                "Cached Skoda widget render → %s (%d KB)",
                                local, len(content) // 1024,
                            )
                except Exception:  # noqa: BLE001
                    pass


def _write_file(path: str, content: bytes) -> None:
    """Write bytes to file (runs in executor)."""
    with open(path, "wb") as f:
        f.write(content)




class VagRenderImageEntity(VagConnectEntity, ImageEntity):
    """One render image entity for a single MediaType + vehicle combination.

    Attributes expose all metadata for Lovelace use:
      - source_url: the original public URL from mediaservice
      - local_path: /local/vehicles/{vin}_{tag}.png (usable in picture-entity)
      - tag, media_type, view_description, recommended_use, file_size_approx
      - vehicle_name, vin, media_short_name, media_long_name
    """

    _attr_content_type = "image/png"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VagConnectCoordinator,
        vin: str,
        meta: dict[str, str],
        initial_url: str,
    ) -> None:
        VagConnectEntity.__init__(self, coordinator, vin, meta["entity_suffix"])
        ImageEntity.__init__(self, hass, verify_ssl=True)
        self._meta = meta
        self._attr_name = self._label_for(meta)
        self._attr_image_url = initial_url
        self._attr_image_last_updated = datetime.now(tz=timezone.utc)

    @staticmethod
    def _label_for(meta: dict[str, str]) -> str:
        """Human-readable name, e.g. 'Seitenprofil groß'."""
        return meta["view_description"]

    @property
    def image_url(self) -> str | None:
        """Return current URL — refreshes if vehicle config changed."""
        vehicle = self._vehicle
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        fresh = image_urls.get(self._meta["media_type"])
        if fresh and fresh != self._attr_image_url:
            self._attr_image_url = fresh
            self._attr_image_last_updated = datetime.now(tz=timezone.utc)
            self._cached_image = None  # type: ignore[assignment]
            # Delete stale local cache so it gets re-downloaded
            local = _local_path(self.hass, self._vin, self._meta["tag"])
            try:
                if os.path.exists(local):
                    os.remove(local)
            except OSError:
                pass
        return self._attr_image_url if isinstance(self._attr_image_url, str) else None

    @property
    def extra_state_attributes(self) -> dict:
        """Full metadata for Lovelace and automations."""
        vehicle = self._vehicle
        image_urls: dict[str, str] = vehicle.get("image_urls") or {}
        url = image_urls.get(self._meta["media_type"])
        local = _local_url(self._vin, self._meta["tag"])
        local_abs = _local_path(self.hass, self._vin, self._meta["tag"])

        attrs: dict = {
            "media_type":       self._meta["media_type"],
            "tag":              self._meta["tag"],
            "view_description": self._meta["view_description"],
            "recommended_use":  self._meta["recommended_use"],
            "file_size_approx": self._meta["file_size_approx"],
            "source_url":       url,
            "local_path":       local,
            "local_cached":     os.path.exists(local_abs),
            "vin":              self._vin,
        }

        # Media names from GraphQL
        if vehicle.get("media_short_name"):
            attrs["vehicle_short_name"] = vehicle["media_short_name"]
        if vehicle.get("media_long_name"):
            attrs["vehicle_long_name"] = vehicle["media_long_name"]
        if vehicle.get("media_exterior_color"):
            attrs["exterior_color"] = vehicle["media_exterior_color"]

        return attrs


class VagSkodaWidgetImageEntity(VagConnectEntity, ImageEntity):
    """v1.22.0 (Bundle 2 Phase B) — Skoda widget render image.

    Single ImageEntity per Skoda VIN, populated from
    ``data["render_url"]`` (which v1.20.0 widget endpoint set from
    ``vehicle.renderUrl`` per myskoda PR #557).

    Differences vs ``VagRenderImageEntity``:
    - Skoda exposes ONE render URL (not 7 MediaType variants like
      Audi/VW GraphQL)
    - URL refresh check uses ``data["render_url"]`` instead of
      ``image_urls`` dict lookup
    - Cached locally as ``{vin}_widget.png`` (single file per VIN)
    """

    _attr_content_type = "image/png"
    _SKODA_TAG = "widget"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VagConnectCoordinator,
        vin: str,
        initial_url: str,
    ) -> None:
        VagConnectEntity.__init__(self, coordinator, vin, "render_widget")
        ImageEntity.__init__(self, hass, verify_ssl=True)
        self._attr_name = "Vehicle Render"
        self._attr_image_url = initial_url
        self._attr_image_last_updated = datetime.now(tz=timezone.utc)

    @property
    def image_url(self) -> str | None:
        """Return current URL — refreshes if widget endpoint published
        a new renderUrl (e.g. user changed paint via app)."""
        vehicle = self._vehicle
        fresh = vehicle.get("render_url")
        if (
            isinstance(fresh, str)
            and fresh.startswith("http")
            and fresh != self._attr_image_url
        ):
            self._attr_image_url = fresh
            self._attr_image_last_updated = datetime.now(tz=timezone.utc)
            self._cached_image = None  # type: ignore[assignment]
            local = _local_path(self.hass, self._vin, self._SKODA_TAG)
            try:
                if os.path.exists(local):
                    os.remove(local)
            except OSError:
                pass
        return (
            self._attr_image_url
            if isinstance(self._attr_image_url, str)
            else None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Skoda widget metadata for Lovelace use."""
        vehicle = self._vehicle
        url = vehicle.get("render_url")
        local = _local_url(self._vin, self._SKODA_TAG)
        local_abs = _local_path(self.hass, self._vin, self._SKODA_TAG)
        attrs: dict = {
            "tag":              self._SKODA_TAG,
            "view_description": "Skoda widget render",
            "source":           "myskoda widget endpoint (v1.20.0)",
            "source_url":       url,
            "local_path":       local,
            "local_cached":     os.path.exists(local_abs),
            "vin":              self._vin,
        }
        if vehicle.get("license_plate"):
            attrs["license_plate"] = vehicle["license_plate"]
        if vehicle.get("model"):
            attrs["model"] = vehicle["model"]
        return attrs
