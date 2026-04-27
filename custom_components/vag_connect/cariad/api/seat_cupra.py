# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""SEAT/CUPRA API client — ola.prod.code.seat.cloud.vwgroup.com.

API endpoints based on WulfgarW/pycupra (Apache-2.0) — clean-room reimplementation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from aiohttp import ClientSession

from ..exceptions import APIError
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
        """IDK auth + capture user_id from redirect chain."""
        await super().authenticate()
        if self._auth.user_id:
            self._user_id = self._auth.user_id
            _LOGGER.debug("SEAT/CUPRA user_id from auth redirect: %s", self._user_id[:8])
        else:
            await self._fetch_user_id()

    async def _fetch_user_id(self) -> None:
        """Fallback: extract user_id from JWT or API call."""
        if self._tokens and self._tokens.id_token:
            try:
                import base64  # noqa: PLC0415
                import json as _json  # noqa: PLC0415
                payload_b64 = self._tokens.id_token.split(".")[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
                sub = payload.get("sub")
                if sub:
                    self._user_id = sub
                    _LOGGER.debug("SEAT/CUPRA user_id from JWT: %s", sub[:8])
                    return
            except Exception:  # noqa: BLE001
                pass

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
        await self._fetch_renders(vins)
        await self.fetch_images()
        return vins

    async def _fetch_renders(self, vins: list[str]) -> None:
        """Fetch vehicle render images from OLA renders endpoint."""
        for vin in vins:
            try:
                data = await self._get(f"{_BASE}/v2/vehicles/{vin}/renders")
                urls: dict[str, str] = {}
                for render in data if isinstance(data, list) else data.get("renders", []):
                    view = render.get("viewPoint") or render.get("type", "")
                    url = render.get("url", "")
                    if view and url:
                        urls[view] = url
                if urls:
                    from .graphql import VehicleImageData  # noqa: PLC0415
                    self._image_data[vin] = VehicleImageData(
                        vin=vin, image_urls=urls, short_name=None, long_name=None, exterior_color=None
                    )
                    _LOGGER.debug("SEAT/CUPRA renders for %s: %d views", vin[-6:], len(urls))
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not fetch renders for %s", vin[-6:])

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full status from OLA server."""
        v = self._val
        d = VehicleData(vin=vin)

        results = await asyncio.gather(
            self._get(f"{_BASE}/v5/users/{self._user_id}/vehicles/{vin}/mycar"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/parkingposition"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/ranges"),
            self._get(f"{_BASE}/v2/vehicles/{vin}/status"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/charging/status"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/charging/info"),
            self._get(f"{_BASE}/v2/vehicles/{vin}/climatisation"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/maintenance"),
            self._get(f"{_BASE}/v1/vehicles/{vin}/remote-availability"),
            return_exceptions=True,
        )
        mycar, parking, ranges, status, charge_status, charge_info, climate, maintenance, availability = results

        # ── Main vehicle data (mycar) ────────────────────────────────────────
        if isinstance(mycar, dict):
            measurements = v(mycar, "measurements") or {}
            d.odometer_km = v(measurements, "mileage", "value")
            d.fuel_level = v(measurements, "fuelLevelStatus", "value", "currentFuelLevel_pct")
            d.battery_soc = v(measurements, "batteryStatus", "value", "currentSOC_pct")
            d.has_battery = d.battery_soc is not None

            access = v(mycar, "access") or {}
            d.doors_locked = v(access, "accessStatus", "value", "doorLockStatus") == "LOCKED"

        # ── Ranges ───────────────────────────────────────────────────────────
        if isinstance(ranges, dict):
            electric = v(ranges, "electricRange")
            combustion = v(ranges, "gasolineRange") or v(ranges, "dieselRange")
            d.range_km = electric or combustion or v(ranges, "totalRange")
            d.has_combustion = combustion is not None
            d.adblue_range_km = v(ranges, "adBlueRange")

        # ── Detailed vehicle status (doors, windows, trunk) ──────────────────
        if isinstance(status, dict):
            access_s = v(status, "access") or status
            d.doors_open = v(access_s, "doorsOpenedCount", default=0) > 0
            d.windows_open = v(access_s, "windowsOpenedCount", default=0) > 0
            d.trunk_open = v(access_s, "trunk") == "OPEN" or v(access_s, "trunkOpen") is True
            d.trunk_locked = v(access_s, "trunkLocked") is True or v(access_s, "trunkStatus") == "LOCKED"
            d.hood_open = v(access_s, "hood") == "OPEN" or v(access_s, "hoodOpen") is True
            d.sunroof_open = v(access_s, "sunroof") == "OPEN" or v(access_s, "sunroofOpen") is True

            doors = {}
            for key in ("doorClosedLeftFront", "doorClosedRightFront", "doorClosedLeftBack", "doorClosedRightBack"):
                val = v(access_s, key)
                if val is not None:
                    door_id = key.replace("doorClosed", "").replace("LeftFront", "frontLeft").replace("RightFront", "frontRight").replace("LeftBack", "rearLeft").replace("RightBack", "rearRight")
                    doors[door_id] = not val
            if doors:
                d.doors_individual = doors

        # ── Charging status ──────────────────────────────────────────────────
        if isinstance(charge_status, dict):
            bat = v(charge_status, "battery") or charge_status
            if d.battery_soc is None:
                d.battery_soc = v(bat, "stateOfChargeInPercent") or v(bat, "currentSOC_pct")
                d.has_battery = d.battery_soc is not None

            chg = v(charge_status, "charging") or charge_status
            d.charging_state = v(chg, "state") or v(chg, "chargingState")
            d.is_charging = d.charging_state == "CHARGING"
            d.charging_power_kw = v(chg, "chargePowerInKw") or v(chg, "chargePower_kW")
            d.charging_rate_kmh = v(chg, "chargeRateInKmPerHour") or v(chg, "chargeRate_kmph")
            remaining = v(chg, "remainingTimeToFullyChargedInMinutes") or v(chg, "remainingChargingTime")
            if remaining:
                d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=int(remaining))
            d.charging_type = v(chg, "chargeType") or v(chg, "chargingType")

            plug = v(charge_status, "plug") or {}
            plug_state = v(plug, "connectionState") or v(plug, "plugConnectionState")
            d.plug_connected = plug_state == "CONNECTED"
            d.plug_state = plug_state
            d.connector_locked = v(plug, "lockState") == "LOCKED" or v(plug, "externalPower") == "READY"

        # ── Charging info (settings) ─────────────────────────────────────────
        if isinstance(charge_info, dict):
            d.target_soc = v(charge_info, "targetSOC_pct") or v(charge_info, "targetStateOfChargeInPercent")
            d.max_charge_current = v(charge_info, "maxChargeCurrentAC") or v(charge_info, "maxChargeCurrent")
            d.auto_unlock_charge = v(charge_info, "autoUnlockPlugWhenCharged") == "ON" or v(charge_info, "autoUnlockPlugWhenChargedAC") is True

        # ── Climate ──────────────────────────────────────────────────────────
        if isinstance(climate, dict):
            cs = v(climate, "status") or climate
            d.climatisation_state = v(cs, "climatisationState") or v(cs, "state")
            d.climatisation_active = d.climatisation_state not in (None, "OFF", "off")
            d.target_temperature = v(climate, "settings", "targetTemperature_K")
            if d.target_temperature:
                d.target_temperature = round(float(d.target_temperature) - 273.15, 1)
            if not d.target_temperature:
                d.target_temperature = v(climate, "settings", "targetTemperatureInCelsius")
            d.outside_temp = v(cs, "outsideTemperature")
            if d.outside_temp and d.outside_temp > 100:
                d.outside_temp = round(float(d.outside_temp) - 273.15, 1)
            d.window_heating_front = v(cs, "windowHeatingStateFront") == "ON"
            d.window_heating_back = v(cs, "windowHeatingStateRear") == "ON"

        # ── Parking ──────────────────────────────────────────────────────────
        if isinstance(parking, dict):
            d.latitude = v(parking, "lat")
            d.longitude = v(parking, "lon")

        # ── Maintenance ──────────────────────────────────────────────────────
        if isinstance(maintenance, dict):
            d.service_km = v(maintenance, "inspectionDue_km") or v(maintenance, "distanceToInspection")
            d.service_due_at = v(maintenance, "inspectionDue_days") or v(maintenance, "daysToInspection")
            d.oil_service_km = v(maintenance, "oilServiceDue_km") or v(maintenance, "distanceToOilChange")
            d.oil_service_at = v(maintenance, "oilServiceDue_days") or v(maintenance, "daysToOilChange")

        # ── Availability ─────────────────────────────────────────────────────
        if isinstance(availability, dict):
            d.is_online = v(availability, "isOnline") is True or v(availability, "status") == "ONLINE"

        # ── Image data ───────────────────────────────────────────────────────
        img = self._image_data.get(vin)
        if img:
            d.image_urls = img.image_urls
            d.media_short_name = img.short_name
            d.media_long_name = img.long_name
            d.media_exterior_color = img.exterior_color

        # ── Drivetrain ───────────────────────────────────────────────────────
        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        return d

    # ── Commands ─────────────────────────────────────────────────────────────

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

    async def command_flash(
        self,
        vin: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        """SEAT/CUPRA honk-and-flash.

        The OLA endpoint requires a `userPosition` field; without it the API
        returns HTTP 400 "internal-error". Mode must be lowercase "flash"
        (not "FLASH_ONLY"). Coordinates are truncated to 4 decimals (~11 m).

        Despite the field name, OLA expects the **vehicle's** last-known
        position, not the user's phone GPS. Verified against pycupra
        `vehicle.set_honkandflash` (uses `findCarResponse` lat/lon) and the
        myskoda equivalent (sends `PositionType.VEHICLE`). The name is a
        misnomer in the OLA contract — the field acts as a server-side
        sanity token bound to the car's known location.
        """
        if latitude is None or longitude is None:
            raise APIError(
                400,
                f"{_BASE}/v1/vehicles/{vin}/honk-and-flash",
                "Vehicle position is required for honk-and-flash on SEAT/CUPRA. "
                "Wait for the next status poll, then retry.",
            )
        body = {
            "mode": "flash",
            "userPosition": {
                "latitude": int(latitude * 10000) / 10000,
                "longitude": int(longitude * 10000) / 10000,
            },
        }
        await self._post(f"{_BASE}/v1/vehicles/{vin}/honk-and-flash", json=body)

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

    async def command_start_window_heating(self, vin: str) -> None:
        await self._post(f"{_BASE}/v2/vehicles/{vin}/climatisation", json={"action": "startWindowHeating"})

    async def command_stop_window_heating(self, vin: str) -> None:
        await self._post(f"{_BASE}/v2/vehicles/{vin}/climatisation", json={"action": "stopWindowHeating"})
