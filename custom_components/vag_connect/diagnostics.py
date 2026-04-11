"""Diagnostics support for VAG Connect — helps users report bugs."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD, CONF_SPIN, DOMAIN
from .coordinator import VagConnectCoordinator

# Fields to redact from diagnostics output
_REDACT = {CONF_PASSWORD, CONF_SPIN, "latitude", "longitude"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics — passwords + GPS are redacted automatically."""
    coordinator: VagConnectCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Redact sensitive config fields
    config_data = {
        k: ("**REDACTED**" if k in _REDACT else v)
        for k, v in entry.data.items()
    }

    # Build per-vehicle data, redacting GPS
    vehicles_diag: dict[str, Any] = {}
    for vin, vdata in coordinator.vehicles.items():
        vehicles_diag[vin] = {
            k: ("**REDACTED**" if k in _REDACT else v)
            for k, v in vdata.items()
            if k != "_vehicle"  # never include raw CC objects
        }

    return {
        "integration_version": "0.1.0",
        "config": config_data,
        "vehicles": vehicles_diag,
        "vehicle_count": len(coordinator.vehicles),
        "last_update_success": coordinator.last_update_success,
    }
