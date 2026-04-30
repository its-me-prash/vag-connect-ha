# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Coordinator for VAG Connect — async polling via own CARIAD API client.

Data flow:
  CARIAD client polls VAG API → poll_loop pushes to HA via async_set_updated_data
  → asyncio.run_coroutine_threadsafe → async_set_updated_data → entities update.

Thread safety:
  _vehicles_lock (threading.Lock) guards self.vehicles.
  CARIAD client (async) writes vehicles dict; HA entities read via coordinator data.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import threading
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BRAND,
    CONF_ENABLE_REVERSE_GEOCODING,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.helpers import device_registry as dr
from .cariad._error_reporter import ErrorRingBuffer, record_error
from .cariad._reporter_pipeline import (
    ensure_error_reporter_issue,
    ensure_unexpected_keys_issue,
)
from .cariad._unexpected_keys import UnexpectedField, detect_unexpected
from .cariad._util import mask_vin
from .cariad.exceptions import CommandFailureReason, CommandProfile
from .cariad.models import VehicleData

_LOGGER = logging.getLogger(__name__)

# Minimum interval enforced by Audi/VW connector (Sekunden)
_CC_MIN_INTERVAL_S = 180

# Capabilities are mostly static (subscription tier, vehicle features) but
# can change when a user renews/cancels online services. 24h is a balance
# between picking up legitimate changes and avoiding unnecessary calls.
_CAPABILITIES_TTL = timedelta(hours=24)

# Per-VIN failure tolerance before marking the vehicle unavailable.
# Pattern from `mitch-dc/volkswagen_we_connect_id` #215: a single failed
# poll should not flip every entity on the vehicle to "unavailable" because
# the VAG backend is intermittently flaky (especially weekends and during
# software maintenance windows). Three consecutive failures is the same
# threshold the official We Connect ID app uses before showing an offline
# state to the user.
_FAILURE_TOLERANCE = 3

# Stale-cache window: even after exceeding the failure tolerance, keep
# reporting the vehicle as available if we have data younger than this
# window. Pattern from `skodaconnect/homeassistant-myskoda` #731: users
# strongly prefer "old but visible" over "unavailable" — automations
# triggered by the last known state are still useful, and the user can see
# from `last_updated_at` that the data is stale. 6 hours covers normal
# weekend backend outages without serving truly outdated data.
_STALE_CACHE_WINDOW = timedelta(hours=6)


@dataclass
class FeatureState:
    """Per-VIN per-command state, populated lazily as commands are tried.

    Three orthogonal questions:

    - ``supported_by_vehicle`` — does the VIN have the capability registered
      in the manufacturer backend? Cleared by ``MISSING_CAPABILITY`` errors.
    - ``entitled_by_account`` — does the account currently have permission
      to invoke it? Cleared by ``SUBSCRIPTION_EXPIRED`` / ``NOT_ENTITLED``.
    - ``available_now`` — is the vehicle reachable / awake / responsive
      right now? Transient — reset on success or on every reload.

    ``None`` means "not yet determined" for all three. Don't infer anything
    from a None value; only use this once a real attempt has been made.
    """

    supported_by_vehicle: bool | None = None
    entitled_by_account: bool | None = None
    available_now: bool | None = None
    last_error: CommandFailureReason | None = None
    last_error_at: datetime | None = None


class VagConnectCoordinator(DataUpdateCoordinator):
    """Coordinates vehicle data via own CARIAD API client (direct async polling).

    update_interval=None — polling is handled by _poll_loop(), not HA scheduler.
    Updates flow: CARIAD client → _poll_loop → async_set_updated_data → Entities.
    """

    def __init__(self, hass: HomeAssistant, entry: Any) -> None:
        """Initialise coordinator."""
        self.entry = entry
        self._started = False
        self._was_available: bool = True  # tracks availability for log_when_unavailable
        self._cariad_client: Any = None

        # Thread-safe dict for vehicle data
        self.vehicles: dict[str, Any] = {}
        self._vehicles_lock = threading.Lock()

        # Per-VIN poll success tracking — entities use this for availability
        # so a single failing vehicle doesn't blank out the others.
        self.vehicle_success: dict[str, bool] = {}

        # Per-VIN consecutive-failure counter (v1.8.7). Reset to 0 on every
        # successful poll. Used by ``is_vehicle_available`` to apply
        # ``_FAILURE_TOLERANCE`` before flipping availability — prevents
        # single-poll flicker from breaking automations.
        self.vehicle_failure_count: dict[str, int] = {}

        # Per-VIN timestamp of the last successful poll (v1.8.7). Used by
        # ``is_vehicle_available`` together with ``_STALE_CACHE_WINDOW`` to
        # keep entities visible during transient backend outages. Also
        # exposed in diagnostics so users can see how stale the cached
        # state is.
        self.vehicle_last_good_at: dict[str, datetime] = {}

        # Per-VIN capabilities cache. Hydrated best-effort during setup.
        # 2A foundation only — entity platforms don't read from this yet.
        self.vehicle_capabilities: dict[str, dict[str, Any]] = {}
        self._capabilities_fetched_at: dict[str, datetime] = {}

        # Per-VIN per-command feature state. Hydrated lazily as commands
        # succeed or fail; entry creation is deferred to keep memory tight.
        self.feature_states: dict[str, dict[str, FeatureState]] = {}

        # Per-VIN command profile (Session 3A). Brand clients read this to
        # pick the right URL prefix — e.g. AudiClient swaps /vehicle/v1/
        # for /vehicle/v2/ on PPE/Premium models that 404 the v1 paths.
        # Default UNKNOWN means "use the brand client's current default
        # and let it auto-detect". Persisted only in memory — gets re-
        # learned on every restart, which is cheap (one extra 404 per
        # cold start per VIN).
        self.vehicle_command_profile: dict[str, CommandProfile] = {}

        # Reverse-geocoding cache: {(round(lat,3), round(lon,3)): result}
        self._geocode_cache: dict[tuple[float, float], dict[str, str | None]] = {}

        # v1.9.0 — Vehicle Data Scout state. Per-VIN dict of
        # {path -> UnexpectedField}, de-duped so the same drift seen on
        # every poll only reports once. Surfaced via the
        # ``api_observer_findings`` sensor and the
        # ``vehicle_data_scout_findings`` HA repair issue.
        self.unexpected_findings: dict[str, dict[str, UnexpectedField]] = {}

        # v1.9.0 — Error Reporter ring buffer (last 20 captured exceptions).
        # Surfaced via the ``error_reporter_count`` sensor and the
        # ``error_reporter_findings`` HA repair issue. Bounded so memory
        # and the diagnostics export size stay predictable.
        self.error_buffer: ErrorRingBuffer = ErrorRingBuffer()

        # update_interval=None: no HA-level polling
        # Updates arrive reactively via _on_cc_update → async_set_updated_data
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )


    async def async_setup(self) -> bool:
        """Authenticate and fetch initial vehicle data via own CARIAD client."""
        from homeassistant.helpers.aiohttp_client import async_get_clientsession  # noqa: PLC0415
        from .cariad import CariadClientFactory  # noqa: PLC0415
        from .cariad.exceptions import (  # noqa: PLC0415
            AuthenticationError,
            TermsAndConditionsError,
            MarketingConsentError,
            TwoFactorRequiredError,
            RateLimitError,
        )

        brand    = self.entry.data[CONF_BRAND]
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        spin     = self.entry.data.get(CONF_SPIN) or ""

        session = async_get_clientsession(self.hass)
        self._cariad_client = CariadClientFactory.create(brand, session, username, password, spin)

        try:
            await self._cariad_client.authenticate()
            vins = await self._cariad_client.get_vehicles()
            if not vins:
                return False

            # Fetch status for all vehicles
            results = await asyncio.gather(
                *[self._cariad_client.get_status(vin) for vin in vins],
                return_exceptions=True,
            )

            with self._vehicles_lock:
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.warning("Could not fetch status for %s: %s", mask_vin(vin), result)
                        if hasattr(self, "vehicle_success"):
                            self.vehicle_success[vin] = False
                        continue
                    if isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        self.vehicles[vin] = await self._enrich(data)
                        if hasattr(self, "vehicle_success"):
                            self.vehicle_success[vin] = True

            # Best-effort capabilities prefetch — never blocks setup.
            # Result lives in self.vehicle_capabilities for entity platforms
            # to read in Session 2B. Failure is debug-logged and ignored.
            await asyncio.gather(
                *[self.refresh_capabilities(vin) for vin in self.vehicles],
                return_exceptions=True,
            )

            self._started = True
            found = len(self.vehicles)
            _LOGGER.info("VAG Connect: setup complete — %d vehicle(s)", found)

            # Start background polling — use background task so HA bootstrap doesn't wait
            self.hass.async_create_background_task(self._poll_loop(), f"{DOMAIN}_poll")
            return found > 0

        except TermsAndConditionsError as err:
            raise ValueError("terms_and_conditions") from err
        except MarketingConsentError as err:
            raise ValueError("marketing_consent") from err
        except TwoFactorRequiredError as err:
            raise ValueError("two_factor_required") from err
        except RateLimitError as err:
            raise ValueError("too_many_requests") from err
        except AuthenticationError as err:
            raise ValueError("invalid_credentials") from err
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect setup failed: %s", err)
            return False

    def _trigger_reauth(self, reason: str) -> None:
        """Stop the poll loop and ask HA to start the reauth flow.

        Used when refresh + re-login both fail at runtime so the user gets a
        proper UI prompt instead of a silently failing integration that floods
        the log with retries.
        """
        self._started = False
        for vin in list(self.vehicles.keys()):
            self.vehicle_success[vin] = False
        try:
            self.entry.async_start_reauth(self.hass)
        except Exception:  # noqa: BLE001
            # entry may not support reauth in tests; the loop stop is enough.
            pass
        _LOGGER.error("VAG Connect: stopping poll loop, reauth required (%s)", reason)

    async def _poll_loop(self) -> None:
        """Background polling loop — runs independently of HA scheduler.

        Re-reads scan_interval from entry.options on every iteration so that
        Options-Flow changes take effect without a full integration reload.

        Nightly reduction (22:00–05:00): doubles the polling interval to reduce
        API calls and avoid rate limits during low-activity hours.
        """
        while self._started:
            # Re-read interval every iteration — picks up Options-Flow changes live
            interval_s = max(
                int(
                    self.entry.options.get(CONF_SCAN_INTERVAL)
                    or self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ) * 60,
                _CC_MIN_INTERVAL_S,
            )
            # Nightly reduction: double interval between 22:00 and 05:00
            hour = datetime.now().hour
            if hour >= 22 or hour < 5:
                interval_s = interval_s * 2
                _LOGGER.debug("Nightly reduction active — interval doubled to %ds", interval_s)
            await asyncio.sleep(interval_s)
            if not self._started:
                break
            try:
                # Lazy-initialise per-VIN tracking so tests bypassing __init__ work.
                if not hasattr(self, "vehicle_success"):
                    self.vehicle_success = {}
                vins = list(self.vehicles.keys())
                results = await asyncio.gather(
                    *[self._cariad_client.get_status(vin) for vin in vins],
                    return_exceptions=True,
                )
                fresh: dict[str, Any] = {}
                any_success = False
                # Lazy-initialise v1.8.7 tracking dicts so tests that bypass
                # __init__ (and pre-1.8.7 instances reloaded after upgrade)
                # still work.
                if not hasattr(self, "vehicle_failure_count"):
                    self.vehicle_failure_count = {}
                if not hasattr(self, "vehicle_last_good_at"):
                    self.vehicle_last_good_at = {}
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.debug("Poll failed for %s: %s", mask_vin(vin), result)
                        old = self.vehicles.get(vin, {})
                        old["_poll_failed"] = True
                        fresh[vin] = old
                        self.vehicle_success[vin] = False
                        self.vehicle_failure_count[vin] = (
                            self.vehicle_failure_count.get(vin, 0) + 1
                        )
                        # v1.9.0 — Error Reporter capture. Per-VIN poll failure
                        # gets logged in the ring buffer with masked context so
                        # users can 1-click report it. Wrapped in try/except —
                        # error reporting must NEVER raise.
                        try:
                            record_error(
                                self.error_buffer,
                                exception=result,
                                brand=self.entry.data.get(CONF_BRAND, ""),
                                vin=vin,
                                model_year=self.vehicles.get(vin, {}).get("model_year"),
                                firmware=self.vehicles.get(vin, {}).get("firmware_version"),
                                endpoint="get_status",
                            )
                        except Exception:  # noqa: BLE001
                            pass
                    elif isinstance(result, VehicleData):
                        # v1.10.1 (#58 Phase 2) — wrap to_dict + _enrich
                        # in their own try/except. A single VehicleData
                        # field with an unexpected type used to crash
                        # the whole vehicle's poll mid-update; now the
                        # vehicle stays available with its previous data
                        # and the failure goes to the Error Reporter.
                        try:
                            data = result.to_dict()
                            data["_client"] = self._cariad_client
                            data["_poll_failed"] = False
                            enriched = await self._enrich(data)
                        except Exception as parse_err:  # noqa: BLE001
                            _LOGGER.warning(
                                "VAG Connect: post-parse failure for %s — "
                                "keeping previous data: %s",
                                mask_vin(vin), parse_err,
                            )
                            old = self.vehicles.get(vin, {})
                            old["_poll_failed"] = True
                            fresh[vin] = old
                            self.vehicle_success[vin] = False
                            self.vehicle_failure_count[vin] = (
                                self.vehicle_failure_count.get(vin, 0) + 1
                            )
                            try:
                                record_error(
                                    self.error_buffer,
                                    exception=parse_err,
                                    brand=self.entry.data.get(CONF_BRAND, ""),
                                    vin=vin,
                                    model_year=self.vehicles.get(vin, {}).get("model_year"),
                                    firmware=self.vehicles.get(vin, {}).get("firmware_version"),
                                    endpoint="parse",
                                )
                            except Exception:  # noqa: BLE001
                                pass
                            continue
                        fresh[vin] = enriched
                        any_success = True
                        self.vehicle_success[vin] = True
                        self.vehicle_failure_count[vin] = 0
                        self.vehicle_last_good_at[vin] = datetime.now(tz=timezone.utc)
                        # v1.9.0 — Vehicle Data Scout. Inspect raw responses
                        # the brand client opted to stash; never blocks the
                        # poll if the detector itself raises.
                        try:
                            self._scan_for_unexpected_keys(vin)
                        except Exception:  # noqa: BLE001
                            pass
                    else:
                        fresh[vin] = self.vehicles.get(vin, {})
                        self.vehicle_success[vin] = False
                        self.vehicle_failure_count[vin] = (
                            self.vehicle_failure_count.get(vin, 0) + 1
                        )
                with self._vehicles_lock:
                    self.vehicles.update(fresh)
                # v1.9.0 — Refresh the two reporter repair issues. Cheap to
                # call: ``ensure_*_issue`` deletes when empty and updates
                # in-place when the IDs already exist.
                self._refresh_reporter_issues()
                await self._async_push_update(fresh, success=any_success)
            except Exception as err:  # noqa: BLE001
                # Auth failure that survived the client's refresh-then-relogin
                # fallback means the credentials are stale. Trigger HA reauth.
                from .cariad.exceptions import AuthenticationError  # noqa: PLC0415
                if isinstance(err, AuthenticationError):
                    self._trigger_reauth(str(err) or type(err).__name__)
                    await self._async_push_update({}, success=False)
                    return
                _LOGGER.error("VAG Connect poll error: %s", err)
                # v1.9.0 — Error Reporter: outer poll-loop crash gets a
                # buffer entry too. Critical because these are the kind of
                # errors users hit and never know about (silent except).
                try:
                    record_error(
                        self.error_buffer,
                        exception=err,
                        brand=self.entry.data.get(CONF_BRAND, ""),
                        endpoint="poll_loop",
                    )
                    self._refresh_reporter_issues()
                except Exception:  # noqa: BLE001
                    pass
                if not hasattr(self, "vehicle_success"):
                    self.vehicle_success = {}
                if not hasattr(self, "vehicle_failure_count"):
                    self.vehicle_failure_count = {}
                # Mark all known VINs as failed — avoids stale-as-fresh.
                # ``is_vehicle_available`` still tolerates this for up to
                # ``_FAILURE_TOLERANCE`` consecutive failures and within
                # ``_STALE_CACHE_WINDOW`` so single-poll backend hiccups
                # don't ripple through every entity (we_connect_id #215).
                for vin in list(self.vehicles.keys()):
                    self.vehicle_success[vin] = False
                    self.vehicle_failure_count[vin] = (
                        self.vehicle_failure_count.get(vin, 0) + 1
                    )
                await self._async_push_update({}, success=False)

    async def async_shutdown(self) -> None:
        """Stop polling loop and release resources."""
        self._started = False
        self._cariad_client = None
        _LOGGER.debug("VAG Connect: shutdown complete")

    # ── Vehicle Data Scout + Error Reporter (v1.9.0) ───────────────────────

    def _scan_for_unexpected_keys(self, vin: str) -> None:
        """Run ``detect_unexpected`` over the brand client's stashed responses.

        Brand clients opt in by populating ``last_raw_responses`` in
        ``get_status`` with logical endpoint names matching the
        ``EXPECTED_KEYS`` table. Findings are de-duped per VIN — the same
        drift seen on every poll only takes one slot in the buffer and one
        line in the report.

        Caller wraps in try/except so a detector bug never breaks polling.
        """
        client = self._cariad_client
        if client is None or not hasattr(client, "last_raw_responses"):
            return
        brand = self.entry.data.get(CONF_BRAND, "")
        if not brand:
            return
        if not hasattr(self, "unexpected_findings"):
            self.unexpected_findings = {}
        per_vin = self.unexpected_findings.setdefault(vin, {})
        for endpoint, payload in (client.last_raw_responses or {}).items():
            for finding in detect_unexpected(brand, endpoint, payload):
                # De-dupe by path — keep the first observation timestamp.
                per_vin.setdefault(finding.path, finding)

    def _refresh_reporter_issues(self) -> None:
        """Recreate / delete the two HA repair issues from current buffers.

        Called after every poll cycle. The pipeline functions handle the
        empty case (delete the issue) and the populated case (create or
        refresh in-place — registry de-dupes by issue_id).

        Wrapped here so a registry hiccup can't take down the poll loop.
        """
        brand = self.entry.data.get(CONF_BRAND, "")
        entry_id = getattr(self.entry, "entry_id", "") or ""

        # Flatten per-VIN findings into a single chronological list.
        all_findings = []
        for per_vin in getattr(self, "unexpected_findings", {}).values():
            all_findings.extend(per_vin.values())

        try:
            ensure_unexpected_keys_issue(
                self.hass,
                entry_id=entry_id,
                findings=all_findings,
                brand=brand,
            )
        except Exception:  # noqa: BLE001
            pass

        try:
            buffer = getattr(self, "error_buffer", None)
            records = list(buffer.records) if buffer is not None else []
            ensure_error_reporter_issue(
                self.hass,
                entry_id=entry_id,
                records=records,
                brand=brand,
            )
        except Exception:  # noqa: BLE001
            pass

    def reporter_findings_count(self) -> int:
        """Return the total number of distinct unexpected-key findings.

        Surfaced by the ``api_observer_findings`` sensor as its native
        value. Counting distinct paths (not raw observations) avoids
        misleadingly large numbers when the same drift hits every poll.
        """
        total = 0
        for per_vin in getattr(self, "unexpected_findings", {}).values():
            total += len(per_vin)
        return total

    def reporter_error_count(self) -> int:
        """Return the number of records in the error reporter ring buffer."""
        buffer = getattr(self, "error_buffer", None)
        return len(buffer) if buffer is not None else 0

    @property
    def is_active(self) -> bool:
        """Return True if the CARIAD polling loop is active."""
        return self._started

    def is_vehicle_available(self, vin: str) -> bool:
        """Return True if *vin* should be reported available to entities.

        Two-stage tolerance (v1.8.7):

        1. Up to ``_FAILURE_TOLERANCE`` consecutive failed polls do not
           flip the vehicle to unavailable. Single-poll backend hiccups
           are common on the CARIAD BFF and would otherwise break
           automations watching binary sensors (we_connect_id #215).
        2. Even past the tolerance threshold, if we still have a recent
           successful poll within ``_STALE_CACHE_WINDOW``, keep the
           vehicle visible. The cached state is shown with its
           ``last_updated_at`` so the user can tell it is stale; this
           matches the UX preference documented in myskoda #731.

        Defaults to True for unknown VINs (covers initial setup).
        """
        failures: dict[str, int] = getattr(self, "vehicle_failure_count", {}) or {}
        count = failures.get(vin, 0)
        if count < _FAILURE_TOLERANCE:
            return True
        last_good_map: dict[str, datetime] = (
            getattr(self, "vehicle_last_good_at", {}) or {}
        )
        last_good = last_good_map.get(vin)
        if last_good is not None:
            age = datetime.now(tz=timezone.utc) - last_good
            if age < _STALE_CACHE_WINDOW:
                return True
        # Truly unavailable — past tolerance and stale-cache window.
        return False

    # ── Capabilities & feature-state plumbing (Session 2A foundation) ──────

    def get_feature_state(self, vin: str, command: str) -> FeatureState:
        """Return (or lazily create) the FeatureState for *vin*+*command*.

        2A only sets the dict structure up; later sessions will read from it
        in entity platforms to gate creation/availability.
        """
        states = getattr(self, "feature_states", None)
        if states is None:
            self.feature_states = {}
            states = self.feature_states
        per_vin = states.setdefault(vin, {})
        if command not in per_vin:
            per_vin[command] = FeatureState()
        return per_vin[command]

    def record_command_failure(
        self, vin: str, command: str, reason: CommandFailureReason
    ) -> None:
        """Update the FeatureState after a command failed.

        Conservative — only flips ``supported_by_vehicle`` to False on an
        explicit ``MISSING_CAPABILITY`` response. Other reasons leave the
        flag untouched so a transient backend hiccup never permanently
        hides an entity.
        """
        state = self.get_feature_state(vin, command)
        state.last_error = reason
        state.last_error_at = datetime.now(tz=timezone.utc)
        if reason is CommandFailureReason.MISSING_CAPABILITY:
            state.supported_by_vehicle = False
        elif reason in (
            CommandFailureReason.SUBSCRIPTION_EXPIRED,
            CommandFailureReason.NOT_ENTITLED,
        ):
            state.entitled_by_account = False

    def record_command_success(self, vin: str, command: str) -> None:
        """Mark a command as known-good for *vin*."""
        state = self.get_feature_state(vin, command)
        state.supported_by_vehicle = True
        state.entitled_by_account = True
        state.available_now = True
        state.last_error = None
        state.last_error_at = None

    def is_capabilities_cache_fresh(self, vin: str) -> bool:
        """Return True if cached capabilities for *vin* are within TTL."""
        fetched_at: datetime | None = getattr(
            self, "_capabilities_fetched_at", {}
        ).get(vin)
        if fetched_at is None:
            return False
        return bool(datetime.now(tz=timezone.utc) - fetched_at < _CAPABILITIES_TTL)

    def is_command_known_unsupported(self, vin: str, command: str) -> bool:
        """Return True only if a previous attempt established the command
        is *definitely* not available for *vin*.

        v1.9.1 (Capability-Filter Phase 2, #56) — entity platforms read
        this in their ``available`` property to gracefully hide commands
        that the backend has already rejected with a definitive reason
        (missing capability, expired subscription, not entitled). The
        2A foundation populated ``FeatureState`` but no entity yet read
        from it; Phase 2 wires the read side.

        Conservative: returns ``True`` *only* when at least one of the
        explicit "definitive no" flags is set. Transient backend errors
        leave both flags as ``None`` so the entity stays visible.
        """
        states = getattr(self, "feature_states", None)
        if not states:
            return False
        state = states.get(vin, {}).get(command)
        if state is None:
            return False
        if state.supported_by_vehicle is False:
            return True
        if state.entitled_by_account is False:
            return True
        return False

    def get_command_profile(self, vin: str) -> CommandProfile:
        """Return the cached command profile for *vin*, or ``UNKNOWN``.

        Brand clients consult this before dispatching a command so they
        can pick the right URL prefix without re-discovering it on every
        call. ``UNKNOWN`` means "use the brand client's current default"
        and lets the client auto-learn on the first 404.
        """
        profiles: dict[str, CommandProfile] = (
            getattr(self, "vehicle_command_profile", {}) or {}
        )
        return profiles.get(vin, CommandProfile.UNKNOWN)

    def set_command_profile(self, vin: str, profile: CommandProfile) -> None:
        """Cache the detected command profile for *vin*.

        Called by brand clients after a successful endpoint probe (e.g. a
        v1 404 followed by a v2 200 on Audi premium models). Persisted
        only in memory; cheap to re-learn on restart.
        """
        if not hasattr(self, "vehicle_command_profile"):
            self.vehicle_command_profile = {}
        previous = self.vehicle_command_profile.get(vin, CommandProfile.UNKNOWN)
        self.vehicle_command_profile[vin] = profile
        if previous is not profile:
            _LOGGER.info(
                "VAG Connect: command profile for %s = %s (was %s)",
                mask_vin(vin),
                profile.value,
                previous.value,
            )

    def vehicle_supports_capability(
        self, vin: str, capability_id: str
    ) -> bool | None:
        """Return ``True`` / ``False`` / ``None`` for a capability lookup.

        - ``True``  — capability is present in the cached document and has
          no documented limitations (empty ``status`` array on OLA).
        - ``False`` — capability is present but the backend lists explicit
          limitations, OR the cache is populated and the capability is not
          listed at all (callers can treat both as "do not show entity").
        - ``None``  — no cached document for this VIN yet (e.g. brand has
          no capabilities endpoint, or the prefetch failed). Callers must
          NOT hide entities in this case — the data simply isn't there.

        Conservative on purpose: returns ``None`` for unknown rather than
        guessing. Only an explicit cache hit warrants gating decisions.
        """
        caps = getattr(self, "vehicle_capabilities", {}).get(vin)
        if not isinstance(caps, dict):
            return None
        items = caps.get("capabilities")
        if not isinstance(items, list):
            return None
        for entry in items:
            if not isinstance(entry, dict):
                continue
            if entry.get("id") != capability_id:
                continue
            status = entry.get("status")
            # Empty list / missing → fully usable. Anything in status[] is
            # a limitation (e.g. deactivated, license required, ...).
            return not bool(status)
        # Cache is populated but capability isn't listed — explicit absence.
        return False

    async def refresh_capabilities(self, vin: str, force: bool = False) -> None:
        """Best-effort fetch of the per-VIN capabilities document.

        Failure is logged at debug and never blocks setup or polling. The
        cache stays as-is on error so we don't lose previously known data.
        Only SEAT/CUPRA's OLA endpoint is implemented in this PR; other
        brands return silently from the client side.
        """
        if not force and self.is_capabilities_cache_fresh(vin):
            return
        client = self._cariad_client
        if client is None or not hasattr(client, "get_capabilities"):
            return
        try:
            data = await client.get_capabilities(vin)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Capabilities fetch failed for %s: %s",
                mask_vin(vin),
                err,
            )
            return
        if not isinstance(data, dict):
            return
        if not hasattr(self, "vehicle_capabilities"):
            self.vehicle_capabilities = {}
        if not hasattr(self, "_capabilities_fetched_at"):
            self._capabilities_fetched_at = {}
        self.vehicle_capabilities[vin] = data
        self._capabilities_fetched_at[vin] = datetime.now(tz=timezone.utc)
        _LOGGER.debug(
            "Capabilities cached for %s (%d entries)",
            mask_vin(vin),
            len(data),
        )

    async def _async_push_update(self, data: dict, success: bool = True) -> None:
        """Push vehicle data to HA.

        Implements log_when_unavailable: logs once when going offline,
        once when coming back online — never fills logs with repeated errors.
        Also removes stale devices when vehicles disappear from the account.
        """
        if success:
            if not self._was_available:
                _LOGGER.info(
                    "VAG Connect: vehicle reachable again (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = True

            # Remove devices for VINs no longer present in the account
            await self._async_remove_stale_devices(set(data.keys()))

            self.async_set_updated_data(data)
            _LOGGER.debug("VAG Connect: pushed %d vehicle(s) to HA", len(data))
        else:
            if self._was_available:
                _LOGGER.warning(
                    "VAG Connect: vehicle unreachable — entities set to unavailable (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = False
            self.last_update_success = False
            self.async_update_listeners()

    async def _async_remove_stale_devices(self, current_vins: set) -> None:
        """Remove device registry entries for VINs no longer in the account.

        Implements the stale-devices Gold quality scale rule.
        Only removes devices that were previously seen (in coordinator.data)
        but are no longer returned by the API.
        """
        if not self.data:
            return  # First run — nothing to clean up


        device_reg = dr.async_get(self.hass)
        previous_vins = set(self.data.keys()) - {"_meta"}

        for stale_vin in previous_vins - current_vins:
            device_entry = device_reg.async_get_device(
                identifiers={(DOMAIN, stale_vin)}
            )
            if device_entry is not None:
                _LOGGER.info(
                    "VAG Connect: vehicle %s removed from account — device deleted",
                    stale_vin,
                )
                device_reg.async_remove_device(device_entry.id)



    async def _enrich(self, data: dict) -> dict:
        """Universal post-processing after every get_status() call.

        Sets fields that every brand should have but individual clients may omit:
        - last_updated_at: always UTC now
        - vehicle_state: derived from is_driving / charging_state / connection
        - is_driving: if not set by client, derive from vehicle_state
        - parking_address / parking_city: reverse geocode if lat/lon available (best-effort)
        """

        # Always stamp when we fetched
        data["last_updated_at"] = datetime.now(tz=timezone.utc)

        # Fix #32: Defensive is_charging reset.
        # When plug is disconnected, charging MUST be False regardless of API state.
        # Prevents is_charging staying stuck on "True" after charging ends.
        if not data.get("plug_connected") and data.get("is_charging"):
            data["is_charging"] = False
            _LOGGER.debug(
                "is_charging reset to False — plug not connected (defensive fix #32)"
            )

        # Derive vehicle_state if not set by client
        if not data.get("vehicle_state"):
            if not data.get("is_online", True):
                data["vehicle_state"] = "OFFLINE"
            elif data.get("is_driving"):
                data["vehicle_state"] = "DRIVING"
            elif data.get("is_charging"):
                data["vehicle_state"] = "CHARGING"
            else:
                data["vehicle_state"] = "PARKED"

        # Derive is_driving from vehicle_state if client didn't set it
        if not data.get("is_driving") and data.get("vehicle_state") == "DRIVING":
            data["is_driving"] = True

        # Reverse geocode parking position — opt-in, privacy-aware (#60).
        # Default OFF: vehicle GPS is sensitive and would otherwise be sent
        # to a third-party service (OpenStreetMap Nominatim) on every poll.
        if self._reverse_geocoding_enabled():
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat and lon and not data.get("parking_address"):
                try:
                    result = await self._reverse_geocode(float(lat), float(lon))
                    if result:
                        data["parking_address"] = result.get("address")
                        data["parking_city"] = result.get("city")
                except Exception:  # noqa: BLE001
                    pass  # geocoding is optional — never fail an update because of it

        return data

    def _reverse_geocoding_enabled(self) -> bool:
        """Return True if the user explicitly opted into reverse geocoding."""
        # Use direct comparison to True so MagicMock entries in tests don't
        # accidentally evaluate as truthy and trigger an HTTP call.
        options = getattr(self.entry, "options", None) or {}
        data = getattr(self.entry, "data", None) or {}
        return (
            options.get(CONF_ENABLE_REVERSE_GEOCODING, False) is True
            or data.get(CONF_ENABLE_REVERSE_GEOCODING, False) is True
        )

    async def _reverse_geocode(
        self, lat: float, lon: float
    ) -> dict[str, str | None] | None:
        """Reverse geocode lat/lon via Nominatim using HA's shared aiohttp session.

        Coordinates are rounded to 3 decimals (~110m precision) for caching
        so we do not hit Nominatim every poll for the same parking spot.
        """
        from homeassistant.helpers.aiohttp_client import (  # noqa: PLC0415
            async_get_clientsession,
        )

        # Lazy initialisation so tests bypassing __init__ still work.
        if not hasattr(self, "_geocode_cache"):
            self._geocode_cache = {}

        cache_key = (round(lat, 3), round(lon, 3))
        if cache_key in self._geocode_cache:
            return self._geocode_cache[cache_key]

        from aiohttp import ClientTimeout  # noqa: PLC0415

        session = async_get_clientsession(self.hass)
        url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lon}&format=json&addressdetails=1"
        )
        headers = {"User-Agent": "VAGConnect/1.x (+https://github.com/its-me-prash/vag-connect-ha)"}
        try:
            async with session.get(
                url, headers=headers, timeout=ClientTimeout(total=5)
            ) as resp:
                if resp.status != 200:
                    return None
                payload = await resp.json()
        except Exception:  # noqa: BLE001
            return None

        addr = payload.get("address", {}) if isinstance(payload, dict) else {}
        road = addr.get("road") or addr.get("pedestrian") or addr.get("path", "")
        house = addr.get("house_number", "")
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality", "")
        )
        display = payload.get("display_name", "") if isinstance(payload, dict) else ""

        street = f"{road} {house}".strip() if house else road
        address = (
            f"{street}, {city}".strip(", ")
            if street and city
            else (city or display[:60])
        )

        result: dict[str, str | None] = {
            "address": address or None,
            "city": city or None,
        }
        self._geocode_cache[cache_key] = result
        return result

    async def _async_update_data(self) -> dict[str, Any]:
        """Manual refresh — fetches fresh status for all known VINs."""
        if not self._started or self._cariad_client is None:
            with self._vehicles_lock:
                return dict(self.vehicles)
        try:
            vins = list(self.vehicles.keys())
            results = await asyncio.gather(
                *[self._cariad_client.get_status(vin) for vin in vins],
                return_exceptions=True,
            )
            with self._vehicles_lock:
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.debug("Refresh failed for %s: %s", mask_vin(vin), result)
                        continue
                    if isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        self.vehicles[vin] = await self._enrich(data)
            _LOGGER.debug("VAG Connect: Manual refresh OK")
            return dict(self.vehicles)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect: Manual refresh failed: %s", err)
            with self._vehicles_lock:
                return dict(self.vehicles)


    async def async_lock(self, vin: str) -> None:
        # SEAT/CUPRA lock requires a SecToken obtained from S-PIN verify.
        # Surface the missing-PIN case before the API call so HA shows a
        # clean translation key rather than a low-level SpinError trace.
        #
        # v1.9.1 (#92): Audi/VW EU also need the S-PIN for lock on premium
        # models (CARIAD BFF returns ``403 spin_error`` otherwise). We pass
        # the configured S-PIN through to ``command_lock``; if it's empty
        # the call still goes through (older/non-premium models that don't
        # enforce S-PIN on lock keep working) but premium models will
        # hit the 403 with ``spinState=DEFINED`` — that's then a clear
        # signal to configure the S-PIN, not an integration bug.
        brand = self.entry.data.get(CONF_BRAND, "").lower()
        options = getattr(self.entry, "options", None) or {}
        data = getattr(self.entry, "data", None) or {}
        spin = ""
        if isinstance(options, dict):
            spin = str(options.get(CONF_SPIN) or "")
        if not spin and isinstance(data, dict):
            spin = str(data.get(CONF_SPIN) or "")
        if brand in ("seat", "cupra") and not spin:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="spin_required",
            )
        if brand in ("audi", "volkswagen") and spin:
            await self._cariad_cmd(vin, "command_lock", spin=spin)
        else:
            await self._cariad_cmd(vin, "command_lock")

    async def async_unlock(self, vin: str) -> None:
        # Prefer options (Options Flow) over data (initial config). Use real
        # dict semantics so MagicMock values in tests don't accidentally pass
        # the truthiness check.
        options = getattr(self.entry, "options", None) or {}
        data = getattr(self.entry, "data", None) or {}
        spin = ""
        if isinstance(options, dict):
            spin = str(options.get(CONF_SPIN) or "")
        if not spin and isinstance(data, dict):
            spin = str(data.get(CONF_SPIN) or "")
        if not spin:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="spin_required",
            )
        await self._cariad_cmd(vin, "command_unlock", spin=spin)

    async def async_start_climatisation(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_climate")

    async def async_stop_climatisation(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_climate")

    async def async_start_charging(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_charging")

    async def async_stop_charging(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_charging")

    async def async_flash_lights(self, vin: str) -> None:
        # SEAT/CUPRA require the user position in the honk-and-flash payload
        # (HTTP 400 otherwise). Other brands accept and ignore it.
        vehicle = self.vehicles.get(vin, {})
        await self._cariad_cmd(
            vin,
            "command_flash",
            latitude=vehicle.get("latitude"),
            longitude=vehicle.get("longitude"),
        )

    async def async_set_target_soc(self, vin: str, target: int) -> None:
        await self._cariad_cmd(vin, "command_set_target_soc", target=target)

    async def async_set_climatisation_temperature(self, vin: str, temp_c: float) -> None:
        await self._cariad_cmd(vin, "command_set_climate_temperature", temp_c=temp_c)

    async def async_set_departure_timer(
        self,
        vin: str,
        timer_id: int,
        enabled: bool,
        departure_time: str | None,
    ) -> None:
        """Set a departure timer via CARIAD API."""
        await self._cariad_cmd(
            vin,
            "command_set_departure_timer",
            timer_id=timer_id,
            enabled=enabled,
            departure_time=departure_time,
        )

    async def _cariad_cmd(self, vin: str, method: str, **kwargs: Any) -> None:
        """Dispatch a command to the CARIAD client then refresh state.

        v1.9.1 (Capability-Filter Phase 2, #56) — every command outcome
        flows into ``FeatureState`` automatically:

        - **Success** → ``record_command_success(vin, method)`` flips
          ``supported_by_vehicle`` and ``entitled_by_account`` to ``True``
          and clears ``last_error``. So a once-broken command that starts
          working again (e.g. after subscription renewal) re-appears
          without a HA restart.
        - **Failure** → ``classify_command_failure(err)`` derives a
          ``CommandFailureReason`` from the body content (spin_error,
          subscription, entitlement keywords) plus HTTP status, and
          ``record_command_failure(vin, method, reason)`` updates the
          ``FeatureState`` flags accordingly. The exception still
          propagates so HA shows the user a service-call error — auto-
          classification is purely additive bookkeeping.
        """
        if self._cariad_client is None:
            _LOGGER.error("VAG Connect: no CARIAD client — cannot execute %s", method)
            return
        try:
            fn = getattr(self._cariad_client, method)
            await fn(vin, **kwargs)
            await self.async_request_refresh()
            try:
                self.record_command_success(vin, method)
            except Exception:  # noqa: BLE001
                pass  # bookkeeping must never affect command outcome
            _LOGGER.debug("VAG Connect: %s(%s) OK", method, mask_vin(vin))
        except Exception as err:  # noqa: BLE001
            from .cariad.exceptions import classify_command_failure  # noqa: PLC0415

            try:
                reason = classify_command_failure(err)
                self.record_command_failure(vin, method, reason)
                _LOGGER.info(
                    "VAG Connect: %s(%s) classified as %s",
                    method, mask_vin(vin), reason.value,
                )
            except Exception:  # noqa: BLE001
                pass
            _LOGGER.error("VAG Connect: %s(%s) failed: %s", method, mask_vin(vin), err)
            raise

    async def async_set_charge_mode(self, vin: str, mode: str) -> None:
        """Set charging mode (MANUAL / TIMER / PREFERRED_CHARGING_TIMES)."""
        await self._cariad_cmd(vin, "command_set_charge_mode", mode=mode)

    async def async_set_min_soc(self, vin: str, min_soc: int) -> None:
        """Set minimum SoC for PHEV departure timer."""
        await self._cariad_cmd(vin, "command_set_min_soc", min_soc=min_soc)

    async def async_set_max_charge_current(self, vin: str, ampere: int) -> None:
        """Set max charge current — not supported by current API client.

        Raises ServiceValidationError so HA shows a clear error to the user
        instead of silently swallowing the action (#60). The entity itself
        is hidden in number.py until a real API command exists.
        """
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="feature_not_supported",
            translation_placeholders={"feature": "max_charge_current"},
        )

    async def async_start_window_heating(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_window_heating")

    async def async_stop_window_heating(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_window_heating")

    async def async_wake_vehicle(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_wake")

