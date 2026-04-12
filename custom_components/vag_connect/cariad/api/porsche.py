# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Porsche Connect API client — api.ppa.porsche.com.

Endpoints from CJNE/pyporscheconnectapi (Apache-2.0).
Clean-room reimplementation using aiohttp.
Source: https://github.com/CJNE/pyporscheconnectapi
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from ..auth.porsche import PorscheAuth
from ..exceptions import APIError, AuthenticationError, TokenExpiredError
from ..models import VehicleData, TokenSet

_LOGGER = logging.getLogger(__name__)

_API_BASE   = "https://api.ppa.porsche.com"
_X_CLIENT   = "41843fb4-691d-4970-85c7-2673e8ecef40"
_USER_AGENT = "My Porsche/2.1.0 (iPhone; iOS 17.0; Scale/3.00)"


class PorscheClient:
    """Porsche Connect API client.

    Uses Auth0 PKCE (identity.porsche.com) — completely separate from IDK/CARIAD.
    Not a subclass of CariadBaseClient because the auth system is different.
    """

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        spin: str = "",
    ) -> None:
        self._session = session
        self._email   = email
        self._password = password
        self._spin    = spin
        self._tokens: TokenSet | None = None
        self._auth = PorscheAuth(session)

    async def authenticate(self, mfa_code: str | None = None) -> None:
        """Auth0 PKCE login."""
        self._tokens = await self._auth.authenticate(self._email, self._password)
        _LOGGER.debug("Porsche Connect auth complete")

    async def get_vehicles(self) -> list[str]:
        """Return list of VINs from Porsche Connect garage."""
        data = await self._get(f"{_API_BASE}/app/connect/v1/vehicles")
        vins = []
        for v in data if isinstance(data, list) else []:
            vin = v.get("vin") or v.get("VIN")
            if vin:
                vins.append(vin)
                _LOGGER.debug("Porsche: found VIN %s model=%s", vin, v.get("modelName"))
        return vins

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full vehicle status from Porsche API."""
        v = self._val
        d = VehicleData(vin=vin)

        # Fetch vehicle details + measurements in parallel
        results = await asyncio.gather(
            self._get(f"{_API_BASE}/app/connect/v1/vehicles/{vin}"),
            self._get(f"{_API_BASE}/app/connect/v1/vehicles/{vin}/measurements", params={
                "fields": ",".join([
                    "BATTERY_LEVEL", "E_RANGE", "FUEL_LEVEL", "MILEAGE",
                    "CHARGING_SUMMARY", "CHARGING_STATE", "CLIMATIZER_STATE",
                    "GPS_LOCATION", "LOCK_STATE_VEHICLE", "OPEN_STATE_DOOR_FRONT_LEFT",
                    "OPEN_STATE_DOOR_FRONT_RIGHT", "OPEN_STATE_DOOR_REAR_LEFT",
                    "OPEN_STATE_DOOR_REAR_RIGHT", "OPEN_STATE_LID_FRONT",
                    "OPEN_STATE_LID_REAR", "OPEN_STATE_SUNROOF",
                    "MAIN_SERVICE_RANGE", "OIL_SERVICE_RANGE",
                ])
            }),
            return_exceptions=True,
        )
        vehicle_data, measurements = results

        # ── Vehicle meta ─────────────────────────────────────────────────────
        if isinstance(vehicle_data, dict):
            d.model        = vehicle_data.get("modelName")
            d.model_year   = v(vehicle_data, "modelType", "year")
            d.manufacturer = "Porsche"
            engine = v(vehicle_data, "modelType", "engine", default="")
            d.is_electric    = engine == "BEV"
            d.is_hybrid      = engine == "PHEV"
            d.has_battery    = engine in ("BEV", "PHEV")
            d.has_combustion = engine in ("PHEV", "COMBUSTION")

        # ── Measurements ──────────────────────────────────────────────────────
        if isinstance(measurements, (list, dict)):
            m = {item["key"]: item.get("value", {}) for item in (measurements if isinstance(measurements, list) else [])}

            d.battery_soc   = v(m, "BATTERY_LEVEL", "percent")
            d.range_km      = v(m, "E_RANGE", "distance") or v(m, "FUEL_LEVEL", "distanceToEmpty")
            d.fuel_level    = v(m, "FUEL_LEVEL", "percent")
            d.odometer_km   = v(m, "MILEAGE", "mileage")

            # Charging
            ch = m.get("CHARGING_SUMMARY", {})
            d.charging_state    = v(ch, "status")
            d.is_charging       = d.charging_state in ("CHARGING", "CHARGING_AC", "CHARGING_DC")
            d.charging_power_kw = v(ch, "chargingPower")
            d.plug_connected    = v(ch, "plugState") == "CONNECTED"
            d.plug_state        = v(ch, "plugState")
            d.target_soc        = v(ch, "targetSoc")

            # Lock
            lock = v(m, "LOCK_STATE_VEHICLE", "lockState")
            d.doors_locked = lock == "LOCKED"

            # Doors
            d.doors_open = any(
                v(m, f"OPEN_STATE_DOOR_{pos}", "openState") == "OPEN"
                for pos in ("FRONT_LEFT", "FRONT_RIGHT", "REAR_LEFT", "REAR_RIGHT")
            )
            d.hood_open   = v(m, "OPEN_STATE_LID_FRONT",  "openState") == "OPEN"
            d.trunk_open  = v(m, "OPEN_STATE_LID_REAR",   "openState") == "OPEN"
            d.sunroof_open = v(m, "OPEN_STATE_SUNROOF",   "openState") == "OPEN"

            # Climate
            clim = m.get("CLIMATIZER_STATE", {})
            d.climatisation_state  = v(clim, "climatisationState")
            d.climatisation_active = d.climatisation_state not in (None, "OFF")

            # GPS
            gps = m.get("GPS_LOCATION", {})
            d.latitude  = v(gps, "latitude")
            d.longitude = v(gps, "longitude")

            # Service
            d.service_km    = v(m, "MAIN_SERVICE_RANGE", "distance")
            d.oil_service_km = v(m, "OIL_SERVICE_RANGE", "distance")

        return d

    async def command_lock(self, vin: str) -> None:
        await self._command(vin, "LOCK")

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        await self._command(vin, "UNLOCK")

    async def command_start_climate(self, vin: str) -> None:
        await self._command(vin, "REMOTE_CLIMATIZER_START")

    async def command_stop_climate(self, vin: str) -> None:
        await self._command(vin, "REMOTE_CLIMATIZER_STOP")

    async def command_start_charging(self, vin: str) -> None:
        await self._command(vin, "DIRECT_CHARGING_START")

    async def command_stop_charging(self, vin: str) -> None:
        await self._command(vin, "DIRECT_CHARGING_STOP")

    async def command_flash(self, vin: str) -> None:
        await self._command(vin, "HONK_FLASH")

    async def command_wake(self, vin: str) -> None:
        # Porsche doesn't have a dedicated wake — flash serves as ping
        await self._command(vin, "HONK_FLASH")

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        await self._post(
            f"{_API_BASE}/app/connect/v1/vehicles/{vin}/commands",
            json={"commandName": "CHARGING_SETTINGS_EDIT", "payload": {"targetSoc": target}},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        await self._post(
            f"{_API_BASE}/app/connect/v1/vehicles/{vin}/commands",
            json={"commandName": "REMOTE_CLIMATIZER_START", "payload": {"temperature": temp_c}},
        )

    async def command_start_window_heating(self, vin: str) -> None:
        await self._command(vin, "REMOTE_HEATING_START")

    async def command_stop_window_heating(self, vin: str) -> None:
        await self._command(vin, "REMOTE_HEATING_STOP")

    async def command_set_departure_timer(
        self, vin: str, timer_id: int, enabled: bool, departure_time: str | None
    ) -> None:
        payload: dict[str, Any] = {"timerId": timer_id, "enabled": enabled}
        if departure_time:
            payload["departureTime"] = departure_time
        await self._post(
            f"{_API_BASE}/app/connect/v1/vehicles/{vin}/commands",
            json={"commandName": "DEPARTURES_EDIT" if enabled else "TIMERS_DISABLE", "payload": payload},
        )

    # ── HTTP helpers ─────────────────────────────────────────────────────────

    async def _command(self, vin: str, command: str, payload: dict | None = None) -> None:
        await self._post(
            f"{_API_BASE}/app/connect/v1/vehicles/{vin}/commands",
            json={"commandName": command, **(payload or {})},
        )

    async def _get(self, url: str, **kwargs: Any) -> Any:
        return await self._request("GET", url, **kwargs)

    async def _post(self, url: str, **kwargs: Any) -> Any:
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, retry: bool = True, **kwargs: Any) -> Any:
        if not self._tokens:
            raise AuthenticationError("Not authenticated")
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {self._tokens.access_token}",
            "X-Client-ID":   _X_CLIENT,
            "User-Agent":    _USER_AGENT,
            "Accept":        "application/json",
        })
        async with self._session.request(
            method, url, headers=headers,
            timeout=ClientTimeout(total=30), **kwargs
        ) as resp:
            if resp.status == 401 and retry:
                await self._refresh()
                return await self._request(method, url, retry=False, **kwargs)
            if resp.status == 204:
                return {}
            if resp.status not in (200, 202):
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
