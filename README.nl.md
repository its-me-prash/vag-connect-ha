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

Ik wilde mijn Audi volledig in Home Assistant besturen. Dus bouwde ik dit.

**VAG Connect** is een zelfstandige Home Assistant integratie voor alle VAG-merken. Geen externe afhankelijkheden, geen Docker, geen externe diensten.

Vanaf v0.14.1 communiceert de integratie **rechtstreeks** met de CARIAD API — eigen async-client, volledig zelfstandig. Cloud-polling architectuur, 80+ entities over 10 platforms, 14 services.

> ✅ **Actief onderhouden multi-merk opvolger** van [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (gearchiveerd op 2025-10-29) en [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated op 2025-03-14). Eén integratie voor Audi, VW, Škoda, SEAT, CUPRA, Porsche en VW US/CA — geen aparte plugin per merk.

## Huidige status & eerlijke beperkingen (v1.8.12)

### ✅ Wat NU werkt (alle 7 merken)

- 🟢🟡⚫ **Multi-Brand Connection-State sensor** — online / standby / offline voor alle merken (v1.8.12).
- 🛡️ **Defensieve stabiliteit** — 504 retry, transient-network-error retry, 6h stale-cache + 3-fail tolerance (v1.8.7).
- 🔓 **Lock / Climate / Charging commando's** voor Audi 2024+ en VW Passat 2025 — 10 commando's met CARIAD `/v1/` ↔ `/v2/` fallback (v1.8.5 + v1.8.8).
- 🚪 **CUPRA / SEAT volledige entities** met geverifieerde OLA JSON paden + binary sensors per venster (v1.8.9).
- 🚙 **Škoda** `detail` block + `reliableLockStatus` + `fullyChargedAt` (v1.8.11).

### 🔬 Binnenkort: 1-klik bug reports & feature requests (v1.9.0)

> **Jij helpt ons de integratie te verbeteren — zonder een woord GitHub of Markdown te leren.**

Twee nieuwe diagnose-sensoren in v1.9.0:

| Sensor | Wat het doet | Hoe het je helpt |
|---|---|---|
| 🔬 **Voertuigdata-verkenner** | Detecteert automatisch nieuwe velden in de API van je auto die we nog niet uitlezen | Als je Audi A4 2017 of VW Golf 7 GTE velden levert die we niet kennen → we voegen ze toe in de volgende versie |
| 🛠️ **Foutrapport** | Verzamelt recente fouten met geanonimiseerde context (model, firmware, stack trace) | In plaats van forum-screenshot zonder info → gestructureerd bug report dat we direct kunnen fixen |

**1-klik workflow** (gelijk voor beide sensoren):

```
1. HA toont een notificatie wanneer iets nieuws gedetecteerd wordt
2. Klik "Meer info" → modal met geanonimiseerde inhoud + 2 knoppen:

   📤 Op GitHub melden    ← opent vooringevuld bug report
   📋 Kopiëren voor forum/FB ← Markdown naar clipboard

3. Submit → klaar in 30 seconden
```

🔒 **Privacy-belofte:** **Geen auto-push.** Niets verlaat je HA-installatie zonder jouw expliciete klik. VINs, GPS, user-IDs anoniem. GDPR-compliant.

🤝 **Waarom we dit nodig hebben:** We zijn de enige actieve VAG HA-integratie voor alle 7 merken. Met jouw 1-klik bijdrage ontdekken we verschillen tussen modellen in **dagen in plaats van maanden**.

### ⚠️ Nog in uitvoering

Capability filter fase 2 (v1.9.1) · Defensive coding fase 2 (v1.9.2) · Optimistic Lock/Climate (v1.9.3) · Diagnostics + Smart-wake + 12V drain bescherming (v1.10.0) · Push updates (v1.10.x) · Trip stats + EU Data Act (v1.11.0 / v2.0.0).

### 🚫 Bewuste beperkingen

- **Image-platform:** geen officiële CARIAD render API. Wordt verwijderd of omgezet naar gebruiker-URLs in v1.10.0.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — graceful degradation in plaats van 404.
- **Ford / niet-VAG merken:** buiten scope — zie [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass).

### 🔧 Privacy-vereiste

**"Locatie delen"** moet ingeschakeld zijn in My-VW / My-Audi / MySkoda / MyCupra — anders backend 403.

### 📚 Meer info

- 🗺️ [`../docs/ROADMAP.md`](../docs/ROADMAP.md) · 📜 [`../docs/CHANGELOG_TECHNICAL.md`](../docs/CHANGELOG_TECHNICAL.md) · 🤝 [`../docs/SESSION_HANDOFF.md`](../docs/SESSION_HANDOFF.md) · 🔬 [`../docs/RESEARCH_NOTES_2026-04-29.md`](../docs/RESEARCH_NOTES_2026-04-29.md)

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

### Tot nu toe bereikt

| Versie | Inhoud | Status |
|---|---|---|
| v1.0–v1.5 | 9 platformen, 7 merken, bugfixes & entiteit-audit | ✅ Klaar |
| v1.6.0 | SEAT/CUPRA 9 endpoints, Škoda fix, Audi PPC, vergrendeling, nachtmodus | ✅ Klaar |
| v1.7.0 | Complete Škoda herschrijving, autovriendelijke vertalingen alle talen, betrouwbaarheid | ✅ Klaar |

### Sessieplan (P0 → P2)

| Sessie | Versie | Scope | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 | iot_class, beschikbaarheid per VIN, S-PIN fail-fast, neppe writables verwijderd | **#60** |
| **1.5 — Privacy & Auth** | v1.8.1 | VIN-masking in logs/diagnostics, ConfigEntryAuthFailed bij verouderde credentials, userPosition-documentatie | — |
| **2A — Capabilities Foundation** | v1.8.2 | Error-taxonomie, 3-state model, capabilities-cache (24h TTL) | #68 |
| **2B — Button gating** | v1.8.3 | Flash/wake op SEAT/CUPRA verbergen volgens capabilities | #56 |
| **2C — Lock debug + userPosition** | v1.8.4 | Lock `internal-error` onderzoeken + userPosition verifiëren | #56 |
| **3 — Command Profile** | v1.8.5 | Merk/regio/platform routing, RS e-tron GT fix | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.6 | Geanonimiseerde diagnostics, regressietests | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Read-only modus, command locking, cloud vs wake | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | MQTT broker integratie | #57 |
| **9 — Feature batch** | v1.10.0 | Ritstats, laadgeschiedenis, vertrektimer-UI, alarm, laadprofielen | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live tests alle merken, compatibility matrix, EU Data Act | #13, #59 |

> Strikte P0 → P1 → P2 volgorde. Sessies 1–4 zijn niet onderhandelbaar voor nieuwe features.

---

## Licentie

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** is een niet-geregistreerd handelsmerk (™, niet ®). Gebruik deze naam niet in forks om verwarring te voorkomen.

Deze integratie is een onafhankelijk communityproject zonder enige verbinding met Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG of andere VAG-dochterondernemingen.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
