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

I wanted to control my Audi in Home Assistant — fully, not half-heartedly. So I built this.

**VAG Connect** is a self-contained Home Assistant integration for all VAG brands. No external dependencies, no Docker, no separate service. Install the integration, enter credentials, done.

From v0.14.1, the integration talks **directly** to the CARIAD API — its own async client, fully self-contained, no upstream blockers.

---

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

> **Porsche:** Porsche uses a completely separate Auth0 authentication system — distinct from the VAG IDK used by the other brands. The integration is fully documented technically and planned for v0.15.0. For Porsche today: [ha-porscheconnect](https://github.com/CJNE/ha-porscheconnect) (MIT, actively maintained) can be installed alongside.

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
| Charge ETA | ✓ | ✓ | ✓ | ✓ |
| Charge target % | ✓ | ✓ | ✓ | ✓ |
| Window heating | ✓ | ✓ | ✓ | ✓ |
| Departure timers 1–3 | ✓ | ✓ | — | — |
| Battery temperature | ✓ | ✓ | — | — |
| AdBlue range | ✓ | ✓ | — | — |

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
- **Porsche** — separate Auth0 system, planned for v0.15.0
- **VW North America** — separate auth server, planned for v0.16.0
- **VW China 2026+** — new CEA/XPeng platform, API not public, no ETA

---

## Roadmap

| Version | Content |
|---|---|
| ✅ v0.14.1 | Platinum, own CARIAD client |
| ✅ Beta | Porsche (Auth0 + PPA API) |
| ✅ Beta | VW North America |
| 🎯 v1.0.0 | HACS Official |

---

## License

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** is an unregistered trademark (™, not ®). Please do not use this name in forks to avoid confusion.

This integration is an independent community project with no affiliation to Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG or any VAG subsidiary.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
