# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Capability-ID Mapping per Brand — Single Source of Truth.

v1.13.0 (#56 Phase 3) — when an HA platform's ``async_setup_entry``
decides whether to register a command-bound entity, it asks
``coordinator.command_capability_supported(vin, command_id)``. That
helper translates the integration-level command name (e.g.
``"command_flash"``) into the brand-specific capability ID (e.g.
``"honkAndFlash"`` for VW EU CARIAD-BFF, ``"honk-and-flash"`` for
SEAT/CUPRA OLA, ``"honk-and-flash"`` for Skoda mysmob) before
querying the capability cache.

Why this lives in its own module:
- Pre-v1.13.0 the brand→cap-id mapping was implicit — Phase 2 only
  recorded post-failure outcomes (`MISSING_CAPABILITY`) and the
  brand-string never mattered.
- Phase 3 needs to PRE-decide; that requires a stable lookup table.
- Putting it in const.py would mix infra constants with business
  vocabulary; here it's a focused single-source-of-truth that the
  research notes (`docs/RESEARCH_NOTES_2026-05-02.md`) reference
  directly.

Design rules:
- Keep the table CONSERVATIVE — when in doubt, do NOT add a
  capability mapping. Phase 3 falls through to Phase 2 (which
  catches at runtime) if no cap-id is registered.
- Annotate confidence with comments per row: ✅ verified in production
  vs ⚠️ [Inference] vs ❌ unknown.
- New brands (vw_na, porsche) start empty — capabilities discovered
  via Vehicle Data Scout reports get added here once verified.
"""

from __future__ import annotations

from typing import Final

# Per-brand: command-id → capability-id string.
#
# ``command_id`` is the same string used by ``coordinator.record_command_*``
# (e.g. "command_lock", "command_flash"). ``cap_id`` is the brand-specific
# string the backend's capabilities endpoint publishes.
#
# When a row is missing from a brand's table, ``command_capability_supported``
# returns ``None`` (= unknown, don't filter). That's the safe default —
# Phase 2's runtime filter catches missing capabilities post-failure.
CAPABILITY_MAP: Final[dict[str, dict[str, str]]] = {
    # ─────────────────────────────────────────────────────────────────
    # VW EU CARIAD-BFF — capabilities endpoint:
    #   GET /vehicle/v1/vehicles/{vin}/capabilities
    # Schema: {capabilities: [{id, status: [...]}]}
    # status=[] → fully usable; non-empty → limitation present
    # ─────────────────────────────────────────────────────────────────
    "volkswagen": {
        "command_lock": "access",                # ✅ verified — used by lock platform
        "command_unlock": "access",              # ✅ same capability gates both
        "command_flash": "honkAndFlash",         # ✅ verified — vw_eu.py:120 reference
        "command_start_climate": "climatisation",   # ✅ standard CARIAD vocabulary
        "command_stop_climate": "climatisation",
        "command_start_charging": "charging",       # ✅
        "command_stop_charging": "charging",
        "command_set_target_soc": "charging",       # ✅ same parent capability
        "command_set_charge_mode": "charging",
        "command_set_min_soc": "charging",
        "command_set_max_charge_current": "charging",
        # ⚠️ [Inference] — pattern from CARIAD vocabulary, not yet seen
        # in a Scout-Whitelist-confirmed capabilities response.
        "command_wake": "vehicleWakeUpTrigger",
        "command_start_window_heating": "windowHeating",
        "command_stop_window_heating": "windowHeating",
        "command_set_climate_temperature": "climatisation",
        "command_set_departure_timer": "departureTimers",
        # v1.14.0 (#24) — Trip Statistics (subscription-required: Audi
        # connect Plus / WeConnect Plus). ⚠️ [Inference] cap-id matches
        # CARIAD camelCase pattern; not yet seen in a Scout-confirmed
        # capabilities response. Phase 3 returns ``None`` → don't filter
        # if the cap row is absent, so vehicles without a published
        # capability still get the entities.
        "command_trip_stats": "tripStatistics",
    },
    # ─────────────────────────────────────────────────────────────────
    # Audi inherits VW EU's CARIAD-BFF capabilities (AudiClient(VWEUClient)).
    # Identical endpoint, identical schema, mostly identical cap-ids.
    # See cariad/api/audi.py for the inheritance.
    #
    # v1.14.0 (#28) — Audi-only ICE Remote Engine Start has no
    # corresponding entry in CAPABILITY_MAP["volkswagen"] — VW EU's
    # CARIAD-BFF doesn't expose the /engine/ subtree. The Audi-only
    # cap-id is patched in below the inheritance assignment.
    # ─────────────────────────────────────────────────────────────────
    "audi": {},  # populated at module load below from "volkswagen"
    # ─────────────────────────────────────────────────────────────────
    # SEAT/CUPRA OLA — capabilities endpoint:
    #   GET /v1/vehicles/{vin}/capabilities  (or /v5/users/{userId}/...)
    # Schema same dict-shape but cap-ids are kebab-case.
    # ─────────────────────────────────────────────────────────────────
    "cupra": {
        "command_lock": "access",                # ✅ verified
        "command_unlock": "access",
        "command_flash": "honk-and-flash",       # ✅ verified — seat_cupra.py:87 reference
        # ⚠️ [Inference] — kebab-case pattern from OLA, plus missing-capability
        # responses observed for these on Gerhard's Born (#53 — CUPRA Born
        # 2023 Active subscription, capabilities did NOT include these).
        "command_wake": "vehicle-wakeup",
        "command_start_climate": "climatisation",
        "command_stop_climate": "climatisation",
        "command_start_charging": "charging",
        "command_stop_charging": "charging",
        "command_set_target_soc": "charging",
        "command_set_charge_mode": "charging",
        "command_set_min_soc": "charging",
        "command_set_max_charge_current": "charging",
        "command_start_window_heating": "window-heating",
        "command_stop_window_heating": "window-heating",
        "command_set_climate_temperature": "climatisation",
        "command_set_departure_timer": "departure-timers",
    },
    # SEAT shares OLA backend with CUPRA — same capability vocabulary.
    "seat": {},  # populated at module load below from "cupra"
    # ─────────────────────────────────────────────────────────────────
    # Skoda mysmob — capabilities endpoint:
    #   GET /api/v1/vehicle-access/{vin}/capabilities  (NEW in v1.13.0)
    # Schema: {capabilities: [{id, active, editable?, user-enabled?,
    #          status?, license-issue?, parameters?}]}
    # Different shape — uses "active" + "user-enabled" booleans plus
    # optional "status" array. See vehicle_supports_capability for the
    # schema-compatibility logic.
    # ─────────────────────────────────────────────────────────────────
    "skoda": {
        "command_lock": "access",
        "command_unlock": "access",
        # ⚠️ [Inference] — kebab-case Skoda pattern matches OLA convention.
        # Real Skoda capabilities response not yet captured in a Scout
        # report; treat as inferred and let Phase 2 catch failures.
        "command_flash": "honk-and-flash",
        "command_wake": "vehicleWakeUpTrigger",
        "command_start_climate": "air-conditioning",   # mysmob endpoint name
        "command_stop_climate": "air-conditioning",
        "command_start_charging": "charging",
        "command_stop_charging": "charging",
        "command_set_target_soc": "charging",
        "command_set_charge_mode": "charging",
        "command_set_min_soc": "charging",
        "command_start_window_heating": "air-conditioning",
        "command_stop_window_heating": "air-conditioning",
        "command_set_climate_temperature": "air-conditioning",
        "command_set_departure_timer": "departure-timers",
    },
    # ─────────────────────────────────────────────────────────────────
    # VW NA + Porsche — different backends, capabilities not yet
    # reverse-engineered. Empty table = Phase 3 falls through to Phase 2
    # (runtime-detect after failure). Safe fallback.
    # ─────────────────────────────────────────────────────────────────
    "volkswagen_na": {},  # ❌ unknown — VW NA Auth/API distinct from CARIAD
    "porsche": {},        # ❌ unknown — Auth0 + PPA backend, separate vocabulary
}

# Audi inherits the VW EU mapping at module load time. SEAT inherits CUPRA's.
# Same alias-trick used for EXPECTED_KEYS in cariad/_unexpected_keys.py.
CAPABILITY_MAP["audi"] = CAPABILITY_MAP["volkswagen"]
CAPABILITY_MAP["seat"] = CAPABILITY_MAP["cupra"]

# v1.14.0 (#28) — Audi-only ICE Engine Start. Replace the alias with a
# COPY so we can add Audi-specific entries without polluting VW EU's
# table (the alias trick above shares the same dict by reference).
# ⚠️ [Inference] cap-id ``engineRemoteStart`` is the camelCase guess
# that matches CARIAD vocabulary patterns (``honkAndFlash``,
# ``vehicleWakeUpTrigger``). NOT confirmed in a live capabilities
# response yet — when a Scout report surfaces the real id we update.
CAPABILITY_MAP["audi"] = dict(CAPABILITY_MAP["audi"])
CAPABILITY_MAP["audi"]["command_engine_start"] = "engineRemoteStart"
CAPABILITY_MAP["audi"]["command_engine_stop"] = "engineRemoteStart"


def cap_id_for(brand: str, command_id: str) -> str | None:
    """Return the brand-specific capability-id for a command, or None.

    None means the command-id has no registered capability mapping for
    this brand. Phase 3 in the platform setup interprets this as "don't
    filter" (Phase 2 catches it at runtime if it really doesn't work).

    Pure function — safe to call from any thread, no I/O.
    """
    return CAPABILITY_MAP.get(brand, {}).get(command_id)
