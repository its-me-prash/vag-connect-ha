# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Base async API client — injected aiohttp session, token management."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from ..auth.idk import IDKAuth
from ..exceptions import APIError, AuthenticationError, TokenExpiredError
from ..models import BrandConfig, TokenSet, VehicleData

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 30


class CariadBaseClient:
    """Base class for all CARIAD brand API clients.

    Subclasses implement get_vehicles() and get_status(vin).
    Token refresh is handled transparently.
    """

    def __init__(
        self,
        session: ClientSession,
        brand: BrandConfig,
        email: str,
        password: str,
        spin: str = "",
    ) -> None:
        self._session = session
        self._brand = brand
        self._email = email
        self._password = password
        self._spin = spin
        self._tokens: TokenSet | None = None
        self._auth = IDKAuth(session, brand)

    @property
    def brand(self) -> BrandConfig:
        """Brand configuration."""
        return self._brand

    async def authenticate(self) -> None:
        """Perform full login and store tokens."""
        self._tokens = await self._auth.authenticate(self._email, self._password)
        _LOGGER.debug("Authenticated for brand %s", self._brand.name)

    async def get_vehicles(self) -> list[str]:
        """Return list of VINs in the account garage."""
        raise NotImplementedError

    async def get_status(self, vin: str) -> VehicleData:
        """Return current vehicle data for the given VIN."""
        raise NotImplementedError

    async def command_lock(self, vin: str) -> None:
        """Remote lock."""
        raise NotImplementedError

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        """Remote unlock — may require S-PIN."""
        raise NotImplementedError

    async def command_start_climate(self, vin: str) -> None:
        """Start pre-conditioning."""
        raise NotImplementedError

    async def command_stop_climate(self, vin: str) -> None:
        """Stop pre-conditioning."""
        raise NotImplementedError

    async def command_start_charging(self, vin: str) -> None:
        """Start charging."""
        raise NotImplementedError

    async def command_stop_charging(self, vin: str) -> None:
        """Stop charging."""
        raise NotImplementedError

    async def command_flash(self, vin: str) -> None:
        """Honk and flash."""
        raise NotImplementedError

    async def command_wake(self, vin: str) -> None:
        """Wake vehicle from sleep."""
        raise NotImplementedError

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        """Set charge target SoC (20–100%)."""
        raise NotImplementedError

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        """Set pre-conditioning target temperature."""
        raise NotImplementedError

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    async def _get(self, url: str, **kwargs: Any) -> Any:
        """Authenticated GET — auto-refreshes token on 401."""
        return await self._request("GET", url, **kwargs)

    async def _post(self, url: str, **kwargs: Any) -> Any:
        """Authenticated POST."""
        return await self._request("POST", url, **kwargs)

    async def _request(
        self, method: str, url: str, retry: bool = True, **kwargs: Any
    ) -> Any:
        """Execute an authenticated request, refreshing tokens on 401."""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        headers["Accept"] = "application/json"
        headers["Content-Type"] = headers.get("Content-Type", "application/json")
        headers["User-Agent"] = self._brand.user_agent

        async with self._session.request(
            method, url, headers=headers, timeout=ClientTimeout(total=_REQUEST_TIMEOUT), **kwargs
        ) as resp:
            if resp.status == 401 and retry:
                await self._refresh_tokens()
                return await self._request(method, url, retry=False, **kwargs)
            if resp.status == 204:
                return None
            if resp.status not in (200, 202, 207):
                body = await resp.text()
                raise APIError(resp.status, url, body)
            ct = resp.headers.get("Content-Type", "")
            if "json" in ct:
                return await resp.json()
            return await resp.text()

    async def _refresh_tokens(self) -> None:
        """Attempt token refresh; fall back to full re-login."""
        if self._tokens and self._tokens.refresh_token:
            try:
                self._tokens = await self._auth.refresh(self._tokens.refresh_token)
                return
            except TokenExpiredError:
                pass
        _LOGGER.info("Token refresh failed — re-authenticating for %s", self._brand.name)
        await self.authenticate()

    @property
    def _access_token(self) -> str:
        if not self._tokens:
            raise AuthenticationError("Not authenticated — call authenticate() first.")
        return self._tokens.access_token

    def _val(self, data: dict[str, Any], *path: str, default: Any = None) -> Any:
        """Safe nested dict access. _val(d, 'a', 'b', 'c') → d['a']['b']['c']."""
        node: Any = data
        for key in path:
            if not isinstance(node, dict):
                return default
            node = node.get(key, default)
            if node is None:
                return default
        return node
