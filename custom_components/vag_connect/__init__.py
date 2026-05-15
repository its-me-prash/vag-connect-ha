# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""VAG Connect — Home Assistant integration for Audi, VW, Škoda, SEAT and CUPRA.

Architecture:
  The CARIAD API client polls the VAG API at a
  configurable interval.  When data changes, it fires an observer callback
  which bridges to the HA event loop via asyncio.run_coroutine_threadsafe and
  calls async_set_updated_data.  HA never polls itself (update_interval=None).
"""

from __future__ import annotations

import logging
from typing import Any, TypeAlias

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_BRAND, CONF_USERNAME, CONF_PASSWORD
from .coordinator import VagConnectCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.LOCK,
    Platform.IMAGE,
    Platform.SELECT,
    # v1.16.0 (#26) — Klima-Timer / Departure-Timer editing UI.
    # Adds time entities ``time.{auto}_departure_timer_X`` for each of
    # the three timers per VIN. Reuses existing
    # ``vag_connect.set_departure_timer`` service in async_set_value.
    Platform.TIME,
]

SERVICE_VIN_SCHEMA = vol.Schema({vol.Required("vin"): cv.string})

VagConnectConfigEntry: TypeAlias = ConfigEntry[VagConnectCoordinator]

_SETUP_ERRORS: dict[str, str] = {
    "terms_and_conditions": (
        "Terms and conditions must be accepted. Open the app, sign in, and confirm."
    ),
    "marketing_consent": (
        "New privacy consent required. App → Profile → Consents."
    ),
    "too_many_requests": (
        "Account temporarily blocked (rate limit). Wait 15 minutes, then restart HA."
    ),
    "two_factor_required": (
        "2FA required. Sign in manually in the app once and confirm the code."
    ),
    "invalid_credentials": (
        "Invalid credentials. Check email and password in the app."
    ),
}


def _get_coordinator(hass: HomeAssistant, vin: str) -> VagConnectCoordinator | None:
    """Return the coordinator that owns *vin*, or None if not found."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if not hasattr(entry, "runtime_data"):
            continue
        coordinator: VagConnectCoordinator = entry.runtime_data
        if vin in coordinator.vehicles:
            return coordinator
    return None


async def async_setup_entry(hass: HomeAssistant, entry: VagConnectConfigEntry) -> bool:
    """Set up a VAG Connect config entry."""
    coordinator = VagConnectCoordinator(hass, entry)

    try:
        ok = await coordinator.async_setup()
    except ValueError as err:
        reason = str(err)
        from .repairs import raise_issue_auth_required  # noqa: PLC0415
        raise_issue_auth_required(hass, entry.entry_id, reason)
        message = _SETUP_ERRORS.get(reason, str(err))
        # invalid_credentials is a hard auth failure — let HA show the reauth
        # prompt instead of looping ConfigEntryNotReady retries forever.
        if reason == "invalid_credentials":
            raise ConfigEntryAuthFailed(message) from err
        raise ConfigEntryNotReady(message) from err
    except Exception as err:  # noqa: BLE001
        if "RequirementsNotFound" in type(err).__name__ or "requirements" in str(err).lower():
            from .repairs import raise_issue_requirements_conflict  # noqa: PLC0415
            raise_issue_requirements_conflict(hass)
            raise ConfigEntryNotReady(
                "VAG Connect setup failed. Check logs for details."
            ) from err
        raise ConfigEntryNotReady(str(err)) from err

    if not ok:
        raise ConfigEntryNotReady("No vehicles found. Check credentials and network.")

    from .repairs import clear_auth_issues  # noqa: PLC0415
    clear_auth_issues(hass, entry.entry_id)

    coordinator.async_set_updated_data(dict(coordinator.vehicles))
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, "lock"):
        _register_services(hass)

    _LOGGER.info("VAG Connect ready: %d vehicle(s)", len(coordinator.vehicles))
    return True


def _register_services(hass: HomeAssistant) -> None:
    """Register all VAG Connect action services."""

    def _coord(vin: str) -> VagConnectCoordinator:
        c = _get_coordinator(hass, vin)
        if c is None:
            raise ServiceValidationError(
                f"Vehicle '{vin}' not found.",
                translation_domain=DOMAIN,
                translation_key="vehicle_not_found",
            )
        return c

    def _coord_writeable(vin: str) -> VagConnectCoordinator:
        """v1.13.0 (#63 Phase 2) — like _coord but blocks if read-only.

        Service-call-side enforcement so YAML automations can't bypass
        the entity-side read-only filter (Phase 1 only blocked entity
        creation; raw service calls still went through).
        """
        c = _coord(vin)
        if c.is_read_only():
            raise ServiceValidationError(
                "Read-only mode is enabled. Disable it in the integration "
                "options to send vehicle commands.",
                translation_domain=DOMAIN,
                translation_key="read_only_mode_active",
            )
        return c

    async def _handle_lock(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_lock(call.data["vin"])

    async def _handle_unlock(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_unlock(call.data["vin"])

    async def _handle_start_clim(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_start_climatisation(call.data["vin"])

    async def _handle_stop_clim(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_stop_climatisation(call.data["vin"])

    async def _handle_start_charge(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_start_charging(call.data["vin"])

    async def _handle_stop_charge(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_stop_charging(call.data["vin"])

    async def _handle_start_window(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_start_window_heating(call.data["vin"])

    async def _handle_stop_window(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_stop_window_heating(call.data["vin"])

    async def _handle_wake(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_wake_vehicle(call.data["vin"])

    async def _handle_flash(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_flash_lights(call.data["vin"])

    async def _handle_set_target_soc(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_set_target_soc(
            call.data["vin"], int(call.data["target"])
        )

    async def _handle_set_clim_temp(call: ServiceCall) -> None:
        await _coord_writeable(call.data["vin"]).async_set_climatisation_temperature(
            call.data["vin"], float(call.data["temperature"])
        )

    async def _handle_set_departure_timer(call: ServiceCall) -> None:
        # v2.0.0 (Big-Bang) — accept optional ``recurring_on`` weekday
        # list (e.g. ``["MONDAY","TUESDAY","FRIDAY"]``). Forwarded to
        # the brand client; ignored by clients that don't support
        # weekly preheat (e.g. Porsche).
        await _coord_writeable(call.data["vin"]).async_set_departure_timer(
            call.data["vin"],
            int(call.data["timer_id"]),
            bool(call.data["enabled"]),
            call.data.get("departure_time"),
            call.data.get("recurring_on"),
        )

    async def _handle_engine_start(call: ServiceCall) -> None:
        """v1.14.0 (#28) — Audi ICE Remote Engine Start.

        S-PIN is taken from the saved config entry, NOT from the service
        call (so it never lands in HA service-call logs). Returns
        ``ServiceValidationError`` if the brand isn't audi or no S-PIN
        is configured.
        """
        await _coord_writeable(call.data["vin"]).async_engine_start(call.data["vin"])

    async def _handle_engine_stop(call: ServiceCall) -> None:
        """v1.14.0 (#28) — Audi ICE Remote Engine Stop. No S-PIN required."""
        await _coord_writeable(call.data["vin"]).async_engine_stop(call.data["vin"])

    # ── v1.17.1 (Bruno-Collection) — SEAT/CUPRA new commands ────────

    async def _handle_start_ventilation(call: ServiceCall) -> None:
        """v1.17.1 — SEAT/CUPRA cabin ventilation start (Bruno seq 31)."""
        await _coord_writeable(call.data["vin"]).async_start_ventilation(
            call.data["vin"]
        )

    async def _handle_stop_ventilation(call: ServiceCall) -> None:
        """v1.17.1 — Ventilation stop (Bruno seq 32)."""
        await _coord_writeable(call.data["vin"]).async_stop_ventilation(
            call.data["vin"]
        )

    async def _handle_start_aux_heating(call: ServiceCall) -> None:
        """v1.17.1 — Webasto auxiliary heating start (SecToken required).

        S-PIN taken from saved config entry — never lands in service-call log.
        """
        await _coord_writeable(call.data["vin"]).async_start_aux_heating(
            call.data["vin"]
        )

    async def _handle_stop_aux_heating(call: ServiceCall) -> None:
        """v1.17.1 — Webasto stop (no S-PIN per Bruno seq 30)."""
        await _coord_writeable(call.data["vin"]).async_stop_aux_heating(
            call.data["vin"]
        )

    async def _handle_send_destination(call: ServiceCall) -> None:
        """v1.17.1 (#36) — Send navigation destination to vehicle."""
        await _coord_writeable(call.data["vin"]).async_send_destination(
            call.data["vin"],
            float(call.data["latitude"]),
            float(call.data["longitude"]),
            str(call.data["name"]),
            city=str(call.data.get("city", "")),
            country=str(call.data.get("country", "")),
            state=str(call.data.get("state", "")),
            street=str(call.data.get("street", "")),
            house_number=str(call.data.get("house_number", "")),
            zip_code=str(call.data.get("zip_code", "")),
        )

    async def _handle_refresh(_call: ServiceCall) -> None:
        """Pull latest cloud-cached state — does NOT wake the vehicle.

        v1.13.0 (#63 Phase 3) — explicit semantic separation. This
        service triggers ``async_request_refresh`` which polls the
        manufacturer backend for the cached vehicle state. The vehicle
        stays asleep. Use ``wake_vehicle`` instead if you need a fresh
        live reading from the car (counts against daily wake budget).
        """
        for entry in hass.config_entries.async_entries(DOMAIN):
            if hasattr(entry, "runtime_data"):
                await entry.runtime_data.async_request_refresh()

    async def _handle_refresh_cloud_cache(_call: ServiceCall) -> None:
        """v1.13.0 (#63 Phase 3) — semantic alias for ``refresh_vehicle``.

        Same behaviour: pulls cloud-cached state, does NOT wake the car.
        New name makes the contract explicit; old name kept for
        backwards-compat (existing automations don't break).
        """
        await _handle_refresh(_call)

    for name, handler, schema in [
        ("lock",                           _handle_lock,                SERVICE_VIN_SCHEMA),
        ("unlock",                         _handle_unlock,              SERVICE_VIN_SCHEMA),
        ("start_climatisation",            _handle_start_clim,          SERVICE_VIN_SCHEMA),
        ("stop_climatisation",             _handle_stop_clim,           SERVICE_VIN_SCHEMA),
        ("start_charging",                 _handle_start_charge,        SERVICE_VIN_SCHEMA),
        ("stop_charging",                  _handle_stop_charge,         SERVICE_VIN_SCHEMA),
        ("start_window_heating",           _handle_start_window,        SERVICE_VIN_SCHEMA),
        ("stop_window_heating",            _handle_stop_window,         SERVICE_VIN_SCHEMA),
        ("wake_vehicle",                   _handle_wake,                SERVICE_VIN_SCHEMA),
        ("flash_lights",                   _handle_flash,               SERVICE_VIN_SCHEMA),
        ("refresh_vehicle",                _handle_refresh,             vol.Schema({})),
        # v1.13.0 (#63 Phase 3) — explicit semantic-clear alias.
        ("refresh_cloud_cache",            _handle_refresh_cloud_cache, vol.Schema({})),
        ("set_target_soc",                 _handle_set_target_soc,
            vol.Schema({
                vol.Required("vin"):    str,
                vol.Required("target"): vol.All(vol.Coerce(int), vol.Range(20, 100)),
            })),
        ("set_climatisation_temperature",  _handle_set_clim_temp,
            vol.Schema({
                vol.Required("vin"):         str,
                vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(16, 30)),
            })),
        ("set_departure_timer",            _handle_set_departure_timer,
            vol.Schema({
                vol.Required("vin"):            cv.string,
                vol.Required("timer_id"):       vol.All(vol.Coerce(int), vol.In([1, 2, 3])),
                vol.Required("enabled"):        cv.boolean,
                vol.Optional("departure_time"): cv.string,
                # v2.0.0 (Big-Bang) — weekly preheat schedule. Each
                # element must be one of the ISO weekday names
                # (UPPER-case canonical, the client also accepts
                # mixed-case inputs).
                vol.Optional("recurring_on"):   vol.All(
                    cv.ensure_list, [cv.string]
                ),
            })),
        # v1.14.0 (#28) — Audi-only ICE Remote Engine Start/Stop.
        ("engine_start",                   _handle_engine_start,        SERVICE_VIN_SCHEMA),
        ("engine_stop",                    _handle_engine_stop,         SERVICE_VIN_SCHEMA),
        # v1.17.1 (Bruno-Collection) — SEAT/CUPRA new commands.
        ("start_ventilation",              _handle_start_ventilation,   SERVICE_VIN_SCHEMA),
        ("stop_ventilation",               _handle_stop_ventilation,    SERVICE_VIN_SCHEMA),
        ("start_aux_heating",              _handle_start_aux_heating,   SERVICE_VIN_SCHEMA),
        ("stop_aux_heating",               _handle_stop_aux_heating,    SERVICE_VIN_SCHEMA),
        ("send_destination",               _handle_send_destination,
            vol.Schema({
                vol.Required("vin"):       cv.string,
                vol.Required("latitude"):  vol.All(vol.Coerce(float), vol.Range(-90, 90)),
                vol.Required("longitude"): vol.All(vol.Coerce(float), vol.Range(-180, 180)),
                vol.Required("name"):      cv.string,
                vol.Optional("city"):         cv.string,
                vol.Optional("country"):      cv.string,
                vol.Optional("state"):        cv.string,
                vol.Optional("street"):       cv.string,
                vol.Optional("house_number"): cv.string,
                vol.Optional("zip_code"):     cv.string,
            })),
    ]:
        hass.services.async_register(DOMAIN, name, handler, schema)


async def async_remove_entry(hass: HomeAssistant, entry: VagConnectConfigEntry) -> None:
    """Clean up persisted IDK tokens when the user removes the integration.

    v1.19.2 (#118 follow-up) — coordinator's TokenStorage writes
    tokens to ``.storage/vag_connect_tokens_<entry_id>``; on
    full-remove (not reload!) we delete that file so the next
    setup of this same brand+account doesn't accidentally pick up
    stale tokens that were issued for a now-removed config-entry.
    """
    from homeassistant.helpers.storage import Store  # noqa: PLC0415
    from .cariad.auth._token_storage import (  # noqa: PLC0415
        TokenStorage,
        storage_key_for_entry,
        _STORAGE_VERSION,
    )
    store: Store[dict[str, Any]] = Store(
        hass, _STORAGE_VERSION, storage_key_for_entry(entry.entry_id),
    )
    storage = TokenStorage(store)
    await storage.clear()


async def async_unload_entry(hass: HomeAssistant, entry: VagConnectConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: VagConnectCoordinator | None = getattr(entry, "runtime_data", None)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and coordinator is not None:
        await coordinator.async_shutdown()

    if not hass.config_entries.async_entries(DOMAIN):
        for svc in [
            "lock", "unlock", "start_climatisation", "stop_climatisation",
            "start_charging", "stop_charging", "start_window_heating",
            "stop_window_heating", "wake_vehicle", "flash_lights",
            "refresh_vehicle", "refresh_cloud_cache", "set_target_soc",
            "set_climatisation_temperature", "set_departure_timer",
            "engine_start", "engine_stop",
            # v1.17.1 (Bruno-Collection)
            "start_ventilation", "stop_ventilation",
            "start_aux_heating", "stop_aux_heating",
            "send_destination",
        ]:
            if hass.services.has_service(DOMAIN, svc):
                hass.services.async_remove(DOMAIN, svc)

    return bool(unload_ok)


async def _async_update_listener(
    hass: HomeAssistant, entry: VagConnectConfigEntry
) -> None:
    """Handle options changes — reload only when credentials change.

    scan_interval and spin are applied live without a full reload:
    - scan_interval: _poll_loop re-reads it on every iteration
    - spin: coordinator reads it directly from entry.data at command time

    A full reload is only triggered when brand, username or password changes
    (those require a new authenticated API client).
    """
    coordinator: VagConnectCoordinator | None = getattr(entry, "runtime_data", None)

    # Fields that require a full reload (new auth client needed)
    _RELOAD_KEYS = {CONF_BRAND, CONF_USERNAME, CONF_PASSWORD}
    options: dict = dict(entry.options) if entry.options else {}

    changed = {
        k for k in _RELOAD_KEYS
        if entry.data.get(k) != options.get(k, entry.data.get(k))
    }

    if changed:
        _LOGGER.info("VAG Connect: config changed (%s) — reloading", changed)
        await hass.config_entries.async_reload(entry.entry_id)
    else:
        # Soft update: merge options into entry data so coordinator picks them up
        new_data: dict = {**dict(entry.data), **options}
        hass.config_entries.async_update_entry(entry, data=new_data, options={})
        if coordinator:
            _LOGGER.debug(
                "VAG Connect: settings applied live (no restart needed)"
            )
            # Trigger one immediate refresh so users see the effect
            await coordinator.async_request_refresh()
