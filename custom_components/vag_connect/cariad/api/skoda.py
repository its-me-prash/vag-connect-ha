# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Škoda API client — mysmob.api.connect.skoda-auto.cz.

Source: skodaconnect/myskoda (MIT) — clean-room reimplementation of endpoints.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from aiohttp import ClientSession

from ..models import BRAND_SKODA, VehicleData
from .base import CariadBaseClient

_LOGGER = logging.getLogger(__name__)
_BASE = "https://mysmob.api.connect.skoda-auto.cz"


class SkodaClient(CariadBaseClient):
    """Škoda API client."""

    def __init__(
        self, session: ClientSession, email: str, password: str, spin: str = ""
    ) -> None:
        super().__init__(session, BRAND_SKODA, email, password, spin)

    async def get_vehicles(self) -> list[str]:
        """Return VINs from Škoda garage."""
        params = {
            "connectivityGenerations": ["MOD1", "MOD2", "MOD3", "MOD4"],
        }
        data = await self._get(f"{_BASE}/v2/garage", params=params)
        vehicles: list[dict[str, Any]] = data.get("vehicles", [])
        vins = [v["vin"] for v in vehicles if v.get("vin")]
        await self.fetch_images()
        return vins

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full status from Škoda API."""
        v = self._val
        d = VehicleData(vin=vin)

        # Parallel fetch of key endpoints
        results = await asyncio.gather(
            self._get(f"{_BASE}/v2/vehicle-status/{vin}"),
            self._get(f"{_BASE}/v1/charging/{vin}"),
            self._get(f"{_BASE}/v2/air-conditioning/{vin}"),
            self._get(f"{_BASE}/v1/maps/positions?vin={vin}"),
            self._get(f"{_BASE}/v2/vehicle-status/{vin}/driving-range"),
            self._get(f"{_BASE}/v3/vehicle-maintenance/vehicles/{vin}"),
            self._get(f"{_BASE}/v2/connection-status/{vin}/readiness"),
            return_exceptions=True,
        )
        status, charging, ac, positions, driving_range, maintenance, readiness = results

        # ── Access ──────────────────────────────────────────────────────────
        if isinstance(status, dict):
            access = v(status, "access") or {}
            d.doors_locked = v(access, "overallStatus") != "OPEN"
            d.doors_open = v(access, "doorsOpenedCount", default=0) > 0
            d.windows_open = v(access, "windowsOpenedCount", default=0) > 0
            d.odometer_km = v(status, "detail", "mileageInKm")

        # ── Charging ────────────────────────────────────────────────────────
        if isinstance(charging, dict):
            c = charging.get("status", {})
            d.battery_soc = v(c, "battery", "stateOfChargeInPercent")
            d.charging_state = v(c, "charging", "state")
            d.is_charging = d.charging_state == "CHARGING"
            d.charging_power_kw = v(c, "charging", "chargePowerInKw")
            d.charging_rate_kmh = v(c, "charging", "chargeRateInKmPerHour")
            remaining = v(c, "charging", "remainingTimeToFullyChargedInMinutes")
            if remaining:
                d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=int(remaining))
            plug = v(c, "plug", "connectionState")
            d.plug_connected = plug == "CONNECTED"
            d.plug_state = plug
            d.has_battery = d.battery_soc is not None

            settings = charging.get("settings", {})
            d.target_soc = v(settings, "targetStateOfChargeInPercent")
            d.auto_unlock_charge = v(settings, "autoUnlockPlugWhenChargedAC") == "ON"

        # ── Air conditioning ─────────────────────────────────────────────────
        if isinstance(ac, dict):
            status_ac = ac.get("status", {})
            d.climatisation_state = v(status_ac, "state")
            d.climatisation_active = d.climatisation_state not in (None, "OFF")
            d.target_temperature = v(ac, "settings", "targetTemperatureInCelsius")

        # ── Position ─────────────────────────────────────────────────────────
        if isinstance(positions, dict):
            parking = v(positions, "positions", default=[])
            if isinstance(parking, list) and parking:
                pos = parking[0].get("gpsCoordinates", {})
                d.latitude = pos.get("latitude")
                d.longitude = pos.get("longitude")

        # ── Range ────────────────────────────────────────────────────────────
        if isinstance(driving_range, dict):
            electric = v(driving_range, "electricRange", "distanceInKm")
            total = v(driving_range, "totalRangeInKm")
            d.range_km = electric or total
            fuel = v(driving_range, "combustionRange")
            d.has_combustion = fuel is not None

        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        # ── Maintenance ──────────────────────────────────────────────────────
        if isinstance(maintenance, dict):
            d.service_km = v(maintenance, "maintenanceStatus", "inspectionDue_km")
            d.service_due_at = v(maintenance, "maintenanceStatus", "inspectionDue_days")
            d.oil_service_km = v(maintenance, "maintenanceStatus", "oilServiceDue_km")

        # ── Readiness / online ───────────────────────────────────────────────
        if isinstance(readiness, dict):
            d.is_online = v(readiness, "connectionState", "isOnline") is True

        return d

    async def command_lock(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicle-access/{vin}/lock", json={})

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        payload: dict[str, Any] = {}
        if spin or self._spin:
            payload["spin"] = spin or self._spin
        await self._post(f"{_BASE}/v1/vehicle-access/{vin}/unlock", json=payload)

    async def command_start_climate(self, vin: str) -> None:
        await self._post(f"{_BASE}/v2/air-conditioning/{vin}/start", json={})

    async def command_stop_climate(self, vin: str) -> None:
        await self._post(f"{_BASE}/v2/air-conditioning/{vin}/stop", json={})

    async def command_start_charging(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/charging/{vin}/start", json={})

    async def command_stop_charging(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/charging/{vin}/stop", json={})

    async def command_flash(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicle-access/{vin}/honk-and-flash", json={"mode": "FLASH_ONLY"})

    async def command_wake(self, vin: str) -> None:
        await self._post(f"{_BASE}/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true", json={})

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        await self._post(
            f"{_BASE}/v1/charging/{vin}/set-charge-limit",
            json={"targetStateOfChargeInPercent": target},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        await self._post(
            f"{_BASE}/v2/air-conditioning/{vin}/settings/target-temperature",
            json={"temperatureValue": temp_c, "unitInCar": "CELSIUS"},
        )
