<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration for Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/its-me-prash/vag-connect-ha/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/downloads/its-me-prash/vag-connect-ha/total?style=for-the-badge&label=Downloads" alt="Downloads"></a>
  <a href="../custom_components/vag_connect/quality_scale.yaml"><img src="https://img.shields.io/badge/Quality%20Scale-Platinum%20%F0%9F%8F%86-gold?style=for-the-badge"></a>
</p>

<p align="center">
  <a href="../README.md">Deutsch</a> ·
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

**VAG Connect** connects Home Assistant directly to your Audi, VW, Škoda, SEAT, CUPRA, Porsche or VW US/CA — no middleware, no Docker, no extra service. Enter your app credentials, done.

80+ entities across 10 platforms, 14 services, cloud-polling architecture. All 7 VAG Group brands in one integration — no separate plugin per brand needed.

Since v0.14.1, VAG Connect speaks **directly** to the CARIAD API via its own async client. No external dependencies, no upstream blockers.

> ✅ **Active multi-brand successor** to [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archived 2025-10-29) and [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated 2025-03-14). One integration for Audi, VW, Škoda, SEAT, CUPRA, Porsche and VW US/CA — no separate plugin per brand.

## Current Status & Honest Limits (v1.12.3)

VAG Connect is under active development. So you know what works and what's coming:

### ✅ What works NOW (all 7 brands)

**🛰️ 1-Click Bug Reports & Feature Requests (LIVE since v1.9.0)**

Two diagnostic sensors with a shared reporter pipeline — **first real live-validation by community users** in v1.10.2 (Gerhard / CUPRA Born), v1.12.2 (tritanium73 / Skoda) and v1.12.3 (DnnsJp74 / Audi):

- 🔬 **Vehicle Data Scout** — automatically detects unknown JSON fields in your car's API. Brand-localized in 8 languages (DE: API-Beobachter, FR: Observateur d'API, etc.).
- 🚨 **Error Reporter** — Ring-buffer of the last 20 integration errors with anonymized context (model, firmware, stack trace).
- 🔘 **Reporter Pipeline:** both sensors automatically create HA Repair notifications with a pre-filled GitHub issue as a 1-click link. Plus a diagnostics download with everything masked for forum/Facebook.
- 🔒 **Privacy promise:** Nothing leaves your HA without your explicit click. VINs masked, GPS rounded to 1 decimal, JWTs/UUIDs/emails removed. GDPR-compliant.

**🟢🟡⚫ Multi-Brand Connection-State (v1.8.12)**

`connection_state` sensor (online / standby / offline) for Audi, VW EU, Škoda, SEAT, CUPRA — first VAG integration with centralized connection status. Brand-agnostic helper `compute_connection_state` with recursive `carCapturedTimestamp` walk.

**🔋 12V Battery Monitoring + Smart-Wake (v1.12.0)**

- `voltage_12v` sensor (V) + `warning_12v_low` binary at <11.5V — prevents silent API outages caused by an empty starter battery
- `wake_count_today` sensor + soft-cap of 3 wakes/day (`_WAKE_BUDGET_PER_DAY`) protects 12V from wake-loops, raises `wake_budget_exhausted` BEFORE the API call

**💨 Optimistic UI for Lock/Climate/Charging (v1.11.1)**

Switches flip immediately on click (myskoda PR #832 pattern), API roundtrip in the background. On failure: revert + ServiceValidationError. 8 actuator methods migrated.

**🔋 PHEV-Range-Triple (v1.10.0 + #94 + #96 follow-up in v1.11.1)**

Three explicit range sensors: `electric_range_km`, `combustion_range_km`, `total_range_km`. VW EU/Audi parser classifies by engine type (4 sources instead of 2). Audi diesel fallback from `measurements.rangeStatus.value.dieselRange`. Verified via evcc-io/evcc#19045 + Audi Q4 sample + CarConnectivity logs.

**🔒 Read-only Mode Phase 1 (v1.12.0)**

Options toggle "Read-only Mode" → skip lock/switch/button(non-refresh)/climate/number platforms for privacy/safety-conservative owners. Sensors + binary_sensors + device_tracker remain.

**⚡ Writeable Max-Charge-Current Number (v1.12.0)**

Slider 6–32A instead of just a read-only sensor. New `command_set_max_charge_current` POST chargingSettings.

**💡 Per-Light Binary-Sensors (v1.12.0)**

Dynamically per light type from `lights_individual` dict + aggregate `lights_on` + `lights_count`.

**🛠️ Defensive Stability (v1.8.7 + v1.10.1)**

- 504-retry, transient-network-error retry, 6h stale-cache + 3-failure tolerance
- Token-refresh-storm protection (max 3/h) — prevents IP bans
- `safe_int` / `safe_float` / `safe_enum` helpers — tolerate backend quirks

**🚪 CUPRA Born 2026 Firmware-Shapes (v1.10.2 — Gerhard's #53 first live-validation)**

Field-name fallback chain: `battery.currentSocPercentage` (Born 2026) → `currentPct` (Rainer #109) → `currentSOC_pct` (legacy). Lowercase enum tolerance for `"connected"` / `"locked"`. Backwards compatibility preserved.

**🔓 Lock + Wake for Audi/VW (v1.9.1, #92 Audi S6 C8)**

`command_lock` now sends S-PIN for Audi/VW (CARIAD BFF answered `403 spin_error`). `command_wake` uses v1→v2 fallback.

**🛡️ Capability-Filter Phase 2 (v1.9.1, #56)**

`classify_command_failure` body-sniffing for `missing-capability` / `subscription_expired` / `not_entitled` / `spin_error` markers. `_cariad_cmd` writes every outcome to FeatureState. Command-bound entities (Lock/Climate/Switch/Buttons) automatically go unavailable on a definitive backend "no".

### ⚠️ Still in progress / What's still planned (planned sessions)

- **v1.13.0 MINOR** — Anonymized Diagnostics-Export (#62) + Capability-Filter Phase 3 (`capability.active && user-enabled` PRE-entity-creation, hides buttons like the MyCupra app) + Read-only Phase 2/3 (Command-Locking + cloud_refresh vs wake_vehicle service separation).
- **v1.14.0 MINOR** — Trip Statistics from Audi `tripstatistics/v1` (#24, #35).
- **v1.15.0+ MINOR** — PPC Climate Body conditional shape (#29, #51), Theft/Alarm Binary (#33), Climate-Timer UI (#26).
- **v1.16.0 MINOR** — Location-specific Charge-Target SoC + Charge profiles (#25, #31).
- **v1.17.0 MINOR** — Remote Start ICE (#28, audi_connect_ha #717 pattern).
- **v1.18.0 MINOR** — Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) for real-time updates without polling (#57, #27).
- **v2.0.0 MAJOR** — HACS Default + Live tests all brands + EU Data Act ready (pycupra `EUDAConnection` as reference, September 2026 deadline) (#13, #59).

### 🚫 Conscious limits

- **Image platform:** no official CARIAD render-image API exists. The image entity will switch to user-supplied URLs in a future release.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — new E³ 1.2 architecture, not yet publicly reverse-engineered (not even in audi_connect_ha or CarConnectivity). VAG Connect detects these vehicles and does **graceful degradation** instead of 404 errors.
- **Ford / non-VAG brands:** out of scope — see [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass) for Ford.

### 🔧 Privacy prerequisite

For GPS position, vehicle status and pre-heating to work, **"Share my position"** must be enabled in your My-VW / My-Audi / MySkoda / MyCupra app — otherwise the backend responds with 403.

### 📚 More info

- 🗺️ Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md) — complete P0/P1/P2/P3 prioritization of all open issues
- 📜 Tech Changelog: [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md) — per release field mappings + architecture decisions + external source refs
- 🤝 Session Handoff (for contributors & AI tools): [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md)
- 🔒 Privacy & data handling rules: [`CONTRIBUTING.md`](CONTRIBUTING.md) section (post-#53 third-party review)
- 📋 FAQ Subscription / Service Plus / `missing-capability` diagnosis: [`CONTRIBUTING.md`](CONTRIBUTING.md) FAQ section

## Supported Brands

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Both brands are available as Beta since v1.0.0. Porsche uses Auth0 (separate from VAG IDK), VW NA uses a separate auth server. Testers wanted — report feedback as an [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

---

## Features

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Fuel / Battery level | ✓ | ✓ | ✓ | ✓ |
| Range | ✓ | ✓ | ✓ | ✓ |
| Odometer | ✓ | ✓ | ✓ | ✓ |
| GPS position | ✓ | ✓ | ✓ | ✓ |
| Doors (total + per door) | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ |
| Climate start/stop | ✓ | ✓ | ✓ | ✓ |
| Target temperature | ✓ | ✓ | ✓ | ✓ |
| Lock / Unlock | ✓ | ✓ | ✓ | ✓ |
| Flash lights | ✓ | ✓ | ✓ | ✓ |
| Wake vehicle | ✓ | ✓ | ✓ | ✓ |
| Service due km/days | ✓ | ✓ | ✓ | ✓ |
| Online status | ✓ | ✓ | ✓ | ✓ |
| Battery SoC % | ✓ | ✓ | ✓ | ✓ |
| Charge state | ✓ | ✓ | ✓ | ✓ |
| Charge power kW | ✓ | ✓ | ✓ | ✓ |
| Charge speed km/h | ✓ | ✓ | ✓ | ✓ |
| Charge ETA | ✓ | ✓ | ✓ | ✓ |
| Charge target % | ✓ | ✓ | ✓ | ✓ |
| Trunk / hood / sunroof | ✓ | ✓ | ✓ | ✓ |
| Window heating | ✓ | ✓ | ✓ | ✓ |
| Vehicle renders | ✓ | — | — | ✓ |
| Departure timers 1–3 | ✓ | ✓ | — | — |
| Battery temperature | ✓ | ✓ | — | — |
| AdBlue range | ✓ | ✓ | — | ✓ |

---

## Installation

### HACS

1. HACS → Integrations → ⋮ → Custom Repositories
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Category: Integration
3. Install **VAG Connect** → Restart Home Assistant
4. Settings → Integrations → **+ Integration** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Restart Home Assistant.

---

## Configuration

| Field | Required | Description |
|---|---|---|
| Brand | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| Email | ✓ | Login email from the manufacturer app |
| Password | ✓ | Password from the app |
| S-PIN | — | Required for locking (under Security in the app) |
| Poll interval | — | Minutes between updates (default: 5) |

**Which app?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Known Limitations

- **S-PIN** required for locking — set in the app under Security
- **Poll interval** minimum 5 minutes — too short leads to temporary account lock
- **2FA** — confirm once manually in the app, then automatic
- **Porsche / VW NA** — functional as Beta, testers wanted
- **VW China 2026+** — new CEA/XPeng platform, API not public, no ETA

---

## Roadmap

> 📍 **Single Source of Truth:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — complete P0/P1/P2/P3 prioritization with all ~20 open issues categorized.

### Recent releases (2026-04-29 + 2026-04-30 + 2026-05-01)

| Version | Content | Date |
|---|---|---|
| v1.8.6–v1.8.12 | Foundation Sprint: defensive stability, Capability-Filter Phase 2, Multi-Brand Connection-State, all brand parsers on verified live API paths | 2026-04-29 |
| v1.9.0 | 🛰️ Vehicle Data Scout + Error Reporter + Reporter Pipeline | 2026-04-29 |
| v1.9.1 | Audi/VW Lock + Wake hotfix (#92) + Capability-Filter Phase 2 + Scout paths #90/#91 | 2026-04-29 |
| v1.10.0–v1.10.2 | PHEV-Range-Triple (#94), Defensive Coding Phase 2 (#58), CUPRA Born 2026 firmware (#53 Gerhard) | 2026-04-29/30 |
| v1.11.0–v1.11.1 | Issue #91 closure (Light/Service/Number), Golf GTE fuel-range fix (#96), Optimistic UI (3B-Part-3) | 2026-04-30 |
| v1.12.0 | 🔋💡⚡🧯🔒 5-in-1 Sprint: 12V (#23) + Per-Light + Writeable Number + Smart-Wake (#55) + Read-only Phase 1 (#63) | 2026-04-30 |
| v1.12.1 | Scout paths #105/#106 + Gerhard's Born fixture (#53 with consent) + #47 FAQ | 2026-04-30 |
| v1.12.2 | 🌟 **First community Scout report** (Skoda #107 from tritanium73) | 2026-05-01 |
| **v1.12.3** | Scout paths #111+#113+#114 bundled with wildcard strategy (`fuelStatus.rangeStatus.value.*` etc.) | **2026-05-01** |

### Next sessions

| Version | Scope | Issues |
|---|---|---|
| **v1.13.0** ⭐ MINOR | Anonymized Diagnostics-Export + Capability-Filter Phase 3 + Read-only Phase 2/3 | #62, #56 Phase 3, #63 Phase 2/3 |
| **v1.14.0** MINOR | Trip Statistics from Audi `tripstatistics/v1` | #24, #35 |
| **v1.15.0+** MINOR | PPC Climate (#29, #51), Theft/Alarm Binary (#33), Climate-Timer UI (#26) | various |
| **v1.18.0** MINOR | Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) | #57, #27 |
| **v2.0.0** 🎉 MAJOR | HACS Default + Live tests all brands + EU Data Act ready (Sept 2026 deadline) | #13, #59 |

> Order is **strictly P0 → P1 → P2**. Bug fixes always take priority over features.

---

## License

Apache License 2.0 — [LICENSE](LICENSE)

**VAG Connect™** is an unregistered trademark (™, not ®). Please do not use this name in forks to avoid confusion.

This integration is an independent community project with no affiliation to Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG or any VAG subsidiary.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
