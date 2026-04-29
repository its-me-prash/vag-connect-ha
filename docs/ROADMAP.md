# VAG Connect — Roadmap

> Single canonical source of truth for sessions, versions and issue mapping.
> The README ships an identical short version in 8 languages; this file
> mirrors it for archive/historical purposes and links the active GitHub
> issues for each session.

**Last updated:** 2026-04-29 — post v1.8.12 sprint (Multi-Brand
Connection-State live)

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
| **Vehicle Data Scout + Error Reporter** | v1.8.13 | Zwei diagnostische Sensoren mit **gemeinsamer Reporter Pipeline** für crowd-sourced Bug-Discovery. (1) **Vehicle Data Scout** loggt unbekannte JSON-Felder (folgt tillsteinbach CC-* "Unexpected Keys"-Pattern, unsere beste API-Quelle). (2) **Error Reporter** captured letzte N Exceptions/API-Errors mit Brand+Model+Firmware-Context. **Reporter Pipeline (1-Klick, beide Quellen):** HA Repair Notification → User klickt "Mehr Info" → Modal mit anonymisiertem Inhalt + 2 Buttons: `📤 Bug auf GitHub melden` (pre-filled Issue) UND `📋 Copy für Forum/Facebook` (Markdown in Clipboard). **Besonders wertvoll für Facebook-Community** — nicht-technische User können in 1 Klick brauchbare Bug-Reports teilen ohne Markdown oder GitHub zu lernen. ~30 Sek. KEIN Auto-Push (GDPR + HACS + GitHub ToS); opt-in Telemetry eigene v1.9.x Session. Brand-localised sensor names (DE: "API-Beobachter" / "Fehler-Berichter", FR/ES/NL/PL/CS/SV equivalents). Implementation: `cariad/_unexpected_keys.py` + `cariad/_error_reporter.py` + shared `_reporter_pipeline.py` + 8-Sprach-Strings | new |
| **Capability-Filter Phase 2** | v1.8.14 | `capability.active && capability.user-enabled` before entity creation. CC-seatcupra #64 pattern. Likely solves more "missing entity" reports across all brands | #56 |
| **Defensive Coding Phase 2** | v1.8.15 | Generic `except Exception` audit across all API clients. Enum tolerance for `CHARGING_INTERRUPTED`, `NOT_ACTIVATED`, `NO_UPDATE_AVAILABLE` etc. Optional fields enforcement (myskoda PR #565 pattern) | #58 |
| **3B-Part-3 — Optimistic Lock/Climate** | v1.8.16 | myskoda #832 pattern — optimistic update + state restoration after `set_*` commands so entities don't go "unavailable" between click and next poll | — |
| **4 — Diagnostics + Fixtures** | v1.9.0-pre | Anonymized diagnostics export with `last_seen_at`, `command_profile`, `device_platform`, `connection_state`, `consecutive_failures`, `capability_404_endpoints`. Fixtures from CC-seatcupra #109, CC-skoda #50, volkswagencarnet #921 as test cases | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6 — Read-only + Smart-Wake** | v1.9.0 | Read-only mode; persistent wake counter (max 3/day); `wake_count_today` sensor; **NEVER auto-wake** from coordinator. Plus 12V drain detection from `connectionWarning.insufficientBatteryLevelWarning` (volkswagencarnet #940) — extend stale-cache to 24-72h when 12V is low | #63, #55, #23 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via `mqtt.messagehub.de` | #57, #27 |
| **8 — Push Škoda** | v1.9.2 | mysmob MQTT broker (Škoda-only, not portable to other brands per myskoda PR #566 / #533) | #57 |
| **9 — Trip Stats + Image refactor** | v1.10.0 | Audi `tripstatistics/v1` schema (verified `audi_services.py:337`); per-trip data model (numeric aggregate in state, JSON in attrs per audi #113); image platform → user-supplied URL or removal (no official render API exists) | #24, #35, #36 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live tests all brands, compatibility matrix, EU Data Act ready (pycupra `EUDAConnection` reference implementation ready to port) | #13, #59 |

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
  reaching v1.9.0.
- Translation strings: English in `strings.json`, mirrored across
  `translations/{de,en,cs,es,fr,nl,pl,sv}.json`.
- CHANGELOG is now split: human-friendly in `CHANGELOG.md` (with emojis,
  for HACS browsers and end users), full technical with all source
  citations in `docs/CHANGELOG_TECHNICAL.md`.
- Research-Agent recipe documented in `docs/RESEARCH_NOTES_2026-04-29.md`
  section 7.

---

## How an AI tool resumes this work

If a fresh AI session lands here without context:

1. Read [`docs/SESSION_HANDOFF.md`](SESSION_HANDOFF.md) — orientation
2. Read [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md) — verified API facts
3. Pick the next un-shipped session from this file
4. Follow the recipe at the bottom of `docs/SESSION_HANDOFF.md`
   ("How to start the next session")
