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
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge"></a>
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

## Current state & honest limits (v1.8.12)

VAG Connect is under active development. So you know what works and what's coming:

### ✅ What works NOW (all 7 brands)

- 🟢🟡⚫ **Multi-brand connection-state sensor** — online / standby / offline for Audi, VW EU, Škoda, SEAT, CUPRA (v1.8.12). First VAG integration with centralized connection status across all brands.
- 🛡️ **Defensive stability** — 504 retry, transient-network-error retry, 6h stale-cache + 3-failure tolerance (v1.8.7). Weekend backend hiccups no longer break automations.
- 🔓 **Lock / Climate / Charging commands** for modern Audi 2024+ and VW Passat 2025 — 10 commands have automatic CARIAD `/v1/` ↔ `/v2/` fallback (v1.8.5 + v1.8.8).
- 🚪 **CUPRA / SEAT complete door / window / trunk / sunroof entities** with verified OLA paths + per-window binary sensors (v1.8.9).
- 🚙 **Škoda `detail.{sunroof,trunk,bonnet}`, `reliableLockStatus`, `fullyChargedAt`** (v1.8.11) from live API findings.
- 🔐 **Token refresh storm protection** (max 3/h, v1.8.7) — prevents IP bans.

### 🔬 Coming next: 1-click bug reports & feature requests (v1.9.0)

> **You help us improve the integration — without learning a single word of GitHub or Markdown.**

Two new diagnostic sensors in v1.9.0:

| Sensor | What it does | How it helps you |
|---|---|---|
| 🔬 **Vehicle Data Scout** | Automatically detects new fields in your car's API that we don't parse yet | If your Audi A4 2017 or VW Golf 7 GTE returns fields we don't know → we add them in the next release |
| 🛠️ **Error Reporter** | Collects recent errors with anonymised context (model, firmware, stack trace) | Instead of a forum screenshot without info → structured bug report we can fix immediately |

**1-click workflow** (same for both sensors):

```
1. HA shows a notification when something new is detected
2. You click "More info" → modal with anonymised content + 2 buttons:

   📤 Report on GitHub    ← opens pre-filled bug report
   📋 Copy for forum/FB   ← Markdown to clipboard for Facebook group

3. Submit → done in 30 seconds
```

🔒 **Privacy promise:** **No auto-push.** Nothing leaves your HA installation without your explicit click. VINs, GPS, user IDs are anonymised before display. GDPR-compliant, HACS-Default-compatible.

🤝 **Why we need it:** We are the only active VAG HA integration for all 7 brands. Every new model returns slightly different API responses. With your 1-click contribution we discover these differences in **days instead of months**.

### ⚠️ Still in progress

- **Capability filter phase 2** (v1.9.1) · **Defensive coding phase 2** (v1.9.2) · **Optimistic Lock/Climate** (v1.9.3) · **Diagnostics + Smart-wake + 12V drain protection** (v1.10.0) · **Push updates** (v1.10.x) · **Trip statistics + EU Data Act** (v1.11.0 / v2.0.0).

### 🚫 Conscious limits

- **Image platform:** no official CARIAD render-image API exists. Will be removed or replaced with user-supplied URLs in v1.10.0.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — new E³ 1.2 architecture, not publicly reverse-engineered. **Graceful degradation** instead of 404 errors.
- **Ford / non-VAG brands:** out of scope — see [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass) for Ford.

### 🔧 Privacy prerequisite

GPS position, vehicle status and pre-heating require **"Share my position"** enabled in your My-VW / My-Audi / MySkoda / MyCupra app — otherwise the backend responds with 403.

### 📚 More info

- 🗺️ Roadmap: [`../docs/ROADMAP.md`](../docs/ROADMAP.md)
- 📜 Tech changelog: [`../docs/CHANGELOG_TECHNICAL.md`](../docs/CHANGELOG_TECHNICAL.md)
- 🤝 Session handoff (for contributors & AI tools): [`../docs/SESSION_HANDOFF.md`](../docs/SESSION_HANDOFF.md)
- 🔬 Verified API paths: [`../docs/RESEARCH_NOTES_2026-04-29.md`](../docs/RESEARCH_NOTES_2026-04-29.md)

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

### Achieved so far

| Version | Content | Status |
|---|---|---|
| v1.0–v1.5 | 9 platforms, 7 brands, bugs & entity audit | ✅ Done |
| v1.6.0 | SEAT/CUPRA 9 endpoints, Škoda fix, Audi PPC, Lock, nightly reduction | ✅ Done |
| v1.7.0 | Complete Škoda rewrite, car-friendly translations all languages, reliability | ✅ Done |

### Session plan (P0 → P2)

| Session | Version | Scope | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 | iot_class, per-VIN availability, S-PIN fail-fast, fake writables removed, geocoding opt-in, platforms sync | **#60** |
| **1.5 — Privacy & Auth Polish** | v1.8.1 | VIN masking in logs/diagnostics, ConfigEntryAuthFailed on stale credentials, userPosition documentation | — |
| **2A — Capabilities Foundation** | v1.8.2 | Error taxonomy, 3-state feature model, capabilities cache (24h TTL) | #68 |
| **2B — Button gating** | v1.8.3 | Hide flash/wake on SEAT/CUPRA when capabilities say no | #56 |
| **2C — Lock debug + userPosition** | v1.8.4 | Investigate lock `internal-error` + verify userPosition semantics | #56 |
| **3 — Command Profile** | v1.8.5 | Brand/region/platform routing, RS e-tron GT fix | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.6 | Anonymized diagnostics, regression tests | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Read-only mode, command locking, cloud vs wake | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | MQTT broker integration | #57 |
| **9 — Feature batch** | v1.10.0 | Trip stats, charging history, departure timer UI, alarm, charge profiles | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live tests all brands, compatibility matrix, EU Data Act ready | #13, #59 |

> Strict P0 → P1 → P2 order. Sessions 1–4 are non-negotiable before any new features land.

---

## License

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** is an unregistered trademark (™, not ®). Please do not use this name in forks to avoid confusion.

This integration is an independent community project with no affiliation to Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG or any VAG subsidiary.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
