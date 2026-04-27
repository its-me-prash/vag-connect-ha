# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Volkswagen North America API client — b-h-s.spr.{country}00.p.con-veh.net.

Endpoints from matpoulin/CarConnectivity-connector-volkswagen-na (Apache-2.0).
Clean-room reimplementation using aiohttp + IDK PKCE auth.
Source: https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from aiohttp import ClientSession

from .._util import mask_vin as _mask_vin
from ..models import VehicleData
from ..exceptions import AuthenticationError, APIError, TokenExpiredError
from ..auth.idk import IDKAuth
from ..models import BrandConfig, TokenSet

_LOGGER = logging.getLogger(__name__)

# Country → API base: US=us, CA=ca
_COUNTRY_BASES: dict[str, str] = {
    "us": "https://b-h-s.spr.us00.p.con-veh.net",
    "ca": "https://b-h-s.spr.ca00.p.con-veh.net",
}

BRAND_VW_NA = BrandConfig(
    name="volkswagen_na",
    client_id="59992128-69a9-42c3-8621-7942041ba824_MYVW_ANDROID",
    redirect_uri="kombi:///login",
    user_agent="MyVW/1.0 Android",
    api_base="https://b-h-s.spr.us00.p.con-veh.net",
    scope="openid profile email offline_access mbb vin cars dealers",
)


class VWNAClient:
    """VW North America client.

    Uses a country-specific auth endpoint (b-h-s.spr.{cc}00.p.con-veh.net/oidc/v1/).
    Vehicle data uses UUID (not VIN directly in path) — VIN is mapped after garage fetch.
    """

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        spin: str = "",
        country: str = "us",
    ) -> None:
        self._session  = session
        self._email    = email
        self._password = password
        self._spin     = spin
        self._country  = country.lower()
        self._base     = _COUNTRY_BASES.get(self._country, _COUNTRY_BASES["us"])
        self._tokens: TokenSet | None = None
        # VW NA uses IDK auth but against a country-specific endpoint
        brand = BrandConfig(
            name=f"volkswagen_{self._country}",
            client_id=BRAND_VW_NA.client_id,
            redirect_uri=BRAND_VW_NA.redirect_uri,
            user_agent=BRAND_VW_NA.user_agent,
            api_base=self._base,
            scope=BRAND_VW_NA.scope,
        )
        self._auth = IDKAuth(session, brand)
        # UUID cache: VIN → UUID (returned by garage)
        self._vin_to_uuid: dict[str, str] = {}

    async def authenticate(self, mfa_code: str | None = None) -> None:
        """IDK PKCE login against VW NA endpoint."""
        self._tokens = await self._auth.authenticate(self._email, self._password)
        _LOGGER.debug("VW NA auth complete (%s)", self._country.upper())

    async def get_vehicles(self) -> list[str]:
        """Return VINs from VW NA garage."""
        data = await self._get(f"{self._base}/account/v1/garage")
        vins = []
        for v in data.get("vehicles", []):
            vin  = v.get("vin")
            uuid = v.get("uuid") or v.get("vehicleId")
            if vin:
                if uuid:
                    self._vin_to_uuid[vin] = uuid
                vins.append(vin)
                _LOGGER.debug("VW NA: found VIN %s uuid=%s", _mask_vin(vin), uuid)
        return vins

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch vehicle status using UUID."""
        v = self._val
        uuid = self._vin_to_uuid.get(vin, vin)
        d = VehicleData(vin=vin, manufacturer="Volkswagen")

        results = await asyncio.gather(
            self._get(f"{self._base}/rvs/v1/vehicle/{uuid}"),
            self._get(f"{self._base}/ev/v1/vehicle/{uuid}/charge/summary"),
            self._get(f"{self._base}/ev/v1/vehicle/{uuid}/climate/summary"),
            return_exceptions=True,
        )
        vehicle_raw, charge, climate = results

        # ── Vehicle status ────────────────────────────────────────────────────
        if isinstance(vehicle_raw, dict):
            power = v(vehicle_raw, "powerStatus") or {}
            d.odometer_km = v(power, "odometer")
            d.fuel_level  = v(power, "fuelPercentRemaining")
            d.range_km    = v(power, "cruiseRange")

            # Battery
            bat = v(vehicle_raw, "batteryStatus") or {}
            d.battery_soc = v(bat, "stateOfChargePercent")
            d.has_battery = d.battery_soc is not None

            # Doors
            door_status = v(vehicle_raw, "doorStatus") or {}
            d.doors_locked = v(door_status, "overallStatus") == "LOCKED"
            d.doors_open   = any(
                v(door_status, k) == "OPEN"
                for k in ("frontLeftDoor", "frontRightDoor", "rearLeftDoor", "rearRightDoor")
            )
            d.trunk_open = v(door_status, "trunk") == "OPEN"
            d.hood_open  = v(door_status, "hood") == "OPEN"

            # Windows
            win = v(vehicle_raw, "windowStatus") or {}
            d.windows_open = any(
                v(win, k) == "OPEN"
                for k in ("frontLeftWindow", "frontRightWindow", "rearLeftWindow", "rearRightWindow")
            )

            # GPS
            pos = v(vehicle_raw, "vehicleLocation") or {}
            d.latitude  = v(pos, "latitude")
            d.longitude = v(pos, "longitude")

            # Connection
            d.is_online = v(vehicle_raw, "connectionStatus", "connectionState") == "CONNECTED"

            # Drivetrain type
            engine = v(vehicle_raw, "vehicleType", "engine") or ""
            d.is_electric    = engine in ("BEV", "ELECTRIC")
            d.is_hybrid      = engine == "PHEV"
            d.has_battery    = d.is_electric or d.is_hybrid or d.has_battery
            d.has_combustion = engine in ("PHEV", "ICE", "GASOLINE", "DIESEL") or (
                d.fuel_level is not None
            )

        # ── Charging ──────────────────────────────────────────────────────────
        if isinstance(charge, dict):
            d.charging_state    = v(charge, "chargingStatus", "chargingState")
            d.is_charging       = d.charging_state == "CHARGING"
            d.charging_power_kw = v(charge, "chargingStatus", "chargePower_kW")
            plug = v(charge, "plugStatus", "plugConnectionState")
            d.plug_connected    = plug == "CONNECTED"
            d.plug_state        = plug
            d.target_soc        = v(charge, "chargingSettings", "targetSOC_pct")
            remaining           = v(charge, "chargingStatus", "remainingChargingTimeToComplete_min")
            if remaining:
                d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=int(remaining))

        # ── Climate ────────────────────────────────────────────────────────────
        if isinstance(climate, dict):
            d.climatisation_state  = v(climate, "climatisationStatus", "climatisationState")
            d.climatisation_active = d.climatisation_state not in (None, "OFF")
            temp_k = v(climate, "climatisationSettings", "targetTemperature_K")
            d.target_temperature = round(float(temp_k) - 273.15, 1) if temp_k else None

        d.is_electric    = d.has_battery and not d.has_combustion
        d.is_hybrid      = d.has_battery and d.has_combustion
        return d

    async def command_lock(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/lock", json={"action": "lock"})

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        payload: dict[str, Any] = {"action": "unlock"}
        if spin or self._spin:
            payload["spin"] = spin or self._spin
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/lock", json=payload)

    async def command_start_climate(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/pretripclimate/start", json={})

    async def command_stop_climate(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/pretripclimate/stop", json={})

    async def command_start_charging(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/charging/start", json={})

    async def command_stop_charging(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/charging/stop", json={})

    async def command_flash(
        self,
        vin: str,
        latitude: float | None = None,  # noqa: ARG002
        longitude: float | None = None,  # noqa: ARG002
    ) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/horn-and-lights", json={"action": "FLASH_ONLY"})

    async def command_wake(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(f"{self._base}/ev/v1/vehicle/{uuid}/wakeup", json={})

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(
            f"{self._base}/ev/v1/vehicle/{uuid}/charging/settings",
            json={"targetSOC_pct": target},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(
            f"{self._base}/ev/v1/vehicle/{uuid}/pretripclimate/settings",
            json={"targetTemperature_K": temp_c + 273.15, "tempUnit": "C"},
        )

    async def command_start_window_heating(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(
            f"{self._base}/ev/v1/vehicle/{uuid}/pretripclimate/windowheating/start", json={}
        )

    async def command_stop_window_heating(self, vin: str) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        await self._post(
            f"{self._base}/ev/v1/vehicle/{uuid}/pretripclimate/windowheating/stop", json={}
        )

    async def command_set_departure_timer(
        self, vin: str, timer_id: int, enabled: bool, departure_time: str | None
    ) -> None:
        uuid = self._vin_to_uuid.get(vin, vin)
        payload: dict[str, Any] = {"id": timer_id, "enabled": enabled}
        if departure_time:
            payload["departureTime"] = {"time": departure_time}
        await self._post(
            f"{self._base}/ev/v1/vehicle/{uuid}/climatisation/timers",
            json=payload,
        )

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    async def _get(self, url: str, **kwargs: Any) -> Any:
        return await self._request("GET", url, **kwargs)

    async def _post(self, url: str, **kwargs: Any) -> Any:
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, retry: bool = True, **kwargs: Any) -> Any:
        from aiohttp import ClientTimeout  # noqa: PLC0415
        if not self._tokens:
            raise AuthenticationError("Not authenticated")
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {self._tokens.access_token}",
            "User-Agent":    BRAND_VW_NA.user_agent,
            "Accept":        "application/json",
        })
        async with self._session.request(
            method, url, headers=headers, timeout=ClientTimeout(total=30), **kwargs
        ) as resp:
            if resp.status == 401 and retry:
                await self._refresh()
                return await self._request(method, url, retry=False, **kwargs)
            if resp.status == 204:
                return {}
            if resp.status not in (200, 202, 207):
                body = await resp.text()
                raise APIError(resp.status, url, body)
            return await resp.json()

    async def _refresh(self) -> None:
        if self._tokens and self._tokens.refresh_token:
            try:
                self._tokens = await self._auth.refresh(self._tokens.refresh_token)
                return
            except TokenExpiredError:
                pass
        await self.authenticate()

    @staticmethod
    def _val(data: dict, *path: str, default: Any = None) -> Any:
        node: Any = data
        for key in path:
            if not isinstance(node, dict):
                return default
            node = node.get(key, default)
            if node is None:
                return default
        return node
