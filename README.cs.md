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

Chtěl jsem plně ovládat své Audi v Home Assistant. Tak jsem to postavil.

**VAG Connect** je samostatná integrace Home Assistant pro všechny značky VAG. Bez externích závislostí, bez Dockeru, bez externích služeb.

Od v0.14.1 integrace **přímo** komunikuje s CARIAD API — vlastní async klient, plně autonomní. Architektura cloud-polling, 80+ entit napříč 10 platformami, 14 služeb.

> ✅ **Aktivně udržovaný multi-značkový nástupce** projektů [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archivováno 2025-10-29) a [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated 2025-03-14). Jedna integrace pro Audi, VW, Škoda, SEAT, CUPRA, Porsche a VW US/CA — bez samostatného pluginu pro každou značku.

## Aktuální stav a upřímné limity (v1.8.12)

### ✅ Co funguje TEĎ (všech 7 značek)

- 🟢🟡⚫ **Multi-Brand Connection-State sensor** — online / standby / offline pro všechny značky (v1.8.12).
- 🛡️ **Defenzivní stabilita** — retry 504, retry přechodných síťových chyb, 6h stale-cache + tolerance 3 selhání (v1.8.7).
- 🔓 **Příkazy Lock / Climate / Charging** pro Audi 2024+ a VW Passat 2025 — 10 příkazů s fallback CARIAD `/v1/` ↔ `/v2/` (v1.8.5 + v1.8.8).
- 🚪 **CUPRA / SEAT kompletní entity** s ověřenými OLA JSON cestami + binary sensors na okno (v1.8.9).
- 🚙 **Škoda** `detail` block + `reliableLockStatus` + `fullyChargedAt` (v1.8.11).

### ⚠️ Ještě v procesu

Capability filter fáze 2 (v1.8.13) · Defenzivní kódování fáze 2 (v1.8.14) · Anonymizované diagnostiky (Session 4) · Smart-wake + ochrana drain 12V (Session 6) · Push updates (v1.9.1/2) · Trip stats + EU Data Act (v1.10.0+).

### 🚫 Vědomé limity

- **Image platforma:** neexistuje oficiální CARIAD render API. Bude odstraněna nebo přepnuta na URL od uživatele v v1.10.0.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — graceful degradation místo 404.
- **Ford / značky mimo VAG:** mimo rozsah — viz [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass).

### 🔧 Předpoklad ochrany soukromí

**"Sdílet mou polohu"** musí být aktivní v My-VW / My-Audi / MySkoda / MyCupra — jinak backend 403.

### 📚 Více informací

- 🗺️ [`../docs/ROADMAP.md`](../docs/ROADMAP.md) · 📜 [`../docs/CHANGELOG_TECHNICAL.md`](../docs/CHANGELOG_TECHNICAL.md) · 🤝 [`../docs/SESSION_HANDOFF.md`](../docs/SESSION_HANDOFF.md) · 🔬 [`../docs/RESEARCH_NOTES_2026-04-29.md`](../docs/RESEARCH_NOTES_2026-04-29.md)

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

### Dosaženo

| Verze | Obsah | Stav |
|---|---|---|
| v1.0–v1.5 | 9 platforem, 7 značek, opravy & audit entit | ✅ Hotovo |
| v1.6.0 | SEAT/CUPRA 9 endpointů, Škoda oprava, Audi PPC, zámek, noční režim | ✅ Hotovo |
| v1.7.0 | Kompletní přepis Škoda, automobilové překlady ve všech jazycích, spolehlivost | ✅ Hotovo |

### Plán sessions (P0 → P2)

| Session | Verze | Rozsah | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 | iot_class, per-VIN dostupnost, S-PIN fail-fast, falešné writable odstraněny, geokódování opt-in | **#60** |
| **1.5 — Soukromí & Auth** | v1.8.1 | Maskování VIN v logu a diagnostice, ConfigEntryAuthFailed při neplatných údajích, dokumentace userPosition | — |
| **2A — Capabilities Foundation** | v1.8.2 | Error taxonomy, 3-state model, capabilities cache (24h TTL) | #68 |
| **2B — Button gating** | v1.8.3 | Skrýt flash/wake u SEAT/CUPRA dle capabilities | #56 |
| **2C — Lock debug + userPosition** | v1.8.4 | Lock `internal-error` analyzovat + ověřit userPosition | #56 |
| **3 — Command Profile** | v1.8.5 | Routing podle značky/regionu/platformy, RS e-tron GT fix | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.6 | Anonymizované diagnostiky, regresní testy | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Read-only režim, command locking, cloud vs wake | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | MQTT broker integrace | #57 |
| **9 — Feature batch** | v1.10.0 | Statistiky jízd, historie nabíjení, UI časovačů, alarm, profily nabíjení | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live testy všech značek, compatibility matrix, EU Data Act | #13, #59 |

> Striktní P0 → P1 → P2 pořadí. Sessions 1–4 jsou nezaměnitelné před přidáváním nových funkcí.

---

## Licence

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** je neregistrovaná ochranná známka (™, ne ®). Prosíme, nepoužívejte tento název ve forkách, abyste předešli záměně.

Tato integrace je nezávislý komunitní projekt bez jakéhokoliv spojení s Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG nebo jakoukoliv pobočkou Volkswagen Group.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
