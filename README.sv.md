<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration för Audi · VW · Škoda · SEAT · CUPRA</strong>
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

Jag ville styra min Audi i Home Assistant — fullständigt. Så jag byggde detta.

**VAG Connect** är en fristående Home Assistant-integration för alla VAG-märken. Inga externa beroenden, ingen Docker, inga externa tjänster.

Från v0.14.1 kommunicerar integrationen **direkt** med CARIAD API — egen async-klient, helt fristående.

---

## Stödda Märken

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Båda märkena har varit tillgängliga som Beta sedan v1.0.0. Testare sökes — rapportera feedback som [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

---

## Funktioner

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

1. HACS → Integrationer → ⋮ → Anpassade förråd
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Kategori: Integration
3. Installera **VAG Connect** → Starta om Home Assistant
4. Inställningar → Integrationer → **+ Integration** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Starta om Home Assistant.

---

## Konfiguration

| Field | Required | Description |
|---|---|---|
| Märke | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| E-post | ✓ | Inloggnings-e-post från tillverkarens app |
| Lösenord | ✓ | Lösenord från appen |
| S-PIN | — | Krävs för låsning (under Säkerhet i appen) |
| Intervall | — | Minuter mellan uppdateringar (standard: 5) |

**Vilken app?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Kända Begränsningar

- **S-PIN** krävs för låsning
- **Intervall** minst 5 minuter
- **2FA** — bekräfta en gång manuellt i appen
- **Porsche / VW NA** — fungerar som Beta, testare sökes

---

## Vägkarta

| Version | Content | Status |
|---|---|---|
| v1.0–v1.5 | 9 platforms, 7 brands, bugs & entity audit | ✅ Done |
| v1.6.0 | Charging profiles, alarm, consumption, climate timer | 🔜 |
| v1.7.0 | Navigation → vehicle, remote start, PPC platform 2025 | 🔜 |
| v2.0.0 | HACS Official (live tests all 7 brands) | 🎯 |

---

## Licens

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** är ett oregistrerat varumärke (™, inte ®). Använd inte detta namn i forks för att undvika förvirring.

Denna integration är ett oberoende gemenskapsprojekt utan koppling till Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG eller något VAG-dotterbolag.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
