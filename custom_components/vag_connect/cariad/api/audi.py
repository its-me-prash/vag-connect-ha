# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Audi EU API client — CARIAD BFF with legacy IDK signin-service auth.

The audiconnect client_id (09b6cbec-...) uses the old IDK signin-service
flow instead of Auth0. After successful PKCE login, the IDK access_token
is used directly against the CARIAD BFF (same endpoints as VW EU).

Image fetching requires a *separate* token from the myAudi portal client
(ea73e952-...). AudiClient.fetch_images() performs a lightweight second
IDK auth with that client to obtain a portal-scoped Bearer token, then
uses that for the vgql GraphQL call.

Source for audiconnect client_id: arjenvrh/audi_connect_ha (MIT)
Source for portal client_id: Issue #15 research (April 2026)
"""

from __future__ import annotations

import logging

from aiohttp import ClientSession

from ..auth.idk import IDKAuth
from ..models import BRAND_AUDI, BrandConfig
from .graphql import VehicleImageFetcher, VehicleImageData
from .vw_eu import VWEUClient

_LOGGER = logging.getLogger(__name__)

# The myAudi portal app client ID — gives token accepted by vgql proxy
# Different from the CARIAD BFF client (09b6cbec-...) used for vehicle data
_PORTAL_CLIENT_ID = "ea73e952-ecd9-4b44-aa39-8acc33f3ff9b@apps_vw-dilab_com"
_PORTAL_REDIRECT  = "myaudi:///"
_PORTAL_SCOPE = (
    "openid profile email mbb offline_access mbbuserid"
    " myaudi_proxy_vin myaudi_proxy_garage"
)

_PORTAL_BRAND = BrandConfig(
    name="audi",
    client_id=_PORTAL_CLIENT_ID,
    redirect_uri=_PORTAL_REDIRECT,
    user_agent="Android/4.31.0 (Build 800341641.root project 'myaudi_android'.ext.buildTime) Android/13",
    api_base="https://www.audi.de",
    scope=_PORTAL_SCOPE,
)


class AudiClient(VWEUClient):
    """Audi EU client — identical to VW EU plus portal-token image fetching."""

    def __init__(self, session: ClientSession, email: str, password: str, spin: str = "") -> None:
        # Call CariadBaseClient directly with BRAND_AUDI (not VWEUClient which hardcodes BRAND_VW_EU)
        from .base import CariadBaseClient  # noqa: PLC0415
        CariadBaseClient.__init__(self, session, BRAND_AUDI, email, password, spin)
        self._portal_token: str | None = None
        self._portal_auth = IDKAuth(session, _PORTAL_BRAND)

    async def fetch_images(self) -> None:
        """Override: use the myAudi portal client token for vgql.

        The CARIAD-BFF token (09b6cbec-...) is rejected by the vgql proxy
        with HTTP 403. The portal token (ea73e952-...) has the correct scopes.

        We cache the portal token — it is refreshed when expired.
        """
        # Obtain portal token (separate IDK auth with myAudi portal client ID)
        if not self._portal_token:
            try:
                portal_tokens = await self._portal_auth.authenticate(
                    self._email, self._password
                )
                self._portal_token = portal_tokens.access_token
                _LOGGER.info("Audi portal token acquired for image fetching")
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "Audi portal auth failed (images will be unavailable): %s", err
                )
                self._image_data = {}
                return

        # Fetch images with portal token
        try:
            fetcher = VehicleImageFetcher(self._session)
            data: dict[str, VehicleImageData] = await fetcher.fetch_image_data(
                self._portal_token, "audi"
            )
            if data:
                self._image_data = data
                _LOGGER.info(
                    "Audi images: render URLs for %d vehicle(s)", len(data)
                )
            else:
                # Portal token may have expired — reset to force re-auth next time
                self._portal_token = None
                _LOGGER.debug("Audi images: empty response, portal token reset")
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Audi image fetch failed: %s", err)
            self._portal_token = None  # force refresh next attempt
            self._image_data = {}
