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
from typing import TypeAlias

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
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
        raise ConfigEntryNotReady(_SETUP_ERRORS.get(reason, str(err))) from err
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

    async def _handle_lock(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_lock(call.data["vin"])

    async def _handle_unlock(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_unlock(call.data["vin"])

    async def _handle_start_clim(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_start_climatisation(call.data["vin"])

    async def _handle_stop_clim(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_stop_climatisation(call.data["vin"])

    async def _handle_start_charge(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_start_charging(call.data["vin"])

    async def _handle_stop_charge(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_stop_charging(call.data["vin"])

    async def _handle_start_window(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_start_window_heating(call.data["vin"])

    async def _handle_stop_window(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_stop_window_heating(call.data["vin"])

    async def _handle_wake(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_wake_vehicle(call.data["vin"])

    async def _handle_flash(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_flash_lights(call.data["vin"])

    async def _handle_set_target_soc(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_set_target_soc(
            call.data["vin"], int(call.data["target"])
        )

    async def _handle_set_clim_temp(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_set_climatisation_temperature(
            call.data["vin"], float(call.data["temperature"])
        )

    async def _handle_set_departure_timer(call: ServiceCall) -> None:
        await _coord(call.data["vin"]).async_set_departure_timer(
            call.data["vin"],
            int(call.data["timer_id"]),
            bool(call.data["enabled"]),
            call.data.get("departure_time"),
        )

    async def _handle_refresh(_call: ServiceCall) -> None:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if hasattr(entry, "runtime_data"):
                await entry.runtime_data.async_request_refresh()

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
            })),
    ]:
        hass.services.async_register(DOMAIN, name, handler, schema)


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
            "refresh_vehicle", "set_target_soc", "set_climatisation_temperature",
            "set_departure_timer",
        ]:
            if hass.services.has_service(DOMAIN, svc):
                hass.services.async_remove(DOMAIN, svc)

    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: VagConnectConfigEntry
) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
