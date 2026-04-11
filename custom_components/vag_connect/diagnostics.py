"""Diagnostics for VAG Connect — helps users report bugs without exposing credentials."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD, CONF_SPIN
from .coordinator import VagConnectCoordinator

# Fields redacted from diagnostics output — never sent to issue trackers
_REDACT = frozenset({CONF_PASSWORD, CONF_SPIN, "latitude", "longitude"})


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics data — credentials and GPS coordinates are redacted."""
    coordinator: VagConnectCoordinator = entry.runtime_data

    # Redact sensitive config fields
    config_diag = {
        k: ("**REDACTED**" if k in _REDACT else v)
        for k, v in entry.data.items()
    }

    # Per-vehicle data with GPS and credentials redacted
    vehicles_diag: dict[str, Any] = {}
    for vin, vdata in coordinator.vehicles.items():
        vehicles_diag[vin] = {
            k: ("**REDACTED**" if k in _REDACT else v)
            for k, v in vdata.items()
            if k != "_vehicle"  # never include raw CC objects
        }

    return {
        "config": config_diag,
        "vehicles": vehicles_diag,
        "vehicle_count": len(coordinator.vehicles),
        "last_update_success": coordinator.last_update_success,
        "cloud_push_active": coordinator._started,  # noqa: SLF001
    }
