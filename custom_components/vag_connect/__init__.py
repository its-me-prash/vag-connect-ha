"""
VAG Connect — Home Assistant integration for all VAG brands.

Supports: Audi · VW (EU) · VW (US/CA) · Škoda · SEAT · CUPRA
Engine:   CarConnectivity by Till Steinbach (MIT)

Architecture:
  - CarConnectivity runs its own background thread (polls VAG API at configured interval)
  - Observer pattern: CC fires VALUE_CHANGED -> HA updates immediately (cloud_push)
  - No HA-level polling (update_interval=None), no race conditions
  - entry.runtime_data holds the coordinator (modern HA pattern)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import VagConnectCoordinator

if TYPE_CHECKING:
    pass

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

# Type alias for config entries using this integration
type VagConnectConfigEntry = ConfigEntry[VagConnectCoordinator]


def _get_coordinator(
    hass: HomeAssistant, vin: str
) -> VagConnectCoordinator | None:
    """Find the coordinator that owns the given VIN across all config entries."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if not hasattr(entry, "runtime_data"):
            continue
        coordinator: VagConnectCoordinator = entry.runtime_data
        if vin in coordinator.vehicles:
            return coordinator
    return None


async def async_setup_entry(hass: HomeAssistant, entry: VagConnectConfigEntry) -> bool:
    """Set up VAG Connect from a config entry."""
    coordinator = VagConnectCoordinator(hass, entry)

    _ERROR_MAP = {
        "terms_and_conditions": (
            "Nutzungsbedingungen müssen akzeptiert werden. "
            "App öffnen, anmelden und Bedingungen bestätigen."
        ),
        "marketing_consent": (
            "Neue Datenschutzzustimmung erforderlich. "
            "App → Profil → Zustimmungen."
        ),
        "too_many_requests": (
            "Account temporär gesperrt (zu viele Anfragen). "
            "15 Minuten warten, dann HA neu starten."
        ),
        "two_factor_required": (
            "2FA erforderlich. "
            "Einmal manuell in der App anmelden und 2FA-Code bestätigen."
        ),
        "invalid_credentials": (
            "Zugangsdaten falsch. E-Mail und Passwort aus der App prüfen."
        ),
    }

    try:
        ok = await coordinator.async_setup()
    except ValueError as err:
        reason = str(err)
        msg = _ERROR_MAP.get(reason, f"Setup-Fehler: {err}")
        from .repairs import raise_issue_auth_required  # noqa: PLC0415
        raise_issue_auth_required(hass, entry.entry_id, reason)
        raise ConfigEntryNotReady(msg) from err
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(f"Verbindungsfehler: {err}") from err

    if not ok:
        raise ConfigEntryNotReady(
            "Keine Fahrzeuge gefunden. Zugangsdaten und Netzwerk prüfen."
        )

    # Auth OK — clear any existing auth repair issues
    from .repairs import clear_auth_issues  # noqa: PLC0415
    clear_auth_issues(hass, entry.entry_id)

    # Seed coordinator.data before platform setup so entities have values at creation
    coordinator.async_set_updated_data(dict(coordinator.vehicles))

    # Store coordinator in entry.runtime_data (modern HA pattern, replaces hass.data)
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, "lock"):
        _register_services(hass)

    _LOGGER.info(
        "VAG Connect bereit: %d Fahrzeug(e), reaktive Updates via CC-Observer",
        len(coordinator.vehicles),
    )
    return True


def _register_services(hass: HomeAssistant) -> None:
    """Register all VAG Connect HA services."""

    def _require_coordinator(vin: str, service_name: str) -> VagConnectCoordinator:
        """Get coordinator for VIN or raise ServiceValidationError."""
        coord = _get_coordinator(hass, vin)
        if coord is None:
            raise ServiceValidationError(
                f"Fahrzeug mit VIN '{vin}' nicht gefunden. "
                f"VIN prüfen und sicherstellen dass die Integration gestartet ist.",
                translation_domain=DOMAIN,
                translation_key="vehicle_not_found",
            )
        return coord

    async def _handle_lock(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "lock")
        await c.async_lock(call.data["vin"])

    async def _handle_unlock(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "unlock")
        await c.async_unlock(call.data["vin"])

    async def _handle_start_clim(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "start_climatisation")
        await c.async_start_climatisation(call.data["vin"])

    async def _handle_stop_clim(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "stop_climatisation")
        await c.async_stop_climatisation(call.data["vin"])

    async def _handle_start_charge(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "start_charging")
        await c.async_start_charging(call.data["vin"])

    async def _handle_stop_charge(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "stop_charging")
        await c.async_stop_charging(call.data["vin"])

    async def _handle_start_window(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "start_window_heating")
        await c.async_start_window_heating(call.data["vin"])

    async def _handle_stop_window(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "stop_window_heating")
        await c.async_stop_window_heating(call.data["vin"])

    async def _handle_wake(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "wake_vehicle")
        await c.async_wake_vehicle(call.data["vin"])

    async def _handle_set_target_soc(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "set_target_soc")
        await c.async_set_target_soc(call.data["vin"], int(call.data["target"]))

    async def _handle_set_clim_temp(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "set_climatisation_temperature")
        await c.async_set_climatisation_temperature(
            call.data["vin"], float(call.data["temperature"])
        )

    async def _handle_set_departure_timer(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "set_departure_timer")
        await c.async_set_departure_timer(
            call.data["vin"],
            int(call.data["timer_id"]),
            bool(call.data["enabled"]),
            call.data.get("departure_time"),
        )

    async def _handle_flash(call: ServiceCall) -> None:
        c = _require_coordinator(call.data["vin"], "flash_lights")
        await c.async_flash_lights(call.data["vin"])

    async def _handle_refresh(_call: ServiceCall) -> None:
        for entry in hass.config_entries.async_entries(DOMAIN):
            if hasattr(entry, "runtime_data"):
                await entry.runtime_data.async_request_refresh()

    for name, handler, schema in [
        ("lock",                  _handle_lock,           SERVICE_VIN_SCHEMA),
        ("unlock",                _handle_unlock,          SERVICE_VIN_SCHEMA),
        ("start_climatisation",   _handle_start_clim,      SERVICE_VIN_SCHEMA),
        ("stop_climatisation",    _handle_stop_clim,       SERVICE_VIN_SCHEMA),
        ("start_charging",        _handle_start_charge,    SERVICE_VIN_SCHEMA),
        ("stop_charging",         _handle_stop_charge,     SERVICE_VIN_SCHEMA),
        ("start_window_heating",  _handle_start_window,    SERVICE_VIN_SCHEMA),
        ("stop_window_heating",   _handle_stop_window,     SERVICE_VIN_SCHEMA),
        ("wake_vehicle",          _handle_wake,            SERVICE_VIN_SCHEMA),
        ("flash_lights",          _handle_flash,           SERVICE_VIN_SCHEMA),
        ("set_target_soc",        _handle_set_target_soc,
            vol.Schema({
                vol.Required("vin"):    str,
                vol.Required("target"): vol.All(vol.Coerce(int), vol.Range(20, 100)),
            })),
        ("set_climatisation_temperature", _handle_set_clim_temp,
            vol.Schema({
                vol.Required("vin"):         str,
                vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(16, 30)),
            })),
        ("set_departure_timer", _handle_set_departure_timer,
            vol.Schema({
                vol.Required("vin"):            cv.string,
                vol.Required("timer_id"):       vol.All(vol.Coerce(int), vol.In([1, 2, 3])),
                vol.Required("enabled"):        cv.boolean,
                vol.Optional("departure_time"): cv.string,
            })),
        ("refresh_vehicle",       _handle_refresh,         vol.Schema({})),
    ]:
        hass.services.async_register(DOMAIN, name, handler, schema)


async def async_unload_entry(hass: HomeAssistant, entry: VagConnectConfigEntry) -> bool:
    """Unload a config entry — cleanly stops CC background thread."""
    coordinator: VagConnectCoordinator | None = getattr(entry, "runtime_data", None)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and coordinator is not None:
        await coordinator.async_shutdown()

    # Remove services only when the last entry is unloaded
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
    """Reload when options change (interval, S-PIN)."""
    await hass.config_entries.async_reload(entry.entry_id)
