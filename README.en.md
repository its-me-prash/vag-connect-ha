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
  <a href="../tests/"><img src="https://img.shields.io/badge/Tests-337%2F337-brightgreen?style=for-the-badge"></a>
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

80+ entities across 10 platforms, 14 services, cloud-push architecture. All 7 VAG Group brands in one integration — no separate plugin per brand needed.

Since v0.14.1, VAG Connect speaks **directly** to the CARIAD API via its own async client. No external dependencies, no upstream blockers.

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
| **2 — Capabilities** | v1.8.2 | Capability-gated entities, subscription detection (2A→2B→2C) | #56, #68 |
| **3 — Command Profile** | v1.8.3 | Brand/region/platform routing, RS e-tron GT fix | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.4 | Anonymized diagnostics, regression tests | #62, #58 |
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
