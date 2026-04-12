# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Audi EU API client — CARIAD BFF + AZS token + MBB OAuth registration.

Audi uses the same CARIAD BFF endpoints as VW EU but requires two
additional authentication steps after IDK login:
  1. AZS token exchange (identity.vwgroup.io → Audi authorization server)
  2. MBB client registration + auth (mbboauth-1d.prd.ece.vwg-connect.com)

Source: audiconnect/audi_connect_ha (MIT) — clean-room reimplementation.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession

from ..auth.idk import IDKAuth
from ..exceptions import AuthenticationError
from ..models import BRAND_AUDI, TokenSet
from .vw_eu import VWEUClient

_LOGGER = logging.getLogger(__name__)

_AZS_URL = "https://emea.bff.cariad.digital/login/v1/audi/token"
_MBB_BASE = "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth"
_XAPP_VERSION = "4.31.0"


class AudiClient(VWEUClient):
    """Audi EU client — identical endpoints to VW EU, extended auth chain."""

    def __init__(
        self, session: ClientSession, email: str, password: str, spin: str = ""
    ) -> None:
        # Override brand to Audi before super().__init__
        super().__init__(session, email, password, spin)
        self._brand = BRAND_AUDI
        self._auth = IDKAuth(session, BRAND_AUDI)
        self._xclient_id: str | None = None
        self._vw_token: TokenSet | None = None

    async def authenticate(self) -> None:
        """Full Audi auth: IDK → AZS → MBB register → MBB auth."""
        # Step 1–4: standard IDK PKCE flow
        self._tokens = await self._auth.authenticate(self._email, self._password)
        _LOGGER.debug("Audi IDK auth OK")

        # Step 5: AZS token exchange
        await self._exchange_azs()

        # Step 6–7: MBB client registration + auth
        await self._mbb_register_and_auth()

        _LOGGER.debug("Audi full auth chain complete")

    async def _exchange_azs(self) -> None:
        """Exchange IDK id_token → Audi AZS token."""
        if not self._tokens:
            raise AuthenticationError("IDK tokens required before AZS exchange.")
        headers = {
            "Accept": "application/json",
            "X-App-Version": _XAPP_VERSION,
            "X-App-Name": "myAudi",
            "User-Agent": self._brand.user_agent,
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "token": self._tokens.access_token,
            "grant_type": "id_token",
            "stage": "live",
            "config": "myaudi",
        }
        async with self._session.post(_AZS_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise AuthenticationError(f"AZS token exchange failed {resp.status}: {body[:200]}")
            azs: dict[str, Any] = await resp.json()

        # AZS gives us a different access_token — update stored tokens
        self._tokens = TokenSet(
            access_token=azs.get("access_token", self._tokens.access_token),
            refresh_token=azs.get("refresh_token", self._tokens.refresh_token),
            id_token=azs.get("id_token", self._tokens.id_token),
        )

    async def _mbb_register_and_auth(self) -> None:
        """Register a virtual MBB client and get the VW token."""
        if not self._tokens:
            raise AuthenticationError("AZS tokens required before MBB registration.")

        headers = {
            "Accept": "application/json",
            "User-Agent": self._brand.user_agent,
            "Content-Type": "application/json; charset=utf-8",
        }
        reg_payload = {
            "client_name": "SM-A405FN",
            "platform": "google",
            "client_brand": "Audi",
            "appName": "myAudi",
            "appVersion": _XAPP_VERSION,
            "appId": "de.myaudi.mobile.assistant",
        }
        async with self._session.post(
            f"{_MBB_BASE}/mobile/register/v1", json=reg_payload, headers=headers
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise AuthenticationError(f"MBB registration failed {resp.status}: {body[:200]}")
            reg: dict[str, Any] = await resp.json()

        self._xclient_id = reg.get("client_id")

        # MBB auth with id_token → get vwToken (used for older legacy endpoints if needed)
        mbb_auth_headers = {
            **headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Client-ID": self._xclient_id or "",
        }
        mbb_auth_data = {
            "grant_type": "id_token",
            "token": self._tokens.id_token,
            "scope": "sc2:fal",
        }
        async with self._session.post(
            f"{_MBB_BASE}/mobile/oauth2/v1/token",
            data=mbb_auth_data,
            headers=mbb_auth_headers,
        ) as resp:
            if resp.status != 200:
                _LOGGER.warning("MBB auth step returned %s — continuing without vwToken", resp.status)
                return
            vw: dict[str, Any] = await resp.json()

        self._vw_token = TokenSet(
            access_token=vw.get("access_token", ""),
            refresh_token=vw.get("refresh_token", ""),
            id_token=vw.get("id_token", ""),
        )
        _LOGGER.debug("MBB auth complete, xclient_id=%s", self._xclient_id)
