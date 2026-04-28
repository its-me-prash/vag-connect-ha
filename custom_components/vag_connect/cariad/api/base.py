# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Base async API client — injected aiohttp session, token management."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from aiohttp import (
    ClientConnectorError,
    ClientPayloadError,
    ClientSession,
    ClientTimeout,
    ServerDisconnectedError,
)

from ..auth.idk import IDKAuth
from .graphql import VehicleImageFetcher, VehicleImageData
from ..exceptions import APIError, AuthenticationError, TokenExpiredError
from ..models import BrandConfig, TokenSet, VehicleData

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 60

# Token-refresh storm protection (v1.8.7).
# Capped at 3 successful-or-attempted refreshes per rolling hour. If the
# CARIAD identity backend hands out short-lived tokens or returns transient
# 401s, this prevents us from looping login → 401 → login until the IP gets
# rate-limited or the account temporarily locked. Patterns from
# `skodaconnect/myskoda` #976 and `robinostlund/homeassistant-volkswagencarnet`
# #683 — both repos shipped fixes after users reported account suspensions
# triggered by integrations refreshing tokens every poll cycle.
_REFRESH_MAX_PER_HOUR = 3
_REFRESH_WINDOW_S = 3600

# Transient network exceptions that should be retried with the same
# exponential backoff as 5xx server errors. Verified against:
#   - `mitch-dc/volkswagen_we_connect_id` #166 (`socket.gaierror` /
#     `ClientConnectorError` was being misclassified as auth failure)
#   - `skodaconnect/homeassistant-myskoda` #731 ("server unavailable" UX)
# DNS, connection refused, and mid-stream disconnects from the CARIAD BFF
# happen routinely on weekends and during VAG maintenance windows. They are
# not auth failures and must not trigger reauth.
_TRANSIENT_NET_ERRORS: tuple[type[BaseException], ...] = (
    ClientConnectorError,
    ServerDisconnectedError,
    ClientPayloadError,
    asyncio.TimeoutError,
)


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
        self._image_data: dict[str, VehicleImageData] = {}
        self._refresh_lock: asyncio.Lock | None = None
        # Sliding window of token refresh attempt timestamps (monotonic seconds).
        # Pruned to the last `_REFRESH_WINDOW_S` on every refresh attempt.
        # Prevents the spiral documented in myskoda #976 / volkswagencarnet #683.
        self._refresh_history: list[float] = []
        self._auth = IDKAuth(session, brand)

    @property
    def brand(self) -> BrandConfig:
        """Brand configuration."""
        return self._brand

    async def authenticate(self, mfa_code: str | None = None) -> None:
        """Perform full login and store tokens."""
        self._tokens = await self._auth.authenticate(self._email, self._password)
        _LOGGER.debug("Authenticated for brand %s", self._brand.name)

    async def get_vehicles(self) -> list[str]:
        """Return list of VINs in the account garage."""
        raise NotImplementedError

    async def get_status(self, vin: str) -> VehicleData:
        """Return current vehicle data for the given VIN."""
        raise NotImplementedError

    async def fetch_images(self) -> None:
        """Fetch render image URLs via GraphQL — Audi only.

        Called once during get_vehicles(). Populates self._image_data.
        SEAT/CUPRA use OLA renders endpoint instead (in SeatCupraClient).
        Škoda, Porsche, VW NA do not have a GraphQL image endpoint.
        """
        if self._brand.name not in ("audi",):
            return
        try:
            fetcher = VehicleImageFetcher(self._session)
            data = await fetcher.fetch_image_data(self._access_token, self._brand.name)
            self._image_data = data
            if data:
                _LOGGER.info(
                    "VAG images (%s): render URLs for %d vehicle(s)",
                    self._brand.name, len(data),
                )
        except Exception:  # noqa: BLE001
            self._image_data = {}

    async def command_lock(self, vin: str) -> None:
        """Remote lock."""
        raise NotImplementedError

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        """Remote unlock — may require S-PIN."""
        raise NotImplementedError

    async def get_capabilities(self, vin: str) -> dict[str, Any]:
        """Return the per-VIN capabilities document.

        Default implementation returns ``{}`` (i.e. "no data") so callers
        can rely on the helper existing without checking ``hasattr``.
        Brand-specific clients that have a real capabilities endpoint
        override this — currently SEAT/CUPRA (OLA) and the CARIAD BFF
        family (VW EU + Audi). Škoda mysmob and Porsche PPA do not expose
        a discrete capabilities endpoint and keep the default.
        """
        return {}

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

    async def command_flash(
        self,
        vin: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        """Honk and flash. SEAT/CUPRA require the user position; others ignore it."""
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

    async def command_set_charge_mode(self, vin: str, mode: str) -> None:
        """Set charging mode (MANUAL | TIMER | PREFERRED_CHARGING_TIMES)."""
        raise NotImplementedError

    async def command_set_min_soc(self, vin: str, min_soc: int) -> None:
        """Set minimum SoC for PHEV departure timer (0–100%)."""
        raise NotImplementedError

    async def command_start_window_heating(self, vin: str) -> None:
        """Start window (windscreen + rear) heating."""
        raise NotImplementedError

    async def command_stop_window_heating(self, vin: str) -> None:
        """Stop window heating."""
        raise NotImplementedError

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    async def _get(self, url: str, **kwargs: Any) -> Any:
        """Authenticated GET — auto-refreshes token on 401."""
        return await self._request("GET", url, **kwargs)

    async def _post(self, url: str, **kwargs: Any) -> Any:
        """Authenticated POST."""
        return await self._request("POST", url, **kwargs)

    async def _request(
        self, method: str, url: str, retry: bool = True, _attempt: int = 0, **kwargs: Any
    ) -> Any:
        """Execute an authenticated request with retry for transient errors.

        Retry behaviour (v1.8.7 hardening):

        - HTTP 401 → token refresh + 1 retry. Refresh itself is throttled
          to ``_REFRESH_MAX_PER_HOUR`` per rolling hour (storm protection).
        - HTTP 429 → exponential backoff up to 3 attempts (5s/10s/20s).
        - HTTP 500/502/503/504 → exponential backoff up to 3 attempts
          (3s/6s/12s). 504 added in v1.8.7 — Gateway Timeouts from the
          CARIAD BFF are routine on weekends and were previously surfaced
          as fatal API errors.
        - Transient network errors (DNS / connection refused / mid-stream
          disconnects / asyncio timeouts) → same backoff as server errors.
          Verified pattern from we_connect_id #166 and myskoda #731.
        """
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        headers["Accept"] = "application/json"
        headers["Content-Type"] = headers.get("Content-Type", "application/json")
        headers["User-Agent"] = self._brand.user_agent

        try:
            async with self._session.request(
                method, url, headers=headers, timeout=ClientTimeout(total=_REQUEST_TIMEOUT), **kwargs
            ) as resp:
                if resp.status == 401 and retry:
                    await self._refresh_tokens()
                    return await self._request(method, url, retry=False, **kwargs)
                if resp.status == 429 and _attempt < 3:
                    wait = (2 ** _attempt) * 5
                    _LOGGER.debug("Rate limited (429) — retrying in %ds", wait)
                    await asyncio.sleep(wait)
                    return await self._request(method, url, retry=retry, _attempt=_attempt + 1, **kwargs)
                if resp.status in (500, 502, 503, 504) and _attempt < 3:
                    wait = (2 ** _attempt) * 3
                    _LOGGER.debug("Server error %d — retrying in %ds", resp.status, wait)
                    await asyncio.sleep(wait)
                    return await self._request(method, url, retry=retry, _attempt=_attempt + 1, **kwargs)
                if resp.status == 204:
                    return None
                if resp.status not in (200, 201, 202, 207):
                    body = await resp.text()
                    raise APIError(resp.status, url, body)
                ct = resp.headers.get("Content-Type", "")
                if "json" in ct:
                    return await resp.json()
                return await resp.text()
        except _TRANSIENT_NET_ERRORS as err:
            if _attempt < 3:
                wait = (2 ** _attempt) * 3
                _LOGGER.debug(
                    "Transient network error (%s) — retrying in %ds",
                    type(err).__name__,
                    wait,
                )
                await asyncio.sleep(wait)
                return await self._request(
                    method, url, retry=retry, _attempt=_attempt + 1, **kwargs
                )
            raise APIError(0, url, f"transient: {type(err).__name__}: {err}") from err

    async def _refresh_tokens(self) -> None:
        """Attempt token refresh; fall back to full re-login.

        Uses a lock to prevent concurrent refresh attempts from racing.

        Storm protection (v1.8.7): if more than ``_REFRESH_MAX_PER_HOUR``
        refresh attempts occur within ``_REFRESH_WINDOW_S`` seconds, raise
        ``AuthenticationError`` to surface the problem instead of silently
        looping. The coordinator catches this in its poll loop and triggers
        the HA reauth flow — the user gets a UI prompt instead of a slowly
        rate-limited account. Patterns from myskoda #976 and
        volkswagencarnet #683.
        """
        if self._refresh_lock is None:
            self._refresh_lock = asyncio.Lock()
        async with self._refresh_lock:
            now = time.monotonic()
            cutoff = now - _REFRESH_WINDOW_S
            self._refresh_history = [t for t in self._refresh_history if t > cutoff]
            if len(self._refresh_history) >= _REFRESH_MAX_PER_HOUR:
                _LOGGER.error(
                    "Token refresh storm: %d attempts in last %ds for %s — pausing"
                    " to prevent IP ban; please reauthenticate from the UI",
                    len(self._refresh_history),
                    _REFRESH_WINDOW_S,
                    self._brand.name,
                )
                raise AuthenticationError(
                    "Token refresh storm — please reauthenticate"
                )
            self._refresh_history.append(now)

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
