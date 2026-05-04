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

from .._util import compute_connection_state, safe_float, safe_int
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

    async def get_charging_profiles(self, vin: str) -> dict[str, Any]:
        """v1.16.0 (#25, #31) — Skoda charging profiles (read-only).

        Endpoint: ``GET /api/v1/charging/{vin}/profiles``
        Response shape (verified myskoda/models/chargingprofiles.py):
            {
              "chargingProfiles": [
                {"id": 1, "name": "Home",
                 "settings": {
                   "maxChargingCurrent": "MAXIMUM"|"REDUCED",
                   "minBatteryStateOfCharge": {"minimumBatteryStateOfChargeInPercent": 20},
                   "targetStateOfChargeInPercent": 80,
                   "autoUnlockPlugWhenCharged": "PERMANENT"|"ON"|"OFF"
                 },
                 "preferredChargingTimes": [{"id": 1, "enabled": true,
                    "startTime": "22:00", "endTime": "06:00"}],
                 "timers": [{"id": 1, "enabled": false, "time": "07:30",
                    "type": "RECURRING"|"ONE_OFF",
                    "recurringOn": ["MONDAY", ...]}],
                 "location": {"latitude": 47.39, "longitude": 8.21} | None
                },
                ...
              ],
              "currentVehiclePositionProfile": {
                "id": 1, "name": "Home",
                "targetStateOfChargeInPercent": 80,
                "nextChargingTime": "22:00" | None
              } | None,
              "carCapturedTimestamp": "..." | None
            }

        ``currentVehiclePositionProfile`` is the killer field for #25
        (location-based target SoC) — backend tells us which of the user's
        registered profiles is active right now based on the car's
        current GPS position.

        Best-effort: 404 / 403 → exception in caller's gather. Returns
        ``{}`` for non-dict responses.
        """
        url = f"{_BASE}/api/v1/charging/{vin}/profiles"
        data = await self._get(url)
        return data if isinstance(data, dict) else {}

    async def get_charging_history(
        self, vin: str, limit: int = 50
    ) -> dict[str, Any]:
        """v1.15.0 (#35) — Skoda charging history (myskoda PR shipped 2026).

        Endpoint: ``GET /api/v1/charging/{vin}/history?userTimezone=UTC&limit={N}``
        Response shape (verified via myskoda/models/charging_history.py):
            {
              "nextCursor": "<ISO datetime>" | null,
              "periods": [
                {"totalChargedInKWh": 12.5, "sessions": [
                   {"startAt": "...", "chargedInKWh": 12.5,
                    "durationInMinutes": 45, "currentType": "AC"|"DC"},
                   ...
                ]},
                ...
              ]
            }

        Best-effort: 404 / 403 on accounts without the cap → exception
        in caller's gather. Returns ``{}`` for non-dict responses.
        """
        url = f"{_BASE}/api/v1/charging/{vin}/history"
        data = await self._get(
            url, params={"userTimezone": "UTC", "limit": limit}
        )
        return data if isinstance(data, dict) else {}

    async def get_capabilities(self, vin: str) -> dict[str, Any]:
        """Return mysmob capabilities document for *vin*.

        v1.13.0 (#56 Phase 3 prerequisite) — Skoda mysmob capabilities
        endpoint. Required so Capability-Filter Phase 3 can hide
        unsupported entities for Skoda vehicles (without this, the
        coordinator's ``vehicle_supports_capability`` returns ``None``
        for every Skoda capability and Phase 3 falls through to the
        Phase 2 post-failure-unavailable fallback).

        Endpoint: ``GET /api/v1/vehicle-access/{vin}/capabilities``
        Schema (mysmob — different from CARIAD-BFF):
            {
              "capabilities": [
                {"id": "<cap_id>", "active": true|false,
                 "editable"?, "user-enabled"?, "status"?,
                 "license-issue"?, "parameters"?}
              ]
            }
        Verified via Issue #56 body + RESEARCH_NOTES_2026-04-29 §3
        Skoda capability section.

        Failure raises APIError (caller swallows — capabilities are
        best-effort metadata, never load-bearing). The default cache
        TTL (24h via coordinator) keeps this cheap.
        """
        data = await self._get(
            f"{_BASE}/api/v1/vehicle-access/{vin}/capabilities",
        )
        return data if isinstance(data, dict) else {}

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
            # v1.15.0 — software-version + update-status (myskoda PR #541,
            # requires Skoda app v8.10.0+). Best-effort: 404 on older
            # firmware, 403 on accounts without the cap — both turn into
            # exceptions in ``return_exceptions=True`` and we skip below.
            self._get(
                f"{_BASE}/api/v1/vehicle-information/{vin}/software-version/update-status"
            ),
            return_exceptions=True,
        )
        (
            status, charging, ac, parking, driving_range,
            maintenance, readiness, sw_update,
        ) = results

        # v1.9.0 — Vehicle Data Scout opt-in. Stash raw responses keyed by
        # the same endpoint names used in ``EXPECTED_KEYS["skoda"]`` so the
        # coordinator can run drift detection without parsing twice.
        # Exceptions are skipped — only successful dict responses are stashed.
        self.last_raw_responses = {}
        for name, payload in (
            ("vehicle-status", status),
            ("charging", charging),
            ("air-conditioning", ac),
            ("parking", parking),
            ("driving-range", driving_range),
            ("maintenance", maintenance),
            ("readiness", readiness),
            # v1.15.0 — register the new endpoint so Vehicle Data Scout
            # detects new fields once a 2026+ Skoda surfaces them.
            ("software-version-update-status", sw_update),
        ):
            if isinstance(payload, dict):
                self.last_raw_responses[name] = payload

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
                # v1.10.1 (#58) — safe_int instead of bare int(). New
                # firmwares occasionally ship the field as a stringified
                # decimal ("12.5") which crashed pre-1.10.1 with
                # ValueError and took the entire vehicle's poll down.
                remaining = safe_int(v(c, "remainingTimeToFullyChargedInMinutes"))
                if remaining:
                    d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=remaining)
            d.has_battery = d.battery_soc is not None

            settings = charging.get("settings", {})
            d.target_soc = v(settings, "targetStateOfChargeInPercent")
            d.auto_unlock_charge = v(settings, "autoUnlockPlugWhenChargedAC") == "ON"

        # ── Air conditioning (also has plug state!) ──────────────────────────
        if isinstance(ac, dict):
            d.climatisation_state = v(ac, "state")
            d.climatisation_active = d.climatisation_state not in (None, "OFF", "INVALID")
            # v1.10.1 (#58) — safe_float. Skoda firmwares have shipped
            # ``"21,5"`` (locale-comma) on EU accounts at least once.
            d.target_temperature = safe_float(
                v(ac, "targetTemperature", "temperatureValue")
            )

            wh = v(ac, "windowHeatingState") or {}
            d.window_heating_front = v(wh, "front") == "ON"
            d.window_heating_back = v(wh, "rear") == "ON"

            # v1.17.7 (#129 rocksandclouds + #130 Chr1sDub + #133
            # christianmhz — three converging Skoda Scout-Reports
            # 2026-05-03/04). Skoda mysmob now exposes the outside
            # temperature on the air-conditioning endpoint, mirroring
            # what VW EU + SEAT/CUPRA already provided. Native Celsius
            # value (no Kelvin conversion needed). Stale-detection via
            # carCapturedTimestamp is left to the existing connection-
            # state pipeline. ``safe_float`` handles locale-comma
            # variants (Skoda firmwares have shipped "21,5" once).
            outside_t = v(ac, "outsideTemperature", "temperatureValue")
            if outside_t is not None:
                # Backend always sends Celsius for Skoda (verified across
                # 3 user reports), but defensively check unit anyway.
                unit = v(ac, "outsideTemperature", "temperatureUnit")
                ot_val = safe_float(outside_t)
                if ot_val is not None:
                    if unit == "FAHRENHEIT":
                        ot_val = round((ot_val - 32) * 5 / 9, 1)
                    d.outside_temp = ot_val

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
            # v1.10.0 (#94) — Skoda mysmob exposes the same per-engine
            # split as the CARIAD BFF, just under different keys:
            #   electricRange.distanceInKm
            #   combustionRange.distanceInKm  (was previously read as the
            #     scalar ``combustionRange`` only — wrong on Kodiaq iV)
            #   totalRangeInKm
            # Each is its own entity now; ``range_km`` keeps its old
            # "headline" semantics (electric for EV/PHEV, total for ICE).
            electric = v(driving_range, "electricRange", "distanceInKm")
            total = v(driving_range, "totalRangeInKm")
            combustion = v(driving_range, "combustionRange", "distanceInKm")
            if combustion is None:
                # Older firmwares published a flat scalar without the
                # ``distanceInKm`` wrapper — keep that path as a fallback.
                flat_combustion = v(driving_range, "combustionRange")
                if isinstance(flat_combustion, (int, float)):
                    combustion = flat_combustion
            try:
                if electric is not None:
                    d.electric_range_km = int(electric)
            except (TypeError, ValueError):
                pass
            try:
                if combustion is not None:
                    d.combustion_range_km = int(combustion)
            except (TypeError, ValueError):
                pass
            try:
                if total is not None:
                    d.total_range_km = int(total)
            except (TypeError, ValueError):
                pass
            d.has_combustion = combustion is not None
            # Headline number priority: electric for EV/PHEV, then total,
            # then combustion. Matches VW EU/Audi semantics from vw_eu.py.
            if d.has_battery and d.electric_range_km is not None:
                d.range_km = d.electric_range_km
            elif d.total_range_km is not None:
                d.range_km = d.total_range_km
            elif d.combustion_range_km is not None:
                d.range_km = d.combustion_range_km
            else:
                d.range_km = electric or total
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
            # v1.11.0 (#91 closure) — explicit raw int day-counts
            # alongside the existing DATE-converted sensors.
            d.service_due_in_days = safe_int(d.service_due_at)
            d.oil_service_due_in_days = safe_int(d.oil_service_at)
            # v1.17.7 (#130 Chr1sDub + #133 christianmhz, 2026-05-04) —
            # Skoda mysmob now exposes the user's preferred-workshop
            # registration on the maintenance endpoint. Surfaced as
            # extra_state_attributes on the ``service_due_in_days``
            # sensor (sensor.py) so users see the workshop name +
            # contact data alongside the next-service countdown.
            #
            # We pass the raw dict through verbatim — backend ships
            # nested contact/address/location/openingHours blocks
            # whose exact keys vary (DE vs CH vs AT vehicles see
            # different address shapes). HA's recorder is fine with
            # nested attrs as long as the total serialised size fits;
            # for CIS-region accounts the openingHours array can be
            # large so we drop it (rarely actionable in HA UI).
            workshop = v(maintenance, "preferredServicePartner")
            if isinstance(workshop, dict) and workshop:
                # Shallow copy + drop openingHours to keep attrs lean
                # in the HA state machine. Users who need full hours
                # can read the diagnostics export.
                trimmed = {
                    k: val for k, val in workshop.items()
                    if k != "openingHours"
                }
                d.preferred_workshop = trimmed

        # ── Connection status ────────────────────────────────────────────────
        if isinstance(readiness, dict):
            unreachable = v(readiness, "unreachable")
            # When unreachable is unknown (None), assume reachable (True)
            # to avoid setting is_online to a falsy default.
            d.is_online = unreachable is None or unreachable is False
            d.is_driving = v(readiness, "inMotion") is True

        # ── carCapturedTimestamp → connection_state (v1.8.12 refactor) ────
        # v1.8.11 introduced this logic Skoda-only; v1.8.12 extracted the
        # algorithm into ``cariad/_util.compute_connection_state`` so VW EU,
        # Audi and CUPRA/SEAT can apply the same Pattern (Multi-Brand
        # Connection-State). The recursive timestamp walk in the helper
        # also handles VW EU CARIAD-BFF's deeper-nested structure
        # (``service.statusName.value.carCapturedTimestamp`` — verified
        # via robinostlund/volkswagencarnet issue #921 ID.4 2025
        # Live-Response).
        d.connection_state, d.last_seen_at = compute_connection_state(
            status, charging, ac, parking, driving_range, maintenance, readiness,
        )

        # ── v1.15.0 — Software-version + OTA update status (myskoda PR #541) ─
        # Endpoint shipped in Skoda app v8.10.0+ — older accounts return
        # 404 / 403 which surfaces as an exception in our gather(); we
        # leave the fields ``None`` in that case.
        if isinstance(sw_update, dict):
            sw_status = sw_update.get("status")
            if isinstance(sw_status, str):
                # Defensive enum tolerance for forward-compat with new
                # values (myskoda raises UnexpectedSoftwareUpdateStatusError
                # for unknown). We just pass through raw + derive a bool.
                d.software_update_status = sw_status
                d.ota_update_available = sw_status.upper() not in {
                    "NO_UPDATE_AVAILABLE", "UPDATE_SUCCESSFUL",
                }
            curr = sw_update.get("currentSoftwareVersion")
            if isinstance(curr, str):
                d.software_version = curr
            notes = sw_update.get("releaseNotesUrl")
            if isinstance(notes, str) and notes:
                d.ota_release_notes_url = notes

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
