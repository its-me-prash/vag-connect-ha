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

## Huidige status & eerlijke beperkingen (v1.8.5)

VAG Connect is in actieve ontwikkeling. Zodat je weet wat werkt en wat niet:

- **Capability-gating:** Op dit moment alleen actief voor SEAT/CUPRA flash- en wake-knoppen. Voor andere merken worden entities nog zonder capability-controle aangemaakt — ze kunnen dus "niet beschikbaar" tonen als je model de functie niet heeft. Wordt merk-voor-merk uitgerold (Sessies 3B / 3C / 3S).
- **CARIAD v1/v2 auto-fallback:** Op dit moment alleen actief voor 4 set-value commando's (laaddoel, klimaattemperatuur, laadmodus, minimale SoC). Dit deblokkeert Audi RS e-tron GT en VW Passat 2025 vanaf v1.8.5. Lock/unlock, climate start/stop en charging start/stop volgen in Sessie 3B.
- **Image-platform:** Er is geen officiële render-image API in de CARIAD-pipeline. De image-entity is daarom een placeholder en wordt in v1.10.0 ofwel verwijderd ofwel omgezet naar door de gebruiker opgegeven URLs.
- **PPC/PPE-platform (Audi Q5 2025, Q6 e-tron, A5/S5, A6 e-tron):** Deze 2025+ modellen gebruiken de nieuwe E³ 1.2 architectuur. Er zijn nog geen openbaar gereverse-engineerde endpoints bekend. VAG Connect detecteert deze voertuigen en maakt geen command-entities aan, in plaats van 404-fouten te produceren.
- **Privacy-vereiste:** GPS-positie, voertuigstatus en standkachel vereisen **"Locatie delen"** ingeschakeld in je My-VW / My-Audi / MySkoda / MyCupra app — anders antwoordt de backend met 403.

Actuele roadmap en gedetailleerde status: [`../docs/SESSION_HANDOFF.md`](../docs/SESSION_HANDOFF.md)

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
