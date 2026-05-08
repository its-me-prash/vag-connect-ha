# Sprint C — v1.25.0 Detail Plan

> **Status:** Plan written 2026-05-08, post v1.24.2 ship.
> **Target:** v1.25.0 (MINOR — new entities + new services + new write-side commands).
> **Estimated effort:** 3-4 dev days, split across 4 sub-bundles.
> **Risk:** Medium — first major coordinator refactor + first write-side bundle in 6 weeks.
> **Dependencies:** v1.24.1 (lokaler Test-Pfad) + v1.24.2 (property-tests + safe_int/float) müssen geshipped sein. Beide ✅ done.

---

## Why v1.25.0 (and not v1.24.3 + v1.24.4 + v1.24.5)

The Audit identified four related-but-independent changes:

1. **Charging-Profile + Departure-Timer Write-Side bundle** (slipped 4×, user-visible)
2. **`cariad/_normalize.py`** (DRY for Kelvin↔Celsius + drivetrain + first_status_value)
3. **`BaseAPIClient` extract** (Porsche unter HTTP-machinery für retry/quota/storm-protection)
4. **`coordinator.py` Phase-1 refactor** (extract `CommandDispatcher`)

Bundling them into one MINOR makes sense because:
- Items 2-4 are pure refactor / infrastructure — they touch the SAME files that Item 1 touches
- Shipping Item 1 alone over the existing copy-pasted parsers would re-cement the DRY violations
- Shipping refactors first then write-side later doubles the test burden (every refactor needs a re-validation against the new write paths)
- Risk: bundling a refactor with a feature is the classic "where's the bug?" trap. **Mitigation:** ship in **four separate PRs** within v1.25.0 sprint, merge in the order **2 → 3 → 4 → 1** (refactors first, then feature on stable foundation). Branch protection ensures each PR gets its own CI gate.

---

## Sub-bundle Order + Per-PR Plan

### PR-A: `cariad/_normalize.py` foundation (sub-day, low risk)

**Files added:**
- `custom_components/vag_connect/cariad/_normalize.py` — pure-function module, no HA imports
- `tests/test_v1250_normalize.py` — property tests + parametrized fixture tests

**Functions to extract (with current site-of-truth):**

| Function | Replaces sites |
|---|---|
| `k_to_c(k: float \| None) → float \| None` | `vw_eu.py:880,884`, `seat_cupra.py:540,555`, `vw_na.py:176` (5 sites, all `round(x - 273.15, 1)`) |
| `c_to_k(c: float \| None) → float \| None` | `seat_cupra.py:831`, `vw_na.py:243` (write side — celsius input → kelvin payload) |
| `first_status_value(node: Any) → Any` | `vw_eu.py:906,912,918` (the `door.get("status",[{}])[0].get("value")` pattern, vererbt zu Audi) |
| `derive_drivetrain(has_battery: bool, has_combustion: bool) → tuple[bool, bool]` returns `(is_electric, is_hybrid)` | `skoda.py:603,604`, `vw_eu.py`, `seat_cupra.py`, `vw_na.py:176,177`, `porsche.py:96-98` (4 sites) |
| `derive_range_headline(electric_km, total_km, combustion_km, has_battery) → int \| None` | `skoda.py:589-598` (~10 lines), `vw_eu.py:865-870` (~6 lines) — same logic, slightly different fallback chain |

**Migration approach (mechanical):**
1. Add the new module + tests
2. Each migration site: add `from .._normalize import k_to_c, ...`, replace the inline expression with the helper call
3. **NO behavioral change** — every helper is a 1:1 extraction
4. Run full test suite + Bruno + ruff + mypy

**Test plan:**
- `tests/test_v1250_normalize.py` ~80 LOC:
  - Property: `k_to_c(k_to_c.inverse(c)) ≈ c` for all c ∈ [-50, 60]
  - Property: `c_to_k` always returns `≥ 0` for any input
  - Property: `derive_drivetrain` is exhaustive (4 input combinations)
  - Edge: None propagation, garbage strings (via safe_float chain)
  - Spot: `first_status_value({"status": [{"value": 42}]}) == 42`
  - Edge: `first_status_value({})` and `first_status_value(None)` → None

**Estimated time:** 3-4h
**Risk:** Low — pure functions, every site is mechanical replacement.
**CI gate:** ruff + mypy + property tests + existing brand-parser tests must all stay green.

---

### PR-B: `BaseAPIClient` extract for Porsche (1 day, medium risk)

**Goal:** Lift HTTP machinery (retry, rate-limit header capture, storm-protection, transient-error handling) out of `CariadBaseClient` into a new abstract `BaseAPIClient`. Make Porsche inherit from `BaseAPIClient` directly so it gets the v1.8.7 + v1.19.1 hardening it currently lacks.

**Files restructured:**
- New: `custom_components/vag_connect/cariad/api/_base_http.py` — abstract `BaseAPIClient`:
  - `async def _get(url, params=None, headers=None) → dict | list`
  - `async def _post(url, json=None, headers=None) → dict`
  - `async def _request(method, url, ...) → ...` (the workhorse with retry+backoff)
  - `_capture_rate_limit_headers(response)` (v1.19.1 quota tracking)
  - `_handle_5xx_retry(...)`, `_handle_429(...)` (v1.8.7 storm-protection)
  - `last_rate_limit_remaining`, `last_rate_limit_limit`, `last_rate_limit_reset_at` properties
  - **Auth handling stays brand-specific** — `BaseAPIClient` holds `_session: ClientSession` and a `_brand: BrandConfig` only. Auth (refresh, token-storm guard) lives in subclasses.

**Refactored:**
- `cariad/api/base.py` — `CariadBaseClient` now extends `BaseAPIClient`, keeps Cariad-specific token-refresh + IDK-aware retry. Diff should be: ~150 lines of HTTP machinery moved to `_base_http.py`, ~40 lines of Cariad-auth integration stay.
- `cariad/api/porsche.py` — `PorscheClient` extends `BaseAPIClient` (currently extends nothing). Removes ~80 LOC duplicated `_get`, `_post`, `_request` methods. Auth stays in PorscheClient since Porsche uses Auth0 + PPA differently from Cariad IDK.

**Test plan:**
- Existing tests in `test_cariad.py` for the Cariad chain: must stay green
- `test_v1242_porsche_vw_na_parity.py::TestPorscheParserHappy/Degraded`: must stay green (proves Porsche parser still works through new HTTP layer)
- New: `test_v1250_base_api_client.py` — tests `_capture_rate_limit_headers`, `_handle_429` retry-after, transient error retry. ~50 LOC.
- New: prove Porsche client now exposes `last_rate_limit_remaining` (was None before, can now be int).

**Estimated time:** 1 dev day (4-6h coding + 2h test verification)
**Risk:** Medium — HTTP layer change touches every brand. **Mitigation:** Cariad chain stays unchanged in behavior; only Porsche gets new capabilities. If Cariad breaks → revert just `_base_http.py` extract, keep PR-A.
**CI gate:** Full test suite + brand-parser tests + Bruno strict.

---

### PR-C: `coordinator.py` Phase-1 refactor (1-2 days, medium risk)

**Goal:** Extract `CommandDispatcher` from the 2549-LOC `coordinator.py`. Coordinator goes from ~2549 LOC + 70 methods to ~1700 LOC + ~40 methods. CommandDispatcher gets ~700-800 LOC + ~25 methods.

**Files restructured:**
- New: `custom_components/vag_connect/_command_dispatcher.py` — owns:
  - The 30+ command wrapper methods (`async_lock`, `async_unlock`, `async_start_climatisation`, etc. — currently lines ~1949-2549 of coordinator)
  - The per-VIN-per-command-class asyncio.Lock map (`_command_locks`)
  - The 5-min wake cooldown (`_wake_cooldown`)
  - The optimistic-update orchestration (rollback-on-failure pattern)
  - The CommandFailureReason classification dispatch (`record_command_failure`/`record_command_success`)
  - Holds a reference to the coordinator for capability lookups + write-back to feature_states + push-update triggers
- Modified: `coordinator.py` — slimmer. The command methods become thin proxies that forward to `self._dispatcher.lock(vin)`. (Or removed entirely if all callers are HA platforms — they call `coordinator.async_lock(vin)`, easy to find via grep.)

**Mechanical migration:**
1. Create `_command_dispatcher.py` with empty `CommandDispatcher` class
2. Move the lock/unlock/climate/charge/etc. methods one by one. Each move:
   - Cut from `coordinator.py`
   - Paste into `_command_dispatcher.py`
   - Replace `self.<thing>` references with either `self._coordinator.<thing>` or pass the value as a parameter
3. In `coordinator.__init__`: instantiate `self._dispatcher = CommandDispatcher(self)`
4. Add proxy methods on coordinator for backward compat (HA platforms expect `coordinator.async_lock(vin)`)
5. Test pass — every change must keep platform-side behavior identical

**Test plan:**
- All existing tests in `tests/test_v1XYZ_*.py` that touch command wrappers must stay green
- New: `tests/test_v1250_command_dispatcher.py` — unit-test the dispatcher in isolation:
  - Lock acquire/release per-VIN-per-command-class
  - Wake cooldown enforcement
  - Optimistic update + rollback on classified-failure
  - Capability gating (don't dispatch if `is_command_known_unsupported`)

**Estimated time:** 1-2 dev days (heavy test verification)
**Risk:** Medium — touches the most-used code path. **Mitigation:** keep the proxy methods; rollback = revert one file (`_command_dispatcher.py`) + restore old coordinator.py methods.
**CI gate:** Full test suite must pass with NO change in expected behavior.

---

### PR-D: Charging-Profile + Departure-Timer Write-Side Bundle (1 day, low-medium risk)

**Goal:** Ship the user-visible feature. Slipped 4× — Audit cited it 6 days ago, now finally lands on the stable refactor foundation.

#### Charging-Profile write side

**Brand support matrix** (read-side already shipped v1.16.0, write-side new):

| Brand | Read endpoint (existing) | Write endpoint (to add) |
|---|---|---|
| Skoda | `GET /api/v1/charging/{vin}/profiles` | `POST/PUT /api/v1/charging/{vin}/profiles/{profileId}` (per myskoda PR #647) |
| VW EU / Audi | not yet wired | `PUT /vehicle/v1/vehicles/{vin}/charging/profiles` (Cariad-BFF, per pycupra reference) |
| CUPRA / SEAT | not yet wired | `PUT /v1/vehicles/{vin}/charging/profiles` (OLA, per pycupra reference) |
| VW NA | `PUT /ev/v1/vehicle/{uuid}/charge/profile` | included |
| Porsche | not supported | n/a |

**API methods to add:**
- `cariad/api/skoda.py:command_update_charging_profile(vin, profile_id, **fields)`
- `cariad/api/vw_eu.py:command_update_charging_profile(vin, profile_id, **fields)`
- `cariad/api/seat_cupra.py:command_update_charging_profile(vin, profile_id, **fields)`
- `cariad/api/vw_na.py:command_update_charging_profile(vin, profile_id, **fields)`

**HA exposure:**
- New `select.py` entries for `select.<vin>_active_charging_profile` (writeable enum)
- New `number.py` entries for `number.<vin>_charging_profile_<id>_target_soc` (per profile, writeable 0-100)
- New service: `vag_connect.set_charging_profile` (vin + profile_id + fields)

#### Departure-Timer write side (closes the loop on v1.16.0 read side)

**Existing:** `command_set_departure_timer(vin, timer_id, enabled, departure_time)` already partially exists in `vw_eu.py:610` + `vw_na.py:258` + `porsche.py:205`. Skoda + SEAT/CUPRA missing.

**To add:**
- `cariad/api/skoda.py:command_set_departure_timer(vin, timer_id, enabled, departure_time)` — POST `/api/v1/air-conditioning/{vin}/timers/{timer_id}`
- `cariad/api/seat_cupra.py:command_set_departure_timer(vin, timer_id, enabled, departure_time)` — PUT `/v1/vehicles/{vin}/timers/{timer_id}`

**HA exposure:**
- Existing time-platform entries (`time.<vin>_departure_timer_X_time_set`) get write-back wired (currently read-only display)
- Existing switch entries (`switch.<vin>_departure_timer_X_enabled`) get write-back

#### Bruno fixtures

- `tests/bruno/skoda/29_PUT_charging_profile.bru`
- `tests/bruno/skoda/30_POST_departure_timer.bru`
- `tests/bruno/seat_cupra/37_PUT_charging_profile.bru`
- `tests/bruno/seat_cupra/38_PUT_departure_timer.bru`
- `tests/bruno/cariad_bff/22_PUT_charging_profile.bru`
- (vw_na has no Bruno coverage today, audit-flagged)

**Bruno coverage will jump 84/84 → 89/89 strict pass.**

**Test plan:**
- `tests/test_v1250_charging_profile_write.py` — per-brand happy + 401-spin-required + 503-retry. ~150 LOC
- `tests/test_v1250_departure_timer_write.py` — per-brand happy + read-back + invalid time format. ~100 LOC

**Estimated time:** 1 dev day
**Risk:** Low-medium — write-side commands need at least one live test from a maintainer-fleet vehicle to be confident. **Mitigation:** ship behind a `services.yaml` flag with EXPERIMENTAL marker for the first patch; remove on first community confirmation.
**CI gate:** Bruno strict 89/89 + per-brand parity tests + ruff + mypy.

---

## Cumulative v1.25.0 Sizing

| PR | Files added | Files modified | LOC delta | Tests added | Effort |
|---|---|---|---|---|---|
| PR-A `_normalize.py` | 2 | 4-5 brand modules | +120 / -80 = +40 | 10-12 | 3-4h |
| PR-B `BaseAPIClient` | 2 | base.py + porsche.py | +180 / -100 = +80 | 5-7 | 1d |
| PR-C `CommandDispatcher` | 2 | coordinator.py | +750 / -750 = 0 (extracted) | 8-10 | 1-2d |
| PR-D Write-Side bundle | 6 (Bruno) + 2 (tests) | 4 brand modules + select.py + number.py + time.py + switch.py | +400 / -50 | 15-20 | 1d |
| **Total v1.25.0** | **14** | **~13** | **+520** | **38-49** | **3-4 dev days** |

---

## Verification Strategy

Every PR must pass before next is opened. Sequence:

1. **PR-A** opens after v1.24.2 ships → Property tests + brand-parser tests stay green → merge
2. **PR-B** opens after PR-A merges → Cariad chain stays identical, Porsche gets new capabilities → merge
3. **PR-C** opens after PR-B merges → All command tests stay green, dispatcher unit tests pass → merge
4. **PR-D** opens after PR-C merges → Bruno 89/89, all write-side tests pass → merge

**Final v1.25.0 release** = manifest bump + CHANGELOG aggregation + git tag. After PR-D merge, one final tiny PR bumps manifest 1.24.2 → 1.25.0 + adds the v1.25.0 CHANGELOG header summarizing all 4 sub-bundles.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Coordinator refactor breaks live HA | Proxy methods kept; revert single file restores old behavior |
| Write-side commands need real-car test | EXPERIMENTAL marker; first patch (v1.25.1) confirms with maintainer-fleet then removes the marker |
| BaseAPIClient extract breaks Cariad timing | Cariad behavior must be byte-identical post-extract; if not, revert PR-B (PR-C+D can ship without PR-B's Porsche win) |
| New Bruno fixtures don't match real responses | Each `.bru` file is documentation-only at this stage; live verification deferred to v1.25.x patch |
| 4-PR sequence stalls if PR-A or PR-B fails | Each PR is independently mergeable. PR-D (the user-visible feature) can ship without PR-A/B/C if absolutely necessary, just with copy-pasted boilerplate that v1.26.x can clean up. |

---

## Out-of-Scope for v1.25.0 (deferred)

- **Coordinator Phase-2 refactor** (`CapabilityCache` + `EnrichmentService` extracts) → v1.26.x
- **All 6 untracked ROADMAP-Items** — separate housekeeping task
- **Push Phase 2 wire-in** — external-blocked (community testers)
- **MBB Phase 2** — external-blocked (maintainer-fleet wake live-test)
- **HomeRegion full wire-in** — external-blocked (#75 Christian region info)
- **`coordinator.py` god-class FULLY split** — PR-C is Phase 1 only

---

## After-v1.25.0 Roadmap Sketch

| Version | Title | Effort | Status |
|---|---|---|---|
| v1.25.x | Live-test confirmation + EXPERIMENTAL marker removal | 1-2h per brand | wait-on-tester |
| v1.26.0 | Coordinator Phase-2 refactor (CapabilityCache + Enrichment) | 3-4d | ready when v1.25.0 stable |
| v1.x | MBB Phase 2 (lock/climate/charger fallbacks) | 1d | wait-on-maintainer-fleet |
| v1.x | Push Phase 2 wire-in (per-brand patches) | 2-3d/brand | wait-on-community-tester |
| v2.0.0 | HACS Default + Live-Tests alle Marken + EU Data Act | weeks | September 2026 deadline |
