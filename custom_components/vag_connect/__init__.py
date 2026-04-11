"""
VAG Connect — Home Assistant integration for all VAG brands.

Supports: Audi · VW (EU) · VW (US/CA) · Škoda · SEAT · CUPRA
Engine:   CarConnectivity by Till Steinbach (MIT)

Architecture:
  - CarConnectivity runs its own background thread (polls VAG API)
  - Observer pattern: CC fires VALUE_CHANGED -> HA updates immediately
  - No double-polling, no race conditions
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
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


def _get_coordinator(hass: HomeAssistant, vin: str) -> VagConnectCoordinator | None:
    for coordinator in hass.data.get(DOMAIN, {}).values():
        if vin in coordinator.vehicles:
            return coordinator
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VAG Connect from a config entry."""
    coordinator = VagConnectCoordinator(hass, entry)

    # Startet CC Background-Thread + erster Fetch + Observer-Registrierung
    ok = await coordinator.async_setup()
    if not ok or not coordinator.vehicles:
        raise ConfigEntryNotReady(
            "VAG Connect: Keine Fahrzeuge gefunden oder Verbindung fehlgeschlagen. "
            "Zugangsdaten und Netzwerk prüfen."
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
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
    """Registriert alle VAG Connect HA-Services."""

    async def _handle_lock(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_lock(call.data["vin"])

    async def _handle_unlock(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_unlock(call.data["vin"])

    async def _handle_start_clim(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_start_climatisation(call.data["vin"])

    async def _handle_stop_clim(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_stop_climatisation(call.data["vin"])

    async def _handle_start_charge(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_start_charging(call.data["vin"])

    async def _handle_stop_charge(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_stop_charging(call.data["vin"])

    async def _handle_flash(call: ServiceCall) -> None:
        if c := _get_coordinator(hass, call.data["vin"]):
            await c.async_flash_lights(call.data["vin"])

    async def _handle_refresh(_call: ServiceCall) -> None:
        for coordinator in hass.data.get(DOMAIN, {}).values():
            await coordinator.async_request_refresh()

    for name, handler, schema in [
        ("lock",                _handle_lock,         SERVICE_VIN_SCHEMA),
        ("unlock",              _handle_unlock,        SERVICE_VIN_SCHEMA),
        ("start_climatisation", _handle_start_clim,    SERVICE_VIN_SCHEMA),
        ("stop_climatisation",  _handle_stop_clim,     SERVICE_VIN_SCHEMA),
        ("start_charging",      _handle_start_charge,  SERVICE_VIN_SCHEMA),
        ("stop_charging",       _handle_stop_charge,   SERVICE_VIN_SCHEMA),
        ("flash_lights",        _handle_flash,         SERVICE_VIN_SCHEMA),
        ("refresh_vehicle",     _handle_refresh,       vol.Schema({})),
    ]:
        hass.services.async_register(DOMAIN, name, handler, schema)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry — stoppt CC Background-Thread sauber."""
    coordinator: VagConnectCoordinator = hass.data[DOMAIN].get(entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if coordinator:
            await coordinator.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id, None)

    if not hass.data.get(DOMAIN):
        for svc in ["lock", "unlock", "start_climatisation", "stop_climatisation",
                    "start_charging", "stop_charging", "flash_lights", "refresh_vehicle"]:
            hass.services.async_remove(DOMAIN, svc)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload bei Optionsänderung (Intervall, S-PIN)."""
    await hass.config_entries.async_reload(entry.entry_id)
