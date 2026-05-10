# vag-connect-ha Strategic Roadmap — v1.27.0 → v2.0.0

**Date:** 2026-05-11
**Period:** May 2026 → Q4 2026
**Status:** Draft — pending maintainer review
**Author:** Synthesized from competitor analysis + ecosystem research + audit findings

---

## 1. Current State (May 2026)

vag-connect-ha is at **v1.26.2** (hotfix shipped May 9, 2026 — reverted `hacs.json` `zip_release`
change that broke installs for v1.25.x users). The integration covers **7 VAG brands** (Audi,
VW EU, Skoda, SEAT, CUPRA, Porsche, VW US/CA), claims **80+ entities across 10 platforms** and
**14 services**, with direct cloud auth (no middleware).

**May 2026 sprint shipped a lot fast:**
- v1.24.1 → v1.24.2 → v1.25.0 (PR-A through PR-EFG) → v1.26.0 → hotfixes (PR #176, #177)
- 7 new entities + cross-brand parity in v1.26.0 (PR #175)
- Architectural foundation: `_normalize.py`, `CommandDispatcher` (Phase 1A), listener pattern
  across 10 platforms, GPS hardening, Porsche HTTP retry/quota

**Current branch: PR #179 (Pre-Cariad MBB research + Bruno collection)** — research complete,
ready to merge. The 6-hour audit (`docs/research/2026-05_pre-cariad-mbb-and-golf-7-gte-audit.md`)
confirmed:
- Legacy MBB direct-data path is structurally walled (XID_APP_VW gate)
- Pre-Cariad cars work via Cariad-BFF (12/12 selectivestatus jobs)
- ~12 new entity candidates identified for v1.27.0

---

## 2. Open Issues Triage

**Total open: 12 issues + 1 PR** (PR #179 = the research branch).

### 🔴 P0 — Active, fresh, user-blocked
- **#53** — Cupra Born Funktionstest (Gerhard2808, real user, 2026-04-24, last touched 2026-05-09) — entities load but actions return **400 Bad Request**. Only true external user blocker right now.

### 🟠 P1 — Planned (roadmap-defining)
- **#178** — Re-introduce v1.26.1-reverted polish features (manifest loggers, `configuration_url`, `suggested_area`, `quality_scale`) — quick-win, tee'd up
- **#160** — MBB Legacy Phase 2: port lock/unlock/climate/charger fallbacks (write-side commands for older MIB3) — direct successor to PR #179
- **#161** — Push Phase 2 Live-Activation: Skoda MQTT + CUPRA/SEAT/Audi/VW FCM real network code
- **#163** — `heaterSource` exposure (needs ID.x heat-pump tester)

### 🟡 P2 — Backlog
- **#162** — Custom Lovelace Card repo (parallel session, separate HACS plugin)
- **#33** — Diebstahl-/Fahrzeug-Alarm as `binary_sensor`

### 🔵 Wait-on-User
- **#13** — Live tests on Škoda/SEAT/CUPRA hardware

### 🟣 Discussion / Meta
- **#59** — EU Data Act research tracker (Sept 2026 deadline)

### Vehicle Data Scout (auto-generated, fold into v1.27.0)
- **#180, #181, #182** — three new fields detected: `chargingStatus.value.chargeRate_kmph` (VW + Audi) and `charging.chargingSettings.requests` (Audi). All from May 8–10, 2026.

### ⚫ Stale / should-close
- None yet — issue hygiene is solid.

---

## 3. Competitive Landscape

### audiconnect/audi_connect_ha (primary Audi MBB reference)
- **Latest: v2.0.1-beta.9 (March 15, 2026)** — added Engine Start/Stop service actions
- **v2.0.1-beta.8 (March 14, 2026)** — major refactor to coordinator/runtime_data, reconfigure flow for password updates, vehicle device selector replacing VIN text input, system health panel
- **Recurring issues:** #728 (auth fails after every HA core update), #721 (502 on Q8 e-tron climate), #691 (2024 S6 remote start request), #330 (refresh 403)
- **Takeaway:** They're modernizing infra (runtime_data, device selectors) — we already shipped CommandDispatcher and listener pattern in v1.25.0. **We're architecturally ahead.**

### robinostlund/homeassistant-volkswagencarnet (VW Cariad-BFF reference)
- **Latest: v5.4.5 (January 21, 2026)** — reverted refactoring due to VW backend inconsistency (red flag for them, opportunity for us)
- **v5.4.1** added ID-series AC departure timer + parking lights sensor
- **Recurring issues:** #917 (`charging_rate` unavailable on ID.4 2025 — same field our scout caught in #180/#181/#182!), #954 (climate buttons missing), #890 (FR: contract expiration visibility)
- **Takeaway:** Stagnant since January. The `chargeRate_kmph` field collision validates our scout pipeline.

### tillsteinbach/CarConnectivity-connector-volkswagen
- **Latest: v0.10.5 (April 24, 2026)** — minor dep bumps
- **v0.10.3** added charging-station lookup by lat/long
- **Hot issues:** #92 (2FA email-code support — VW now requires it!), #79 (login "no Location header"), #80 (long-term trip data request)
- **Takeaway:** **2FA is the next auth wall.** VW rolled out email-code MFA. We don't handle it yet. P0 if we want EU users.

### skodaconnect/homeassistant-myskoda
- **Latest: v1.32.2 (April 28, 2026)** — MQTT restored via Firebase MQTTv5 fix
- **Active:** #1087 (active ventilation switch PR), #1074 (departure-timer service draft), #1078 (runtime_data migration)
- **Takeaway:** Their MQTT auth pattern is the Push Phase 2 pattern in our #161.

### evcc-io/evcc
- **#29760** — VW marketing-consent prompts force evcc reboot. Same auth flow issue as CarConnectivity #89.
- **Takeaway:** "Marketing consent" + 2FA + token expiry is the **single biggest cross-integration pain point** in 2026.

---

## 4. Ecosystem Trends

**Cariad reorg (Oct 2025):** VW scaled Cariad back; it now coordinates **three parallel architectures**: Global (Cariad legacy), SDV East (Xpeng, Asia), SDV West (Rivian JV, Western markets, winter-testing Q1 2026). Up to **30M vehicles** across brands. **Implication:** Cariad-BFF is **stable for 2026** (legacy track) but a new SDV-West backend is coming for 2027+ Audi/VW/Scout models.

**EU Data Act — Article 3 deadline September 2026:** OEMs must give end users + chosen third-parties direct vehicle-data access. COVESA recommends VSS (Vehicle Signal Specification) + VISS (Vehicle Information Service Specification) as the API standard, **but it's non-binding** — VW can pick its own. Compliance window: now → March 2026 = inventory; March → July = test; July → Sept = parallel-run.

**New car platforms hitting in 2026:**
- **Audi Q6 e-tron / PPE platform / E3 1.2** — first PPE production model, 5 HCPs, Cariad-developed; 2027MY gets HW/SW updates
- **VW ID.7** — confirmed working with WeConnect ID
- **Skoda Enyaq facelift, Octavia 4** — likely existing endpoint coverage

**Auth wall changes (2026):**
- VW EU rolled out **email-code 2FA** (CarConnectivity #92)
- **Marketing consent prompts** can break sessions (evcc #29760, CarConnectivity #89)
- HA core updates frequently invalidate Audi credentials (audi_connect_ha #728)

---

## 5. Community Wishlist (top 5)

From HA forum + competitor-issue convergence:
1. **Charge target / max charge %** — repeatedly requested
2. **Long-term trip data** (distance, duration, avg speed, consumption) — top of CarConnectivity #80
3. **Departure timers as proper HA entities** — Skoda #1074 PR
4. **Auth resilience** — survives 2FA email codes, marketing-consent prompts, HA core updates
5. **Sensors actually update without manual reload** — listener-pattern refactor (PR #170) addresses

---

## 6. Strategic Pillars

1. **Single integration, all 7 brands, no middleware.** This is the moat. Lean into cross-brand parity.
2. **Pre-Cariad PHEV first-class citizen.** No competitor handles Golf 7 GTE / B8 Passat GTE / Audi A3 e-tron well end-to-end.
3. **Auth that survives 2026 reality.** 2FA email codes, marketing-consent prompts, HA-update credential loss.
4. **Push > Poll where possible.** Skoda MQTT, FCM for VW/Audi/CUPRA/SEAT — Issue #161.
5. **EU Data Act-ready architecture.** Don't bet on VSS/VISS yet (non-binding) but isolate the data-mapping layer.

---

## 7. Detailed Roadmap

### v1.27.0 — Pre-Cariad PHEV + new entities (target: 2-3 weeks)
**Core:** merge PR #179 audit + Bruno collection.

**New Entities (from audit's ~12 candidates + scout fields #180-#182):**
- `sensor.chargeRate_kmph` (VW + Audi — addresses volkswagencarnet #917 too)
- `sensor.charging_settings_requests` (Audi diagnostic)
- MBB metadata sensors: `binary_sensor.is_phev`, `sensor.subscription_active_until`, `sensor.user_role`, `sensor.vehicle_lifecycle_status`
- Long-term trip statistics (3 sensors: distance, duration, avg speed)
- Departure timer entities (3 timer profiles × 4 attrs each = 12 entities, plus `number.departure_min_soc`, `sensor.next_departure_time`)
- Charging settings (`number.target_soc`, `select.charging_mode`)

**Polish:** ship Issue #178 minus `quality_scale` (which broke v1.26.1).

**Bug:** investigate #53 (Cupra Born 400 errors) using Bruno collection.

### v1.28.0 — Auth resilience (target: 4 weeks)
**Theme: survive 2026 auth reality.**
- Email-code 2FA flow (VW EU) — preempt the wall before it blocks users
- Marketing-consent prompt detection + re-auth UI in HA (no more silent failure)
- Token-refresh hardening
- Reconfigure flow for password updates (audi_connect_ha v2.0.1-beta.8 parity)
- Persistent session storage so HA-core updates don't invalidate
- Diagnostics export (mask PII) for triage

### v1.29.0 — Push Phase 2 Live (target: 4 weeks; parallel with v1.28.0 testers)
**Theme: ship Issue #161.**
- Skoda MQTT live activation (port myskoda v1.32.2 Firebase MQTTv5 pattern)
- FCM live activation: CUPRA, SEAT, Audi, VW
- Push-vs-poll fallback logic
- New service: `force_refresh_now` with rate-limit awareness
- Closes #161

### v1.30.0 — MBB Phase 2 + Lovelace Card (target: 6 weeks)
- Issue #160: lock/unlock/climate/charger write-side fallbacks for MIB3
- Issue #33: alarm `binary_sensor`
- Issue #163: `heaterSource` (after tester confirms read-only vs writable)
- Companion: Issue #162 — custom Lovelace card repo seeded (separate release cadence)

### v2.0.0 — EU Data Act + SDV-West readiness (target: Q3/Q4 2026)
**Theme: future-proof for VW Group's three-architecture world.**
- Backend abstraction layer: Cariad-Global, SDV-West (Rivian JV), SDV-East (Xpeng)
- EU Data Act compliance shim: optional VSS-mapped output channel
- Breaking change: drop legacy MBB direct-data shims (audit-confirmed walled)
- New auth: SDV-West account flow when Rivian-JV vehicles ship
- Migration tooling for users on v1.x configs
- Re-enable polished `quality_scale` once HA core's validator is stable

---

## 8. What to STOP doing

- **Stop reverse-engineering legacy MBB direct-data endpoints.** Audit confirmed structural wall.
- **Stop adding scout-detected fields without entity intent.** Every #180-style issue should either become an entity in the next minor or be closed with a "noted, not promoted" comment.
- **Stop shipping `quality_scale` improvements until HA core stabilizes its validator** (v1.26.1 root cause). Track upstream, defer.
- **Stop polish-only releases.** Bundle polish into feature releases.

---

## 9. What to START doing

- **Start a public `ROADMAP.md`** — competitors don't have one, easy differentiator.
- **Start a quarterly "VAG ecosystem report"** in `docs/research/` — your audit pattern is gold.
- **Start "tester-of-the-month" recognition** — pulls volunteers out of the woodwork.
- **Start a 2FA + marketing-consent test matrix** — every major release must run through it.
- **Start CI smoke against the Bruno collection** — nightly against sandbox so backend drift is caught early.

---

## 10. Risk & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| VW EU enforces 2FA email-codes for all accounts | High (already rolling out) | Breaks integration | v1.28.0 prioritization |
| Marketing-consent prompts trigger silent auth failure | High (evcc, CarConnectivity hit it) | Sensors stop updating | v1.28.0 detection logic |
| HA core 2026.x changes runtime_data API | Medium | Breaking change | Subscribe to HA core changelog, ship reconfigure flow in v1.28.0 |
| EU Data Act (Sept 2026) forces VSS exposure on OEMs | Medium (non-binding rec) | Cariad-BFF endpoints could change | v2.0.0 abstraction layer |
| SDV-West vehicles ship 2027 with new backend | Medium-low | New auth + endpoints needed | v2.0.0 prep |
| `quality_scale` validator instability in HA core | Medium | Repeat of v1.26.1 install break | Don't re-enable until upstream stable |
| Hostinger/CI dep bumps | Low | Build breaks | Already covered by Dependabot grouping |

**External dependencies to monitor:**
- HA core releases (monthly)
- Cariad-BFF endpoint changes (no public changelog — scout pipeline is our radar)
- VW Group app updates (mirror sometimes leaks new endpoints)

---

## 11. Quick Wins (next 7 days)

1. **Merge PR #179** (audit + Bruno collection) — research is done.
2. **Ship Issue #178** (the 4 reverted polish features minus `quality_scale`) as v1.26.3.
3. **Convert scout issues #180/#181/#182 into v1.27.0 entity tickets** — they're the same field as volkswagencarnet #917 (validates demand).
4. **Triage Cupra Born #53** with Bruno against Gerhard2808's vehicle profile — likely a 400 = missing `If-Match` or stale ETag, fixable in a day.
5. **Open a public `ROADMAP.md`** with this document distilled to ~300 words — kills three competitor-comparison threads on the HA forum overnight.
6. **Add a `2FA + marketing-consent` label** and tag #161, evcc-mirrored #29760 case, future user reports.
7. **Document the `chargeRate_kmph` field** in the audit doc as the first cross-brand canonical example.

---

**Sources:**
- [vag-connect-ha repo](https://github.com/its-me-prash/vag-connect-ha)
- [audi_connect_ha repo](https://github.com/audiconnect/audi_connect_ha)
- [homeassistant-volkswagencarnet repo](https://github.com/robinostlund/homeassistant-volkswagencarnet)
- [CarConnectivity-connector-volkswagen repo](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen)
- [homeassistant-myskoda repo](https://github.com/skodaconnect/homeassistant-myskoda)
- [evcc-io/evcc](https://github.com/evcc-io/evcc)
- [EU Data Act vehicle guidance — Grape Up](https://grapeup.com/blog/eu-data-act-vehicle-guidance-2025-what-automotive-oems-must-share-by-september-2026)
- [COVESA EU Data Act recommendations](https://covesa.global/eu-data-act-covesa-recommendations/)
- [VW reassigns Cariad as coordinator of Rivian and Xpeng — electrive.com](https://www.electrive.com/2025/10/06/vw-reassigns-cariad-as-coordinator-of-rivian-and-xpeng-software/)
- [Audi Q6 e-tron PPE platform — Audi Club NA](https://audiclubna.org/audi-future-models-roadmap-ppe-architecture-large-evs/)
