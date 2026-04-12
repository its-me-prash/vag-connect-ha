# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""VAG Group GraphQL client for vehicle render images.

Fetches render image URLs via the VW Group vgql proxy.
Images are publicly accessible (no auth needed to GET the PNG URL).

Endpoint confirmed working for Audi (April 2026):
  POST https://www.audi.de/userinfo-emea/v2/myaudi/proxy/vgql/v1/graphql
  Auth: Bearer {IDK access_token}

Research source: vag-connect-ha Issue #15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession, ClientTimeout

_LOGGER = logging.getLogger(__name__)

# GraphQL endpoints per brand (proxy path differs, vgql layer is shared VW Group)
_GRAPHQL_ENDPOINTS: dict[str, str] = {
    "audi":       "https://www.audi.de/userinfo-emea/v2/myaudi/proxy/vgql/v1/graphql",
    "volkswagen": "https://www.volkswagen.de/app/proxy/vgql/v1/graphql",
    "skoda":      "https://www.skoda-auto.com/myskoda/proxy/vgql/v1/graphql",
    "seat":       "https://www.seat.com/myway/proxy/vgql/v1/graphql",
    "cupra":      "https://www.cupraofficial.com/mycupra/proxy/vgql/v1/graphql",
}

# Complete metadata for all 7 render image types
# Order = preference (best for Lovelace first)
RENDER_IMAGE_TYPES: list[dict[str, str]] = [
    {
        "media_type":       "MYAPN8NB",
        "entity_suffix":    "render_side_lg",
        "tag":              "side_large",
        "view_description": "Seitenprofil groß",
        "recommended_use":  "⭐ Empfohlen für Lovelace-Karten und Dashboards",
        "file_size_approx": "309 KB",
    },
    {
        "media_type":       "MYAAN8NB",
        "entity_suffix":    "render_angle_lg",
        "tag":              "angle_large",
        "view_description": "3/4-Ansicht groß",
        "recommended_use":  "Dashboard-Karten, Picture-Entity Cards",
        "file_size_approx": "879 KB",
    },
    {
        "media_type":       "MS_MYP5",
        "entity_suffix":    "render_medium",
        "tag":              "medium",
        "view_description": "3/4-Ansicht mittel",
        "recommended_use":  "Standard-Karten, Grid-Layouts",
        "file_size_approx": "196 KB",
    },
    {
        "media_type":       "MYAPN3NB",
        "entity_suffix":    "render_side_sm",
        "tag":              "side_small",
        "view_description": "Seitenprofil klein",
        "recommended_use":  "Kompakte Seitenansicht, horizontale Karten",
        "file_size_approx": "158 KB",
    },
    {
        "media_type":       "MS_MYP4",
        "entity_suffix":    "render_small",
        "tag":              "small",
        "view_description": "3/4-Ansicht klein",
        "recommended_use":  "Kleine Karten, Sidebar-Widgets",
        "file_size_approx": "117 KB",
    },
    {
        "media_type":       "MS_MYP3",
        "entity_suffix":    "render_icon",
        "tag":              "icon",
        "view_description": "3/4-Ansicht Icon",
        "recommended_use":  "Mini-Icon in Listen, Badges, Chip-Cards",
        "file_size_approx": "76 KB",
    },
    {
        "media_type":       "MYAAN3NB",
        "entity_suffix":    "render_angle_hd",
        "tag":              "angle_hd",
        "view_description": "3/4-Ansicht HD",
        "recommended_use":  "Hero-Banner, Vollbild-Dashboards, Wallpaper",
        "file_size_approx": "1.7 MB",
    },
]

# Quick lookup: media_type → metadata dict
RENDER_TYPE_BY_MEDIA: dict[str, dict[str, str]] = {
    r["media_type"]: r for r in RENDER_IMAGE_TYPES
}

# Preferred order for "best single image" fallback
_PREFERRED_ORDER = [r["media_type"] for r in RENDER_IMAGE_TYPES]

_GQL_QUERY = """
query GET_USER_VEHICLES {
  userVehicles {
    vin
    nickname
    vehicle {
      brand { name }
      media {
        shortName
        longName
        exteriorColor
        interiorColor
      }
      renderPictures(
        mediaTypes: [
          "MYAAN8NB"
          "MYAPN8NB"
          "MYAAN3NB"
          "MYAPN3NB"
          "MS_MYP3"
          "MS_MYP4"
          "MS_MYP5"
        ]
      ) {
        mediaType
        url
      }
    }
  }
}
"""


@dataclass
class VehicleImageData:
    """All render image data for a single vehicle."""

    vin: str
    image_urls: dict[str, str]          # {mediaType: public URL}
    short_name: str | None = None       # e.g. "Q4 e-tron"
    long_name: str | None = None        # e.g. "Audi Q4 50 e-tron quattro"
    exterior_color: str | None = None
    nickname: str | None = None         # User-set nickname in app


class VehicleImageFetcher:
    """Fetches vehicle render image URLs via VW Group GraphQL API.

    fetch_image_data(access_token, brand) → dict[vin, VehicleImageData]
    URLs are public — no further auth needed to GET the actual PNG.
    """

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def fetch_image_data(
        self, access_token: str, brand: str
    ) -> dict[str, VehicleImageData]:
        """Return {vin: VehicleImageData} for all vehicles in the account.

        Returns empty dict on any error — images are optional, never block startup.
        """
        endpoint = _GRAPHQL_ENDPOINTS.get(brand.lower())
        if not endpoint:
            _LOGGER.debug("No GraphQL endpoint configured for brand '%s'", brand)
            return {}

        try:
            async with self._session.post(
                endpoint,
                json={"query": _GQL_QUERY},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type":  "application/json",
                    "Accept":        "application/json",
                },
                timeout=ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.debug(
                        "GraphQL %s returned %d — images unavailable for %s",
                        endpoint, resp.status, brand,
                    )
                    return {}
                data = await resp.json()

        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("GraphQL image fetch failed for %s: %s", brand, err)
            return {}

        return self._parse_response(data)

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> dict[str, VehicleImageData]:
        """Extract VehicleImageData per VIN from GraphQL response."""
        result: dict[str, VehicleImageData] = {}
        try:
            vehicles = data.get("data", {}).get("userVehicles", []) or []
            for v in vehicles:
                vin = v.get("vin")
                if not vin:
                    continue
                vehicle = v.get("vehicle") or {}
                media   = vehicle.get("media") or {}
                pictures = vehicle.get("renderPictures") or []

                urls: dict[str, str] = {}
                for pic in pictures:
                    mt  = pic.get("mediaType")
                    url = pic.get("url")
                    if mt and url:
                        urls[mt] = url

                result[vin] = VehicleImageData(
                    vin=vin,
                    image_urls=urls,
                    short_name=media.get("shortName"),
                    long_name=media.get("longName"),
                    exterior_color=media.get("exteriorColor"),
                    nickname=v.get("nickname"),
                )
                _LOGGER.debug(
                    "GraphQL images for %s (%s): %d mediaTypes",
                    vin, media.get("shortName", "?"), len(urls),
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("GraphQL response parse error: %s", err)
        return result

    @staticmethod
    def best_url(image_urls: dict[str, str] | None) -> str | None:
        """Return the best available image URL (MYAPN8NB preferred)."""
        if not image_urls:
            return None
        for mt in _PREFERRED_ORDER:
            url = image_urls.get(mt)
            if url:
                return url
        return next(iter(image_urls.values()), None)
