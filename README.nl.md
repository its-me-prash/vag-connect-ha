<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integratie voor Audi · VW · Škoda · SEAT · CUPRA</strong>
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

Ik wilde mijn Audi volledig in Home Assistant besturen. Dus bouwde ik dit.

**VAG Connect** is een zelfstandige Home Assistant integratie voor alle VAG-merken. Geen externe afhankelijkheden, geen Docker, geen externe diensten.

Vanaf v0.14.1 communiceert de integratie **rechtstreeks** met de CARIAD API — eigen async-client, volledig zelfstandig.

---

## Ondersteunde Merken

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Beide merken zijn sinds v1.0.0 beschikbaar als Beta. Testers gezocht — meld feedback als [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

---

## Functies

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

## Installatie

### HACS

1. HACS → Integraties → ⋮ → Aangepaste opslagplaatsen
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Categorie: Integratie
3. **VAG Connect** installeren → Home Assistant opnieuw opstarten
4. Instellingen → Integraties → **+ Integratie** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Herstart Home Assistant.

---

## Configuratie

| Field | Required | Description |
|---|---|---|
| Merk | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| E-mail | ✓ | Aanmeldings-e-mail van de fabrikants-app |
| Wachtwoord | ✓ | Wachtwoord van de app |
| S-PIN | — | Vereist voor vergrendeling (onder Beveiliging in de app) |
| Poll-interval | — | Minuten tussen updates (standaard: 5) |

**Welke app?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Bekende Beperkingen

- **S-PIN** vereist voor vergrendeling
- **Poll-interval** minimaal 5 minuten
- **2FA** — eenmalig handmatig bevestigen in de app
- **Porsche / VW NA** — functioneel als Beta, testers gezocht

---

## Roadmap

| Version | Content | Status |
|---|---|---|
| v1.0–v1.5 | 9 platforms, 7 brands, bugs & entity audit | ✅ Done |
| v1.6.0 | Charging profiles, alarm, consumption, climate timer | 🔜 |
| v1.7.0 | Navigation → vehicle, remote start, PPC platform 2025 | 🔜 |
| v2.0.0 | HACS Official (live tests all 7 brands) | 🎯 |

---

## Licentie

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** is een niet-geregistreerd handelsmerk (™, niet ®). Gebruik deze naam niet in forks om verwarring te voorkomen.

Deze integratie is een onafhankelijk communityproject zonder enige verbinding met Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG of andere VAG-dochterondernemingen.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
