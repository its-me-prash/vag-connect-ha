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

from .._util import compute_connection_state, safe_int
from ..exceptions import APIError, SpinError
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

    async def get_capabilities(self, vin: str) -> dict[str, Any]:
        """Return the OLA capabilities document for *vin*.

        The response shape is roughly:
            {"capabilities": [{"id": "honk-and-flash", "status": [...]}, ...]}

        Caller is responsible for caching (handled by the coordinator with a
        24h TTL). Failure raises ``APIError`` — caller should swallow it
        because capabilities are best-effort metadata, never load-bearing.
        """
        data = await self._get(f"{_BASE}/v1/vehicles/{vin}/capabilities")
        return data if isinstance(data, dict) else {}

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

        # v1.9.0 — Vehicle Data Scout opt-in. Endpoint names match
        # ``EXPECTED_KEYS["cupra"]`` (SEAT inherits the same table).
        self.last_raw_responses = {}
        for name, payload in (
            ("mycar", mycar),
            ("status", status),
            ("charging", charge_status),
            ("charging-info", charge_info),
            ("climatisation", climate),
        ):
            if isinstance(payload, dict):
                self.last_raw_responses[name] = payload

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
        # OLA `/v2/vehicles/{vin}/status` for SEAT/CUPRA returns a structured
        # tree, NOT the flat ``doorsOpenedCount`` shape that CARIAD BFF uses.
        # The real shape (verified against `WulfgarW/pycupra/vehicle.py` lines
        # ~3100–3325, the pycupra dashboard reads identical paths):
        #
        #   status:
        #     doors:
        #       frontLeft:  { locked: bool, open: bool }
        #       frontRight: { locked: bool, open: bool }
        #       rearLeft:   { locked: bool, open: bool }
        #       rearRight:  { locked: bool, open: bool }
        #     windows:
        #       frontLeft:  "closed" | "open"      # string state
        #       frontRight: "closed" | "open"
        #       rearLeft:   "closed" | "open"
        #       rearRight:  "closed" | "open"
        #       sunroof:    "closed" | "open"      # sometimes here, sometimes top-level
        #     trunk:   { open: bool, locked?: bool }
        #     hood:    { open: bool }              # newer firmware
        #     sunroof: "closed" | "open"           # legacy/alternative position
        #
        # Pre-v1.8.9 used CARIAD-BFF flat keys (``doorsOpenedCount``,
        # ``doorClosedLeftFront`` etc.) which do not exist on OLA — so for
        # CUPRA Born / Formentor / Tavascan the door, window, trunk, hood
        # and sunroof entities silently never populated. Fix verified via
        # pycupra source — the legacy-flat fallback below stays in place
        # for the rare model that sends the older shape.
        if isinstance(status, dict):
            access_s = v(status, "access") or status
            doors_obj = v(status, "doors") or {}
            windows_obj = v(status, "windows") or {}
            trunk_obj = v(status, "trunk") or {}
            hood_obj = v(status, "hood") or {}

            # Per-door (locked + open). Aggregate ``doors_open`` and
            # ``doors_locked`` are derived once we have the dict.
            door_individual: dict[str, bool] = {}
            for pos in ("frontLeft", "frontRight", "rearLeft", "rearRight"):
                door = v(doors_obj, pos) or {}
                if not door:
                    continue
                # ``open`` may be bool or "open"/"closed" string — normalise
                open_raw = door.get("open")
                if isinstance(open_raw, bool):
                    is_closed = not open_raw
                elif isinstance(open_raw, str):
                    is_closed = open_raw.lower() == "closed"
                else:
                    is_closed = None
                if is_closed is not None:
                    door_individual[pos] = is_closed
            if door_individual:
                d.doors_individual = door_individual
                d.doors_open = any(not closed for closed in door_individual.values())
                # ``doors_locked`` is True only when every position reports
                # locked=True. If any position doesn't report (None),
                # fall back to the access endpoint or stay False.
                locked_states = []
                for pos in ("frontLeft", "frontRight", "rearLeft", "rearRight"):
                    door = v(doors_obj, pos) or {}
                    locked = door.get("locked")
                    if locked is not None:
                        locked_states.append(bool(locked))
                if locked_states:
                    d.doors_locked = all(locked_states)

            # Per-window (string-state). New ``windows_individual`` dict
            # mirrors ``doors_individual`` so binary sensors can expose
            # one entity per window.
            window_individual: dict[str, bool] = {}
            for pos in ("frontLeft", "frontRight", "rearLeft", "rearRight"):
                wstate = v(windows_obj, pos)
                if isinstance(wstate, str):
                    window_individual[pos] = wstate.lower() == "closed"
                elif isinstance(wstate, bool):
                    # Some firmware returns bool. Convention: True == closed.
                    window_individual[pos] = wstate
            if window_individual:
                d.windows_individual = window_individual
                d.windows_open = any(not closed for closed in window_individual.values())

            # Trunk + hood — both as nested {open, locked}. Sunroof can be
            # at status.sunroof OR status.windows.sunroof (pycupra checks
            # both due to firmware variance).
            if trunk_obj:
                trunk_open = trunk_obj.get("open")
                if trunk_open is not None:
                    d.trunk_open = bool(trunk_open) if isinstance(trunk_open, bool) else trunk_open == "open"
                trunk_locked = trunk_obj.get("locked")
                if trunk_locked is not None:
                    d.trunk_locked = bool(trunk_locked)
            if hood_obj:
                hood_open = hood_obj.get("open")
                if hood_open is not None:
                    d.hood_open = bool(hood_open) if isinstance(hood_open, bool) else hood_open == "open"
            # Sunroof can be at three different positions depending on
            # firmware/model. Issue #5 (CC-seatcupra) confirms ``sunRoof``
            # (camelCase with capital R) as a top-level field on Seat Leon
            # KL — verified live. pycupra checks both ``sunroof`` and
            # ``windows.sunroof`` due to firmware variance. Accept all three.
            sunroof_state = (
                v(status, "sunRoof")                # CC-seatcupra #5 — verified
                or v(status, "sunroof")              # pycupra path
                or v(windows_obj, "sunroof")         # pycupra alternative
            )
            if isinstance(sunroof_state, str):
                d.sunroof_open = sunroof_state.lower() == "open"
            elif isinstance(sunroof_state, bool):
                d.sunroof_open = sunroof_state

            # Engine state — top-level field on OLA `/v2/vehicles/{vin}/status`.
            # CC-seatcupra issue #50 reports ``engine: 'on' | 'off'`` from
            # multiple users (Seat Leon KL, Cupra Born). When 'on' the car
            # is being driven; this is the only reliable signal for driving
            # state because the official ``vehicle.state`` field stays at
            # ``parked`` for many users (CC-seatcupra issue #18).
            engine_state = v(status, "engine")
            if isinstance(engine_state, str):
                d.is_driving = engine_state.lower() == "on"
                if d.is_driving:
                    d.vehicle_state = "DRIVING"

            # v1.10.2 (#53 Gerhard's Born Live-Dump 2026-04-30) — newer
            # OLA firmware ships flat top-level overall fields ALONGSIDE
            # the structured `doors`/`windows`/etc. tree. Use them as a
            # backstop when the structured tree didn't yield a value:
            #   status.locked        : true/false (overall door-locked)
            #   status.lights        : "off" / "on" (vehicle lights state)
            #   status.hood.locked   : "false"/"true" string
            top_locked = v(status, "locked")
            if isinstance(top_locked, bool) and not d.doors_locked:
                d.doors_locked = top_locked
            top_hood_locked = v(status, "hood", "locked")
            if isinstance(top_hood_locked, str) and d.hood_open is None:
                # hood.locked is the inverse of hood.open — only set if
                # we don't already have an explicit hood.open value.
                d.hood_open = top_hood_locked.lower() == "false"

            # ── Legacy CARIAD-BFF-style flat fallback ────────────────────
            # If the new structured paths produced nothing (older firmware,
            # corrupted response, or a future OLA API change) fall back to
            # the pre-v1.8.9 flat shape. Defensive only — should not fire
            # for any current SEAT/CUPRA model verified against pycupra.
            if not door_individual and not window_individual:
                d.doors_open = v(access_s, "doorsOpenedCount", default=0) > 0
                d.windows_open = v(access_s, "windowsOpenedCount", default=0) > 0
                if d.trunk_open is None:
                    d.trunk_open = v(access_s, "trunk") == "OPEN" or v(access_s, "trunkOpen") is True
                if d.trunk_locked is None:
                    d.trunk_locked = v(access_s, "trunkLocked") is True or v(access_s, "trunkStatus") == "LOCKED"
                if d.hood_open is None:
                    d.hood_open = v(access_s, "hood") == "OPEN" or v(access_s, "hoodOpen") is True
                if d.sunroof_open is None:
                    d.sunroof_open = v(access_s, "sunroof") == "OPEN" or v(access_s, "sunroofOpen") is True

                doors_legacy: dict[str, bool] = {}
                for key in ("doorClosedLeftFront", "doorClosedRightFront",
                            "doorClosedLeftBack", "doorClosedRightBack"):
                    val = v(access_s, key)
                    if val is not None:
                        door_id = (key.replace("doorClosed", "")
                                   .replace("LeftFront", "frontLeft")
                                   .replace("RightFront", "frontRight")
                                   .replace("LeftBack", "rearLeft")
                                   .replace("RightBack", "rearRight"))
                        # v1.8.10 hotfix: pre-v1.8.9 legacy code had
                        # ``doors_legacy[door_id] = not val`` which inverted
                        # the semantics — the field is named "doorClosed*"
                        # so ``True`` means the door IS closed, matching our
                        # ``doors_individual`` convention (True == closed).
                        # The accidental ``not val`` was caught by the v1.8.9
                        # regression test ``test_v189_status_legacy_flat_fallback_still_works``
                        # which failed in CI on the v1.8.9 PR (#82) but the
                        # PR was merged anyway because branch protection on
                        # required-checks isn't enabled.
                        doors_legacy[door_id] = bool(val)
                if doors_legacy:
                    d.doors_individual = doors_legacy

        # ── Charging status ──────────────────────────────────────────────────
        # OLA charging endpoint field-name variance. Path order is now
        # **real-world response first, legacy guesses last** (v1.8.9
        # methodology fix): the older paths in this file were inferred
        # from CARIAD-BFF / pycupra back when we had no live OLA dump.
        # Now that we have a verified live CUPRA Born response from
        # `tillsteinbach/CarConnectivity-connector-seatcupra` issue #109
        # (user "Rainer", 2026-03-27 — same OLA host, same brand),
        # those field names are known good and must be tried first so a
        # vehicle that returns BOTH shapes doesn't accidentally pick a
        # zero from a legacy field.
        #
        # /v1/vehicles/{vin}/charging — observed shapes:
        #   Real-world (Rainer #109 shape B):
        #     {"state": "notReadyForCharging", "chargedPowerInKw": 0.0,
        #      "remainingTimeInMinutes": 0, "type": "invalid", "mode": "manual"}
        #   Real-world (Rainer #109 shape A — same endpoint, alt firmware):
        #     {"status": "NotReadyForCharging", "currentPct": 43,
        #      "remainingTime": 0, "chargeMode": "manual",
        #      "preferredChargeMode": "manual", "active": false}
        #   Legacy (pre-v1.8.9 inferred, kept as defensive fallback):
        #     {"chargingState": ..., "chargePowerInKw": ...,
        #      "remainingTimeToFullyChargedInMinutes": ..., "chargeType": ...}
        if isinstance(charge_status, dict):
            bat = v(charge_status, "battery") or charge_status
            if d.battery_soc is None:
                # v1.10.2 (#53 — Gerhard's Born Live-Dump 2026-04-30):
                # newer OLA firmware ships ``battery.currentSocPercentage``
                # (camelCase, no underscores). Ranks first because Born
                # users on 2026+ firmware would otherwise see no SoC at
                # all — Rainer's #109 dump (used as v1.8.9 reference)
                # was already on a firmware that's been superseded.
                d.battery_soc = (
                    v(bat, "currentSocPercentage")        # Born 2026 firmware (#53)
                    or v(charge_status, "currentPct")  # Rainer #109 shape A — verified
                    or v(bat, "stateOfChargeInPercent")
                    or v(bat, "currentSOC_pct")
                )
                d.has_battery = d.battery_soc is not None

            # v1.10.2 (#53 Gerhard) — ``battery.estimatedRangeInKm`` is the
            # new short field. Only sets ``range_km`` if not already set
            # by the dedicated ranges endpoint (which we prefer when
            # available since it splits electric vs. combustion).
            if d.range_km is None:
                est_range = v(bat, "estimatedRangeInKm")
                est_int = safe_int(est_range)
                if est_int is not None:
                    d.range_km = est_int
                    if d.electric_range_km is None:
                        d.electric_range_km = est_int

            chg = v(charge_status, "charging") or charge_status
            d.charging_state = (
                v(chg, "state")             # Rainer #109 shape B — verified
                or v(chg, "status")         # Rainer #109 shape A — verified
                or v(chg, "chargingState")  # Legacy — inferred pre-v1.8.9
            )
            # Charging-state values are camelCase or PascalCase depending on
            # firmware; treat case-insensitively. v1.10.2 (#53 Gerhard):
            # newer Born firmware ships purely lowercase camelCase like
            # ``"notReadyForCharging"``, ``"readyForCharging"``,
            # ``"charging"`` — the case-insensitive comparison already
            # covers it but we explicitly document the lowercase pattern.
            d.is_charging = (
                isinstance(d.charging_state, str)
                and d.charging_state.lower() == "charging"
            )
            d.charging_power_kw = (
                v(chg, "chargedPowerInKw")  # Rainer #109 shape B — verified
                or v(chg, "chargePowerInKw")  # Legacy
                or v(chg, "chargePower_kW")   # Legacy
            )
            d.charging_rate_kmh = v(chg, "chargeRateInKmPerHour") or v(chg, "chargeRate_kmph")
            remaining = (
                v(chg, "remainingTimeInMinutes")  # Rainer #109 shape B — verified
                or v(chg, "remainingTime")        # Rainer #109 shape A — verified
                or v(chg, "remainingTimeToFullyChargedInMinutes")  # Legacy
                or v(chg, "remainingChargingTime")                  # Legacy
            )
            # v1.10.1 (#58) — safe_int. Multiple OLA firmwares ship the
            # remaining-time field as a stringified decimal occasionally;
            # bare int() crashed the entire status parse pre-1.10.1.
            remaining_int = safe_int(remaining)
            if remaining_int:
                d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=remaining_int)
            d.charging_type = (
                v(chg, "type")          # Rainer #109 shape B — verified
                or v(chg, "chargeType")  # Legacy
                or v(chg, "chargingType")  # Legacy
            )

            plug = v(charge_status, "plug") or {}
            # v1.10.2 (#53 Gerhard's Born Live-Dump) — newer OLA firmware
            # uses short field names ``plug.connection`` and ``plug.lock``
            # plus lowercase enum values ("connected"/"disconnected",
            # "locked"/"unlocked"). The previous parser only knew
            # ``plug.connectionState=="CONNECTED"`` shape — Born owners
            # on 2026 firmware saw plug_connected=False even with cable
            # plugged in. Read all three field-name variants and compare
            # case-insensitively against both casings.
            plug_state_raw = (
                v(plug, "connection")          # Born 2026 firmware (#53)
                or v(plug, "connectionState")     # Rainer #109 shape
                or v(plug, "plugConnectionState")  # Legacy CARIAD
            )
            d.plug_state = plug_state_raw
            d.plug_connected = (
                isinstance(plug_state_raw, str)
                and plug_state_raw.lower() == "connected"
            )
            plug_lock_raw = (
                v(plug, "lock")                # Born 2026 firmware (#53)
                or v(plug, "lockState")           # Rainer #109 shape
                or v(plug, "plugLockState")        # Legacy CARIAD
            )
            d.connector_locked = (
                isinstance(plug_lock_raw, str)
                and plug_lock_raw.lower() == "locked"
            ) or v(plug, "externalPower") == "READY"

        # ── Charging info (settings) ─────────────────────────────────────────
        # OLA `/v2/vehicles/{vin}/charging/settings` field variance.
        # Real-world (Rainer #109): {"targetSoc_pct": 80, "maxChargeCurrentAC":
        # "maximum", "autoUnlockPlugWhenCharged": "off" | "on" | "permanent"}.
        # The "permanent" value is documented in issue #51 and means the
        # connector unlocks at any SoC, not just at full charge — so
        # ``auto_unlock_charge`` is True for both "on" and "permanent".
        if isinstance(charge_info, dict):
            d.target_soc = (
                v(charge_info, "targetSoc_pct")  # Rainer #109 — verified
                or v(charge_info, "targetSOC_pct")          # Legacy uppercase
                or v(charge_info, "targetStateOfChargeInPercent")  # Legacy verbose
            )
            d.max_charge_current = v(charge_info, "maxChargeCurrentAC") or v(charge_info, "maxChargeCurrent")
            auto_raw = v(charge_info, "autoUnlockPlugWhenCharged")
            auto_str = auto_raw.lower() if isinstance(auto_raw, str) else None
            d.auto_unlock_charge = (
                # #51: "permanent" is also "yes, unlock". Only "off"/None means no.
                auto_str in ("on", "permanent")
                or v(charge_info, "autoUnlockPlugWhenChargedAC") is True
            )

        # ── Climate ──────────────────────────────────────────────────────────
        # CC-seatcupra issue #21 + #8 documented that ``climatisationTrigger``
        # can return ``"unsupported"`` on older Born firmware; pre-v1.8.9
        # treated this state as if the climate was off (since it didn't
        # match "off"/"on" exactly), which still happened to be correct,
        # but a bool ``is_climate_supported`` would let entity platforms
        # hide controls cleanly. For v1.8.9 we keep ``climatisation_active``
        # behaviour stable and just ensure ``"off"``, ``"OFF"``,
        # ``"unsupported"``, and any ``None`` all evaluate to False.
        if isinstance(climate, dict):
            cs = v(climate, "status") or climate
            d.climatisation_state = v(cs, "climatisationState") or v(cs, "state")
            _inactive_states = (None, "OFF", "off", "Off", "unsupported")
            d.climatisation_active = d.climatisation_state not in _inactive_states
            d.target_temperature = v(climate, "settings", "targetTemperature_K")
            if d.target_temperature:
                d.target_temperature = round(float(d.target_temperature) - 273.15, 1)
            if not d.target_temperature:
                # `targetTemperatureCelsius` (no "In") is the Rainer #109
                # Live-response variant; `targetTemperatureInCelsius` is the
                # newer settings-endpoint variant. Try both.
                d.target_temperature = (
                    v(climate, "settings", "targetTemperatureInCelsius")
                    or v(cs, "targetTemperatureCelsius")  # Rainer #109
                )
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

        # ── carCapturedTimestamp → connection_state (v1.8.12 Multi-Brand) ────
        # OLA backend returns ``carCapturedTimestamp`` on multiple
        # sub-responses (verified live in
        # `tillsteinbach/CarConnectivity-connector-seatcupra` issue #109,
        # Rainer's CUPRA Born 2026-03-27 dump shows it on
        # ``climatisationStatus`` and ``chargingSettings``).
        # Same Pattern as Škoda + VW EU; helper handles nested paths and
        # both string + datetime values.
        d.connection_state, d.last_seen_at = compute_connection_state(
            mycar, parking, ranges, status, charge_status, charge_info,
            climate, maintenance, availability,
        )

        return d

    # ── Commands ─────────────────────────────────────────────────────────────

    async def _get_sec_token(self, spin: str) -> str:
        """Verify the S-PIN against OLA and return a SecToken.

        SEAT/CUPRA lock/unlock both require a per-call SecToken obtained
        from a separate `spin/verify` POST. Pycupra does this verbatim:
        POST `/v2/users/{userId}/spin/verify` with ``{"spin": "<pin>"}``,
        read ``securityToken`` from the response, then send that as the
        ``SecToken`` header on the actual lock/unlock POST.

        The S-PIN is passed plain — there's no client-side hashing,
        challenge/response or RSA. The OLA backend handles verification.
        """
        if not spin:
            raise SpinError("S-PIN required for SEAT/CUPRA lock/unlock.")
        if not self._user_id:
            await self._fetch_user_id()
        url = f"{_BASE}/v2/users/{self._user_id}/spin/verify"
        try:
            resp = await self._post(url, json={"spin": spin})
        except APIError as err:
            # 400/401 from /spin/verify means the PIN is wrong or the
            # account is locked. Surface a SpinError so HA can show the
            # right reauth/correct-pin prompt instead of a raw API error.
            raise SpinError(
                f"S-PIN verification failed (HTTP {getattr(err, 'status', '?')}). "
                "Update the S-PIN in the integration options."
            ) from err
        token = (resp or {}).get("securityToken") if isinstance(resp, dict) else None
        if not token:
            raise SpinError("S-PIN verify returned no securityToken.")
        return str(token)

    async def command_lock(self, vin: str) -> None:
        """Lock the vehicle. Requires a verified S-PIN SecToken."""
        token = await self._get_sec_token(self._spin)
        # Empty body is intentional — pycupra/OLA expect no payload here,
        # only the SecToken header. _request adds the Authorization +
        # Content-Type headers automatically.
        await self._post(
            f"{_BASE}/v1/vehicles/{vin}/access/lock",
            headers={"SecToken": token},
        )

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        """Unlock the vehicle. Requires a verified S-PIN SecToken."""
        token = await self._get_sec_token(spin or self._spin)
        await self._post(
            f"{_BASE}/v1/vehicles/{vin}/access/unlock",
            headers={"SecToken": token},
        )

    async def command_start_climate(self, vin: str) -> None:
        """v1.16.1 (#53 Gerhard CUPRA Born) — Fix 404 climatisation.

        OLA returns ``404 No static resource v2/vehicles/{vin}/climati``
        when posting ``{"action": "start"}`` to the bare endpoint. The
        action lives in the URL path, not the body — verified against
        ``WulfgarW/pycupra/connection.py`` (``API_CLIMATER + '/start'``).

        Defensive: try the verified ``/start`` path first; on 404 fall
        back to the legacy bare endpoint with body action so any account
        that the legacy URL DID work for is not broken.
        """
        await self._post_climatisation_action(vin, "start")

    async def command_stop_climate(self, vin: str) -> None:
        """v1.16.1 (#53) — same fix as start."""
        await self._post_climatisation_action(vin, "stop")

    async def _post_climatisation_action(self, vin: str, action: str) -> None:
        """v1.16.1 (#53) — climatisation start/stop with v1/v2 fallback.

        Primary path follows pycupra (verified working in production):
        ``POST /v2/vehicles/{vin}/climatisation/{start|stop}`` with empty
        body. Fallback to legacy ``POST /v2/vehicles/{vin}/climatisation``
        with ``{"action": ...}`` body if the primary returns 404 (in case
        any user's account / firmware was actually using the legacy
        pattern — same defensive approach as our CARIAD-BFF v1/v2
        fallback in ``vw_eu.py``).
        """
        from ..exceptions import APIError  # noqa: PLC0415

        primary = f"{_BASE}/v2/vehicles/{vin}/climatisation/{action}"
        try:
            await self._post(primary, json={})
            return
        except APIError as err:
            if err.status != 404:
                raise
            _LOGGER.debug(
                "OLA climatisation %s 404 on /climatisation/%s — "
                "falling back to legacy /climatisation+body for %s",
                action,
                action,
                vin[-6:],
            )
        # Fallback to the historical pattern with action in body.
        await self._post(
            f"{_BASE}/v2/vehicles/{vin}/climatisation",
            json={"action": action},
        )

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

        ⚠️ **[Inference] — semantic interpretation NOT verified against
        official My SEAT / My CUPRA app traffic.**

        We send the **vehicle's** last-known position rather than the
        user's phone GPS, because:

        - **Verified**: pycupra `vehicle.set_honkandflash` reads
          `findCarResponse.lat/lon` (vehicle position).
        - **Verified**: myskoda equivalent sends `PositionType.VEHICLE`.
        - **NOT verified**: whether the official My SEAT/CUPRA mobile
          apps populate the field from phone GPS or from the cached
          last-known vehicle position. We have NOT captured app traffic
          to confirm.

        Pragmatically the OLA endpoint accepts vehicle coordinates
        (verified live across multiple users on #53). The field name
        ``userPosition`` is likely a misnomer in the OLA contract — it
        appears to act as a server-side sanity token bound to *some*
        recent location. If a future capture of My SEAT/CUPRA app
        traffic shows it actually wants phone GPS, this needs revisiting.

        Status: **WORKING** for OLA endpoint, **INFERENCE** for
        semantic mapping to the official apps.
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
