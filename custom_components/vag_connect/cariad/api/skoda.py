# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Škoda API client — mysmob.api.connect.skoda-auto.cz.

API endpoints verified against skodaconnect/myskoda (MIT) model classes.
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
        data = await self._get(f"{_BASE}/api/v2/garage", params=params)
        vehicles: list[dict[str, Any]] = data.get("vehicles", [])
        vins = [v["vin"] for v in vehicles if v.get("vin")]
        await self.fetch_images()
        return vins

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full status from Škoda API."""
        v = self._val
        d = VehicleData(vin=vin)

        results = await asyncio.gather(
            self._get(f"{_BASE}/api/v2/vehicle-status/{vin}"),
            self._get(f"{_BASE}/api/v1/charging/{vin}"),
            self._get(f"{_BASE}/api/v2/air-conditioning/{vin}"),
            self._get(f"{_BASE}/api/v3/maps/positions/vehicles/{vin}/parking"),
            self._get(f"{_BASE}/api/v2/vehicle-status/{vin}/driving-range"),
            self._get(f"{_BASE}/api/v3/vehicle-maintenance/vehicles/{vin}"),
            self._get(f"{_BASE}/api/v2/connection-status/{vin}/readiness"),
            return_exceptions=True,
        )
        status, charging, ac, parking, driving_range, maintenance, readiness = results

        # ── Access / doors / windows / detail ────────────────────────────────
        if isinstance(status, dict):
            access = v(status, "access") or {}
            d.doors_locked = v(access, "overallStatus") != "OPEN"
            d.doors_open = v(access, "doorsOpenedCount", default=0) > 0
            d.windows_open = v(access, "windowsOpenedCount", default=0) > 0

            # v1.8.11 (Session 3S) — `vehicle-status` real shape verified
            # against tillsteinbach/CarConnectivity-connector-skoda issue #50
            # (Kodiaq iV 2026 Live-Response, posted 2026-03-25):
            #
            #   {"overall":  {"doorsLocked": "YES", "locked": "YES",
            #                 "doors": "CLOSED", "windows": "CLOSED",
            #                 "lights": "OFF",
            #                 "reliableLockStatus": "LOCKED"},
            #    "detail":   {"sunroof": "CLOSED", "trunk": "CLOSED",
    #                          "bonnet": "CLOSED"},
            #    "carCapturedTimestamp": "..."}
            #
            # Pre-v1.8.11 the Skoda parser ignored both ``overall.*`` flags
            # AND the ``detail`` block entirely — sunroof, trunk and hood
            # entities never populated for any Skoda model. Fix: read the
            # detail block; treat "UNSUPPORTED" as "field doesn't apply"
            # (entity stays None / unavailable) so Karoq Diesel doesn't
    #     show a sunroof entity.
            overall = v(status, "overall") or {}
            detail = v(status, "detail") or {}

            # Prefer the new ``reliableLockStatus`` (Kodiaq 2026+) over
            # the older ``doorsLocked`` aggregate when available — the
            # name itself signals it's the trustworthy field.
            lock_raw = (
                v(overall, "reliableLockStatus")
                or v(overall, "doorsLocked")
                or v(overall, "locked")
            )
            if isinstance(lock_raw, str):
                d.doors_locked = lock_raw.upper() in ("YES", "LOCKED", "TRUE")

            def _detail_open(field: str) -> bool | None:
                """Map detail.{sunroof,trunk,bonnet} string to bool open.
                Returns None for "UNSUPPORTED" so the entity stays None."""
                raw = detail.get(field)
                if not isinstance(raw, str):
                    return None
                up = raw.upper()
                if up == "OPEN":
                    return True
                if up == "CLOSED":
                    return False
                # "UNSUPPORTED" or any other value → not applicable
                return None

            sunroof = _detail_open("sunroof")
            if sunroof is not None:
                d.sunroof_open = sunroof
            trunk = _detail_open("trunk")
            if trunk is not None:
                d.trunk_open = trunk
            bonnet = _detail_open("bonnet")  # mysmob calls it bonnet, our field is hood
            if bonnet is not None:
                d.hood_open = bonnet

        # ── Charging ─────────────────────────────────────────────────────────
        # v1.8.11 (Session 3S): `charging.status.fullyChargedAt` is an
        # absolute ISO timestamp returned by current Kodiaq iV 2026
        # firmware (verified in CC-skoda issue #50). Prefer it over
        # `remainingTimeToFullyChargedInMinutes + now()` because the
        # latter drifts: if the backend value is computed at car-side
        # and we receive it 5 minutes later via polling, our derived ETA
        # is 5 minutes off. The absolute timestamp doesn't drift.
        if isinstance(charging, dict):
            c = charging.get("status", {})
            d.battery_soc = v(c, "battery", "stateOfChargeInPercent")
            d.charging_state = v(c, "state")
            d.is_charging = d.charging_state == "CHARGING"
            d.charging_power_kw = v(c, "chargePowerInKw")
            d.charging_rate_kmh = v(c, "chargingRateInKilometersPerHour")
            d.charging_type = v(c, "chargeType")
            fully_at = v(c, "fullyChargedAt")
            if isinstance(fully_at, str):
                try:
                    d.charge_complete_eta = datetime.fromisoformat(
                        fully_at.replace("Z", "+00:00"))
                except ValueError:
                    fully_at = None  # Fall through to remaining-minutes calc below
            if not d.charge_complete_eta:
                remaining = v(c, "remainingTimeToFullyChargedInMinutes")
                if remaining:
                    d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=int(remaining))
            d.has_battery = d.battery_soc is not None

            settings = charging.get("settings", {})
            d.target_soc = v(settings, "targetStateOfChargeInPercent")
            d.auto_unlock_charge = v(settings, "autoUnlockPlugWhenChargedAC") == "ON"

        # ── Air conditioning (also has plug state!) ──────────────────────────
        if isinstance(ac, dict):
            d.climatisation_state = v(ac, "state")
            d.climatisation_active = d.climatisation_state not in (None, "OFF", "INVALID")
            temp_val = v(ac, "targetTemperature", "temperatureValue")
            if temp_val is not None:
                d.target_temperature = float(temp_val)

            wh = v(ac, "windowHeatingState") or {}
            d.window_heating_front = v(wh, "front") == "ON"
            d.window_heating_back = v(wh, "rear") == "ON"

            plug_conn = v(ac, "chargerConnectionState")
            if plug_conn:
                d.plug_connected = plug_conn == "CONNECTED"
                d.plug_state = plug_conn
            d.connector_locked = v(ac, "chargerLockState") == "LOCKED"

        # ── Parking position (v3 with formatted address) ─────────────────────
        if isinstance(parking, dict):
            pos = v(parking, "parkingPosition", "gpsCoordinates") or {}
            d.latitude = pos.get("latitude")
            d.longitude = pos.get("longitude")
            addr = v(parking, "parkingPosition", "formattedAddress")
            if addr:
                d.parking_address = addr

        # ── Driving range ────────────────────────────────────────────────────
        if isinstance(driving_range, dict):
            electric = v(driving_range, "electricRange", "distanceInKm")
            total = v(driving_range, "totalRangeInKm")
            d.range_km = electric or total
            fuel = v(driving_range, "combustionRange")
            d.has_combustion = fuel is not None
            adblue = v(driving_range, "adBlueRange", "distanceInKm")
            if adblue is not None:
                d.adblue_range_km = int(adblue)

        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        # ── Maintenance ──────────────────────────────────────────────────────
        if isinstance(maintenance, dict):
            report = v(maintenance, "maintenanceReport") or maintenance
            d.odometer_km = v(report, "mileageInKm")
            d.service_km = v(report, "inspectionDueInKm")
            d.service_due_at = v(report, "inspectionDueInDays")
            d.oil_service_km = v(report, "oilServiceDueInKm")
            d.oil_service_at = v(report, "oilServiceDueInDays")

        # ── Connection status ────────────────────────────────────────────────
        if isinstance(readiness, dict):
            unreachable = v(readiness, "unreachable")
            # When unreachable is unknown (None), assume reachable (True)
            # to avoid setting is_online to a falsy default.
            d.is_online = unreachable is None or unreachable is False
            d.is_driving = v(readiness, "inMotion") is True

        # ── carCapturedTimestamp → connection_state (v1.8.11 Session 3S) ────
        # Closes #54 (GitHobi). The official Škoda Connect app shows a
        # three-state "Online / Standby / Offline" indicator that is NOT
        # backed by any single API field — it is derived from
        # ``carCapturedTimestamp`` which appears on every status sub-object
        # in the mysmob response. Verified against `skodaconnect/myskoda`
        # source: 9 model files (`models/air_conditioning.py`, `charging.py`,
        # `status.py`, `driving_range.py`, `software_status.py`,
        # `departure.py`, `auxiliary_heating.py`, `chargingprofiles.py`,
        # plus the v2 air_conditioning variant) all decorate
        # `field_options(alias="carCapturedTimestamp")`.
        #
        # Semantics — derived from `homeassistant-myskoda` issues #751, #731:
        #   age < 30 min   → "online"   (live data, just heard from the car)
        #   age < 24 h     → "standby"  (asleep but reachable via /wakeup)
        #   age >= 24 h    → "offline"  (12V flat / underground / service)
        #
        # The freshest timestamp across all sub-objects wins — different
        # systems update independently (e.g. charging publishes more
        # frequently than door state).
        latest_ts: datetime | None = None
        for sub in (status, charging, ac, parking, driving_range, maintenance, readiness):
            if not isinstance(sub, dict):
                continue
            for ts_key in ("carCapturedTimestamp",):
                ts_str = sub.get(ts_key)
                if isinstance(ts_str, str):
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if latest_ts is None or ts > latest_ts:
                            latest_ts = ts
                    except ValueError:
                        # Bad timestamp from backend — ignore, don't crash.
                        pass

        if latest_ts is not None:
            d.last_seen_at = latest_ts
            age_s = (datetime.now(tz=timezone.utc) - latest_ts).total_seconds()
            if age_s < 1800:        # < 30 min
                d.connection_state = "online"
            elif age_s < 86400:     # < 24 h
                d.connection_state = "standby"
            else:
                d.connection_state = "offline"

        return d

    # ── Commands ─────────────────────────────────────────────────────────────

    async def command_lock(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v1/vehicle-access/{vin}/lock", json={})

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        payload: dict[str, Any] = {}
        if spin or self._spin:
            payload["spin"] = spin or self._spin
        await self._post(f"{_BASE}/api/v1/vehicle-access/{vin}/unlock", json=payload)

    async def command_start_climate(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v2/air-conditioning/{vin}/start", json={})

    async def command_stop_climate(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v2/air-conditioning/{vin}/stop", json={})

    async def command_start_charging(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v1/charging/{vin}/start", json={})

    async def command_stop_charging(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v1/charging/{vin}/stop", json={})

    async def command_flash(
        self,
        vin: str,
        latitude: float | None = None,  # noqa: ARG002
        longitude: float | None = None,  # noqa: ARG002
    ) -> None:
        await self._post(f"{_BASE}/api/v1/vehicle-access/{vin}/honk-and-flash", json={"mode": "FLASH_ONLY"})

    async def command_wake(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true", json={})

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        await self._post(
            f"{_BASE}/api/v1/charging/{vin}/set-charge-limit",
            json={"targetStateOfChargeInPercent": target},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        await self._post(
            f"{_BASE}/api/v2/air-conditioning/{vin}/settings/target-temperature",
            json={"temperatureValue": temp_c, "unitInCar": "CELSIUS"},
        )

    async def command_start_window_heating(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v2/air-conditioning/{vin}/start-window-heating", json={})

    async def command_stop_window_heating(self, vin: str) -> None:
        await self._post(f"{_BASE}/api/v2/air-conditioning/{vin}/stop-window-heating", json={})
