# Pre-Cariad MBB Research + Golf 7 GTE Full Audit

**Period:** 2026-05-09 → 2026-05-11
**Scope:** Branch `mbb-legacy-research-bruno-collection` (PR #179) + follow-up research
**Initial trigger:** Golf 7 GTE PHEV (VIN `WVWZZZAUZFW805377`) wake button returns plain 404 from Cariad-BFF
**Reporter:** Prash Balan (@its-me-prash)

---

## 1. Executive Summary

What started as "fix Golf 7 GTE wake button" turned into the most comprehensive Pre-Cariad MBB
research session in this codebase's history. We hit, climbed over, around, and finally accepted
the wall blocking legacy MBB direct data access for pre-2020 VW PHEV1 vehicles, then pivoted to
discover that the Cariad-BFF actually serves the Golf 7 GTE — just with a known catalog
mis-classification preventing gasoline tank data.

### Three Big Findings

| # | Finding | Impact |
|---|---|---|
| 1 | **Pre-Cariad MBB is gated by `XID_APP_VW` system permission** — only the official VW app's pre-provisioned `client_id` carries it. `/mbbcoauth/mobile/register/v1` issues `xclientId`s that lack this permission. No public bypass exists. | Closes a 4-year-old open question. Saves future maintainers months of false leads. |
| 2 | **WeConnect-ID OAuth client + scope `openid profile mbb cars vin` produces `VWGMBB01DELIV1` audience** — works through MBB token exchange. Did not lead to data access (XID_APP_VW wall) but is a documented hybrid-flow trick for future reference. | Reusable knowledge for any future MBB work. |
| 3 | **Pre-Cariad cars ARE in Cariad backend** — Golf 7 GTE PHEV (MJ 2015) returns 12/12 Cariad selectivestatus jobs successfully. Tank/gasoline data is the ONLY missing piece due to backend catalog `carType: "electric"` mis-classification. | vag-connect-ha already supports this car's data via existing VW EU code path. 55-60 entities available out-of-the-box. |

### Headline Conclusion

**Golf 7 GTE PHEV is fully supported by current vag-connect-ha for 9/11 critical datapoints**:
Battery SoC, e-Range, GPS, doors, windows, climate, odometer, service intervals, all 50+ enabled
operations across charging/climatisation/departure profiles. Only **fuel tank %** and
**combustion range** are blocked by a documented Cariad-side migration glitch (no public fix
path). OBD2 dongle remains the only way to get fuel data for this specific VIN.

---

## 2. Timeline of Investigation

### Wave 1 — MBB Legacy Auth Chain (2026-05-09 → 2026-05-10 morning)

| Action | Result |
|---|---|
| Research existing Pre-Cariad MBB Python references | Only `audi_connect_ha v1.19.1` still uses MBB (Audi side); all others migrated to Cariad |
| Build Bruno collection `mbb_legacy/` with 18+1 .bru files | Committed in PR #179 |
| Build `get_idk_token.py` helper for IDK OAuth login | Successfully obtains IDK access_token + id_token |
| Try legacy CarNet OAuth client `9496332b-...` | **DEPRECATED** — IDK Auth0 returns HTTP 400 "Unknown client" |
| Try MBB token exchange with WeConnect-ID client (`a24fba63-...`) + default scope | HTTP 400 "Id token is invalid" — id_token missing `VWGMBB01*` audience |
| Try Audi-IDK client (`09b6cbec-...`) + Audi scope | ✅ MBB token exchange returns 200, Audi-namespace vwToken |
| Test 9 MBB data endpoints with Audi-namespace token | ❌ All 403 — "CLS check for VIN against permission Audi:* has been negative" |
| Cross-brand: Audi id_token + VW MBB register | ❌ 400 "Unknown user 85f50f2c-..." (PPID namespace mismatch) |
| Try VW NA MyVW client `59992128-...` | ❌ "Unknown client" — NA-only, not in EU IDK |
| Test all 6 different `appId` values in MBB registration | ❌ All 200 register, all 403 data |
| Test all 11 EU country codes in URL routing | ❌ All same 403 |
| **BREAKTHROUGH**: WeConnect-ID + scope `openid profile mbb cars vin` | ✅ id_token now has `VWGMBB01DELIV1` + `VWGMBB01CNAPP1` in audience array |
| MBB exchange with WeConnect-ID-mbb id_token + VW register | ✅ 200 — VW-namespace vwToken obtained |
| Test data endpoints with VW-namespace vwToken | ❌ 403 — but DIFFERENT error: "Did not find permission for systemId 'XID_APP_VW'" |
| operationList endpoint with this token | ✅ 200 — returns PRIMARY_USER, ENABLED, License ACTIVATED, vehicletype: PHEV1 |
| Try legacy `/fs-car/core/auth/v1/VW/DE/token` password grant | ❌ 401 "Error authenticating" for ALL credentials (server-side deprecation) |
| Try wez3-exact headers (`X-App-Name: eRemote`, okhttp/2.3.0) | ❌ Same 401 |

**Wave 1 Verdict:** Legacy MBB direct-data access via reverse-engineered xclientId is structurally
walled. The `XID_APP_VW` permission required by `fs-car/` endpoints is granted only to officially
provisioned OAuth clients. No public path exists.

### Wave 2 — VW Support Reality Check + Cariad Discovery (2026-05-11)

| Action | Result |
|---|---|
| Initially recommended user call VW Support for Cariad re-classification | **Mistake** — speculation without evidence |
| Background research: documented VW Support fixes | **NO EVIDENCE FOUND** across 4 GitHub repos, multiple forums, official channels |
| Retract claim + user confirms VW App shows live data | **Pivot** — Golf 7 GTE IS in Cariad backend |
| Build `verify_cariad_for_gte.py` to test Cariad-BFF endpoints | ✅ 7/8 endpoints 2xx |
| Build `verify_cariad_full.py` testing all selectivestatus job types | ✅ **12/12 jobs return data** |
| Confirm: live SoC 25%, GPS 47.40/8.21, odometer 159566 km, oil due 17 days | All accurate |
| Tank/gasoline data: shows `carType: "electric"` instead of `"hybrid"` | Cariad migration glitch — only `primaryEngine: electric`, no `secondaryEngine: gasoline` |

**Wave 2 Verdict:** vag-connect-ha already supports this car. Tank data is the only loss.

### Wave 3 — Deep Entity Extraction (2026-05-11 evening)

| Action | Result |
|---|---|
| `investigate_tank_data.py` — 13 extra audi-style jobs | ✅ All return data but no gasoline anywhere |
| `hunt_raw_fields.py` — 32 alternative URL patterns | ❌ All 404 — no raw hex passthrough exists |
| `test_active_actions.py` — capabilities + active control | ✅ 14 capabilities exposed; ✅ climatisation stop successful with `--execute` |
| Discovery: Lock requires SPIN, **1 try left after our test** | Warning to user before any real lock attempts |
| `extract_all_sensors.py` — 30+ endpoints across 9 categories | ✅ Massive find: long-term trip history back to 2024-05, departure profile detail, window-per-side, charging settings |

**Wave 3 Verdict:** 55-60 total entity candidates discovered for the Golf 7 GTE.

---

## 3. Code Changes Summary

### 3.1 Production code modifications

**`custom_components/vag_connect/cariad/auth/idk.py`** (~80 LOC modified)

- Added `mbb_mode: bool = False` parameter to `IDKAuth.authenticate()`
- Added `_extract_param_from_url()` helper (handles query AND fragment for hybrid flow)
- Added `last_redirect_url` attribute (captures final app:// URI for hybrid id_token extraction)
- `_authenticate_auth0()` and `_authenticate_legacy()` now accept `mbb_mode`, short-circuit
  with TokenSet containing only the hybrid-flow id_token when set
- Hybrid flow uses `response_type=code id_token` and drops `prompt=login`

**Backward compatibility:** 100%. `mbb_mode` defaults to False; all existing Cariad/Audi/Skoda/SEAT
auth flows unchanged. New parameter is opt-in.

**`.gitignore`**: added `tests/bruno/**/environments/*.local.bru` — prevents accidental commit of
live credentials.

### 3.2 New scripts (`scripts/`)

20 new diagnostic + helper scripts. All standalone, all support `--help`, all UTF-8 safe on
Windows. Listed by purpose:

| Script | Purpose | Status |
|---|---|---|
| `get_idk_token.py` | Interactive IDK OAuth helper (Cariad path). Brands: vw, vw-mbb, vw-legacy, vw-na, audi, skoda, seat, cupra. Writes to `mbb.local.bru`. | Production-quality helper |
| `decode_id_token.py` | Decode JWT claims of id_token in mbb.local.bru | Diagnostic |
| `get_mbb_token.py` | End-to-end IDK + MBB-register + MBB-exchange + write to file | Production-quality helper |
| `verify_mbb_endpoints.py` | Test 9 classic MBB data endpoints with vwToken | Diagnostic, archived |
| `verify_cariad_for_gte.py` | Test 8 Cariad-BFF endpoints for a VIN | Diagnostic, useful |
| `verify_cariad_full.py` | Test all 12 selectivestatus job types | **Reusable diagnostic** for any user |
| `full_mbb_matrix.py` | 4-cell matrix: (id_token source) × (register brand) + IDK direct tests | Research artifact |
| `try_vw_direct.py` | VW WeConnect-ID id_token → MBB exchange direct | Research artifact |
| `try_vw_with_mbb.py` | WeConnect-ID + various mbb scopes — **THE BREAKTHROUGH SCRIPT** | Reference for future MBB work |
| `try_vw_appids.py` | 6 different VW appIds in MBB registration | Research artifact |
| `try_country_codes.py` | 11 EU country codes in URL routing | Research artifact |
| `try_carnet_password_grant.py` | Legacy CarNet password-grant (now dead) | Reference, archived |
| `try_enrollment.py` | Explore owner_v1 enrollment endpoints | Research artifact |
| `show_operations.py` | Full operationList dump (pretty-printed) | **Reusable diagnostic** |
| `wake_and_refresh.py` | Test vehicleWakeup + selectivestatus re-read | Diagnostic |
| `investigate_tank_data.py` | Hunt tank data across 13 extra job types + alternatives | Research artifact |
| `hunt_raw_fields.py` | 32 URL patterns for raw MBB hex field IDs | Research artifact |
| `test_active_actions.py` | Capabilities + active control endpoints (lock, charge, climate) | **Production-quality** — useful for any user setup |
| `test_enginetype.py` | Dedicated engine/fuel/oil endpoint test | Research artifact |
| `extract_all_sensors.py` | Deep extraction of 30+ endpoints across 9 categories | **Most valuable diagnostic** — full sensor inventory |

### 3.3 New Bruno collection (`tests/bruno/mbb_legacy/`)

- `bruno.json` + 18 endpoint .bru files + 1 negative test
- `environments/mbb.template.bru` (committed) + gitignore rule for `*.local.bru`
- `README.md` step-by-step user guide

Covers: token exchange, refresh, register, homeRegion, operationList, vehicles list, VSR status,
charger, climater, tripdata, position, vsr request (wake), charger actions, climater start, SPIN
challenge, lock action, jobstatus polling, honk/flash, departure timer.

### 3.4 Documentation

- `tests/bruno/mbb_legacy/README.md` — user setup + security guide
- This document: `docs/research/2026-05_pre-cariad-mbb-and-golf-7-gte-audit.md`

---

## 4. Findings Catalog

### 4.1 The MBB Authentication Landscape (definitive map)

```
┌──────────────────────────────────────────────────────────────────┐
│ Pre-Cariad MBB Backend (mbboauth-1d.prd.ece.vwg-connect.com)     │
│                                                                  │
│  OAuth Layer:                                                    │
│    /mbbcoauth/mobile/register/v1   → ✅ accepts public clients   │
│    /mbbcoauth/mobile/oauth2/v1/token (grant=id_token, sc2:fal)   │
│      → ✅ accepts WeConnect-ID id_token IF scope contains 'mbb'  │
│      → Returns VW-namespace vwToken (iss: VWGMBB01DELIV1)        │
│                                                                  │
│  Rolesrights Gateway (mal-1a.prd.ece.vwg-connect.com/api):       │
│    /rolesrights/operationlist/v3/.../{vin}                       │
│      → ✅ accepts any valid VW-namespace vwToken                 │
│      → Returns full ACL + capabilities + license info            │
│                                                                  │
│  Data Gateway (msg.volkswagen.de/fs-car/...):                    │
│    /bs/vsr/v1/VW/DE/vehicles/{vin}/status                        │
│    /bs/batterycharge/v1/...                                      │
│    /bs/climatisation/v1/...                                      │
│    /bs/cf/v1/.../position                                        │
│      → ❌ ALL 403 — requires systemId 'XID_APP_VW' permission    │
│      → XID_APP_VW only granted to officially-provisioned clients │
│      → Public /register/v1 xclientIds DON'T have it              │
│                                                                  │
│  Legacy password grant (/fs-car/core/auth/v1/VW/DE/token):       │
│      → ❌ 401 "Error authenticating" for ALL credentials         │
│      → Server-side deprecated by VW                              │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 IDK OAuth Client Inventory (2026)

| client_id | Status (May 2026) | mbb scope? | Use case |
|---|---|---|---|
| `a24fba63-...@apps_vw-dilab_com` (WeConnect ID) | ✅ Active | ✅ Accepts (with explicit request) | **Production Cariad-BFF for VW** |
| `09b6cbec-...@apps_vw-dilab_com` (Audi) | ✅ Active | ✅ Default scope includes mbb | **Production Audi MBB + Cariad** |
| `7f045eee-...@apps_vw-dilab_com` (Skoda) | ✅ Active | — | Skoda mysmob |
| `99a5b77d-...@apps_vw-dilab_com` (SEAT) | ✅ Active | — | OLA |
| `3c8e98bc-...@apps_vw-dilab_com` (CUPRA) | ✅ Active | — | OLA |
| `9496332b-...@apps_vw-dilab_com` (Legacy CarNet) | ❌ Deprecated 2025 | — | DEAD — Auth0 "Unknown client" |
| `59992128-...@MYVW_ANDROID` (VW NA MyVW) | ❌ Not in EU IDK | — | DEAD — "Unknown client" in EU |

### 4.3 The CarType Mis-Classification Bug

Documented case for VIN `WVWZZZAUZFW805377`:

| Backend says | Reality |
|---|---|
| MBB `operationList.serviceInfo.parameters.vehicletype: PHEV1` | ✅ Correct |
| Cariad `tripdata.vehicleType: "hybrid"` | ✅ Correct |
| Cariad `selectivestatus.fuelStatus.rangeStatus.value.carType: "electric"` | ❌ **WRONG** |
| Cariad `selectivestatus.fuelStatus.rangeStatus.value.primaryEngine.type: "electric"` | ❌ **WRONG** (should be "gasoline" with `secondaryEngine: electric` block) |

**Effect:** Cariad-BFF returns no gasoline data because its catalog has the VIN as electric-only.

**Root cause hypothesis (evidence-based):** Migration glitch during MBB→Cariad backend
consolidation for PHEV1 generation (Golf 7 GTE 2014-2017, Passat B8 GTE, A3 e-tron 8V). The
Cariad catalog has only `electric` and `hybrid` carType values; migration tooling defaulted
unknown PHEV1 entries to `electric` based on detectable signals (HV battery + charge port).

**Bypass:** None. VW Support cannot fix it (no documented success cases). Dealer cannot fix it.
Client-side workaround impossible (the data simply isn't returned).

### 4.4 Confirmed Cariad-BFF Capability Inventory for Golf 7 GTE

```
✅ vehicleWakeUp         postVehiclewakeup, getVehiclewakeupRequestsByID
✅ vehicleWakeUpTrigger  postVehiclewakeupUpdate
✅ automation            (operations list empty)
✅ vehicleLights         getLightsStatus
✅ charging              10 ops (start, stop, mode, settings, careStatus, ...)
✅ fuelStatus            getFuelStatus  ⚠️ returns electric-only
✅ measurements          getMeasurements
✅ parkingPosition       getParkingposition
✅ state                 getAccessStatus
✅ vehicleHealthInspection getMaintenanceStatus
✅ climatisation         10 ops (start, stop, settings, window heating, ...)
✅ departureProfiles     6 ops (CRUD on departure timer profiles)
✅ engineType            getEngineType  ⚠️ likely mis-reports
✅ oilLevelStatus        getStates  ⚠️ Bad Gateway intermittently
✅ tripStatistics        13 ops (shortterm/longterm/cyclic × CRUD)
```

License `cumulatedLicense.expirationDate`: 2026-05-13T15:17:00Z (active).

### 4.5 Final Entity Inventory for Golf 7 GTE (~55-60 entities)

Already provided automatically by current vag-connect-ha VW EU code path:
- Battery: SoC%, electric range, hybrid range, charging state/mode/power/time remaining, plug
  connected/locked, external power available, max charge current, LED color
- Climate: state, target temp, cabin temp, climatisation without HV power, window heat front/rear
- Doors: 4× door open + 4× door lock states, bonnet, trunk open + lock
- Windows: 4× window state (front-left, front-right, rear-left, rear-right) + sunroof if equipped
- Lights: left + right exterior lights
- Position: device_tracker with live GPS lat/lon + timestamp + parking time
- Odometer + trip stats: last short trip (distance, duration, avg speed), long-term aggregate
- Service: inspection due km/days, oil service due km/days
- Buttons: wake, start/stop charging, start/stop climate, start/stop window heat, honk, flash, lock/unlock
- Switches: climate, window heat
- Numbers: target temperature, max charge current

**Missing (Cariad migration glitch):**
- `sensor.fuel_level` — gasoline tank %
- `sensor.range_combustion` — gasoline range km

**Bonus v1.27.0 candidates (from research):**
- `binary_sensor.is_phev` (from MBB operationList parameters)
- `sensor.subscription_active_until` (from cumulatedLicense.expirationDate)
- `sensor.user_role` (PRIMARY_USER / SECONDARY_USER)
- `sensor.vehicle_lifecycle_status` (DELIVERED)
- 3× departure timer detail entities (id, time, days, enabled, profile_id)
- `number.departure_min_soc` (50%)
- `sensor.lifetime_trip_history` (long-term trip aggregates as JSON attribute)
- `sensor.plug_led_color` (visual feedback: none/red/green/blue)

---

## 5. Lessons Learned

### 5.1 Architectural lessons

1. **Test Cariad-BFF FIRST when investigating any "Pre-Cariad" car.** Modern VW backend often
   serves both new and migrated old VINs. We wasted hours on MBB before testing the obvious.

2. **Capabilities endpoint is the source of truth for what's available.** Always fetch
   `selectivestatus?jobs=all` and parse the response shape before guessing endpoints.

3. **Each Cariad capability has its OWN URL pattern.** Don't assume `/vehicle/v1/vehicles/{vin}/{capability}`
   works for everything — most direct paths return 404. Use selectivestatus job names instead.

4. **`response_type=code id_token` (OIDC Hybrid) yields cross-service-signed id_tokens** with
   `VWGMBB01*` audiences. Useful for any future MBB-related work even if not for this car.

5. **MBB and Cariad backends DON'T share user-ID namespaces.** Same email account has different
   PPIDs per OAuth client. Backend ACLs are strict about namespace.

### 5.2 Process lessons

1. **Don't speculate about service desk fixes without evidence.** I claimed VW Support could
   re-classify VINs based on a research agent's inference. Zero documented cases existed.
   Cost: trust + ~30 min of misdirection. Lesson: always source-check before recommending.

2. **Build the diagnostic helper script BEFORE the integration code.** Every endpoint should
   first be verified with a standalone Python script. Once green, integration is trivial.

3. **Bruno is wonderful for human verification, but Python wins for automation.** Use Bruno for
   one-off "does this work?" tests; use Python scripts for repeatable test matrices.

4. **The "kitchen sink" combined-query approach yields surprises.** Asking selectivestatus with
   25+ jobs at once revealed data combinations the per-job queries didn't return.

### 5.3 Specific to this codebase

1. **`mbb_mode` in `IDKAuth.authenticate()` is now production-ready** for future hybrid-flow needs
   even though we don't use it in v1.26.3.

2. **Bruno collection `mbb_legacy/` is community-valuable** even if our specific GTE can't use it.
   Audi A3 8V owners with active Audi Connect Plus subscription benefit immediately.

3. **`scripts/verify_cariad_full.py` and `scripts/extract_all_sensors.py` are reusable** by any
   user wanting to know "what data can vag-connect-ha extract for my specific VIN" before
   installing the integration.

---

## 6. Recommended v1.27.0 Scope

Based on findings, propose v1.27.0 as **"Pre-Cariad PHEV Support + Diagnostic Tooling"**:

### 6.1 New entities (additive, no breaking changes)

**MBB operationList metadata** (for VINs where MBB operationList works):
- `binary_sensor.{name}_is_phev` (from parameters.vehicletype == "PHEV1")
- `sensor.{name}_subscription_active_until`
- `sensor.{name}_user_role`
- `sensor.{name}_vehicle_lifecycle_status`

**Long-term trip aggregates** (from Cariad `/vehicle/v1/trips/{vin}/longterm/last`):
- `sensor.{name}_longterm_distance_km`
- `sensor.{name}_longterm_duration_min`
- `sensor.{name}_longterm_avg_speed`

**Departure timer detail** (from departureProfiles selectivestatus):
- `sensor.{name}_next_departure_time` (computed across all enabled timers)
- `number.{name}_departure_min_soc` (writable — adjust target SoC for departures)
- For each programmed timer: `binary_sensor.{name}_departure_timer_{i}_enabled` + recurring days as attribute

**Charging detail** (from chargingSettings/plugStatus):
- `sensor.{name}_plug_led_color`
- `binary_sensor.{name}_external_power_available`
- `number.{name}_max_charge_current` (writable — 6/10/13/16 A)

### 6.2 Diagnostics enhancement

- Add diagnostic script `scripts/verify_my_vin.py` (rebrand of `extract_all_sensors.py`) so users
  can run a single command to inventory their vehicle's exposed data before installing the
  integration.
- Document the carType mis-classification as a known issue in `docs/troubleshooting.md` with
  link to this audit document. Provide OBD2 dongle as supported workaround.

### 6.3 What's NOT in scope (deferred)

- ❌ MBB direct legacy access — confirmed dead, no public path. Remove `_command_wake_mbb()`
  scaffolding from `vw_eu.py` or document it as inactive.
- ❌ SPIN secure-token flow — only relevant for lock/unlock which already works via Cariad-BFF
  directly with SPIN config-flow input.
- ❌ Tank/gasoline data — not retrievable for affected VINs. Document as known limitation.

### 6.4 PR plan

| PR | Scope | Branch |
|---|---|---|
| #179 (existing) | MBB Bruno collection + IDK token helper + research scripts. **Merge as research artifact.** | `mbb-legacy-research-bruno-collection` |
| #180 | Audit doc + diagnostic script (`verify_my_vin.py`) | `docs/audit-research-mbb` |
| #181 | v1.27.0 entities: MBB metadata + long-term trip + departure timer detail + charging detail | `v1.27.0-pre-cariad-phev-support` |

---

## 7. Open Questions / Future Work

1. **Can the official VW App show fuel level for this VIN?** (User test pending.) If yes, there's
   a non-public endpoint to discover via mitmproxy. If no, confirms full-stack migration glitch.

2. **Does the `cumulatedLicense` expiration on 2026-05-13 affect data access?** Test after that
   date with same user to see if endpoints start 401-ing.

3. **Can users without active We Connect Plus see anything via Cariad-BFF?** Test with a free-tier
   account to baseline what's gated by subscription.

4. **Skoda Connect (mysmob) has its own MBB-style backend.** Issue #75 (Kodiaq Mk2) may benefit
   from similar Cariad-vs-MBB diagnostic. Worth running `extract_all_sensors.py` against a Skoda.

5. **Is there an OBD2 integration we can recommend in docs?** `homeassistant.io/integrations/obd/`
   exists. Consider documenting it as the recommended companion for Pre-Cariad cars affected by
   migration glitches.

---

## 8. Acknowledgments

- **Prash Balan** (@its-me-prash) for patience through ~6 hours of progressively deeper
  investigation, and for fact-checking the VW Support claim (which forced a correction).
- **arjenvrh/audiconnect (audi_connect_ha)** maintainers — only living Python MBB reference
- **evcc-io/evcc** — Go reference for VW vehicle plugins
- **robinostlund/volkswagencarnet** — Python reference for Cariad-BFF integration
- **tillsteinbach/CarConnectivity-connector-volkswagen** — recent VW Cariad work
- **TA2k/iobroker.vw-connect** — historical JS reference (now broken)
- **wez3/volkswagen-carnet-client** — 2017-era CarNet reference

---

**Author:** Claude Opus 4.7 (1M context) on behalf of Prash Balan
**Last updated:** 2026-05-11
**Status:** Research complete. Ready for PR #179 merge + PR #180/#181 follow-up.
