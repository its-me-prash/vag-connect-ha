# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Pure helpers usable from both the API client layer and the HA layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# Connection-state thresholds (v1.8.12 — Multi-Brand Connection-State).
# Derived from `homeassistant-myskoda` issues #751 and #731 + verified
# against `skodaconnect/myskoda` PR #536 (pattern bestätigt).
#   age < 30 min  → "online"   (live, just heard from the car)
#   age < 24 h    → "standby"  (asleep but reachable via /wakeup)
#   age >= 24 h   → "offline"  (12V flat / underground / service)
_CONNECTION_ONLINE_THRESHOLD_S = 1800
_CONNECTION_STANDBY_THRESHOLD_S = 86400


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


def compute_connection_state(
    *sub_objects: Any,
    timestamp_keys: tuple[str, ...] = ("carCapturedTimestamp",),
) -> tuple[str | None, datetime | None]:
    """Derive ``(connection_state, last_seen_at)`` from sub-object timestamps.

    The mysmob (Škoda), OLA (SEAT/CUPRA) and CARIAD-BFF (VW/Audi) backends
    all decorate every status sub-object with a ``carCapturedTimestamp``
    that records *when the vehicle itself last reported the data* — not
    when we polled the backend. Different sub-objects update independently
    (charging publishes more frequently than door state), so the freshest
    timestamp across all sub-objects wins.

    Pattern source: `skodaconnect/myskoda` PR #536
    (`process_charging_event` compares an event timestamp against the API
    snapshot's `carCapturedTimestamp`; older events are ignored). Our
    semantics: the freshest timestamp determines the *vehicle's*
    connection state, regardless of which sub-system produced it.

    Defensive against:

    - sub-objects that are exceptions (asyncio.gather with
      ``return_exceptions=True``)
    - sub-objects that are not dicts
    - missing timestamp fields (myskoda PR #565 confirms this is allowed —
      ``SoftwareStatus.NO_UPDATE_AVAILABLE`` doesn't include
      ``carCapturedTimestamp``)
    - corrupt ISO strings (``ValueError`` swallowed, sub-object skipped)

    Returns ``(None, None)`` if no usable timestamp is found anywhere —
    callers must NOT fabricate a value (Hard Rule #8). The
    ``connection_state`` sensor will simply read ``None`` and HA renders
    it as "unknown".

    Args:
        *sub_objects: Any number of dict / Exception / None values from
            ``asyncio.gather(..., return_exceptions=True)``.
        timestamp_keys: Override the field names to look for. Default
            covers the common ``carCapturedTimestamp``. Add
            ``"capturedAt"`` etc. for backends that diverge.

    Returns:
        Tuple ``(connection_state, last_seen_at)``:

        - ``connection_state``: "online" / "standby" / "offline" / None
        - ``last_seen_at``: datetime (UTC) of the freshest timestamp, or None
    """
    def _extract_timestamps(node: Any) -> list[datetime]:
        """Recursively walk dicts and lists, collecting any datetime that
        sits under one of ``timestamp_keys``.

        VW EU CARIAD-BFF nests deeper than Škoda mysmob:
        ``selectivestatus`` returns
        ``{access: {accessStatus: {value: {carCapturedTimestamp: ...}}}}``
        verified live in `robinostlund/volkswagencarnet` issue #921.
        Škoda mysmob returns the timestamp at top-level
        ``{carCapturedTimestamp: ..., ...}``. SEAT/CUPRA OLA mostly
        top-level too. The recursive walk handles all three without
        per-brand path lists.

        Accepts both ISO strings (Škoda, OLA) and pre-parsed
        ``datetime`` objects (volkswagencarnet's lib does the conversion
        before storing).
        """
        out: list[datetime] = []
        if isinstance(node, dict):
            for k, val in node.items():
                if k in timestamp_keys:
                    if isinstance(val, datetime):
                        out.append(val if val.tzinfo else val.replace(tzinfo=timezone.utc))
                    elif isinstance(val, str):
                        try:
                            ts = datetime.fromisoformat(val.replace("Z", "+00:00"))
                            out.append(ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc))
                        except ValueError:
                            pass
                else:
                    out.extend(_extract_timestamps(val))
        elif isinstance(node, list):
            for item in node:
                out.extend(_extract_timestamps(item))
        return out

    latest_ts: datetime | None = None
    for sub in sub_objects:
        if isinstance(sub, BaseException):
            continue
        for ts in _extract_timestamps(sub):
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts

    if latest_ts is None:
        return None, None

    age_s = (datetime.now(tz=timezone.utc) - latest_ts).total_seconds()
    if age_s < _CONNECTION_ONLINE_THRESHOLD_S:
        return "online", latest_ts
    if age_s < _CONNECTION_STANDBY_THRESHOLD_S:
        return "standby", latest_ts
    return "offline", latest_ts
