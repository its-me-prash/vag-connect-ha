<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integrace Home Assistant pro Audi · VW · Škoda · SEAT · CUPRA</strong>
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

Chtěl jsem plně ovládat své Audi v Home Assistant. Tak jsem to postavil.

**VAG Connect** je samostatná integrace Home Assistant pro všechny značky VAG. Bez externích závislostí, bez Dockeru, bez externích služeb.

Od v0.14.1 integrace **přímo** komunikuje s CARIAD API — vlastní async klient, plně autonomní.

---

## Podporované Značky

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Obě značky jsou od v1.0.0 k dispozici jako Beta. Hledáme testery — zpětnou vazbu hlaste jako [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

---

## Funkce

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

## Instalace

### HACS

1. HACS → Integrace → ⋮ → Vlastní repozitáře
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Kategorie: Integrace
3. Nainstalovat **VAG Connect** → Restartovat Home Assistant
4. Nastavení → Integrace → **+ Integrace** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Restartujte Home Assistant.

---

## Konfigurace

| Field | Required | Description |
|---|---|---|
| Značka | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| E-mail | ✓ | Přihlašovací e-mail z aplikace výrobce |
| Heslo | ✓ | Heslo z aplikace |
| S-PIN | — | Vyžadováno pro zamykání (v Zabezpečení v aplikaci) |
| Interval | — | Minuty mezi aktualizacemi (výchozí: 5) |

**Která aplikace?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Známá Omezení

- **S-PIN** vyžadováno pro zamykání
- **Interval** minimum 5 minut
- **2FA** — jednou ručně potvrdit v aplikaci
- **Porsche / VW NA** — funkční jako Beta, hledáme testery

---

## Plán

| Verze | Obsah | Stav |
|---|---|---|
| v1.0–v1.5 | 9 platforem, 7 značek, opravy & audit entit | ✅ Hotovo |
| v1.6.0 | SEAT/CUPRA 9 endpointů, Škoda oprava, Audi PPC, zámek, noční režim | ✅ Hotovo |
| v1.7.0 | Kompletní přepis Škoda, automobilové překlady ve všech jazycích, spolehlivost | ✅ Hotovo |
| v1.8.0 | Kontrola schopností (#56), push notifikace (#57), defenzivní kódování (#58) | 🔜 Další |
| v1.9.0 | Statistiky jízd, historie nabíjení, UI časovačů odjezdu, PPC platforma | 🔜 |
| v2.0.0 | HACS Default, všechny značky otestovány, EU Data Act (#59) | 🎯 |

---

## Licence

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** je neregistrovaná ochranná známka (™, ne ®). Prosíme, nepoužívejte tento název ve forkách, abyste předešli záměně.

Tato integrace je nezávislý komunitní projekt bez jakéhokoliv spojení s Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG nebo jakoukoliv pobočkou Volkswagen Group.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
