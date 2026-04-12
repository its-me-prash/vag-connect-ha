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
from typing import Any

from aiohttp import ClientSession, ClientTimeout

_LOGGER = logging.getLogger(__name__)

# GraphQL endpoints per brand (proxy path differs, vgql layer is shared)
_GRAPHQL_ENDPOINTS: dict[str, str] = {
    "audi":       "https://www.audi.de/userinfo-emea/v2/myaudi/proxy/vgql/v1/graphql",
    "volkswagen": "https://www.volkswagen.de/app/proxy/vgql/v1/graphql",
    "skoda":      "https://www.skoda-auto.com/myskoda/proxy/vgql/v1/graphql",
    "seat":       "https://www.seat.com/myway/proxy/vgql/v1/graphql",
    "cupra":      "https://www.cupraofficial.com/mycupra/proxy/vgql/v1/graphql",
}

# Best image per use case — ordered by preference
_PREFERRED_MEDIA_TYPES = [
    "MYAPN8NB",  # Side profile large ~309KB — best for Lovelace cards
    "MYAAN8NB",  # 3/4 angle large ~879KB — dashboard hero
    "MS_MYP5",   # 3/4 angle ~196KB — medium cards
    "MYAPN3NB",  # Side profile ~158KB — compact cards
    "MS_MYP4",   # 3/4 angle ~117KB — small cards
    "MS_MYP3",   # 3/4 angle ~76KB  — icon/badge
]

_GQL_QUERY = """
query GET_USER_VEHICLES {
  userVehicles {
    vin
    vehicle {
      media {
        shortName
        longName
        exteriorColor
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


class VehicleImageFetcher:
    """Fetches vehicle render image URLs via VW Group GraphQL API.

    Call fetch_image_urls(access_token, brand) → dict[vin, dict[mediaType, url]]
    URLs are public — no further auth needed to GET the image.
    """

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def fetch_image_urls(
        self, access_token: str, brand: str
    ) -> dict[str, dict[str, str]]:
        """Return {vin: {mediaType: url}} for all vehicles in the account.

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
    def _parse_response(data: dict[str, Any]) -> dict[str, dict[str, str]]:
        """Extract {vin: {mediaType: url}} from GraphQL response."""
        result: dict[str, dict[str, str]] = {}
        try:
            vehicles = data.get("data", {}).get("userVehicles", []) or []
            for v in vehicles:
                vin = v.get("vin")
                if not vin:
                    continue
                pictures = v.get("vehicle", {}).get("renderPictures", []) or []
                urls: dict[str, str] = {}
                for pic in pictures:
                    mt  = pic.get("mediaType")
                    url = pic.get("url")
                    if mt and url:
                        urls[mt] = url
                if urls:
                    result[vin] = urls
                    _LOGGER.debug(
                        "GraphQL images for %s: %d mediaTypes", vin, len(urls)
                    )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("GraphQL response parse error: %s", err)
        return result

    @staticmethod
    def best_url(image_urls: dict[str, str] | None) -> str | None:
        """Return the best available image URL from a dict of {mediaType: url}."""
        if not image_urls:
            return None
        for mt in _PREFERRED_MEDIA_TYPES:
            url = image_urls.get(mt)
            if url:
                return url
        # Fallback: any available URL
        return next(iter(image_urls.values()), None)
