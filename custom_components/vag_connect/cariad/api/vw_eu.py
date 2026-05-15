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
    # v1.12.0 (#23) — 12V starter battery status. Critical for older
    # vehicles with degrading 12V batteries that cause silent
    # API-no-response weeks before total failure. The CARIAD BFF
    # publishes voltage + warning state here.
    "lvBattery",
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

    async def get_trip_statistics(
        self, vin: str, kind: str = "shortTerm"
    ) -> dict[str, Any]:
        """v1.14.0 (#24) — Trip Stats from CARIAD-BFF.

        ``kind`` is ``"shortTerm"`` (per-ignition-cycle trips, "Seit Start")
        or ``"longTerm"`` (since-last-reset aggregates, "Seit Tanken /
        Gesamt"). Both return a list under ``tripDataList.tripData[]`` —
        callers sort by ``overallMileage`` descending and take ``[0]`` as
        the most recent trip (the audi #113 "aggregate-in-state"
        convention).

        Per-trip fields (verified across audi_connect_ha, audiconnectpy,
        davidgiga1993/AudiAPI, ioBroker/vw-connect):
        - ``timestamp`` (ISO 8601 UTC) — trip end time
        - ``mileage`` (km) — distance of this trip
        - ``startMileage`` / ``overallMileage`` (km) — odometer at start/end
        - ``traveltime`` (minutes)
        - ``averageSpeed`` (km/h)
        - ``averageFuelConsumption`` (l/100 km × 10 — divide by 10)
        - ``averageElectricEngineConsumption`` (kWh/100 km × 10)
        - ``averageAuxConsumerConsumption`` (kWh/100 km × 10, often missing)

        Returns the raw response dict so the coordinator can parse + cache.
        Returns an empty dict if the response is not a JSON object (defensive
        against backend edge-cases — best-effort, never raises into the
        polling loop).

        Subscription-required (Audi connect Plus / WeConnect Plus) — if
        the user lacks the entitlement the backend returns 403; the
        capability-filter Phase 3 (#56, v1.13.0) gates this from the
        platform side via ``cap_id_for(brand, "command_trip_stats")``.
        """
        url = f"{_BASE}/vehicle/v1/vehicles/{vin}/tripstatistics"
        data = await self._get(url, params={"type": kind})
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

        # v1.25.0 PR-G — MBB VSR Phase 2 read-side fallback (Golf 7 GTE
        # Tank-Level use case). Triggers when:
        #   1. Cariad-BFF returned no fuel_level (older PHEV firmware
        #      ships ``fuelStatus.rangeStatus = {error}`` with no
        #      ``currentFuelLevel_pct``)
        #   2. AND the VIN is known-MBB-backed via MBBBackendCache
        #      (was set by a previous wrapper-404 wake fallback in
        #      v1.21.0 Phase 1)
        # Then we GET the legacy MBB ``/fs-car/bs/vsr/v1/.../status``
        # endpoint and parse field IDs ``0x030103000A`` (tank %) +
        # ``0x0301030005`` (total range km). Defensive: any failure
        # leaves ``d.fuel_level`` at None — entity stays unknown.
        if d.fuel_level is None:
            try:
                await self._maybe_fill_from_mbb_vsr(vin, d)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug(
                    "MBB VSR fallback failed for %s — leaving fuel_level None: %s",
                    vin[-6:], type(err).__name__,
                )

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

    async def command_start_climate(
        self, vin: str, ppe_mode: bool = False
    ) -> None:
        """Start pre-conditioning — combined endpoint with separate fallback,
        each on v1/v2.

        Default target temperature 21°C and window heating enabled match
        the previous separate-endpoint payload — kept so behaviour does
        not regress when the combined endpoint isn't available.

        v1.14.0 (#29, audi #644 + #677) — when ``ppe_mode=True`` the
        fallback body uses the PPE/PPC shape:
        - ``climatisationMode: "comfort"`` (mandatory, NOT null)
        - ``targetTemperature`` + ``targetTemperatureUnit`` OMITTED
        Required for Q6 e-tron, A6 e-tron, RS e-tron GT Facelift, A3 2024+
        PHEV — all of which return ``400 Bad Request`` for the legacy
        body shape. Coordinator gates this via ``CONF_FORCE_PPE_CLIMATE``
        option (Audi-only, user-overridable since auto-detection is
        unreliable). ⚠️ [Inference] — body shape verified from upstream
        PRs but Audi never published a definitive PPE compatibility list.
        """
        if ppe_mode:
            fallback_payload = {
                "climatisationMode": "comfort",
                "climatisationWithoutExternalPower": True,
                "windowHeatingEnabled": True,
                # NOTE: targetTemperature* OMITTED for PPE — body validator
                # rejects it on Q6/A6 e-tron / PPC vehicles.
            }
        else:
            fallback_payload = {
                "targetTemperature": 21.0,
                "targetTemperatureUnit": "celsius",
                "climatisationWithoutExternalPower": True,
                "windowHeatingEnabled": True,
            }
        await self._post_command_with_fallback_paths(
            vin,
            primary_suffix="climatisation/start-stop",
            primary_payload={"action": "start"},
            fallback_suffix="climatisation/start",
            fallback_payload=fallback_payload,
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
        """Wake vehicle — Cariad-BFF first, MBB legacy fallback.

        v1.9.1 (#92, Audi S6 C8 2021): premium Audi models return ``404``
        on the legacy ``/vehicle/v1/vehicles/{vin}/vehicleWakeup`` path.
        Same v1 → v2 dispatch we use for every other command — the
        ``_post_command`` helper auto-falls-back to ``/vehicle/v2/...``
        on a 404 and remembers the result per VIN so subsequent calls
        skip the dead path.

        v1.21.0 (Audi A4 B9 / Q5 2021 / VW Golf 7 user-report
        2026-05-07): older MIB3 cars (pre-PPE/MEB) reject Cariad-BFF
        completely — both v1 and v2 return Cariad-wrapper-404 with
        body marker ``"Upstream service responded"`` + ``retry:true``.
        These vehicles speak the **legacy MBB stack** instead.

        New strategy:
        1. Check ``MBBBackendCache`` — if VIN previously detected as
           MBB-backed, skip Cariad-BFF entirely + go straight to MBB
        2. Otherwise: try Cariad-BFF (v1+v2 fallback as before)
        3. If Cariad returns wrapper-404 → mark VIN as MBB-backed,
           resolve homeRegion, retry on MBB
        4. Cache the backend choice for 7 days

        See ``cariad/_mbb.py`` for backend-detection logic and
        ``cariad/_home_region.py`` for per-VIN read-base resolution.
        """
        from .._mbb import (  # noqa: PLC0415
            MBBBackendCache,
            is_cariad_wrapper_404,
        )
        from .._home_region import HomeRegionCache  # noqa: PLC0415

        # Lazy-init per-client caches (one MBBBackendCache + one
        # HomeRegionCache per VWEUClient instance)
        if not hasattr(self, "_mbb_backend_cache"):
            self._mbb_backend_cache: MBBBackendCache = MBBBackendCache()
        if not hasattr(self, "_home_region_cache"):
            self._home_region_cache: HomeRegionCache = HomeRegionCache()

        # Step 1: cached backend?
        cached_backend = self._mbb_backend_cache.get(vin)

        if cached_backend == "mbb":
            # Skip Cariad entirely — go straight to MBB
            await self._command_wake_mbb(vin)
            return

        # Step 2: try Cariad-BFF (existing v1→v2 fallback)
        try:
            await self._post_command(vin, "vehicleWakeup", json={})
            # Success — mark VIN as Cariad-backed if not already
            if cached_backend != "cariad":
                self._mbb_backend_cache.set(vin, "cariad")
            return
        except APIError as err:
            # APIError's message includes body[:200] — use str(err)
            # for marker detection (no separate .body attribute).
            body = str(err)
            if not is_cariad_wrapper_404(body):
                # Real failure — propagate (could be auth, real
                # missing endpoint, etc.)
                raise
            _LOGGER.info(
                "VAG wake: Cariad-wrapper-404 for vin ***%s — "
                "marking as MBB-backed and retrying via legacy path",
                vin[-6:],
            )

        # Step 3: detected MBB — cache the flag and retry
        self._mbb_backend_cache.set(vin, "mbb")
        await self._command_wake_mbb(vin)

    async def _command_wake_mbb(self, vin: str) -> None:
        """v1.21.0 — Wake via MBB legacy stack.

        Resolves per-VIN homeRegion (cached 7d), then POSTs to
        ``{readBase}/fs-car/bs/vsr/v1/{Brand}/{country}/vehicles/{vin}/requests``.
        """
        from .._mbb import build_mbb_wake_url, MBB_DEFAULT_READ_BASE  # noqa: PLC0415
        from .._home_region import resolve_home_region  # noqa: PLC0415

        # Resolve home region — defaults to MBB read-base if discovery fails
        try:
            read_base = await resolve_home_region(
                self, vin, cache=self._home_region_cache,
            )
        except Exception:  # noqa: BLE001
            read_base = MBB_DEFAULT_READ_BASE
        # If discovery returned the Cariad default, MBB needs the actual
        # read base — fall back to msg.volkswagen.de (most common).
        if "cariad.digital" in read_base or "bff.cariad" in read_base:
            read_base = MBB_DEFAULT_READ_BASE

        # Brand segment: Audi/VW. Country defaults to DE — most users
        # are EU. Future enhancement: detect country from IDK token.
        brand_name = self._brand.name  # 'volkswagen' or 'audi'
        country = "DE"
        url = build_mbb_wake_url(read_base, brand_name, country, vin)
        _LOGGER.debug(
            "MBB wake POST → %s (vin ***%s)",
            url.replace(vin, f"***{vin[-6:]}"),
            vin[-6:],
        )
        await self._post(url, json={})

    async def _maybe_fill_from_mbb_vsr(self, vin: str, d: VehicleData) -> None:
        """v1.25.0 PR-G — MBB VSR Phase 2 read-side fallback.

        When Cariad-BFF returns no ``fuel_level`` (Golf 7 GTE / older
        PHEV firmware ships ``fuelStatus.rangeStatus = {error}``), the
        underlying MBB OCU still publishes the field via the legacy
        VSR ``/fs-car/bs/vsr/v1/.../status`` endpoint. This is the
        read-side complement to v1.21.0's wake-side MBB fallback.

        Only fires when:
          1. ``d.fuel_level is None`` (Cariad gave us nothing)
          2. AND VIN is known-MBB-backed (set by previous wrapper-404
             event in MBBBackendCache; new VINs must hit a wake first
             to be classified)

        Defensive: any HTTP failure / empty response leaves
        ``d.fuel_level`` at None — entity stays "unknown".

        References:
          - audi_connect_ha audi_models.py legacy IDS table for the
            field-IDs ``0x030103000A`` (tank %) + ``0x0301030005``
            (total range km)
          - tillsteinbach/WeConnect-python — same field-IDs
            confirmed for VW EU MBB stack
        """
        from .._mbb import (  # noqa: PLC0415
            MBBBackendCache,
            MBB_DEFAULT_READ_BASE,
            MBB_VSR_FIELD_TANK_PCT,
            MBB_VSR_FIELD_TOTAL_RANGE_KM,
            build_mbb_vsr_status_url,
            parse_mbb_vsr_field,
        )
        from .._home_region import HomeRegionCache, resolve_home_region  # noqa: PLC0415
        from .._util import safe_int  # noqa: PLC0415

        # Lazy-init caches (same pattern as command_wake)
        if not hasattr(self, "_mbb_backend_cache"):
            self._mbb_backend_cache = MBBBackendCache()
        if not hasattr(self, "_home_region_cache"):
            self._home_region_cache = HomeRegionCache()

        # Only proceed if we KNOW the VIN is MBB-backed. Don't speculatively
        # probe MBB on every Cariad-BFF poll — too noisy for non-Golf 7
        # vehicles. The first wrapper-404 wake will set the flag.
        if self._mbb_backend_cache.get(vin) != "mbb":
            return

        # Resolve homeRegion-derived read base
        try:
            read_base = await resolve_home_region(
                self, vin, cache=self._home_region_cache,
            )
        except Exception:  # noqa: BLE001
            read_base = MBB_DEFAULT_READ_BASE
        if "cariad.digital" in read_base or "bff.cariad" in read_base:
            read_base = MBB_DEFAULT_READ_BASE

        url = build_mbb_vsr_status_url(read_base, self._brand.name, "DE", vin)
        _LOGGER.debug(
            "MBB VSR GET → %s (vin ***%s) — Phase 2 fallback for fuel_level",
            url.replace(vin, f"***{vin[-6:]}"), vin[-6:],
        )

        try:
            response = await self._get(url)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "MBB VSR fetch failed for ***%s: %s — leaving fuel_level None",
                vin[-6:], type(err).__name__,
            )
            return

        # Tank %
        tank_raw = parse_mbb_vsr_field(response, MBB_VSR_FIELD_TANK_PCT)
        tank_pct = safe_int(tank_raw)
        if tank_pct is not None:
            d.fuel_level = tank_pct
            _LOGGER.info(
                "MBB VSR Phase 2: filled fuel_level=%d%% for ***%s "
                "(Cariad-BFF was empty)", tank_pct, vin[-6:],
            )
        # Total range km — only fill if Cariad didn't already give us one
        if d.combustion_range_km is None:
            range_raw = parse_mbb_vsr_field(response, MBB_VSR_FIELD_TOTAL_RANGE_KM)
            range_km = safe_int(range_raw)
            if range_km is not None:
                d.combustion_range_km = range_km
                _LOGGER.info(
                    "MBB VSR Phase 2: filled combustion_range_km=%d for ***%s",
                    range_km, vin[-6:],
                )

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

    async def command_set_max_charge_current(self, vin: str, ampere: int) -> None:
        """Set max AC charge current in Amperes.

        v1.12.0 (#91 follow-up + #90 verified) — body shape verified
        live in #90 (Golf 7 GTE returns ``maxChargeCurrentAC_A = 16``
        from chargingSettings GET, the symmetrical PUT body uses the
        same field name). Same chargingSettings endpoint as
        ``command_set_target_soc`` / ``command_set_charge_mode`` / etc.,
        so v1 → v2 fallback comes for free via ``_post_command``.

        Typical range: 6, 10, 13, 16, 32 A. The CARIAD BFF doesn't
        clamp invalid values server-side reliably — entity layer
        (``number.py``) enforces 6-32 A range.

        ⚠️ [Inference] — verified on Golf 7 GTE READ side (#90 live
        scout dump = 16 A); WRITE side semantics not yet captured
        from official VW EU app traffic. If the backend rejects the
        write, the response goes through the standard
        ``classify_command_failure`` pipeline and surfaces as
        ``ServiceValidationError`` with the actual reason.
        """
        await self._post_command(
            vin, "charging/settings", json={"maxChargeCurrentAC_A": int(ampere)},
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
        recurring_on: list[str] | None = None,
    ) -> None:
        """Set a departure timer (1–3).

        Args:
            vin:            Vehicle VIN
            timer_id:       1, 2 or 3
            enabled:        True to enable, False to disable
            departure_time: "HH:MM" format, e.g. "07:30" (None = keep existing)
            recurring_on:   v2.0.0 (Big-Bang) — optional list of weekday
                            strings (``MONDAY``, ``TUESDAY``, …, ``SUNDAY``)
                            for weekly preheat. When provided, the timer
                            switches to ``recurring`` mode and fires on
                            each listed day; when None the existing
                            recurrence pattern (or one-off) is preserved.
                            Backed by CARIAD-BFF
                            ``/climatisation/timers`` ``recurringOn`` field.
        """
        payload: dict[str, Any] = {"id": timer_id, "enabled": enabled}
        if departure_time:
            payload["departureTime"] = {"time": departure_time}
        if recurring_on:
            # Validate + uppercase: API only accepts the canonical list.
            valid = {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
                     "FRIDAY", "SATURDAY", "SUNDAY"}
            cleaned = [d.upper() for d in recurring_on if d.upper() in valid]
            if cleaned:
                payload["recurringOn"] = cleaned
                payload["type"] = "RECURRING"
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

        # v1.27.2 — scout #181 (Audi): pending charging-settings change requests.
        # Surfaced as a count diagnostic so users can verify their
        # putChargingSettings POSTs actually queued. Empty list = idle.
        pending = v(raw, "charging", "chargingSettings", "requests")
        if isinstance(pending, list):
            d.charging_settings_pending = len(pending)

        # v1.27.2 — Plug visual feedback (LED color on the charge port) +
        # external-power availability. Both come straight from plugStatus.
        # Helpful for "is the wallbox actually delivering power right now?"
        # diagnostics, especially for users with intermittent EVSE issues.
        d.plug_led_color = v(raw, "charging", "plugStatus", "value", "ledColor")
        ext_power = v(raw, "charging", "plugStatus", "value", "externalPower")
        if isinstance(ext_power, str):
            d.external_power_available = ext_power.lower() == "available"

        # v1.26.0 Welle-6 Feature Backlog (#173) — Battery-Care for VW EU/Audi.
        # Skoda + CUPRA/SEAT have these via own paths since v1.17.5; VW EU/Audi
        # finally exposed via Cariad-BFF (paths from scout reports
        # #144/#145/#146/#147 — were silenced in v1.19.3, now wired as features).
        care_mode = v(raw, "charging", "chargingCareSettings", "value", "batteryCareMode")
        if isinstance(care_mode, str):
            up = care_mode.upper()
            if up in ("ACTIVATED", "ACTIVE", "ON", "TRUE"):
                d.battery_care_enabled = True
            elif up in ("DEACTIVATED", "INACTIVE", "OFF", "FALSE"):
                d.battery_care_enabled = False
        care_target = v(raw, "batteryChargingCare", "chargingCareSettings", "value", "batteryCareTargetSoc")
        if care_target is None:
            care_target = v(raw, "charging", "chargingCareSettings", "value", "batteryCareTargetSoc")
        d.battery_care_target_soc_pct = safe_int(care_target)

        # v1.26.0 — Auto-Unlock plug when charged. From scout #144 VW ID.4 Pro.
        auto_unlock_raw = v(raw, "charging", "chargingSettings", "value", "autoUnlockPlugWhenCharged")
        if isinstance(auto_unlock_raw, str):
            up = auto_unlock_raw.upper()
            if up in ("PERMANENT", "ON", "ACTIVATED", "TRUE", "YES"):
                d.auto_unlock_when_charged = True
            elif up in ("OFF", "DEACTIVATED", "FALSE", "NO"):
                d.auto_unlock_when_charged = False

        # v1.26.0 — Next-Charging-Timer info (read-side complement to v1.16.0
        # write-side). From scout #144/#145/#146/#147 (3-user convergence).
        nct_id = v(raw, "automation", "chargingProfiles", "value", "nextChargingTimer", "id")
        d.next_charging_timer_id = safe_int(nct_id)
        nct_target = v(
            raw, "automation", "chargingProfiles", "value",
            "nextChargingTimer", "targetSOCreachable",
        )
        if isinstance(nct_target, str) and nct_target:
            d.next_charging_timer_target_soc_reachable = nct_target

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
        # v1.11.1 (#96 root-cause fix) — VW Golf 7 GTE 2015 + Passat
        # B7/B8 GTE return ``fuelStatus.rangeStatus = {"error": ...}``
        # instead of the ``.value.primaryEngine/.secondaryEngine`` block.
        # Without these fallback paths, ``has_combustion`` stayed False
        # even though ``measurements.fuelLevelStatus.value.primaryEngineType
        # = "gasoline"`` was published — and the data-present gate then
        # blocked both the ``fuel_level`` and ``combustion_range_km``
        # entities. Issue #96 acceptance criteria documented this exactly
        # (evcc-io/evcc#19045 trace shows the same pattern on Passat GTE).
        #
        # Fix: collect engine types from FOUR sources (was 2):
        #   1. fuelStatus.rangeStatus.value.primaryEngine.type
        #   2. fuelStatus.rangeStatus.value.secondaryEngine.type
        #   3. measurements.fuelLevelStatus.value.primaryEngineType  ← NEW
        #   4. measurements.fuelLevelStatus.value.secondaryEngineType  ← NEW
        # AND treat ``carType="hybrid"`` as both battery+combustion (was
        # only matching substring "electric"/"gasoline"/"diesel"/"gas",
        # which missed pure "hybrid" — verified live on Passat GTE).
        primary_engine = v(raw, "fuelStatus", "rangeStatus", "value", "primaryEngine", "type")
        secondary_engine = v(raw, "fuelStatus", "rangeStatus", "value", "secondaryEngine", "type")
        # New: also read measurements engine-type fields. Same backend
        # value, different path — populated even when fuelStatus errors.
        ms_primary = v(raw, "measurements", "fuelLevelStatus", "value", "primaryEngineType")
        ms_secondary = v(raw, "measurements", "fuelLevelStatus", "value", "secondaryEngineType")
        # carType can live under either fuelStatus or measurements.
        car_type = (
            v(raw, "fuelStatus", "rangeStatus", "value", "carType")
            or v(raw, "measurements", "fuelLevelStatus", "value", "carType")
        )

        electric_types = {"electric", "ev"}
        combustion_types = {"gasoline", "petrol", "diesel", "gas", "cng", "lpg"}

        # Iterate ALL four engine-type fields; whichever the API publishes
        # is enough to set the drivetrain flag.
        for engine_type_raw in (primary_engine, secondary_engine, ms_primary, ms_secondary):
            if not engine_type_raw:
                continue
            lower = str(engine_type_raw).lower()
            if lower in electric_types:
                d.has_battery = True
            if lower in combustion_types:
                d.has_combustion = True

        if car_type:
            lower = str(car_type).lower()
            if "electric" in lower:
                d.has_battery = True
            if any(x in lower for x in ("gasoline", "petrol", "diesel", "gas")):
                d.has_combustion = True
            # v1.11.1 (#96) — pure ``hybrid`` / ``phev`` / ``plug-in
            # hybrid`` carType means BOTH drivetrains. Pre-1.11.1 missed
            # this and Passat GTE with carType="hybrid" but no engine
            # detail blocks ended up has_combustion=False.
            if lower in {"hybrid", "phev", "plug-in hybrid", "pluginhybrid", "plug_in_hybrid"}:
                d.has_battery = True
                d.has_combustion = True

        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        # ── Fuel / range ──────────────────────────────────────────────────────
        # v1.11.1 (#96 Track D) — fuel_level fallback from the engine
        # block. Older GTE firmware ships ``currentFuelLevel_pct``
        # INSIDE ``primaryEngine`` (when type=gasoline) — confirmed by
        # CarConnectivity log in #96. Try the well-known measurements
        # path first, fall back to whichever engine block is combustion.
        d.fuel_level = v(raw, "measurements", "fuelLevelStatus", "value", "currentFuelLevel_pct")
        if d.fuel_level is None:
            for engine_path in (
                ("fuelStatus", "rangeStatus", "value", "primaryEngine"),
                ("fuelStatus", "rangeStatus", "value", "secondaryEngine"),
            ):
                engine = v(raw, *engine_path)
                if not isinstance(engine, dict):
                    continue
                engine_type = (engine.get("type") or "").lower()
                if engine_type not in combustion_types:
                    continue
                fuel_pct = safe_int(engine.get("currentFuelLevel_pct"))
                if fuel_pct is not None:
                    d.fuel_level = fuel_pct
                    break

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
            # v1.24.2 (audit): safe_int instead of bare int() try/except
            value = safe_int(engine_range)
            if value is None:
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
                # v1.24.2 (audit): safe_int handles None + non-numeric
                parsed = safe_int(ms_val)
                if parsed is not None:
                    d.combustion_range_km = parsed

        # Total range — from explicit field if present.
        # v1.11.1 (#96 Track C) — older GTE firmware fails fuelStatus
        # with a ``Bad Gateway`` error object but still publishes total
        # range under ``measurements.rangeStatus.value.totalRange_km``
        # (verified via evcc-io/evcc#19045 Passat GTE trace). Both paths
        # tried in order — fuelStatus preferred when it works, falls
        # through to measurements when it doesn't.
        total_range = (
            v(raw, "fuelStatus", "rangeStatus", "value", "totalRange_km")
            or v(raw, "measurements", "rangeStatus", "value", "totalRange_km")
        )
        if total_range is not None:
            d.total_range_km = safe_int(total_range)

        # Back-compat ``range_km`` headline. Preference order matches
        # users' intuitive expectation — EVs/PHEVs see battery range as
        # primary, ICE see combustion or total.
        battery_range = v(raw, "charging", "batteryStatus", "value", "cruisingRangeElectric_km")
        if d.electric_range_km is None and battery_range is not None:
            # v1.24.2 (audit): safe_int — handles None/string/float defensively
            d.electric_range_km = safe_int(battery_range)
        if d.has_battery and d.electric_range_km is not None:
            d.range_km = d.electric_range_km
        elif d.total_range_km is not None:
            d.range_km = d.total_range_km
        elif d.combustion_range_km is not None:
            d.range_km = d.combustion_range_km

        adblue = v(raw, "measurements", "rangeStatus", "value", "adBlueRange")
        d.adblue_range_km = safe_int(adblue)

        # ── Measurements ──────────────────────────────────────────────────────
        d.odometer_km = v(raw, "measurements", "odometerStatus", "value", "odometer")
        d.outside_temp = v(raw, "measurements", "outsideTemperatureStatus", "value", "outsideTemperature_K")
        # v1.24.2 (audit): safe_float for Kelvin → Celsius. Backend has
        # historically shipped string Kelvin temps + null on some PHEV
        # firmwares — bare float() crashed the whole vehicle's poll.
        outside_k = safe_float(d.outside_temp)
        d.outside_temp = round(outside_k - 273.15, 1) if outside_k is not None else None

        bat_min = v(raw, "measurements", "temperatureBatteryStatus", "value", "temperatureHvBatteryMin_K")
        bat_min_k = safe_float(bat_min)
        d.battery_temp = round(bat_min_k - 273.15, 1) if bat_min_k is not None else None

        # v1.12.0 (#23) — 12V starter battery voltage. The CARIAD BFF
        # ``lvBattery`` job publishes voltage in volts (decimal, e.g.
        # 12.6 = healthy). Threshold for warning is 11.5 V (matches
        # volkswagencarnet PR #940 + ELM327 readings widely cited as
        # the "go to garage soon" line). Below 10.5 V the modem can't
        # keep itself awake and the integration will silently fail to
        # poll — that's the symptom users keep blaming on us.
        voltage_raw = v(raw, "lvBattery", "lvBatteryStatus", "value", "batteryVoltage_V")
        d.voltage_12v = safe_float(voltage_raw)
        if d.voltage_12v is not None:
            d.warning_12v_low = d.voltage_12v < 11.5

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

        # v1.26.0 Welle-6 (#173) — climate-at-unlock + window-heating-enabled
        # SETTINGS (distinct from front/back STATES). Scout #144 VW ID.4 Pro.
        clim_at_unlock = v(raw, "climatisation", "climatisationSettings", "value", "climatizationAtUnlock")
        if isinstance(clim_at_unlock, bool):
            d.climate_at_unlock = clim_at_unlock
        wh_enabled = v(raw, "climatisation", "climatisationSettings", "value", "windowHeatingEnabled")
        if isinstance(wh_enabled, bool):
            d.window_heating_enabled = wh_enabled

        # v1.26.0 (#173) — capabilities_count diagnostic. From scout #144
        # (54 items observed). Useful for power-users debugging "why is
        # entity X missing for me?". Read from selectivestatus envelope.
        caps = v(raw, "userCapabilities", "capabilitiesStatus", "value")
        if isinstance(caps, list):
            d.capabilities_count = len(caps)

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
        # v1.11.0 (#91 closure) — explicit raw int day-counts. Same backend
        # source as ``service_due_at``/``oil_service_at`` (which are
        # int-typed but exposed as DATE sensors via in-sensor.py
        # conversion). The new int sensors complement the date sensors
        # for users who want "5 days remaining" instead of "May 5, 2026".
        d.service_due_in_days = safe_int(d.service_due_at)
        d.oil_service_due_in_days = safe_int(d.oil_service_at)

        # v1.11.0 (#91 closure) — vehicle lights aggregate.
        # Backend shape (from #90 + #91 Scout reports — ``[2 items]``,
        # exact element shape varies):
        #   vehicleLights.lightsStatus.value.lights = [
        #     {"name": "frontLeft", "status": "off"},   # common shape A
        #     {"id": "rearRight", "status": "on"},      # common shape B
        #     ...
        #   ]
        # We extract three things:
        #   1. ``lights_count`` — number of lights reporting "on"
        #      (always set when the array is present)
        #   2. ``lights_on`` — bool aggregate (count > 0)
        #   3. ``lights_individual`` — dict {name -> bool} when shape is
        #      recognised. Per-light entities (binary sensors per light)
        #      only register when this dict is populated, so unknown
        #      firmwares never get phantom entities.
        lights_arr = v(raw, "vehicleLights", "lightsStatus", "value", "lights")
        if isinstance(lights_arr, list):
            on_count = 0
            individual: dict[str, bool] = {}
            for light in lights_arr:
                if not isinstance(light, dict):
                    continue
                # Status: try "status" (most common), then "state".
                # May be a plain string ("on"/"off"), a dict
                # ({"value": "on"}), or a list of dicts (CARIAD-BFF
                # pattern — see doors/windows). All three normalise to
                # a single string we then compare case-insensitively.
                raw_status = light.get("status") or light.get("state")
                if isinstance(raw_status, list) and raw_status:
                    raw_status = raw_status[0]
                if isinstance(raw_status, dict):
                    raw_status = raw_status.get("value") or raw_status.get("status")
                is_on = (
                    isinstance(raw_status, str)
                    and raw_status.lower() == "on"
                )
                if is_on:
                    on_count += 1
                # Try to extract a stable name for the per-light dict.
                # Skip if no recognised name field — keeps unknown
                # shapes from polluting the per-light entity list.
                name = (
                    light.get("name")
                    or light.get("id")
                    or (light.get("location") or {}).get("position")
                )
                if isinstance(name, str) and name:
                    individual[name] = is_on
            d.lights_count = on_count
            d.lights_on = on_count > 0
            if individual:
                d.lights_individual = individual

        # ── Departure timers ──────────────────────────────────────────────────
        timers: list[dict[str, Any]] = v(raw, "departureTimers", "departureTimersStatus", "value", "timers") or []
        for i, timer in enumerate(timers[:3], 1):
            enabled = timer.get("enabled", False)
            time_str = timer.get("departureTime", {}).get("time") if timer.get("departureTime") else None
            setattr(d, f"departure_timer_{i}_enabled", enabled)
            setattr(d, f"departure_timer_{i}_time", time_str)

        # ── Parking position ──────────────────────────────────────────────────
        # v1.27.1 hotfix: Cariad-BFF ``/vehicle/v1/vehicles/{vin}/parkingposition``
        # returns ``{"data": {"lat": ..., "lon": ..., "carCapturedTimestamp": ...}}``.
        # Pre-v1.27.1 parser read ``parking.get("lat")`` directly (no ``data``
        # unwrap) → always None → device_tracker never spawned because
        # ``device_tracker._has_gps()`` filter rejects None values silently.
        # Verified live response shape via ``scripts/verify_cariad_for_gte.py``
        # against Golf 7 GTE on 2026-05-11.
        if parking:
            parking_data = parking.get("data") if isinstance(parking, dict) else None
            if not isinstance(parking_data, dict):
                # Some legacy/historic responses or alternate firmwares may
                # ship lat/lon at top level — keep that as a fallback.
                parking_data = parking
            d.latitude = parking_data.get("lat")
            d.longitude = parking_data.get("lon")
            # v1.25.0 PR-A — Cross-brand parity: parking_address from
            # Cariad-BFF if present (Skoda mysmob ships
            # ``formattedAddress`` since v1.20.0). Cariad-BFF
            # ``parkingposition`` returns
            # ``{"address": {"city": "...", "country": "...", ...}}``
            # on most accounts; some firmwares also surface a
            # composed ``formattedAddress``. Saves the HA
            # reverse-geocoding round-trip when supplied.
            addr_block = parking_data.get("address") if isinstance(parking_data, dict) else None
            if isinstance(addr_block, dict):
                fa = addr_block.get("formattedAddress")
                if isinstance(fa, str) and fa:
                    d.parking_address = fa
                else:
                    # Compose from parts: street, city, country
                    parts = [
                        addr_block.get("street"),
                        addr_block.get("city"),
                        addr_block.get("country"),
                    ]
                    composed = ", ".join(p for p in parts if isinstance(p, str) and p)
                    if composed:
                        d.parking_address = composed
                if isinstance(addr_block.get("city"), str):
                    d.parking_city = addr_block["city"]

        return d
