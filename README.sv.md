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

Jag ville styra min Audi i Home Assistant — fullständigt. Så jag byggde detta.

**VAG Connect** är en fristående Home Assistant-integration för alla VAG-märken. Inga externa beroenden, ingen Docker, inga externa tjänster.

Från v0.14.1 kommunicerar integrationen **direkt** med CARIAD API — egen async-klient, helt fristående. Cloud-polling-arkitektur, 80+ entiteter över 10 plattformar, 14 tjänster.

> ✅ **Aktivt underhållen multi-märkes-efterträdare** till [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (arkiverat 2025-10-29) och [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated 2025-03-14). En integration för Audi, VW, Škoda, SEAT, CUPRA, Porsche och VW US/CA — ingen separat plugin per märke.

## Nuvarande status och ärliga begränsningar / Current Status & Honest Limits (v1.12.3)

VAG Connect utvecklas aktivt vidare. Så att du vet vad som fungerar och vad som kommer:

### ✅ Vad som fungerar NU (alla 7 märken)

**🛰️ 1-klick bug rapporter & feature-önskemål (LIVE sedan v1.9.0)**

Två diagnostiska sensorer med en gemensam reporter pipeline — **första riktiga live-validering av community-användare** i v1.10.2 (Gerhard / CUPRA Born), v1.12.2 (tritanium73 / Skoda) och v1.12.3 (DnnsJp74 / Audi):

- 🔬 **Vehicle Data Scout** — upptäcker automatiskt okända JSON-fält i din bils API. Märkes-lokaliserad på 8 språk (DE: API-Beobachter, FR: Observateur d'API, etc.).
- 🚨 **Error Reporter** — Ring-buffer av de senaste 20 integrationsfelen med anonymiserad kontext (modell, firmware, stack trace).
- 🔘 **Reporter Pipeline:** båda sensorerna skapar automatiskt HA Repair-notifikationer med ett förifyllt GitHub-Issue som 1-klicks länk. Plus en diagnostics-nedladdning med allt maskerat för forum/Facebook.
- 🔒 **Integritetslöfte:** Inget lämnar din HA utan din explicita klick. VIN maskerade, GPS avrundad till 1 decimal, JWT/UUID/e-post borttagna. GDPR-compliant.

**🟢🟡⚫ Multi-Brand Connection-State (v1.8.12)**

Sensor `connection_state` (online / standby / offline) för Audi, VW EU, Škoda, SEAT, CUPRA — första VAG-integration med centraliserad anslutningsstatus. Brand-agnostisk helper `compute_connection_state` med rekursiv `carCapturedTimestamp` walk.

**🔋 12V-batteri-övervakning + Smart-Wake (v1.12.0)**

- Sensor `voltage_12v` (V) + binary `warning_12v_low` vid <11.5V — förhindrar tysta API-avbrott orsakade av tomt startbatteri
- Sensor `wake_count_today` + soft-cap på 3 wakes/dag (`_WAKE_BUDGET_PER_DAY`) skyddar 12V mot wake-loops, höjer `wake_budget_exhausted` INNAN API-anrop

**💨 Optimistisk UI för Lock/Climate/Charging (v1.11.1)**

Switches växlar omedelbart vid klick (myskoda PR #832 mönster), API-roundtrip i bakgrunden. Vid misslyckande: revert + ServiceValidationError. 8 actuator-metoder migrerade.

**🔋 PHEV-Range-Triple (v1.10.0 + #94 + #96 follow-up i v1.11.1)**

Tre explicita räckviddssensorer: `electric_range_km`, `combustion_range_km`, `total_range_km`. VW EU/Audi-parser klassificerar efter motortyp (4 källor istället för 2). Audi-diesel-fallback från `measurements.rangeStatus.value.dieselRange`. Verifierat via evcc-io/evcc#19045 + Audi Q4 sample + CarConnectivity-loggar.

**🔒 Read-only-läge Fas 1 (v1.12.0)**

Options-toggle "Read-only Mode" → hoppa över lock/switch/button(non-refresh)/climate/number-plattformar för privacy/safety-konservativa ägare. Sensors + binary_sensors + device_tracker stannar.

**⚡ Skrivbar Max-Charge-Current Number (v1.12.0)**

Slider 6-32A istället för bara en read-only-sensor. Ny `command_set_max_charge_current` POST chargingSettings.

**💡 Per-Light Binary-Sensors (v1.12.0)**

Dynamiskt per ljustyp från `lights_individual` dict + aggregat `lights_on` + `lights_count`.

**🛠️ Defensiv stabilitet (v1.8.7 + v1.10.1)**

- 504-retry, transient-network-error retry, 6h stale-cache + 3-failure tolerance
- Token-refresh-storm-skydd (max 3/h) — förhindrar IP-bans
- Helpers `safe_int` / `safe_float` / `safe_enum` — tolererar backend-quirks

**🚪 CUPRA Born 2026 Firmware-Shapes (v1.10.2 — Gerhards #53 första live-validering)**

Field-name fallback-kedja: `battery.currentSocPercentage` (Born 2026) → `currentPct` (Rainer #109) → `currentSOC_pct` (legacy). Lowercase enum tolerance för `"connected"` / `"locked"`. Bakåtkompatibilitet bevarad.

**🔓 Lock + Wake för Audi/VW (v1.9.1, #92 Audi S6 C8)**

`command_lock` skickar nu S-PIN för Audi/VW (CARIAD BFF svarade `403 spin_error`). `command_wake` använder v1→v2 fallback.

**🛡️ Capability-Filter Fas 2 (v1.9.1, #56)**

Body-sniffing `classify_command_failure` för `missing-capability` / `subscription_expired` / `not_entitled` / `spin_error` markörer. `_cariad_cmd` skriver varje resultat till FeatureState. Command-bundna entiteter (Lock/Climate/Switch/Buttons) går automatiskt unavailable vid definitivt "nej" från backend.

### ⚠️ Fortfarande pågår / What's still in progress (planerade sessioner)

- **v1.13.0 MINOR** — Anonymized Diagnostics-Export (#62) + Capability-Filter Fas 3 (`capability.active && user-enabled` PRE-entity-creation, döljer knappar som MyCupra-appen) + Read-only Fas 2/3 (Command-Locking + cloud_refresh vs wake_vehicle service-separation).
- **v1.14.0 MINOR** — Trip Statistics från Audi `tripstatistics/v1` (#24, #35).
- **v1.15.0+ MINOR** — PPC Climate Body conditional shape (#29, #51), Theft/Alarm Binary (#33), Climate-Timer UI (#26).
- **v1.16.0 MINOR** — Platsspecifik laddmål-SoC + laddprofiler (#25, #31).
- **v1.17.0 MINOR** — Remote Start ICE (#28, audi_connect_ha #717-mönster).
- **v1.18.0 MINOR** — Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) för realtidsuppdateringar utan polling (#57, #27).
- **v2.0.0 MAJOR** — HACS Default + Live-tester alla märken + EU Data Act ready (pycupra `EUDAConnection` som referens, deadline september 2026) (#13, #59).

### 🚫 Medvetna begränsningar / Conscious limits

- **Image-plattform:** inget officiellt CARIAD render-image API existerar. Image-entiteten kommer i en framtida release att gå över till användar-tillhandahållna URL:er.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — ny E³ 1.2-arkitektur, ännu inte offentligt reverse-engineered (varken i audi_connect_ha eller CarConnectivity). VAG Connect upptäcker dessa fordon och gör **graceful degradation** istället för 404-fel.
- **Ford / icke-VAG-märken:** utanför scope — se [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass) för Ford.

### 🔧 Integritetskrav

För att GPS-position, fordonsstatus och kupévärmare ska fungera måste **"Dela min position"** vara aktiverat i din My-VW / My-Audi / MySkoda / MyCupra-app — annars svarar backend med 403.

### 📚 Mer info / More info

- 🗺️ Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md) — komplett P0/P1/P2/P3-prioritering av alla öppna issues
- 📜 Tech Changelog: [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md) — per release: field-mappings + arkitekturbeslut + externa source-refs
- 🤝 Session Handoff (för bidragsgivare och AI-verktyg): [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md)
- 🔒 Integritets- och datahanteringsregler: sektion [`CONTRIBUTING.md`](CONTRIBUTING.md) (post-#53 third-party review)
- 📋 FAQ Subscription / Service Plus / `missing-capability` diagnos: FAQ-sektion i [`CONTRIBUTING.md`](CONTRIBUTING.md)

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

## Vägkarta / Roadmap

> 📍 **Single Source of Truth:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — komplett P0/P1/P2/P3-prioritering med alla ~20 öppna issues kategoriserade.

### Senaste releases / Recent releases (2026-04-29 + 2026-04-30 + 2026-05-01)

| Version | Innehåll | Datum |
|---|---|---|
| v1.8.6–v1.8.12 | Foundation-Sprint: defensiv stabilitet, Capability-Filter Fas 2, Multi-Brand Connection-State, alla brand-parsers på verifierade live-API-vägar | 2026-04-29 |
| v1.9.0 | 🛰️ Vehicle Data Scout + Error Reporter + Reporter Pipeline | 2026-04-29 |
| v1.9.1 | Audi/VW Lock + Wake hotfix (#92) + Capability-Filter Fas 2 + Scout-vägar #90/#91 | 2026-04-29 |
| v1.10.0–v1.10.2 | PHEV-Range-Triple (#94), Defensive Coding Fas 2 (#58), CUPRA Born 2026-firmware (#53 Gerhard) | 2026-04-29/30 |
| v1.11.0–v1.11.1 | Issue #91-closure (Light/Service/Number), Golf GTE Fuel-Range fix (#96), Optimistisk UI (3B-Part-3) | 2026-04-30 |
| v1.12.0 | 🔋💡⚡🧯🔒 5-i-1 Sprint: 12V (#23) + Per-Light + Skrivbar Number + Smart-Wake (#55) + Read-only Fas 1 (#63) | 2026-04-30 |
| v1.12.1 | Scout-vägar #105/#106 + Gerhards Born-fixture (#53 med samtycke) + #47 FAQ | 2026-04-30 |
| v1.12.2 | 🌟 **Första community-Scout-rapporten** (Skoda #107 från tritanium73) | 2026-05-01 |
| **v1.12.3** | Scout-vägar #111+#113+#114 buntlade med wildcard-strategi (`fuelStatus.rangeStatus.value.*` etc.) | **2026-05-01** |

### Nästa sessioner / Next sessions

| Version | Omfattning | Issues |
|---|---|---|
| **v1.13.0** ⭐ MINOR | Anonymized Diagnostics-Export + Capability-Filter Fas 3 + Read-only Fas 2/3 | #62, #56 Fas 3, #63 Fas 2/3 |
| **v1.14.0** MINOR | Trip Statistics från Audi `tripstatistics/v1` | #24, #35 |
| **v1.15.0+** MINOR | PPC Climate (#29, #51), Theft/Alarm Binary (#33), Climate-Timer UI (#26) | various |
| **v1.18.0** MINOR | Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) | #57, #27 |
| **v2.0.0** 🎉 MAJOR | HACS Default + Live-tester alla märken + EU Data Act ready (deadline sept. 2026) | #13, #59 |

> Ordningen är **strikt P0 → P1 → P2**. Buggfixar har alltid prioritet över funktioner.

---

## Licens

Apache License 2.0 — [LICENSE](LICENSE)

**VAG Connect™** är ett oregistrerat varumärke (™, inte ®). Använd inte detta namn i forks för att undvika förvirring.

Denna integration är ett oberoende gemenskapsprojekt utan koppling till Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG eller något VAG-dotterbolag.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
