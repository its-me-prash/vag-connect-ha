# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Diagnostics for VAG Connect.

v1.13.0 (#62) — expanded redaction:
- Token fields (access_token / refresh_token / id_token) explicitly
  added to the keep-out list so future code paths that accidentally
  store tokens in entry.data (today they only live in coordinator
  in-memory cache) get caught.
- Email values get partial-mask format ``u***@***.com`` instead of
  bare ``**REDACTED**`` — keeps domain shape for context while
  hiding the local-part.
- GPS coordinates: opt-in toggle to keep them rounded to 1 decimal
  (~11 km bucket) instead of full removal. Default still removes
  for privacy-by-default; users who want better debug info can
  enable via the ``CONF_ENABLE_REVERSE_GEOCODING`` option (already
  signals "I'm OK with GPS being processed").
"""

from __future__ import annotations

import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .cariad._error_reporter import serialise_for_diagnostics
from .cariad._util import mask_vin
from .const import (
    CONF_ENABLE_REVERSE_GEOCODING,
    CONF_PASSWORD,
    CONF_SPIN,
    CONF_USERNAME,
)
from .coordinator import VagConnectCoordinator

_REDACT_KEYS = frozenset({
    CONF_PASSWORD,
    CONF_SPIN,
    CONF_USERNAME,
    "vin",
    "address",
    "parking_address",
    "user_id",
    "account_id",
    # v1.13.0 (#62) — explicit token field names. Defensive registration:
    # today these only live in coordinator's in-memory cache, but if a
    # future change adds them to entry.data they'll automatically
    # redact instead of leaking. Includes both snake_case (Python) and
    # camelCase (JSON) forms.
    "access_token",
    "refresh_token",
    "id_token",
    "accessToken",
    "refreshToken",
    "idToken",
    "id_token_hint",
    "client_secret",
})

# v1.13.0 (#62) — email partial-mask. Keeps domain TLD shape (e.g.
# ``.com``/``.de``) for debug context but redacts the local-part and
# domain name.
_EMAIL_RE = re.compile(
    r"\b([A-Za-z0-9._%+-])([A-Za-z0-9._%+-]*)@[A-Za-z0-9.-]+\.([A-Za-z]{2,})\b"
)


def _mask_email(value: str) -> str:
    """Replace ``user@example.com`` → ``u***@***.com``."""
    return _EMAIL_RE.sub(lambda m: f"{m.group(1)}***@***.{m.group(3)}", value)


def _scrub(value: Any, *, gps_round: bool = False) -> Any:
    """Recursively redact sensitive fields from diagnostics output.

    Args:
        value: any nested structure (dict / list / scalar)
        gps_round: when True, round latitude/longitude to 1 decimal
            instead of redacting completely. Default False
            (privacy-by-default per Hard Rule #18).
    """
    if isinstance(value, dict):
        scrubbed: dict[str, Any] = {}
        for k, v in value.items():
            if k in ("_client", "_vehicle"):
                continue
            if k in _REDACT_KEYS:
                scrubbed[k] = "**REDACTED**"
            elif k == "email" and isinstance(v, str):
                # Partial mask preserves debug context.
                scrubbed[k] = _mask_email(v)
            elif k in ("latitude", "longitude"):
                # Privacy-by-default: full removal. Opt-in 1-decimal
                # rounding when user already opted into reverse-geocoding
                # (signals comfort with GPS processing).
                if gps_round and isinstance(v, (int, float)):
                    scrubbed[k] = round(float(v), 1)
                else:
                    scrubbed[k] = "**REDACTED**"
            else:
                scrubbed[k] = _scrub(v, gps_round=gps_round)
        return scrubbed
    if isinstance(value, list):
        return [_scrub(v, gps_round=gps_round) for v in value]
    if isinstance(value, str):
        # Catch emails embedded in free text (log lines, error messages).
        return _mask_email(value)
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics with VIN, GPS, credentials and other PII redacted.

    v1.13.0 (#62) — GPS rounding is opt-in: if the user already enabled
    ``CONF_ENABLE_REVERSE_GEOCODING`` they're comfortable with GPS
    processing for parking-address resolution, so the diagnostics
    surfaces 1-decimal-rounded coords (~11 km bucket — useful for
    debug, still privacy-safe). Otherwise full removal.
    """
    coordinator: VagConnectCoordinator = entry.runtime_data

    # GPS-rounding opt-in — same signal as the reverse-geocoding toggle.
    gps_round = bool(
        entry.options.get(CONF_ENABLE_REVERSE_GEOCODING, False) is True
        or entry.data.get(CONF_ENABLE_REVERSE_GEOCODING, False) is True
    )

    config_diag = _scrub(dict(entry.data), gps_round=False)  # config never rounds
    options_diag = _scrub(dict(entry.options), gps_round=False)

    vehicles_diag: dict[str, Any] = {}
    for vin, vdata in coordinator.vehicles.items():
        vehicles_diag[mask_vin(vin)] = _scrub(vdata, gps_round=gps_round)

    # v1.9.0 — Vehicle Data Scout findings + Error Reporter buffer.
    # Already masked at the source (mask_value / _redact). Surfaced here so
    # users who download diagnostics for forum / Facebook posts get the
    # full anonymised picture in one file.
    unexpected: dict[str, list[dict[str, Any]]] = {}
    for vin, per_vin in getattr(coordinator, "unexpected_findings", {}).items():
        unexpected[mask_vin(vin)] = [
            {
                "path": f.path,
                "sample": f.sample_masked,
                "endpoint": f.endpoint,
                "first_seen_at": f.first_seen_at,
            }
            for f in per_vin.values()
        ]

    error_buffer = getattr(coordinator, "error_buffer", None)
    error_records = (
        serialise_for_diagnostics(error_buffer) if error_buffer is not None else []
    )

    return {
        "config": config_diag,
        "options": options_diag,
        "vehicles": vehicles_diag,
        "vehicle_count": len(coordinator.vehicles),
        "last_update_success": coordinator.last_update_success,
        "cloud_push_active": coordinator.is_active,
        "unexpected_findings": unexpected,
        "error_buffer": error_records,
    }
