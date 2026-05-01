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

Chtěl jsem plně ovládat své Audi v Home Assistant. Tak jsem to postavil.

**VAG Connect** je samostatná integrace Home Assistant pro všechny značky VAG. Bez externích závislostí, bez Dockeru, bez externích služeb.

Od v0.14.1 integrace **přímo** komunikuje s CARIAD API — vlastní async klient, plně autonomní. Architektura cloud-polling, 80+ entit napříč 10 platformami, 14 služeb.

> ✅ **Aktivně udržovaný multi-značkový nástupce** projektů [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archivováno 2025-10-29) a [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated 2025-03-14). Jedna integrace pro Audi, VW, Škoda, SEAT, CUPRA, Porsche a VW US/CA — bez samostatného pluginu pro každou značku.

## Aktuální stav a upřímné limity / Current Status & Honest Limits (v1.12.3)

VAG Connect se aktivně vyvíjí. Abys věděl, co funguje a co přijde:

### ✅ Co funguje TEĎ (všech 7 značek)

**🛰️ Bug reporty a žádosti o funkce 1 kliknutím (LIVE od v1.9.0)**

Dva diagnostické sensory se sdílenou reporter pipeline — **první skutečná live-validace komunitními uživateli** v v1.10.2 (Gerhard / CUPRA Born), v1.12.2 (tritanium73 / Skoda) a v1.12.3 (DnnsJp74 / Audi):

- 🔬 **Vehicle Data Scout** — automaticky detekuje neznámá JSON pole v API tvého auta. Lokalizovaný per značku v 8 jazycích (DE: API-Beobachter, FR: Observateur d'API, etc.).
- 🚨 **Error Reporter** — Ring-buffer posledních 20 chyb integrace s anonymizovaným kontextem (model, firmware, stack trace).
- 🔘 **Reporter Pipeline:** oba sensory automaticky vytvářejí HA Repair notifikace s předvyplněným GitHub-Issue jako 1-klik linkem. Plus diagnostics-download se vším maskovaným pro fórum/Facebook.
- 🔒 **Slib soukromí:** Nic neopustí tvou HA bez tvého explicitního kliknutí. VINy maskovány, GPS zaokrouhlené na 1 desetinné místo, JWT/UUID/e-maily odstraněny. GDPR-compliant.

**🟢🟡⚫ Multi-Brand Connection-State (v1.8.12)**

Sensor `connection_state` (online / standby / offline) pro Audi, VW EU, Škoda, SEAT, CUPRA — první VAG integrace s centralizovaným stavem připojení. Brand-agnostický helper `compute_connection_state` s rekurzivním procházením `carCapturedTimestamp`.

**🔋 Monitoring 12V baterie + Smart-Wake (v1.12.0)**

- Sensor `voltage_12v` (V) + binary `warning_12v_low` při <11.5V — zabraňuje tichým výpadkům API kvůli vybité startovací baterii
- Sensor `wake_count_today` + soft-cap na 3 wakes/den (`_WAKE_BUDGET_PER_DAY`) chrání 12V před wake-loops, vyvolá `wake_budget_exhausted` PŘED API voláním

**💨 Optimistické UI pro Lock/Climate/Charging (v1.11.1)**

Switche se přepínají okamžitě po kliknutí (vzor myskoda PR #832), API roundtrip na pozadí. Při selhání: revert + ServiceValidationError. 8 actuator metod převedeno.

**🔋 PHEV-Range-Triple (v1.10.0 + #94 + #96 follow-up v v1.11.1)**

Tři explicitní range sensory: `electric_range_km`, `combustion_range_km`, `total_range_km`. Parser VW EU/Audi klasifikuje podle typu motoru (4 zdroje místo 2). Audi-diesel-fallback z `measurements.rangeStatus.value.dieselRange`. Ověřeno přes evcc-io/evcc#19045 + Audi Q4 sample + CarConnectivity logy.

**🔒 Read-only režim Fáze 1 (v1.12.0)**

Toggle možností "Read-only Mode" → přeskočí lock/switch/button(non-refresh)/climate/number platformy pro privacy/safety-konzervativní vlastníky. Sensors + binary_sensors + device_tracker zůstávají.

**⚡ Zapisovatelné Max-Charge-Current Number (v1.12.0)**

Slider 6-32A místo pouze read-only sensoru. Nový `command_set_max_charge_current` POST chargingSettings.

**💡 Per-Light Binary-Sensors (v1.12.0)**

Dynamicky per typ světla z dict `lights_individual` + agregáty `lights_on` + `lights_count`.

**🛠️ Defenzivní stabilita (v1.8.7 + v1.10.1)**

- 504-retry, transient-network-error retry, 6h stale-cache + tolerance 3 selhání
- Ochrana před token-refresh-storm (max 3/h) — zabraňuje IP banům
- Helpery `safe_int` / `safe_float` / `safe_enum` — tolerují backend quirks

**🚪 CUPRA Born 2026 Firmware-Shapes (v1.10.2 — Gerhardova #53 první live-validace)**

Field-name fallback řetězec: `battery.currentSocPercentage` (Born 2026) → `currentPct` (Rainer #109) → `currentSOC_pct` (legacy). Lowercase enum tolerance pro `"connected"` / `"locked"`. Zpětná kompatibilita zachována.

**🔓 Lock + Wake pro Audi/VW (v1.9.1, #92 Audi S6 C8)**

`command_lock` posílá nyní S-PIN pro Audi/VW (CARIAD BFF odpovídal `403 spin_error`). `command_wake` používá v1→v2 fallback.

**🛡️ Capability-Filter Fáze 2 (v1.9.1, #56)**

Body-sniffing `classify_command_failure` pro `missing-capability` / `subscription_expired` / `not_entitled` / `spin_error` markery. `_cariad_cmd` zapisuje každý výsledek do FeatureState. Command-bound entity (Lock/Climate/Switch/Buttons) jdou automaticky unavailable při definitivním "ne" backendu.

### ⚠️ Ještě v procesu / What's still in progress (plánované sessions)

- **v1.13.0 MINOR** — Anonymized Diagnostics-Export (#62) + Capability-Filter Fáze 3 (`capability.active && user-enabled` PRE-vytvoření-entity, skrývá tlačítka jako MyCupra aplikace) + Read-only Fáze 2/3 (Command-Locking + oddělení služeb cloud_refresh vs wake_vehicle).
- **v1.14.0 MINOR** — Trip Statistics z Audi `tripstatistics/v1` (#24, #35).
- **v1.15.0+ MINOR** — PPC Climate Body conditional shape (#29, #51), Theft/Alarm Binary (#33), Climate-Timer UI (#26).
- **v1.16.0 MINOR** — Lokalitně-specifický Cíl SoC nabíjení + nabíjecí profily (#25, #31).
- **v1.17.0 MINOR** — Remote Start ICE (#28, vzor audi_connect_ha #717).
- **v1.18.0 MINOR** — Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) pro real-time updaty bez pollingu (#57, #27).
- **v2.0.0 MAJOR** — HACS Default + Live-Tests všech značek + EU Data Act ready (pycupra `EUDAConnection` jako reference, deadline září 2026) (#13, #59).

### 🚫 Vědomé limity / Conscious limits

- **Image platforma:** neexistuje oficiální CARIAD render-image API. Image entita přejde v budoucí release na URL dodávané uživatelem.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — nová architektura E³ 1.2, ještě veřejně reverse-engineered (ani v audi_connect_ha ani v CarConnectivity). VAG Connect tato vozidla detekuje a dělá **graceful degradation** místo 404 chyb.
- **Ford / značky mimo VAG:** mimo rozsah — viz [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass) pro Ford.

### 🔧 Předpoklad ochrany soukromí

Aby GPS poloha, stav vozidla a topení fungovaly, musí být **"Sdílet mou polohu"** aktivní v tvé aplikaci My-VW / My-Audi / MySkoda / MyCupra — jinak backend odpovídá 403.

### 📚 Více informací / More info

- 🗺️ Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md) — kompletní P0/P1/P2/P3 priorizace všech otevřených issues
- 📜 Tech Changelog: [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md) — per release: field-mappings + architektonické rozhodnutí + externí source-refs
- 🤝 Session Handoff (pro přispěvatele a AI nástroje): [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md)
- 🔒 Pravidla soukromí a zacházení s daty: sekce [`CONTRIBUTING.md`](CONTRIBUTING.md) (post-#53 third-party review)
- 📋 FAQ Subscription / Service Plus / diagnóza `missing-capability`: FAQ sekce v [`CONTRIBUTING.md`](CONTRIBUTING.md)

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

## Plán / Roadmap

> 📍 **Single Source of Truth:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — kompletní P0/P1/P2/P3 priorizace se všemi ~20 otevřenými issues kategorizovanými.

### Poslední releases / Recent releases (2026-04-29 + 2026-04-30 + 2026-05-01)

| Verze | Obsah | Datum |
|---|---|---|
| v1.8.6–v1.8.12 | Foundation-Sprint: defenzivní stabilita, Capability-Filter Fáze 2, Multi-Brand Connection-State, všechny brand parsery na ověřených live API cestách | 2026-04-29 |
| v1.9.0 | 🛰️ Vehicle Data Scout + Error Reporter + Reporter Pipeline | 2026-04-29 |
| v1.9.1 | Audi/VW Lock + Wake hotfix (#92) + Capability-Filter Fáze 2 + Scout cesty #90/#91 | 2026-04-29 |
| v1.10.0–v1.10.2 | PHEV-Range-Triple (#94), Defensive Coding Fáze 2 (#58), CUPRA Born 2026 firmware (#53 Gerhard) | 2026-04-29/30 |
| v1.11.0–v1.11.1 | Closure Issue #91 (Light/Service/Number), Golf GTE Fuel-Range fix (#96), Optimistické UI (3B-Part-3) | 2026-04-30 |
| v1.12.0 | 🔋💡⚡🧯🔒 5-v-1 Sprint: 12V (#23) + Per-Light + Zapisovatelné Number + Smart-Wake (#55) + Read-only Fáze 1 (#63) | 2026-04-30 |
| v1.12.1 | Scout cesty #105/#106 + Gerhardova Born fixture (#53 se souhlasem) + #47 FAQ | 2026-04-30 |
| v1.12.2 | 🌟 **První komunitní Scout-Report** (Skoda #107 od tritanium73) | 2026-05-01 |
| **v1.12.3** | Scout cesty #111+#113+#114 sbalené s wildcard strategií (`fuelStatus.rangeStatus.value.*` etc.) | **2026-05-01** |

### Příští sessions / Next sessions

| Verze | Rozsah | Issues |
|---|---|---|
| **v1.13.0** ⭐ MINOR | Anonymized Diagnostics-Export + Capability-Filter Fáze 3 + Read-only Fáze 2/3 | #62, #56 Fáze 3, #63 Fáze 2/3 |
| **v1.14.0** MINOR | Trip Statistics z Audi `tripstatistics/v1` | #24, #35 |
| **v1.15.0+** MINOR | PPC Climate (#29, #51), Theft/Alarm Binary (#33), Climate-Timer UI (#26) | various |
| **v1.18.0** MINOR | Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) | #57, #27 |
| **v2.0.0** 🎉 MAJOR | HACS Default + Live-Tests všech značek + EU Data Act ready (deadline září 2026) | #13, #59 |

> Pořadí je **striktně P0 → P1 → P2**. Bug-fixy mají vždy přednost před funkcemi.

---

## Licence

Apache License 2.0 — [LICENSE](LICENSE)

**VAG Connect™** je neregistrovaná ochranná známka (™, ne ®). Prosíme, nepoužívejte tento název ve forkách, abyste předešli záměně.

Tato integrace je nezávislý komunitní projekt bez jakéhokoliv spojení s Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG nebo jakoukoliv pobočkou Volkswagen Group.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
