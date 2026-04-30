# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Volkswagen EU API client — emea.bff.cariad.digital."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from .._util import compute_connection_state, safe_float, safe_int
from ..exceptions import APIError
from ..models import BRAND_VW_EU, VehicleData
from .base import CariadBaseClient

_LOGGER = logging.getLogger(__name__)

_BASE = "https://emea.bff.cariad.digital"

_SELECTIVE_STATUS_JOBS = ",".join([
    "access",
    "automation",
    "batteryChargingCare",
    "charging",
    "climatisation",
    "climatisationTimers",
    "departureProfiles",
    "departureTimers",
    "fuelStatus",
    "measurements",
    "readiness",
    "userCapabilities",
    "vehicleLights",
    "vehicleHealthInspection",
    "vehicleHealthWarnings",
])


class VWEUClient(CariadBaseClient):
    """VW EU / WeConnect client — emea.bff.cariad.digital.

    Also serves as base for AudiClient (same endpoints, extra auth).
    Data paths documented in docs/research/VAG_GROUP_ECOSYSTEM.md.
    """

    def __init__(self, session: Any, email: str, password: str, spin: str = "") -> None:
        super().__init__(session, BRAND_VW_EU, email, password, spin)

    async def get_vehicles(self) -> list[str]:
        """Return list of VINs from the CARIAD garage."""
        data = await self._get(f"{_BASE}/vehicle/v1/vehicles")
        vehicles: list[dict[str, Any]] = data.get("data", [])

        # Cache nickname/model per VIN — used in _parse_status to set device name
        # CARIAD returns: nickname (user-set in app), model, modelYear
        self._vehicle_metadata: dict[str, dict[str, Any]] = {
            v["vin"]: {
                "model": (
                    v.get("nickname")       # user-set name (e.g. "Golf GTE")
                    or v.get("vehicleNick")
                    or v.get("model")
                    or v.get("carModel")
                ),
                "model_year": v.get("modelYear") or v.get("model_year"),
            }
            for v in vehicles if v.get("vin")
        }
        # Filter unsupported platforms — prevents repeated 400 errors for legacy/PPC vehicles
        # enrollmentStatus: GDC_MISSING = vehicle not enrolled in digital services
        # devicePlatform: UNKNOWN = platform not supported by CARIAD BFF
        _UNSUPPORTED_ENROLLMENT = {"GDC_MISSING", "UNKNOWN", "NOT_ENROLLED"}
        _UNSUPPORTED_PLATFORM   = {"UNKNOWN"}

        supported: list[dict] = []
        skipped:   list[str]  = []
        for v in vehicles:
            vin = v.get("vin")
            if not vin:
                continue
            enrollment = v.get("enrollmentStatus", "")
            platform   = v.get("devicePlatform", "")
            if enrollment in _UNSUPPORTED_ENROLLMENT or platform in _UNSUPPORTED_PLATFORM:
                skipped.append(f"{vin[-6:]} [{enrollment}/{platform}]")
            else:
                supported.append(v)

        if skipped:
            _LOGGER.info(
                "VAG: skipping %d vehicle(s) with unsupported platform: %s",
                len(skipped), ", ".join(skipped),
            )

        vins = [v["vin"] for v in supported if v.get("vin")]
        if vehicles:
            _LOGGER.debug(
                "VAG vehicles raw fields (first car): %s",
                {k: str(v)[:40] for k, v in vehicles[0].items()
                 if k not in ("vin",)},
            )
        _LOGGER.debug(
            "Found %d vehicle(s): %s",
            len(vins),
            {k: m["model"] for k, m in self._vehicle_metadata.items()},
        )

        # Fetch render images via shared base method (best-effort)
        await self.fetch_images()

        return vins

    async def get_capabilities(self, vin: str) -> dict[str, Any]:
        """Return CARIAD BFF capabilities document for *vin*.

        Endpoint identical for VW EU + Audi (same backend, different brand
        token). The JSON shape is roughly:
            {"capabilities": [{"id": "honkAndFlash", "status": [...]}, ...]}

        Failure raises ``APIError`` — caller should swallow it because
        capabilities are best-effort metadata, never load-bearing.
        """
        data = await self._get(f"{_BASE}/vehicle/v1/vehicles/{vin}/capabilities")
        return data if isinstance(data, dict) else {}

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full vehicle status via selectivestatus."""
        url = f"{_BASE}/vehicle/v1/vehicles/{vin}/selectivestatus"
        raw: dict[str, Any] = await self._get(url, params={"jobs": _SELECTIVE_STATUS_JOBS})

        # Parking position (separate endpoint)
        parking: dict[str, Any] = {}
        try:
            parking = await self._get(f"{_BASE}/vehicle/v1/vehicles/{vin}/parkingposition")
        except Exception:  # noqa: BLE001
            pass

        d = self._parse_status(vin, raw, parking)

        # v1.9.0 — Vehicle Data Scout opt-in. Endpoint names match
        # ``EXPECTED_KEYS["volkswagen"]`` (Audi inherits the table via
        # AudiClient(VWEUClient) — same backend, same shape).
        self.last_raw_responses = {}
        if isinstance(raw, dict):
            self.last_raw_responses["selectivestatus"] = raw
        if isinstance(parking, dict):
            self.last_raw_responses["parkingposition"] = parking

        # ── carCapturedTimestamp → connection_state (v1.8.12 Multi-Brand) ────
        # CARIAD-BFF returns ``carCapturedTimestamp`` on the .value of every
        # status sub-object — confirmed live in
        # `robinostlund/volkswagencarnet` issue #921 (ID.4 2025 dump):
        #   access.accessStatus.value.carCapturedTimestamp
        #   charging.chargingStatus.value.carCapturedTimestamp
        #   charging.batteryStatus.value.carCapturedTimestamp
        #   climatisation.climatisationStatus.value.carCapturedTimestamp
        #   measurements.{range,odometer,fuelLevel}Status.value.carCapturedTimestamp
        #   parkingposition.carCapturedTimestamp (separate endpoint)
        # The recursive walk in compute_connection_state() handles the
        # nested .value.carCapturedTimestamp paths without per-brand
        # configuration. AudiClient inherits this since it uses the same
        # selectivestatus endpoint via VWEUClient.
        d.connection_state, d.last_seen_at = compute_connection_state(raw, parking)

        return d

    async def command_lock(self, vin: str, spin: str = "") -> None:
        """Lock vehicle — combined endpoint with separate-endpoint fallback,
        each tried on both /vehicle/v1/ and /vehicle/v2/ paths.

        v1.8.8 (Session 3B): HTTP-404-only fallback via
        ``_post_command_with_fallback_paths``. Auth failures, rate limits
        and 5xx errors propagate so ``classify_command_failure`` handles them.

        v1.9.1 (#92, Audi S6 C8 2021): the CARIAD BFF returns
        ``403 spin_error`` for **lock too** on premium Audi models when no
        S-PIN is sent (same behaviour the unlock path had). The S-PIN, when
        configured, is now included in the lock-unlock payload exactly the
        same way as ``command_unlock``. When the user has no S-PIN
        configured the call still proceeds and may legitimately succeed
        on older / non-premium models that don't enforce the S-PIN
        requirement on lock.
        """
        primary_payload: dict[str, Any] = {"action": "lock"}
        fallback_payload: dict[str, Any] = {}
        if spin or self._spin:
            primary_payload["spin"] = spin or self._spin
            fallback_payload["spin"] = spin or self._spin
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="access/lock-unlock",
            primary_payload=primary_payload,
            fallback_suffix="access/lock",
            fallback_payload=fallback_payload,
        )

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        """Unlock vehicle — S-PIN required if set.

        Same v1/v2 + combined/separate dispatch as ``command_lock``.
        S-PIN, when present, is included in *both* the combined-endpoint
        payload and the separate-endpoint fallback payload (the legacy
        unlock endpoint accepts the PIN in the body, the same way the
        SecToken-using SEAT/CUPRA flow does in v1.8.4).
        """
        primary_payload: dict[str, Any] = {"action": "unlock"}
        fallback_payload: dict[str, Any] = {}
        if spin or self._spin:
            primary_payload["spin"] = spin or self._spin
            fallback_payload["spin"] = spin or self._spin
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="access/lock-unlock",
            primary_payload=primary_payload,
            fallback_suffix="access/unlock",
            fallback_payload=fallback_payload,
        )

    async def command_start_climate(self, vin: str) -> None:
        """Start pre-conditioning — combined endpoint with separate fallback,
        each on v1/v2.

        Default target temperature 21°C and window heating enabled match
        the previous separate-endpoint payload — kept so behaviour does
        not regress when the combined endpoint isn't available.
        """
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="climatisation/start-stop",
            primary_payload={"action": "start"},
            fallback_suffix="climatisation/start",
            fallback_payload={
                "targetTemperature": 21.0,
                "targetTemperatureUnit": "celsius",
                "climatisationWithoutExternalPower": True,
                "windowHeatingEnabled": True,
            },
        )

    async def command_stop_climate(self, vin: str) -> None:
        """Stop pre-conditioning — combined endpoint with separate fallback."""
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="climatisation/start-stop",
            primary_payload={"action": "stop"},
            fallback_suffix="climatisation/stop",
            fallback_payload={},
        )

    async def command_start_charging(self, vin: str) -> None:
        """Start charging — combined endpoint with separate fallback."""
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="charging/start-stop",
            primary_payload={"action": "start"},
            fallback_suffix="charging/start",
            fallback_payload={},
        )

    async def command_stop_charging(self, vin: str) -> None:
        """Stop charging — combined endpoint with separate fallback."""
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="charging/start-stop",
            primary_payload={"action": "stop"},
            fallback_suffix="charging/stop",
            fallback_payload={},
        )

    async def command_flash(
        self,
        vin: str,
        latitude: float | None = None,  # noqa: ARG002
        longitude: float | None = None,  # noqa: ARG002
    ) -> None:
        """Honk and flash."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/vehicleLights/flash",
            json={"action": "flash"},
        )

    async def command_wake(self, vin: str) -> None:
        """Wake vehicle.

        v1.9.1 (#92, Audi S6 C8 2021): premium Audi models return ``404``
        on the legacy ``/vehicle/v1/vehicles/{vin}/vehicleWakeup`` path.
        Same v1 → v2 dispatch we use for every other command — the
        ``_post_command`` helper auto-falls-back to ``/vehicle/v2/...``
        on a 404 and remembers the result per VIN so subsequent calls
        skip the dead path.
        """
        await self._post_command(vin, "vehicleWakeup", json={})

    # ── v1/v2 endpoint dispatch (Session 3A — #51, #74) ─────────────────────
    #
    # Newer premium Audi models (RS e-tron GT, Q6 e-tron, A3 2024+ on PPC/PPE)
    # and recent VW EU models (Passat 2025 B9) reject the /vehicle/v1/...
    # command paths with HTTP 404. The same logical commands exist under
    # /vehicle/v2/...  We learn the right prefix per VIN on the first 404
    # and remember it for subsequent commands. Cache is per-client-instance
    # so a coordinator restart re-learns (one extra 404 per cold start, OK).

    def _supports_v2_paths(self, vin: str) -> bool:
        """Return True if the v2 command prefix is known to work for *vin*."""
        flags: dict[str, bool] = getattr(self, "_v2_command_paths", {}) or {}
        return bool(flags.get(vin, False))

    def _mark_v2_active(self, vin: str) -> None:
        """Remember that v2 worked for *vin* — skip v1 on subsequent calls."""
        if not hasattr(self, "_v2_command_paths"):
            self._v2_command_paths: dict[str, bool] = {}
        if not self._v2_command_paths.get(vin, False):
            _LOGGER.info(
                "CARIAD command profile: %s now using /vehicle/v2/ paths",
                vin[-6:] if vin else "***",
            )
            self._v2_command_paths[vin] = True

    async def _post_command(
        self, vin: str, path_suffix: str, **kwargs: Any
    ) -> Any:
        """POST to /vehicle/v1/vehicles/{vin}/{suffix} with v2 fallback on 404.

        First call per VIN: try v1, on 404 retry v2 and remember.
        Subsequent calls: skip v1 if v2 is known to work for this VIN.
        Other 4xx/5xx errors propagate as-is — this only handles the
        version-mismatch case.
        """
        if self._supports_v2_paths(vin):
            return await self._post(
                f"{_BASE}/vehicle/v2/vehicles/{vin}/{path_suffix}", **kwargs,
            )
        try:
            return await self._post(
                f"{_BASE}/vehicle/v1/vehicles/{vin}/{path_suffix}", **kwargs,
            )
        except APIError as err:
            if getattr(err, "status", 0) != 404:
                raise
            # v1 said the resource doesn't exist — try v2 once
            result = await self._post(
                f"{_BASE}/vehicle/v2/vehicles/{vin}/{path_suffix}", **kwargs,
            )
            self._mark_v2_active(vin)
            return result

    async def _post_command_with_fallback_paths(
        self,
        vin: str,
        primary_suffix: str,
        primary_payload: dict[str, Any],
        fallback_suffix: str,
        fallback_payload: dict[str, Any],
    ) -> Any:
        """POST a vehicle command with full v1/v2 + primary/fallback dispatch.

        Used by lock/unlock and climate/charging start/stop where the
        CARIAD BFF historically exposes both a combined endpoint
        (e.g. ``/access/lock-unlock`` with ``{"action": "lock"}``) and
        separate endpoints (e.g. ``/access/lock`` + ``/access/unlock``).

        Order of attempts (each via ``_post_command``, so each carries its
        own v1 → v2 fallback on 404):

        1. ``primary_suffix`` (combined endpoint, the historically
           preferred form on the older CARIAD BFF)
        2. ``fallback_suffix`` (separate endpoint, what older firmware
           and some current PPE/PPC vehicles still expect)

        The previous implementation caught a bare ``except Exception`` and
        always fell back, which masked auth failures, rate limits and
        backend 500s as if they were endpoint mismatches. v1.8.8 narrows
        the fallback trigger to HTTP 404 only — every other error
        propagates so the coordinator's
        ``classify_command_failure`` can see it.
        """
        try:
            return await self._post_command(
                vin, primary_suffix, json=primary_payload,
            )
        except APIError as err:
            if getattr(err, "status", 0) != 404:
                raise
            return await self._post_command(
                vin, fallback_suffix, json=fallback_payload,
            )

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        """Set charge target SoC. Tries v1 first, falls back to v2 on 404."""
        await self._post_command(
            vin, "charging/settings", json={"targetSOC_pct": target},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        """Set pre-conditioning temperature. v1 → v2 fallback on 404."""
        await self._post_command(
            vin, "climatisation/settings", json={"targetTemperature_C": temp_c},
        )

    async def command_set_charge_mode(self, vin: str, mode: str) -> None:
        """Set charging mode — MANUAL, TIMER, PREFERRED_CHARGING_TIMES.

        v1 → v2 fallback on 404.
        """
        await self._post_command(
            vin, "charging/settings", json={"chargeMode": mode.upper()},
        )

    async def command_set_min_soc(self, vin: str, min_soc: int) -> None:
        """Set minimum SoC for PHEV (0–100%). v1 → v2 fallback on 404."""
        await self._post_command(
            vin, "charging/settings", json={"minChargeLimit_pct": min_soc},
        )

    async def command_start_window_heating(self, vin: str) -> None:
        """Start window heating (front windscreen + rear window)."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/windowheating/start-stop",
            json={"action": "start"},
        )

    async def command_stop_window_heating(self, vin: str) -> None:
        """Stop window heating."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/windowheating/start-stop",
            json={"action": "stop"},
        )

    async def command_set_departure_timer(
        self,
        vin: str,
        timer_id: int,
        enabled: bool,
        departure_time: str | None,
    ) -> None:
        """Set a departure timer (1–3).

        Args:
            vin:            Vehicle VIN
            timer_id:       1, 2 or 3
            enabled:        True to enable, False to disable
            departure_time: "HH:MM" format, e.g. "07:30" (None = keep existing)
        """
        payload: dict[str, Any] = {"id": timer_id, "enabled": enabled}
        if departure_time:
            payload["departureTime"] = {"time": departure_time}
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/timers",
            json=payload,
        )

    # ── data parsing ───────────────────────────────────────────────────────────

    def _parse_status(
        self,
        vin: str,
        raw: dict[str, Any],
        parking: dict[str, Any],
    ) -> VehicleData:
        """Map raw selectivestatus JSON → VehicleData.

        Path documentation: docs/research/VAG_GROUP_ECOSYSTEM.md
        """
        v = self._val
        d = VehicleData(vin=vin)

        # ── Model name from vehicles list (nickname set in app) ────────────────
        meta = getattr(self, "_vehicle_metadata", {}).get(vin, {})
        if meta.get("model"):
            d.model = meta["model"]
        # v1.10.1 (#58) — safe_int. The model_year metadata sometimes
        # arrives as a 4-digit string and sometimes as int depending on
        # how the auth flow normalised the user profile JSON.
        d.model_year = safe_int(meta.get("model_year"), default=d.model_year)

        # ── Charging ──────────────────────────────────────────────────────────
        d.charging_state = v(raw, "charging", "chargingStatus", "value", "chargingState")
        d.is_charging = d.charging_state == "CHARGING"
        d.charging_power_kw = v(raw, "charging", "chargingStatus", "value", "chargePower_kW")
        d.charging_rate_kmh = v(raw, "charging", "chargingStatus", "value", "chargeRate_kmph")

        # v1.10.1 (#58) — safe_int. New CARIAD firmware shipped this as
        # a stringified decimal at least once — see myskoda #503.
        remaining_min = safe_int(
            v(raw, "charging", "chargingStatus", "value", "remainingChargingTimeToComplete_min")
        )
        if remaining_min is not None:
            d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=remaining_min)

        d.battery_soc = v(raw, "charging", "batteryStatus", "value", "currentSOC_pct")
        # v1.10.0 (#94) — ``range_km`` headline assignment moved to the
        # consolidated PHEV-range block further down. Reading the battery
        # range here would clobber the per-engine logic for hybrids where
        # the battery range and the engine block disagree.

        plug_state = v(raw, "charging", "plugStatus", "value", "plugConnectionState")
        d.plug_state = plug_state
        d.plug_connected = plug_state == "CONNECTED"
        d.connector_locked = v(raw, "charging", "plugStatus", "value", "plugLockState") == "LOCKED"

        d.target_soc = v(raw, "charging", "chargingSettings", "value", "targetSOC_pct")
        d.charge_mode = v(raw, "charging", "chargingStatus", "value", "chargeMode")
        d.min_soc = v(raw, "charging", "chargingSettings", "value", "minChargeLimit_pct")
        # v1.10.1 (#58) — safe_float for max charge current too. The
        # ``_A`` field is a clean integer in #90's Live-Dump (16) but the
        # legacy enum form was a string ("MAXIMUM"); this normalises.
        max_ac = safe_float(
            v(raw, "charging", "chargingSettings", "value", "maxChargeCurrentAC_A")
        )
        if max_ac is not None:
            d.max_charge_current = max_ac
        d.auto_unlock_charge = (
            v(raw, "charging", "chargingSettings", "value", "autoUnlockPlugWhenChargedAC") == "ON"
        )

        charging_type = v(raw, "charging", "chargingStatus", "value", "chargeType")
        d.charging_type = charging_type

        # ── Drivetrain detection ───────────────────────────────────────────────
        primary_engine = v(raw, "fuelStatus", "rangeStatus", "value", "primaryEngine", "type")
        secondary_engine = v(raw, "fuelStatus", "rangeStatus", "value", "secondaryEngine", "type")
        car_type = v(raw, "measurements", "fuelLevelStatus", "value", "carType")

        electric_types = {"electric", "ev"}
        combustion_types = {"gasoline", "diesel", "gas", "cng", "lpg"}

        if primary_engine:
            d.has_battery = primary_engine.lower() in electric_types
            d.has_combustion = primary_engine.lower() in combustion_types

        if secondary_engine:
            if secondary_engine.lower() in electric_types:
                d.has_battery = True
            if secondary_engine.lower() in combustion_types:
                d.has_combustion = True

        if car_type:
            lower = car_type.lower()
            if "electric" in lower:
                d.has_battery = True
            if any(x in lower for x in ("gasoline", "diesel", "gas")):
                d.has_combustion = True

        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        # ── Fuel / range ──────────────────────────────────────────────────────
        d.fuel_level = v(raw, "measurements", "fuelLevelStatus", "value", "currentFuelLevel_pct")

        # v1.10.0 (#94) — explicit per-energy-source range fields, plus
        # backward-compatible ``range_km``. Logic order matters:
        #
        # 1. Read the two CARIAD BFF engine blocks. Each carries its own
        #    ``type`` (electric/gasoline/diesel/...) plus its own
        #    ``remainingRange_km``. Older Audi diesels expose
        #    ``measurements.rangeStatus.value.dieselRange`` instead, so
        #    we fall through to that path when the engine blocks are empty.
        # 2. Map by *engine type* not by *position* — primary != electric
        #    forever. A Golf 7 GTE 2015 has primary=gasoline, secondary=
        #    electric in early firmware; modern PHEVs flip them around.
        # 3. ``total_range_km`` is its own field — only set when the API
        #    explicitly publishes it (PHEVs do, pure EVs don't).
        # 4. ``range_km`` (back-compat headline number) prefers electric
        #    for EV/PHEV, otherwise total, otherwise combustion.
        electric_types = {"electric", "ev"}
        combustion_types = {"gasoline", "petrol", "diesel", "gas", "cng", "lpg"}

        for engine_path in (
            ("fuelStatus", "rangeStatus", "value", "primaryEngine"),
            ("fuelStatus", "rangeStatus", "value", "secondaryEngine"),
        ):
            engine = v(raw, *engine_path)
            if not isinstance(engine, dict):
                continue
            engine_type = (engine.get("type") or "").lower()
            engine_range = engine.get("remainingRange_km")
            if engine_range is None:
                continue
            try:
                value = int(engine_range)
            except (TypeError, ValueError):
                continue
            if engine_type in electric_types:
                d.electric_range_km = value
            elif engine_type in combustion_types:
                d.combustion_range_km = value

        # Older Audi models (S6 TDI 2021, A6 e-tron, etc.) expose only the
        # combustion range under ``measurements.rangeStatus.value.dieselRange``
        # / ``gasolineRange`` — no ``fuelStatus.rangeStatus.value`` block.
        # Verified live on Audi S6 C8 2021 (#91).
        if d.combustion_range_km is None:
            for ms_field in ("dieselRange", "gasolineRange"):
                ms_val = v(raw, "measurements", "rangeStatus", "value", ms_field)
                if ms_val is None:
                    continue
                # CARIAD-BFF returns either a scalar km value OR a wrapped
                # ``{"distanceInKm": int}`` shape (the same dual-form shape
                # Skoda uses for its electricRange/combustionRange blocks).
                if isinstance(ms_val, dict):
                    ms_val = ms_val.get("distanceInKm")
                try:
                    d.combustion_range_km = int(ms_val) if ms_val is not None else None
                except (TypeError, ValueError):
                    pass

        # Total range — from explicit field if present.
        total_range = v(raw, "fuelStatus", "rangeStatus", "value", "totalRange_km")
        if total_range is not None:
            try:
                d.total_range_km = int(total_range)
            except (TypeError, ValueError):
                pass

        # Back-compat ``range_km`` headline. Preference order matches
        # users' intuitive expectation — EVs/PHEVs see battery range as
        # primary, ICE see combustion or total.
        battery_range = v(raw, "charging", "batteryStatus", "value", "cruisingRangeElectric_km")
        if d.electric_range_km is None and battery_range is not None:
            try:
                d.electric_range_km = int(battery_range)
            except (TypeError, ValueError):
                pass
        if d.has_battery and d.electric_range_km is not None:
            d.range_km = d.electric_range_km
        elif d.total_range_km is not None:
            d.range_km = d.total_range_km
        elif d.combustion_range_km is not None:
            d.range_km = d.combustion_range_km

        adblue = v(raw, "measurements", "rangeStatus", "value", "adBlueRange")
        if adblue is not None:
            d.adblue_range_km = int(adblue)

        # ── Measurements ──────────────────────────────────────────────────────
        d.odometer_km = v(raw, "measurements", "odometerStatus", "value", "odometer")
        d.outside_temp = v(raw, "measurements", "outsideTemperatureStatus", "value", "outsideTemperature_K")
        if d.outside_temp is not None:
            d.outside_temp = round(float(d.outside_temp) - 273.15, 1)  # Kelvin → Celsius

        bat_min = v(raw, "measurements", "temperatureBatteryStatus", "value", "temperatureHvBatteryMin_K")
        if bat_min is not None:
            d.battery_temp = round(float(bat_min) - 273.15, 1)

        # ── Access / doors / windows ──────────────────────────────────────────
        d.doors_locked = v(raw, "access", "accessStatus", "value", "doorLockStatus") == "LOCKED"
        overall = v(raw, "access", "accessStatus", "value", "overallStatus")
        d.doors_open = False
        d.windows_open = False
        if overall == "UNSAFE":
            doors: list[dict[str, Any]] = v(raw, "access", "accessStatus", "value", "doors") or []
            d.doors_open = any(
                door.get("status", [{}])[0].get("value") == "open"
                for door in doors
                if door.get("status")
            )
            windows: list[dict[str, Any]] = v(raw, "access", "accessStatus", "value", "windows") or []
            d.windows_open = any(
                w.get("status", [{}])[0].get("value") == "open"
                for w in windows
                if w.get("status")
            )
            # Per-door breakdown
            d.doors_individual = {
                door["name"]: door.get("status", [{}])[0].get("value") == "open"
                for door in doors
                if door.get("name") and door.get("status")
            }

        # ── Climatisation ─────────────────────────────────────────────────────
        d.climatisation_state = v(raw, "climatisation", "climatisationStatus", "value", "climatisationState")
        d.climatisation_active = d.climatisation_state not in (None, "OFF", "CLIMATISATION_STATUS_UNAVAILABLE")
        d.target_temperature = v(raw, "climatisation", "climatisationSettings", "value", "targetTemperature_C")

        wh_status = v(raw, "climatisation", "windowHeatingStatus", "value", "windowHeatingStatus") or []
        for wh in wh_status:
            location = wh.get("windowLocation", "")
            state = wh.get("windowHeatingState") == "ON"
            if "front" in location.lower():
                d.window_heating_front = state
            elif "rear" in location.lower() or "back" in location.lower():
                d.window_heating_back = state

        # ── Readiness / online ─────────────────────────────────────────────────
        d.is_online = v(raw, "readiness", "readinessStatus", "value", "connectionState", "isOnline") is True

        # ── Vehicle health / service ──────────────────────────────────────────
        # ── Warning lights ────────────────────────────────────────────────────
        warnings = v(raw, "vehicleHealthWarnings", "warningLights", "value") or []
        if isinstance(warnings, list):
            # Each warning: {warningType, iconId, text}
            warning_types = {w.get("warningType", "").upper() for w in warnings if w.get("warningType")}
            d.warning_oil     = "OIL" in warning_types or "OIL_LEVEL" in warning_types
            d.warning_engine  = "ENGINE" in warning_types or "CHECK_ENGINE" in warning_types
            d.warning_tyre    = any("TYR" in t or "TIRE" in t for t in warning_types)
            d.warning_brakes  = "BRAKE" in warning_types
            d.warning_count   = len(warnings)
            d.warning_active  = len(warnings) > 0

        d.service_km = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "inspectionDue_km")
        d.service_due_at = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "inspectionDue_days")
        d.oil_service_km = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "oilServiceDue_km")
        d.oil_service_at = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "oilServiceDue_days")

        # ── Departure timers ──────────────────────────────────────────────────
        timers: list[dict[str, Any]] = v(raw, "departureTimers", "departureTimersStatus", "value", "timers") or []
        for i, timer in enumerate(timers[:3], 1):
            enabled = timer.get("enabled", False)
            time_str = timer.get("departureTime", {}).get("time") if timer.get("departureTime") else None
            setattr(d, f"departure_timer_{i}_enabled", enabled)
            setattr(d, f"departure_timer_{i}_time", time_str)

        # ── Parking position ──────────────────────────────────────────────────
        if parking:
            d.latitude = parking.get("lat")
            d.longitude = parking.get("lon")

        return d
