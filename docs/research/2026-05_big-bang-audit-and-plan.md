# Big-Bang Audit & Release Plan — vag-connect-ha v2.0.0

**Date:** 2026-05-15
**Scope:** Full cross-ecosystem audit + execution plan for ONE big-bang release
**Baseline:** v1.27.2
**Target:** v2.0.0 (or v1.30.0 if push wiring slips)
**Status:** AWAITING MAINTAINER GO/NO-GO

This document is the planning output. No code changes have been made.
Every PR listed in §8 starts only after explicit user approval.

---

## Executive Summary

vag-connect-ha is architecturally **ahead** of every competitor (listener pattern,
CommandDispatcher, _normalize, BaseAPIClient, Bruno tooling, Vehicle Data Scout)
but functionally **behind on push** because all 3 push managers are scaffolded
since v1.18-v1.23 but never wired into the coordinator.

The Big-Bang's single most valuable PR is wiring the 3 push managers live —
that flips us from "the most architecturally polished VAG-HA integration"
to "the **only** VAG-HA integration with cross-brand live push" = the
genuine "definitive" claim.

The auth-resilience repair flow is the second-most valuable lift because
three competitor integrations (audi_connect_ha, CarConnectivity, evcc) are
all bleeding users to the same 2FA / marketing-consent silent-failure. We
already raise the right exceptions; we just don't surface them as repairs.
~3 days of work for a feature no peer has.

Everything else (TPMS, alarm, driving-score, aux-heating cross-brand,
trip aggregates) is small, mechanical, additive — perfect Big-Bang filler
that grows the entity count without architectural risk.

---

## Headline Numbers

| Metric | Value |
|---|---|
| Open issues right now | 17 (8 scout, 1 user-blocked, 5 roadmap, 3 backlog) |
| Confirmed USPs we already ship | 14 |
| Critical gaps to close | 3 P0 + 6 P1 + 4 P2 + 3 P3 |
| Recommended PR count | 17 |
| Estimated effort | 3-4 weeks (with testers for push) |
| Recommended version | **v2.0.0** (justified by architectural shifts) |

---

## What competitors are doing (May 2026 snapshot)

| Repo | Latest release | Status | What we should learn / borrow |
|---|---|---|---|
| audiconnect/audi_connect_ha | v2.0.1-beta.9 (Mar 15) | Active | runtime_data + reconfigure flow + system_health (parity) |
| robinostlund/volkswagencarnet | v5.4.5 (Jan 21) | Stagnant | — |
| skodaconnect/myskoda | v1.32.2 (Apr 28) | Active | Firebase MQTTv5 fix → Skoda push live |
| tillsteinbach/CarConnectivity | v0.10.5 (Apr 24) | Active | Marketing-consent + email-MFA path (PR #89, unmerged) |
| TA2k/iobroker.vw-connect | broken since Nov 2025 | Dead | — |
| evcc-io/evcc (vehicle/*) | weekly | Very active | IDK auth + idtoken→MBB exchange reference |
| mitch-dc/volkswagen_we_connect_id | archived 2025-10-29 | **Dead** | We absorb their orphaned users |
| skodaconnect/homeassistant-skodaconnect | deprecated 2025-03 | **Dead** | Same — myskoda is the live path |

---

## Our 14 verified USPs (for README positioning, no competitor names)

1. **One install covers all 7 VAG brands** — no middleware
2. **Read-only mode** (`CONF_READ_ONLY`)
3. **12V battery monitoring + low-warning** — explains the "API stops responding" mystery
4. **Smart wake-budget + daily-quota tracking sensor** — protects users from rate-limits
5. **Capability filter** — entities only appear if subscription allows them
6. **Optimistic UI** with auto-revert on failure
7. **OIDC Hybrid flow** (`mbb_mode`) — unlocks Pre-Cariad MBB chain
8. **Bruno + 20 diagnostic-script ecosystem** — community drift-detection
9. **`_normalize.py` cross-brand foundation + Listener Pattern across 10 platforms**
10. **Plug-LED color, charging-settings-pending, external-power-available** sensors
11. **Public ROADMAP.md + quarterly research reports**
12. **8-language READMEs** (DE/EN/FR/ES/NL/PL/CS/SV)
13. **Pre-Cariad PHEV first-class** — Golf 7 GTE et al. with 55-60 entities + carType-glitch documentation
14. **Audi/VW push scaffolding** — even unactivated, no other public Python project has this

---

## Critical gaps (the must-close-before-Big-Bang list)

### P0 — Auth resilience pack (~3 days)
- Wire `MarketingConsentError`, `TwoFactorRequiredError`, `TermsAndConditionsError` into `repairs.py`
- Reconfigure flow for password updates (audi_connect_ha v2.0.1-beta.8 parity)
- Persistent session storage hardening
- **Why:** evcc #29760, audiconnect #728, CarConnectivity #92 — three competitors bleeding users to the same wall

### P0 — Push Phase 2 Live (~1-2 weeks, tester-gated)
- Skoda MQTT live (port myskoda v1.32.2 Firebase MQTTv5 fix)
- CUPRA/SEAT FCM live
- Audi/VW Cariad FCM live (UNIQUE — no public peer has this)
- `force_refresh_now` service with rate-limit awareness

### P1 — Cupra Born #53 fix (~1 day)
- Bruno-driven debugging against Gerhard's profile
- Real user has been blocked since 2026-04-24

### P1 — Long-term trip aggregates cross-brand (~2-3 days)
- Promote `tripStatistics` longterm to first-class entities (VW EU + Skoda)
- Per-trip JSON attribute on a "last_trip" sensor

### P1 — Departure-timer entities (~2-3 days)
- Read-side surfacing — already designed in v1.27.0 audit

### P1 — Tire-pressure (TPMS) sensors for Porsche (~1 day)
- PPA `TIRE_PRESSURE` measurement → 4 sensors

### P1 — Theft / alarm binary_sensor (~2 days)
- Issue #33; data exists in MBB operationList

### P2 — System-health panel (~1 day)
- Drop-in `system_health.py` (audiconnect parity)

### P2 — Re-introduce `configuration_url` + `suggested_area` (~1 day)
- Reverted in v1.26.1 — root cause was `zip_release`, not these fields. Verified safe with regression test.

### P2 — Skoda driving-score + auxiliary heating (~1 day)
- Cross-brand parity wins, endpoints documented

### P2 — Charging-station lookup service (~2 days)
- CarConnectivity v0.10.3 parity

### P3 — EU Data Act abstraction shim (~2 days)
- Interface-only, no behavior change. Sept 2026 non-binding deadline.

---

## Out of scope for Big-Bang (deferred)

- ❌ **Custom Lovelace Card** (Issue #162) — separate repo, separate cadence
- ❌ **Weekly preheat-schedule UI** — too large
- ❌ **`quality_scale: platinum`** — wait for HA core validator stability
- ❌ **MBB direct-data revival** — audit confirmed walled
- ❌ **SDV-West code paths** — vehicles ship 2027

---

## PR-by-PR sequence (17 PRs, ~3-4 weeks)

Branch from `main` after current v1.27.2.

| # | Branch | Scope | Size | Tester needed? |
|---|---|---|---|---|
| 1 | `fix/issue-53-cupra-born-400` | Investigate Cupra Born 400 with Bruno | S | Gerhard2808 |
| 2 | `feat/repairs-auth-resilience` | Wire 3 auth exceptions into repairs.py + reconfigure flow | M | — |
| 3 | `feat/system-health` | Drop-in system_health.py | S | — |
| 4 | `chore/reintroduce-device-info-fields` | Re-add configuration_url + suggested_area with regression test | S | — |
| 5 | `feat/skoda-driving-score-aux-heating` | 2 cross-brand parity wins | S | Skoda owner |
| 6 | `feat/porsche-tpms` | TPMS sensors from PPA | S | Porsche owner |
| 7 | `feat/long-term-trip-aggregates` | Promote tripStatistics longterm cross-brand | M | — |
| 8 | `feat/departure-timer-entities` | Read-side surfacing | M | — |
| 9 | `feat/charging-station-lookup-service` | Service for Cariad station lookup | M | — |
| 10 | `feat/push-skoda-mqtt-live` | Wire SkodaPushManager.start() | M | Skoda owner |
| 11 | `feat/push-cupra-seat-fcm-live` | Wire CupraSeatPushManager.start() | M | CUPRA/SEAT owner |
| 12 | `feat/push-audi-vw-fcm-live` | Wire AudiVWPushManager.start() | M | Audi/VW owner |
| 13 | `feat/issue-33-alarm-sensor` | Theft/alarm binary_sensor | M | — |
| 14 | `feat/issue-163-heatersource` | If tester ready, otherwise skip | M | ID.x heat-pump |
| 15 | `chore/euda-abstraction-shim` | Interface-only | M | — |
| 16 | `docs/readme-restructure` | Multi-language sync, NEW markers, USP positioning | M | — |
| 17 | `release/v2.0.0` | Version bump, mega-changelog, social preview | S | — |

**Sequencing rationale:**
- #1 (Cupra Born fix) first — unblocks a real user immediately
- #2-#4 (auth + health + UX polish) parallel-shippable, low risk
- #5-#9 (entity wins) additive, low blast radius
- #10-#12 (push) gated on testers — slip without blocking the rest
- #13-#15 (alarm, heatersource, EUDA) lower priority, could defer
- #16 (README) only after entity work merged so we know what to mark NEW
- #17 (release) last — version bump + mega-changelog assembly

If push wiring slips testers: ship #1-#9, #13-#16 as **v1.30.0**, push as **v2.0.0** later.

---

## README restructure plan

Current state: 8 README files (DE base + EN/FR/ES/NL/PL/CS/SV translations),
all stale at v1.25.0 references, all contain a "Roadmap" section.

**Target structure (per file, all 8 languages):**

1. **Hero block** — logo, headline, badges (keep current)
2. **Elevator pitch** — "the only HACS integration that covers all 7 VAG brands without middleware" (2 lines)
3. **Brand support table** — current, with `**[NEW v2.0]**` markers for new MY/feature additions
4. **What's new in v2.0.0** — `<details>` collapsible block with the Big-Bang headline features
5. **Differentiators** — bulleted, generic phrasing (no competitor names):
   - All 7 VAG brands in one install — no middleware, no Docker
   - 12V battery monitoring + daily-quota tracking — explains why "the API stopped working"
   - Read-only mode for safe automations
   - Capability filter — entities only appear if your subscription allows them
   - Optimistic UI with auto-revert on failure
   - Live push updates (where backend supports them) — no more wake-budget polling for state changes
6. **Installation** — 3 options (HACS / manual / dev)
7. **Configuration** — keep, add note about new reconfigure flow
8. **Documentation links** — point to `ROADMAP.md`, `docs/research/`, `docs/FAQ.md`, `SECURITY.md`
9. **Languages link bar** — top nav (already exists)
10. **Get involved** — bug reports, testers, contributors

**No roadmap content in README** — reference `ROADMAP.md` only.

**NEW marker convention** — single consistent string `**[NEW v2.0]**` so translators have one term to localise.

**Multi-language sync workflow** — checklist in `CONTRIBUTING.md`:
> Every README content change must touch all 8 language files in the same PR.
> CI lint: file size delta + section-count parity.

---

## Risk matrix (top 5)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Push needs real-account testers we don't have | High | Blocks P0 #10-#12 | Recruit via Issue #13; defer push to v2.0.1 if no tester by freeze |
| Auth-repair UI mis-classifies a flow | Medium | Confusing UX | Keep current "raise + log" path as fallback |
| Cariad-BFF endpoint drift mid-Big-Bang | Medium | New entities silently break | Vehicle Data Scout pipeline + verify_cariad_full.py nightly |
| Big-Bang too large to bisect | High | Hard to diagnose | Strict PR-by-PR sequence; each PR atomic |
| `quality_scale: platinum` re-introduced by accident | Medium | Repeat of v1.26.1 install regression | Explicit guard in release checklist |

---

## Key files for implementation start (after user GO)

- **Auth-resilience repairs:** `custom_components/vag_connect/repairs.py` + `cariad/auth/idk.py` lines 580-825 + `cariad/exceptions.py`
- **Push wiring:** `custom_components/vag_connect/cariad/push/` (3 managers) + `coordinator.py` (instantiate + lifecycle)
- **Reconfigure flow:** `custom_components/vag_connect/config_flow.py`
- **New entities (alarm, TPMS, etc.):** `cariad/models.py` + relevant API client + `sensor.py` / `binary_sensor.py`
- **README restructure:** 8 files in repo root
- **Big-Bang version bump:** `custom_components/vag_connect/manifest.json`

---

## Decision points for maintainer

Before any PR is opened, please confirm:

1. **Version target:** v2.0.0 (with breaking-change semantics: backend abstraction prep, push live) OR v1.30.0 (push deferred)?
2. **PR ordering:** approve sequence above OR re-order?
3. **Testers:** can you recruit Skoda + CUPRA/SEAT + Audi/VW push testers via Issue #13, or should I draft a "tester wanted" announcement?
4. **NEW marker:** is `**[NEW v2.0]**` acceptable as the single localisable token?
5. **Scope cuts:** any P1/P2/P3 items to remove from Big-Bang and defer to a follow-up?
6. **Release window:** when do you want the Big-Bang to ship — 2 weeks / 3 weeks / 4 weeks / when-ready?

After your GO, work proceeds PR-by-PR in the order above. Each PR is small,
atomic, reviewable. Final PR (#17) bundles version bump + assembled mega-changelog
+ social preview into one release.
