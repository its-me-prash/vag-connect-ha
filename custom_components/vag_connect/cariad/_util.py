# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Pure helpers usable from both the API client layer and the HA layer."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

_LOGGER = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# v1.10.1 — Defensive coding helpers (Issue #58, Phase 2).
#
# Three pure conversion helpers that NEVER raise. They're consumed by the
# brand parsers in places where a single malformed API value used to take
# down the whole vehicle's poll. The pattern documented in
# `skodaconnect/myskoda` issues #503 (CHARGING_INTERRUPTED), #207
# (NOT_ACTIVATED) and PR #565 (NO_UPDATE_AVAILABLE) — VAG ships new enum
# values without warning and integrations that don't tolerate them break
# overnight.
# ─────────────────────────────────────────────────────────────────────────────


def safe_int(value: Any, default: int | None = None) -> int | None:
    """Convert ``value`` to int or return ``default``.

    Accepts:
    - int, bool (Python bool is int subclass — preserved)
    - float (truncated)
    - str (numeric or numeric-with-whitespace)

    Returns ``default`` for None, empty strings, non-numeric strings,
    dicts, lists or any TypeError/ValueError. Never raises.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        try:
            return int(value)
        except (OverflowError, ValueError):
            return default
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return int(stripped)
        except ValueError:
            try:
                return int(float(stripped))
            except (ValueError, OverflowError):
                return default
    return default


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Convert ``value`` to float or return ``default``. Never raises."""
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (OverflowError, ValueError):
            return default
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return float(stripped)
        except ValueError:
            # v1.20.2 — locale-comma fallback. Skoda has shipped
            # ``"21,5"`` (comma decimal, EU locale formatting) on EU
            # accounts at least once historically. v1.10.1 #58 docs
            # claimed safe_float handles this but the original code
            # only accepted dot-decimal — locale-comma silently
            # returned default. Try once more with comma → dot.
            if "," in stripped:
                try:
                    return float(stripped.replace(",", ".", 1))
                except ValueError:
                    return default
            return default
    return default


def safe_enum(
    value: Any,
    known_values: Iterable[str],
    *,
    log_name: str = "enum",
    default: str | None = None,
    case_insensitive: bool = True,
) -> str | None:
    """Return ``value`` if it's in ``known_values``, else log + return default.

    Forward-compatibility shield against unannounced VAG backend changes.
    Every brand has shipped at least one new enum value mid-release
    (myskoda #503 CHARGING_INTERRUPTED, #207 NOT_ACTIVATED, PR #565
    NO_UPDATE_AVAILABLE). Without tolerance the integration crashes
    until we publish a hotfix; with tolerance the entity just shows
    ``unknown`` and the user keeps everything else.

    Args:
        value: The string the API returned. Non-strings are coerced
            via ``str()`` before comparison.
        known_values: Iterable of allowed strings. Performance-wise it's
            converted to a frozenset internally, so callers can pass any
            iterable shape (list, tuple, set, generator).
        log_name: Used in the warning log message — pass the field name
            (e.g. ``"charging_state"``) so the log line is actionable.
        default: Returned when ``value`` is None/empty or unknown.
        case_insensitive: When True (default), ``value`` is compared
            case-insensitively but the *original* string is returned on
            match. The CARIAD BFF mostly returns SCREAMING_SNAKE so
            mixed-case responses from a future firmware should still
            classify correctly.

    Returns:
        The original ``value`` if known, otherwise ``default``.
    """
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    if case_insensitive:
        upper = text.upper()
        known_upper = {k.upper() for k in known_values}
        if upper in known_upper:
            return text
    elif text in set(known_values):
        return text
    _LOGGER.warning(
        "vag_connect: unknown %s value %r — keeping vehicle reachable, "
        "Vehicle Data Scout will surface it on next poll. "
        "Please open a GitHub issue with the masked log line.",
        log_name, text,
    )
    return default


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
