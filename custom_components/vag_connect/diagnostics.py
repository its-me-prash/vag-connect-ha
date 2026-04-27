# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Diagnostics for VAG Connect."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .cariad._util import mask_vin
from .const import CONF_PASSWORD, CONF_SPIN, CONF_USERNAME
from .coordinator import VagConnectCoordinator

_REDACT_KEYS = frozenset({
    CONF_PASSWORD,
    CONF_SPIN,
    CONF_USERNAME,
    "latitude",
    "longitude",
    "vin",
    "address",
    "parking_address",
    "user_id",
    "account_id",
    "email",
})


def _scrub(value: Any) -> Any:
    """Recursively redact sensitive fields from diagnostics output."""
    if isinstance(value, dict):
        scrubbed: dict[str, Any] = {}
        for k, v in value.items():
            if k in ("_client", "_vehicle"):
                continue
            if k in _REDACT_KEYS:
                scrubbed[k] = "**REDACTED**"
            else:
                scrubbed[k] = _scrub(v)
        return scrubbed
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics with VIN, GPS, credentials and other PII redacted."""
    coordinator: VagConnectCoordinator = entry.runtime_data

    config_diag = _scrub(dict(entry.data))
    options_diag = _scrub(dict(entry.options))

    vehicles_diag: dict[str, Any] = {}
    for vin, vdata in coordinator.vehicles.items():
        vehicles_diag[mask_vin(vin)] = _scrub(vdata)

    return {
        "config": config_diag,
        "options": options_diag,
        "vehicles": vehicles_diag,
        "vehicle_count": len(coordinator.vehicles),
        "last_update_success": coordinator.last_update_success,
        "cloud_push_active": coordinator.is_active,
    }
