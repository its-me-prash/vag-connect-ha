# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""SEAT/CUPRA API client — ola.prod.code.seat.cloud.vwgroup.com.

Source: WulfgarW/pycupra (Apache-2.0) — clean-room reimplementation of endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession

from ..models import BRAND_CUPRA, BRAND_SEAT, BrandConfig, VehicleData
from .base import CariadBaseClient

_LOGGER = logging.getLogger(__name__)
_BASE = "https://ola.prod.code.seat.cloud.vwgroup.com"


class SeatCupraClient(CariadBaseClient):
    """SEAT/CUPRA API client."""

    def __init__(
        self,
        session: ClientSession,
        brand: str,
        email: str,
        password: str,
        spin: str = "",
    ) -> None:
        brand_cfg: BrandConfig = BRAND_CUPRA if brand.lower() == "cupra" else BRAND_SEAT
        super().__init__(session, brand_cfg, email, password, spin)
        self._user_id: str | None = None

    async def authenticate(self, mfa_code: str | None = None) -> None:
        """IDK auth + fetch user_id."""
        await super().authenticate()
        await self._fetch_user_id()

    async def _fetch_user_id(self) -> None:
        """Fetch user ID needed for garage endpoint.

        Strategy: extract 'sub' claim from the ID token JWT (no API call needed).
        Fallback: GET /v1/users endpoint.
        """
        # Try extracting from ID token first (most reliable)
        if self._tokens and self._tokens.id_token:
            try:
                import base64  # noqa: PLC0415
                import json as _json  # noqa: PLC0415
                # JWT payload is the second segment (base64url-encoded, no padding)
                payload_b64 = self._tokens.id_token.split(".")[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)  # fix padding
                payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                sub = payload.get("sub")
                if sub:
                    self._user_id = sub
                    _LOGGER.debug("SEAT/CUPRA user_id from ID token: %s", sub[:8])
                    return
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not extract user_id from ID token")

        # Fallback: API call
        try:
            data = await self._get(f"{_BASE}/v1/users")
            self._user_id = data.get("userId") or data.get("sub")
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Could not fetch SEAT/CUPRA user ID")

    async def get_vehicles(self) -> list[str]:
        """Return VINs from garage."""
        if not self._user_id:
            await self._fetch_user_id()
        data = await self._get(f"{_BASE}/v2/users/{self._user_id}/garage/vehicles")
        vehicles: list[dict[str, Any]] = data.get("vehicles", [])
        vins = [v["vin"] for v in vehicles if v.get("vin")]
        await self.fetch_images()
        return vins

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full status from OLA server."""
        import asyncio  # noqa: PLC0415
        v = self._val
        d = VehicleData(vin=vin)

        results = await asyncio.gather(
            self._get(f"{_BASE}/v5/users/{self._user_id}/vehicles/{vin}/mycar"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/parkingposition"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/charging"),
            self._get(f"{_BASE}/v2/vehicles/{vin}/climatisation"),
            return_exceptions=True,
        )
        mycar, parking, charging, climate = results

        # ── Main vehicle data ─────────────────────────────────────────────────
        if isinstance(mycar, dict):
            measurements = v(mycar, "measurements") or {}
            d.odometer_km = v(measurements, "mileage", "value")
            d.fuel_level = v(measurements, "fuelLevelStatus", "value", "currentFuelLevel_pct")
            d.battery_soc = v(measurements, "batteryStatus", "value", "currentSOC_pct")
            d.has_battery = d.battery_soc is not None

            access = v(mycar, "access") or {}
            d.doors_locked = v(access, "accessStatus", "value", "doorLockStatus") == "LOCKED"

            service = v(mycar, "vehicleHealthInspection") or {}
            d.service_km = v(service, "maintenanceStatus", "value", "inspectionDue_km")
            d.oil_service_km = v(service, "maintenanceStatus", "value", "oilServiceDue_km")

        # ── Charging ─────────────────────────────────────────────────────────
        if isinstance(charging, dict):
            d.charging_state = v(charging, "status", "chargingStatus", "value", "chargingState")
            d.is_charging = d.charging_state == "CHARGING"
            d.charging_power_kw = v(charging, "status", "chargingStatus", "value", "chargePower_kW")
            plug = v(charging, "status", "plugStatus", "value", "plugConnectionState")
            d.plug_connected = plug == "CONNECTED"
            d.plug_state = plug
            d.target_soc = v(charging, "settings", "targetSOC_pct")

        # ── Climate ───────────────────────────────────────────────────────────
        if isinstance(climate, dict):
            d.climatisation_state = v(climate, "status", "climatisationState")
            d.climatisation_active = d.climatisation_state not in (None, "OFF")
            d.target_temperature = v(climate, "settings", "targetTemperature_K")
            if d.target_temperature:
                d.target_temperature = round(float(d.target_temperature) - 273.15, 1)

        # ── Parking ───────────────────────────────────────────────────────────
        if isinstance(parking, dict):
            d.latitude = v(parking, "lat")
            d.longitude = v(parking, "lon")

        # ── Image data ───────────────────────────────────────────────────────
        img = self._image_data.get(vin)
        if img:
            d.image_urls          = img.image_urls
            d.media_short_name    = img.short_name
            d.media_long_name     = img.long_name
            d.media_exterior_color = img.exterior_color

        # ── Drivetrain ────────────────────────────────────────────────────────
        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        return d

    async def command_lock(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicles/{vin}/access/lock", json={})

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        payload: dict[str, Any] = {}
        if spin or self._spin:
            payload["spin"] = spin or self._spin
        await self._post(f"{_BASE}/v1/vehicles/{vin}/access/unlock", json=payload)

    async def command_start_climate(self, vin: str) -> None:
        await self._post(f"{_BASE}/v2/vehicles/{vin}/climatisation", json={"action": "start"})

    async def command_stop_climate(self, vin: str) -> None:
        await self._post(f"{_BASE}/v2/vehicles/{vin}/climatisation", json={"action": "stop"})

    async def command_start_charging(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicles/{vin}/charging/actions", json={"action": "start"})

    async def command_stop_charging(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicles/{vin}/charging/actions", json={"action": "stop"})

    async def command_flash(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicles/{vin}/honk-and-flash", json={"mode": "FLASH_ONLY"})

    async def command_wake(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicles/{vin}/vehicle-wakeup/request", json={})

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        await self._post(
            f"{_BASE}/v1/vehicles/{vin}/charging/actions",
            json={"action": "settings", "targetSOC_pct": target},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        await self._post(
            f"{_BASE}/v2/vehicles/{vin}/climatisation",
            json={"action": "settings", "targetTemperature_K": temp_c + 273.15},
        )
