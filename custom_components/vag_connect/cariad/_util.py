# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Pure helpers usable from both the API client layer and the HA layer."""

from __future__ import annotations


def mask_vin(vin: str | None) -> str:
    """Return a privacy-safe VIN representation for logs and diagnostics.

    Keeps the last 6 characters (enough for support to disambiguate vehicles
    on a single account) and drops the rest. A VIN ties to registration,
    insurance and ownership records, so full VINs must never end up in
    GitHub issues, public diagnostics or third-party log forwarders.
    """
    if not vin:
        return "***"
    if len(vin) <= 6:
        return f"***{vin}"
    return f"***{vin[-6:]}"
