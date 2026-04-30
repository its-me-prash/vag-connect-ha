# VAG Connect — Roadmap

> Single canonical source of truth for sessions, versions and issue mapping.
> The README ships an identical short version in 8 languages; this file
> mirrors it for archive/historical purposes and links the active GitHub
> issues for each session.

**Last updated:** 2026-04-30 — post v1.11.0 (Issue #91 Closure: Light
Status, Service Days, Max Charge Current als echte Entitäten)

---

## Where to follow progress

- **Issues:** https://github.com/its-me-prash/vag-connect-ha/issues
- **PRs:** https://github.com/its-me-prash/vag-connect-ha/pulls
- **Releases:** https://github.com/its-me-prash/vag-connect-ha/releases
- **Live document for AI tools:** [`docs/SESSION_HANDOFF.md`](SESSION_HANDOFF.md)
- **Verified API facts archive:** [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md)

---

## Achieved (v1.0 → v1.8.12)

| Version | Content | Date |
|---|---|---|
| v1.0 – v1.5 | 9 platforms, 7 brands, bug fixes, entity audit | 2026-04 (early) |
| v1.6.0 | SEAT/CUPRA 9 endpoints, Škoda fix, Audi PPC, lock platform, nightly polling reduction | 2026-04-24 |
| v1.7.0 | Complete Škoda rewrite, car-friendly translations all 8 languages, reliability (rate-limit backoff, token-refresh lock, stale-data tracking) | 2026-04-25 |
| v1.8.0 | **Foundation Fix** — 7 P0 release blockers (#60); per-VIN availability; S-PIN fail-fast; reverse-geocoding opt-in | 2026-04-26 |
| v1.8.1 | Privacy & auth polish — VIN masking; ConfigEntryAuthFailed wiring | 2026-04-27 |
| v1.8.2 | **Session 2A** — error taxonomy + 3-state feature model + capabilities cache (#68) | 2026-04-27 |
| v1.8.3 | **Session 2B** — capability gating SEAT/CUPRA flash + wake | 2026-04-27 |
| v1.8.4 | **Session 2C** — SEAT/CUPRA SecToken lock fix (#53, #68) | 2026-04-27 |
| v1.8.5 | **Session 3A** — Command Profile foundation + v1/v2 fallback for 4 set-value commands (#51, #61, #74) | 2026-04-27 |
| **v1.8.6** | **Docs Truthfulness** — README + 8 translations + Multi-Brand-Successor positioning + dynamic CI badge | **2026-04-29** |
| **v1.8.7** | **Defensive Programming Pass** — 504 retry, transient-error retry, refresh storm guard, 3-failure tolerance, 6h stale-cache (12 new tests) | **2026-04-29** |
| **v1.8.8** | **Session 3B** — CARIAD v1/v2 + combined/separate dispatch for lock/unlock/climate/charging start+stop (4 new tests) | **2026-04-29** |
| **v1.8.9** | **Session 3C** — CUPRA OLA status JSON paths fix (Gerhard's 19 entities) + Live-API findings from CC-seatcupra #5/#8/#18/#21/#50/#51/#109 (12 new tests) | **2026-04-29** |
| **v1.8.10** | Hotfix — legacy CARIAD-flat doors fallback inversion (1-line) | **2026-04-29** |
| **v1.8.11** | **Session 3S** — Škoda `carCapturedTimestamp` connection-state + `detail` block + `reliableLockStatus` + `fullyChargedAt` from CC-skoda #50 Live-Dump (10 new tests, closes #54) | **2026-04-29** |
| **v1.8.12** | **MVP-Move** — Multi-Brand connection-state (Skoda + CUPRA + SEAT + VW EU + Audi via inheritance). Brand-agnostic helper `compute_connection_state` with recursive timestamp walk. Verified via volkswagencarnet #921 ID.4 2025 Live-Dump (12 new tests) | **2026-04-29** |
| **v1.9.0** | 🔬 **Vehicle Data Scout + Error Reporter** — 2 neue Diagnostik-Sensoren mit gemeinsamer 1-Klick Reporter Pipeline. Brand-localized in 8 Sprachen. HA Repair-Issues mit pre-filled GitHub-URL + Diagnostics-Export für Facebook/Forum-Community. Privacy: VIN/GPS/JWT/UUID/Email maskiert, NIE Auto-Push. Aktiv für Skoda + SEAT + CUPRA + VW EU + Audi (18 neue Tests) | **2026-04-29** |
| **v1.9.1** | 🔧 **Audi/VW Lock+Wake Hotfix + Capability-Filter Phase 2** — Issue #92: `command_lock` schickt jetzt S-PIN für Audi/VW (CARIAD BFF antwortete `403 spin_error`); `command_wake` nutzt v1→v2 Fallback. Issues #90+#91: 27 Vehicle Data Scout Findings vom Maintainer registriert (`dieselRange`, `currentFuelLevel_pct`, `maxChargeCurrentAC_A`, `userCapabilities`, `fuelStatus`, `vehicleHealthInspection`, `vehicleHealthWarnings`, `automation`, `departureProfiles`, etc.). Issue #56: Capability-Filter Phase 2 — `classify_command_failure` mit Body-Sniffing (spin_error/subscription/not_entitled), `_cariad_cmd` schreibt jedes Command-Ergebnis in FeatureState, command-bound Entities (Lock/Climate/Switch/Buttons) gehen automatisch unavailable bei definitivem Backend-No. (18 neue Tests) | **2026-04-29** |
| **v1.10.0** | 🔋⛽ **PHEV-Range-Triple + Audi-Diesel-Range** — Issue #94 + Scout-Entity-Implementierung aus #91: drei neue Sensoren `electric_range_km` / `combustion_range_km` / `total_range_km`. VW EU/Audi Parser klassifiziert nach Engine-Typ (nicht Position) aus `fuelStatus.rangeStatus.value.{primary,secondary}Engine`. Audi S6 C8 2021 Diesel-Fallback aus `measurements.rangeStatus.value.dieselRange`. Skoda mysmob `electricRange.distanceInKm` + `combustionRange.distanceInKm` + `totalRangeInKm`. Phantom-Entity-Schutz via `_DATA_PRESENT_REQUIRED` — keine "unknown"-Sensoren auf reinen EVs/ICEs. 8 Sprachen. (13 neue Tests) | **2026-04-29** |
| **v1.10.1** | 🛡️ **Defensive Coding Phase 2** — Issue #58: drei neue Helfer (`safe_int` / `safe_float` / `safe_enum`) in `cariad/_util.py`, NIE-raises Vertrag. An die heißesten Parsing-Stellen angewendet (Skoda `remainingTimeToFullyChargedInMinutes` als String "12.5", VW EU `maxChargeCurrentAC_A` als Enum "MAXIMUM", `model_year` int/string interop). Coordinator wrapped `to_dict()+_enrich()` per VIN in eigenes try/except — Parse-Failure landet in v1.9.0 Error Reporter Ring-Buffer statt Vehicle komplett unavailable zu machen. Forward-Kompatibilität: `safe_enum` loggt unbekannte Werte (myskoda #503 `CHARGING_INTERRUPTED` Pattern) statt zu crashen. (16 neue Tests) | **2026-04-30** |
| **v1.10.2** | 🚗 **CUPRA Born 2026 Firmware-Shapes** — Issue #53 Live-Test (Gerhard, 2026-04-30): Vehicle Data Scout meldete 19 neue Felder. Beim Audit zeigte sich: viele sind **umbenannte** Versionen unserer bekannten Felder (`battery.currentSocPercentage` statt `currentSOC_pct`, `plug.connection`/`plug.lock` kurz statt lang, lowercase enums). `seat_cupra.py` Parser liest jetzt alle drei Field-Namen-Varianten als Fallback-Kette + lowercase enum tolerance. Plus neue Born-2026-Felder genutzt: `battery.estimatedRangeInKm` als range fallback, `status.locked` + `status.hood.locked` als top-level overall fallback. **Erste echte Live-Validation der v1.9.0 Reporter Pipeline (~12h Bug-Report → Hotfix).** (16 neue Tests) | **2026-04-30** |
| **v1.11.0** | 🔆🔧 **Issue #91 Closure: Light-Status, Service-Days, Max-Charge-Current** — fünf neue Entitäten schließen Issue #91 vollständig: `lights_on` Binary-Sensor (any-light-on Aggregate), `lights_count` Sensor, `service_due_in_days` + `oil_service_due_in_days` als raw int Sensoren (komplementär zu den DATE-Sensoren), `max_charge_current_a` als Ampere-Sensor (read-only). Defensive Light-Parsing handhabt 3 bekannte Element-Shapes + Aggregate-Fallback bei unbekannter Shape. `_DATA_PRESENT_REQUIRED` Pattern jetzt auch in binary_sensor.py. 8 Sprachen. (15 neue Tests) | **2026-04-30** |

**Sprint summary 2026-04-29:** 7 releases, ~50 new tests, branch
protection activated, CHANGELOG split into human + technical, 4 parallel
research agents producing the verified-source archive in
`docs/RESEARCH_NOTES_2026-04-29.md`.

---

## Session plan (next sessions, P0 → P1 → P2)

Strict order. The v1.8.6–v1.8.12 sprint already moved most of the
non-negotiable Foundation work; remaining sessions can now pick by
priority.

| Session | Version | Scope | Issues |
|---|---|---|---|
| ~~**Vehicle Data Scout + Error Reporter**~~ | ~~**v1.9.0**~~ ✅ | ✅ Geshipped 2026-04-29 — siehe Achievement-Tabelle oben. | done |
| ~~**Capability-Filter Phase 2**~~ | ~~**v1.9.1**~~ ✅ | ✅ Geshipped 2026-04-29. | done |
| ~~**PHEV-Range-Triple + Audi-Diesel-Range**~~ | ~~**v1.10.0**~~ ✅ | ✅ Geshipped 2026-04-29. Issue #94 + erste echte Scout-Entity-Implementierung aus #91 (Audi `dieselRange`). | done |
| ~~**Defensive Coding Phase 2**~~ | ~~**v1.10.1**~~ ✅ | ✅ Geshipped 2026-04-30. `safe_int`/`safe_float`/`safe_enum` Helfer + Coordinator Parse-Guard. | done |
| ~~**CUPRA Born 2026 Firmware-Shapes**~~ | ~~**v1.10.2**~~ ✅ | ✅ Geshipped 2026-04-30. Erste Live-Validation der Reporter Pipeline. | done |
| ~~**Issue #91 Closure**~~ | ~~**v1.11.0**~~ ✅ | ✅ Geshipped 2026-04-30. `lights_on`/`lights_count`/`service_due_in_days`/`oil_service_due_in_days`/`max_charge_current_a`. | done |
| ~~**Welle 2 Scout-Entitäten**~~ | ~~**v1.11.0**~~ ✅ | ✅ Geshipped 2026-04-30 als #91 Closure. `lights_on/_count`, `*_due_in_days`, `max_charge_current_a` (read-only). Writeable Number + per-Light Entities verschoben auf v1.12.0. | done |
| **3B-Part-3 — Optimistic Lock/Climate** | v1.10.x | myskoda #832 pattern. PATCH. | — |
| **Diagnostics + Smart-Wake + 12V protection** | **v1.12.0** ⭐ | MINOR: Anonymized diagnostics export (CC-seatcupra #109, CC-skoda #50, volkswagencarnet #921 als Fixtures), Read-only Mode, persistent wake counter (max 3/day), `wake_count_today` sensor, **NIE auto-wake**. Plus 12V drain detection (volkswagencarnet #940) — extend stale-cache to 24-72h when 12V low. Plus Capability-Filter Phase 3 (`capability.active && capability.user-enabled` pre-Entity-Creation). | #62, #63, #55, #23 |
| **Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide. Doc-only. | #64 |
| **Push CUPRA/SEAT + Push Škoda** | v1.10.x | Firebase FCM via `mqtt.messagehub.de` (CUPRA/SEAT) + mysmob MQTT broker (Škoda-only — myskoda PR #566). PATCH each. | #57, #27 |
| **Trip Stats + Image refactor** | **v1.11.0** ⭐ | MINOR: Audi `tripstatistics/v1` (verified `audi_services.py:337`); per-trip data model (numeric aggregate in state, JSON in attrs per audi #113); image platform → user-supplied URL or removal. | #24, #35, #36 |
| **HACS Default + v2.0.0** | **v2.0.0** 🎉 | MAJOR: Live tests all brands, compatibility matrix, EU Data Act ready (pycupra `EUDAConnection` ready to port). | #13, #59 |

### Standalone enhancements (no version pin yet)

- **Diesel AdBlue Range** for Škoda (CC-skoda #24): field `adblue_range_km`
  exists in `models.py` but Skoda parser doesn't read it from
  `driving-range` endpoint. Small targeted session.
- **`/v2/widgets/vehicle-status/{vin}`** as lightweight Skoda endpoint
  (myskoda PR #557): for battery-friendly polling. Pairs well with Session 6.
- **Region-routing** `_get_cariad_url(region)` for US users (volkswagencarnet
  PRs #648/#676): hardcoded `emea.` breaks US-based VW EU users.
- **TermsAndConditionsError repair issue** (volkswagencarnet PR #307):
  HA `ir.async_create_issue` with deeplink to vehicle-account login portal
  when 401 with `terms_of_use` body is detected.
- **ICE Engine Start S-PIN flow** (audi_connect_ha PR #717): two-step
  PUT `/engine/{VIN}/userpromptproof` then POST `/engine/{VIN}/start`.
  ICE-only feature, capability-gated.
- **PPE Climate Body** (audi_connect_ha PR #644 + #677): `climatisationMode:
  "comfort"` mandatory, `targetTemperature*` must be omitted for PPE
  (Q6 e-tron, A6 e-tron, etc.). Conditional body shape.

---

## What will not be implemented

| Brand / feature | Reason |
|---|---|
| VW China (2026+) | CEA/XPeng platform — undocumented, near-zero HA user base |
| Lamborghini commands | No verified public API. Research only — see `research/LUXURY_BRANDS.md` |
| Bentley commands | No verified public API. Research only |
| Bugatti | Fleet too small, no API surfaced |
| Ducati | Motorcycles — out of scope |
| MAN / Scania | Commercial fleet APIs — different use case |
| Ford Explorer Electric | FordPass + Ford Auth + Ford API. Out of scope. Use [marq24/ha-fordpass](https://github.com/marq24/ha-fordpass). (#77 closed) |
| VW EU Vehicle Render Image API | No official render API exists. Marketing CDN URLs are not authenticated. (#37 closed) |
| Skoda `/v3/garage` Fallback for Kodiaq Mk2 #75 | Endpoint does not exist in mysmob — verified by grep on `skodaconnect/myskoda` (zero matches). Hard Rule #8 forbids speculation. |

---

## Process notes (current state of the practice)

- Every session = atomic PR + tagged release.
- **Branch protection ON** since 2026-04-29 — 5 required CI checks
  (Lint, Tests, Hassfest, HACS, CHANGELOG). Merging with failing tests
  is now impossible (lesson from v1.8.9 incident).
- Every command-sending entity must be capability-gated (#56) before
  reaching v2.0.0.
- Translation strings: English in `strings.json`, mirrored across
  `translations/{de,en,cs,es,fr,nl,pl,sv}.json`.
- CHANGELOG is now split: human-friendly in `CHANGELOG.md` (with emojis,
  for HACS browsers and end users), full technical with all source
  citations in `docs/CHANGELOG_TECHNICAL.md`.
- Research-Agent recipe documented in `docs/RESEARCH_NOTES_2026-04-29.md`
  section 7.

### Semver-Korrektur (going-forward strict, ab v1.9.0)

Historisch (v1.8.6 → v1.8.12) waren PATCH-Bumps auch für neue Features
üblich (z.B. v1.8.11 hatte einen neuen `connection_state` Sensor — wäre
nach strikter Lesart MINOR gewesen). Tags v1.8.11 + v1.8.12 sind released,
die rebasen wir nicht.

**Going forward — strict semver:**

- **PATCH** (`1.x.Y`) — nur Bug-Fixes, keine neuen Entities, keine API-Änderungen
- **MINOR** (`1.X.0`) — neue Sensoren, neue Services, neue Plattformen
- **MAJOR** (`X.0.0`) — Breaking Changes, Architektur-Wechsel

Konsequenz: `Vehicle Data Scout + Error Reporter` (zwei neue Sensoren)
wird **v1.9.0**, nicht v1.8.13. Folgereihe entsprechend verschoben.

---

## How an AI tool resumes this work

If a fresh AI session lands here without context:

1. Read [`docs/SESSION_HANDOFF.md`](SESSION_HANDOFF.md) — orientation
2. Read [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md) — verified API facts
3. Pick the next un-shipped session from this file
4. Follow the recipe at the bottom of `docs/SESSION_HANDOFF.md`
   ("How to start the next session")
