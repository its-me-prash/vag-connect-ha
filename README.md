<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration für Audi · VW · Škoda · SEAT · CUPRA · Porsche · VW US/CA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Lizenz-Apache%202.0-blue.svg?style=for-the-badge" alt="Lizenz"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue?style=for-the-badge" alt="Home Assistant"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/its-me-prash/vag-connect-ha/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/downloads/its-me-prash/vag-connect-ha/total?style=for-the-badge&label=Downloads" alt="Downloads"></a>
</p>

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

**VAG Connect** verbindet Home Assistant direkt mit deinem Fahrzeug — ohne Middleware, ohne Docker, ohne extra Dienst. App-Zugangsdaten eingeben, fertig.

**80+ Entities** über **10 Plattformen**, **14 Services**. Alle 7 VAG-Marken in einer Integration — kein separates Plugin nötig.

> ✅ **Aktiv gepflegter Multi-Brand-Nachfolger** für [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archiviert am 29.10.2025) und [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated am 14.03.2025). Eine Integration für Audi, VW, Škoda, SEAT, CUPRA, Porsche und VW US/CA — kein separates Plugin pro Marke.

## Aktueller Stand & ehrliche Limits / Current Status & Honest Limits (v1.12.3)

VAG Connect entwickelt sich aktiv weiter. Damit du weißt, was funktioniert und was kommt:

### ✅ Was JETZT funktioniert (alle 7 Marken)

**🛰️ 1-Klick Bug-Reports & Feature-Wünsche (LIVE seit v1.9.0)**

Zwei diagnostische Sensoren mit gemeinsamer Reporter-Pipeline — **erste echte Live-Validation durch Community-User** in v1.10.2 (Gerhard / CUPRA Born), v1.12.2 (tritanium73 / Skoda) und v1.12.3 (DnnsJp74 / Audi):

- 🔬 **Vehicle Data Scout** — erkennt automatisch unbekannte JSON-Felder in der API deines Autos. Brand-lokalisiert in 8 Sprachen (DE: API-Beobachter, FR: Observateur d'API, etc.).
- 🚨 **Error Reporter** — Ring-Buffer der letzten 20 Integration-Fehler mit anonymisiertem Kontext (Modell, Firmware, Stack-Trace).
- 🔘 **Reporter Pipeline:** beide Sensoren erstellen automatisch HA Repair-Notifications mit pre-filled GitHub-Issue als 1-Klick-Link. Plus Diagnostics-Download mit allem maskiert für Forum/Facebook.
- 🔒 **Privacy-Versprechen:** Nichts verlässt deine HA ohne deinen expliziten Klick. VINs maskiert, GPS auf 1 Dezimalstelle gerundet, JWTs/UUIDs/Emails entfernt. GDPR-konform.

**🟢🟡⚫ Multi-Brand Connection-State (v1.8.12)**

Sensor `connection_state` (online / standby / offline) für Audi, VW EU, Škoda, SEAT, CUPRA — erste VAG-Integration mit centralisiertem Verbindungsstatus. Brand-agnostic Helper `compute_connection_state` mit recursive `carCapturedTimestamp` Walk.

**🔋 12V-Batterie Monitoring + Smart-Wake (v1.12.0)**

- `voltage_12v` Sensor (V) + `warning_12v_low` Binary bei <11.5V — verhindert silent API-Outages durch leere Starterbatterie
- `wake_count_today` Sensor + Soft-Cap auf 3 Wakes/Tag (`_WAKE_BUDGET_PER_DAY`) schützt 12V vor Wake-Loops, raised `wake_budget_exhausted` BEVOR API-Call

**💨 Optimistic UI für Lock/Climate/Charging (v1.11.1)**

Switches flippen sofort beim Klick (myskoda PR #832 Pattern), API-Roundtrip im Hintergrund. Bei Failure: revert + ServiceValidationError. 8 Actuator-Methoden umgestellt.

**🔋 PHEV-Range-Triple (v1.10.0 + #94 + #96 follow-up in v1.11.1)**

Drei explizite Range-Sensoren: `electric_range_km`, `combustion_range_km`, `total_range_km`. VW EU/Audi Parser klassifiziert nach Engine-Typ (4 Quellen statt 2). Audi-Diesel-Fallback aus `measurements.rangeStatus.value.dieselRange`. Verifiziert via evcc-io/evcc#19045 + Audi Q4 sample + CarConnectivity Logs.

**🔒 Read-only Mode Phase 1 (v1.12.0)**

Options-Toggle "Read-only Mode" → skip lock/switch/button(non-refresh)/climate/number Plattformen für Privacy/Safety-konservative Owner. Sensors + binary_sensors + device_tracker bleiben.

**⚡ Writeable Max-Charge-Current Number (v1.12.0)**

Slider 6-32A statt nur Read-only-Sensor. Neuer `command_set_max_charge_current` POST chargingSettings.

**💡 Per-Light Binary-Sensors (v1.12.0)**

Dynamisch pro Lichttyp aus `lights_individual` dict + Aggregate `lights_on` + `lights_count`.

**🛠️ Defensive Stabilität (v1.8.7 + v1.10.1)**

- 504-Retry, transient-network-error retry, 6h Stale-Cache + 3-Failure-Tolerance
- Token-Refresh-Storm-Schutz (max 3/h) — verhindert IP-Bans
- `safe_int` / `safe_float` / `safe_enum` Helper — toleriert Backend-Quirks

**🚪 CUPRA Born 2026 Firmware-Shapes (v1.10.2 — Gerhard's #53 erste Live-Validation)**

Field-Name-Fallback-Kette: `battery.currentSocPercentage` (Born 2026) → `currentPct` (Rainer #109) → `currentSOC_pct` (legacy). Lowercase enum tolerance für `"connected"`/`"locked"`. Backwards-compat erhalten.

**🔓 Lock + Wake für Audi/VW (v1.9.1, #92 Audi S6 C8)**

`command_lock` schickt jetzt S-PIN für Audi/VW (CARIAD BFF antwortete `403 spin_error`). `command_wake` nutzt v1→v2 Fallback.

**🛡️ Capability-Filter Phase 2 (v1.9.1, #56)**

`classify_command_failure` body-sniffing für `missing-capability`/`subscription_expired`/`not_entitled`/`spin_error` Marker. `_cariad_cmd` schreibt jedes Outcome in FeatureState. Command-bound Entities (Lock/Climate/Switch/Buttons) gehen automatisch unavailable bei definitivem Backend-No.

### ⚠️ Was noch in Arbeit ist / What's still in progress (geplante Sessions)

**Recent shipped (v1.13.0 → v1.20.0):**

- ~~**v1.13.0**~~ ✅ — Capability-Filter Phase 3 + Read-only Phase 2/3 + Anonymized Diagnostics
- ~~**v1.14.0**~~ ✅ — Trip Statistics + Audi ICE Engine Start (#24, #28)
- ~~**v1.15.0**~~ ✅ — Skoda Charging History + OTA + 8 cap-ids (#35)
- ~~**v1.16.0**~~ ✅ — HA `time` platform für Departure Timers + Skoda Charging Profiles (#25, #26, #31)
- ~~**v1.17.0–v1.17.4**~~ ✅ — Operational Hardening + Bruno-CI Stufe 2 COMPLETE (80/80 strict coverage)
- ~~**v1.17.5–v1.17.7**~~ ✅ — 5 Scout-Wellen + HomeRegion Foundation + Skoda outside_temperature + workshop attrs
- ~~**v1.18.0**~~ ✅ — **Skoda MQTT Push Foundation** (lazy-import; live activation pending Skoda Connect tester)
- ~~**v1.19.0**~~ ✅ — **CUPRA/SEAT FCM Push Foundation** (analog Skoda; pending MyCupra/MySeat tester)
- ~~**v1.19.1**~~ ✅ — Pycupra-style API Quota Sensor (X-RateLimit-Remaining)
- ~~**v1.19.2**~~ ✅ — **Token-Persistence** via HA `Store` (#118 fix, survives HACS-Updates)
- ~~**v1.19.3**~~ ✅ — Scout-Welle 6 silencing (5 Reports closed)
- ~~**v1.19.4**~~ ✅ — T&C Brand-Deeplinks + Quota Repair-Issue
- ~~**v1.20.0**~~ ✅ — **Bundle 2 Phase A**: Skoda widget + vehicle-info + equipment (myskoda PR #557 adoptiert)

**Geplant / Planned:**

- **v1.20.1 PATCH** — Skoda Bug-Fix: BinarySensor LOCK-class invert + S-PIN unlock check (#131 Chr1sDub) + Bundle 2 Phase B vehicle renders
- **v1.21.0 MINOR** — Charging Profile Write-Side (#25/#31 extension) ODER Departure-Timer UI Bundle (#132 follow-up)
- **v1.18.x / v1.19.x Patches** — Push Phase 2 Live-Activation sobald Community-Tester sich melden
- **v1.17.x Patch** — HomeRegion Wire-In wenn #75 Christian non-EU vehicle bestätigt
- **v2.0.0 MAJOR** — HACS Default + Live-Tests alle Marken + EU Data Act ready (pycupra `EUDAConnection` als Reference, September 2026 Deadline) (#13, #59).

### 🚫 Bewusste Limits / Conscious limits

- **Image-Plattform:** Kein offizielles CARIAD Render-Image-API existiert. Image-Entity wird in einer zukünftigen Release auf user-supplied URLs umgestellt.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — neue E³ 1.2 Architektur, öffentlich noch nicht reverse-engineered (auch nicht in audi_connect_ha oder CarConnectivity). VAG Connect erkennt diese Fahrzeuge und macht **graceful degradation** statt 404-Fehler.
- **Ford / nicht-VAG Marken:** Out of scope — siehe [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass) für Ford.

### 🔧 Privacy-Voraussetzung

Damit GPS-Position, Fahrzeugstatus und Standheizung funktionieren, muss in deiner My-VW / My-Audi / MySkoda / MyCupra-App **"Standort teilen"** aktiviert sein — sonst antwortet das Backend mit 403.

### 📚 Mehr Infos / More info

- 🗺️ Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md) — komplette P0/P1/P2/P3 Priorisierung aller offenen Issues
- 📜 Tech Changelog: [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md) — pro Release Field-Mappings + Architektur-Entscheidungen + externe Source-Refs
- 🤝 Session Handoff (für Mitwirkende & AI-Tools): [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md)
- 🔒 Privacy & data handling Rules: [`CONTRIBUTING.md`](CONTRIBUTING.md) Sektion (post-#53 third-party-review)
- 📋 FAQ Subscription / Service Plus / `missing-capability` Diagnose: [`CONTRIBUTING.md`](CONTRIBUTING.md) FAQ-Sektion

## Unterstützte Plattformen

```
sensor  |  binary_sensor  |  device_tracker  |  switch  |  button  |  climate  |  number  |  select  |  image  |  lock
```

---

## Unterstützte Marken

| Marke | Auth-System | API-Basis | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK PKCE | emea.bff.cariad.digital | ✅ Getestet |
| **Audi** | IDK PKCE + AZS | emea.bff.cariad.digital | ✅ Getestet |
| **Škoda** | IDK PKCE | mysmob.api.connect.skoda-auto.cz | ✅ Getestet |
| **SEAT** | IDK PKCE | ola.prod.code.seat.cloud.vwgroup.com | ✅ Getestet |
| **CUPRA** | IDK PKCE | ola.prod.code.seat.cloud.vwgroup.com | ✅ Getestet |
| **Volkswagen US/CA** | IDK PKCE (NA) | b-h-s.spr.{cc}00.p.con-veh.net | ⚗️ Beta — Tester gesucht |
| **Porsche** | Auth0 PKCE | api.ppa.porsche.com | ⚗️ Beta — Tester gesucht |

> **Beta-Marken:** Vollständig implementiert, noch ohne Live-Tester bestätigt. Feedback unter [Issues](https://github.com/its-me-prash/vag-connect-ha/issues) willkommen.

---

## Entities & Features

### Sensoren (27)

| Sensor | Beschreibung | Audi | VW EU | Škoda | SEAT/CUPRA |
|---|---|:---:|:---:|:---:|:---:|
| `odometer_km` | Kilometerstand | ✓ | ✓ | ✓ | ✓ |
| `fuel_level` | Tankstand % | ✓ | ✓ | — | ✓ |
| `battery_soc` | Akkustand % | ✓ | ✓ | ✓ | ✓ |
| `range_km` | Reichweite km | ✓ | ✓ | ✓ | — |
| `vehicle_state` | PARKED / DRIVING / CHARGING / OFFLINE | ✓ | ✓ | ✓ | ✓ |
| `charging_state` | CHARGING / READY_FOR_CHARGING / OFF | ✓ | ✓ | ✓ | ✓ |
| `plug_state` | CONNECTED / DISCONNECTED | ✓ | ✓ | ✓ | ✓ |
| `target_soc` | Ladziel % | ✓ | ✓ | ✓ | ✓ |
| `charging_power_kw` | Ladeleistung kW | ✓ | ✓ | ✓ | ✓ |
| `charging_rate_kmh` | Ladegeschwindigkeit km/h | ✓ | ✓ | ✓ | — |
| `charge_complete_eta` | Ladeende (Uhrzeit) | ✓ | ✓ | ✓ | — |
| `charging_type` | AC / DC | ✓ | ✓ | — | — |
| `climatisation_state` | Klimatisierungsstatus | ✓ | ✓ | ✓ | ✓ |
| `target_temperature` | Zieltemperatur °C | ✓ | ✓ | ✓ | ✓ |
| `outside_temp` | Außentemperatur °C | ✓ | ✓ | — | — |
| `service_km` | Nächste Inspektion km | ✓ | ✓ | ✓ | ✓ |
| `service_due_at` | Nächste Inspektion Tage | ✓ | ✓ | ✓ | — |
| `oil_service_km` | Ölwechsel km | ✓ | ✓ | ✓ | ✓ |
| `oil_service_at` | Ölwechsel Tage | ✓ | ✓ | — | — |
| `battery_temp` | Akkutemperatur °C | ✓ | ✓ | — | — |
| `adblue_range_km` | AdBlue-Reichweite km | ✓ | ✓ | — | — |
| `parking_address` | Standort-Adresse (Reverse Geocoding) | ✓ | ✓ | ✓ | ✓ |
| `parking_city` | Standort-Stadt | ✓ | ✓ | ✓ | ✓ |
| `last_updated_at` | Letztes API-Update | ✓ | ✓ | ✓ | ✓ |
| `departure_timer_1_time` | Abfahrtstimer 1 Uhrzeit | ✓ | ✓ | — | — |
| `departure_timer_2_time` | Abfahrtstimer 2 Uhrzeit | ✓ | ✓ | — | — |
| `departure_timer_3_time` | Abfahrtstimer 3 Uhrzeit | ✓ | ✓ | — | — |

### Binary Sensors (16)

| Binary Sensor | Beschreibung |
|---|---|
| `doors_locked` | Alle Türen verriegelt |
| `doors_open` | Mindestens eine Tür offen |
| `windows_open` | Mindestens ein Fenster offen |
| `connector_locked` | Ladekabel verriegelt |
| `plug_connected` | Ladekabel eingesteckt |
| `is_charging` | Lädt gerade |
| `is_driving` | Fährt gerade |
| `is_online` | Fahrzeug online |
| `climatisation_active` | Klimatisierung aktiv |
| `window_heating_front` | Frontscheibenheizung an |
| `window_heating_back` | Heckscheibenheizung an |
| `warning_active` | Mindestens eine Warnleuchte aktiv *(diagnostisch)* |
| `warning_engine` | Motorwarnung *(diagnostisch)* |
| `warning_oil` | Ölstandwarnung *(diagnostisch)* |
| `warning_tyre` | Reifendruckwarnung TPMS *(diagnostisch)* |
| `warning_brakes` | Bremswarnung *(diagnostisch)* |

### Schalter, Steuerung & Buttons

| Entity | Typ | Beschreibung |
|---|---|---|
| `lock_switch` | Switch | Verriegeln / Entriegeln |
| `climatisation_switch` | Switch | Klimatisierung an/aus |
| `charging_switch` | Switch | Laden an/aus |
| `window_heating_switch` | Switch | Fensterheizung an/aus |
| `seat_heating_switch` | Switch | Sitzheizung an/aus |
| `auto_unlock_switch` | Switch | Auto-Entriegelung beim Laden |
| `departure_timer_{1,2,3}_switch` | Switch | Abfahrtstimer 1–3 aktivieren |
| `target_soc` | Number | Ladziel 20–100 % |
| `min_soc` | Number | Mindest-SoC 0–100 % |
| `max_charge_current` | Number | Max. Ladestrom (A) |
| `target_temperature` | Number | Klimatisierungs-Zieltemperatur 16–30 °C |
| `charge_mode` | Select | MANUAL / TIMER / PREFERRED_CHARGING_TIMES |
| `climate.vorklimatisierung` | Climate | Vorklimatisierung mit Temperatursteuerung |
| `button.aufwecken` | Button | Fahrzeug aufwecken |
| `button.daten_aktualisieren` | Button | Sofortaktualisierung |
| `button.lichtsignal` | Button | Lichter blinken lassen |

---

## Fahrzeugbilder (Image-Plattform)

VAG Connect registriert **7 native `image`-Entities** pro Fahrzeug in Home Assistant.
Die Render-Bilder werden beim ersten Zugriff heruntergeladen und lokal unter `/config/www/vehicles/` gecacht (PNG, transparenter Hintergrund).

> **Aktuell mit Bildern:** Audi ✅ (AZS-Token bestätigt) | Škoda/SEAT/CUPRA experimentell | VW EU: kein bestätigter Endpoint ([Issue #37](https://github.com/its-me-prash/vag-connect-ha/issues/37))

### Verfügbare Image-Entities pro Fahrzeug

| Entity | Dateipfad | Ansicht | Größe | Empfohlen für |
|---|---|---|---|---|
| `image.{auto}_icon` | `{VIN}_icon.png` | 3/4-Ansicht | ~76 KB | Badges, Chip-Cards |
| `image.{auto}_small` | `{VIN}_small.png` | 3/4-Ansicht | ~117 KB | Kleine Karten, Sidebar |
| `image.{auto}_medium` | `{VIN}_medium.png` | 3/4-Ansicht | ~196 KB | Standard-Karten |
| `image.{auto}_side_small` | `{VIN}_side_small.png` | Seitenprofil | ~158 KB | Kompakte Seitenansicht |
| `image.{auto}_side_large` | `{VIN}_side_large.png` | Seitenprofil | ~309 KB | ⭐ **Lovelace-Karten** |
| `image.{auto}_angle_hd` | `{VIN}_angle_hd.png` | 3/4-Ansicht HD | ~1.7 MB | Hero-Banner, Vollbild |
| `image.{auto}_angle_large` | `{VIN}_angle_large.png` | 3/4-Ansicht groß | ~879 KB | Dashboard-Hauptkarte |

Alle Bilder auch als lokaler Pfad nutzbar: `/local/vehicles/{VIN}_{tag}.png`

### Lovelace-Beispiele

**Direktanzeige als Picture Entity (empfohlen):**
```yaml
type: picture-entity
entity: image.audi_s6_avant_side_large
show_name: false
show_state: false
```

**Mit Sensor-Daten-Overlay:**
```yaml
type: picture-entity
entity: sensor.audi_s6_avant_akkustand
image_entity: image.audi_s6_avant_angle_hd
name: "S6 Avant"
```

**Custom Button Card mit Hintergrundbild:**
```yaml
type: custom:button-card
entity: sensor.audi_s6_avant_reichweite
show_icon: false
styles:
  card:
    - background-image: url('/local/vehicles/WVWZZZ1KZAW000000_side_large.png')
    - background-size: contain
    - background-repeat: no-repeat
    - height: 180px
```

**Garage-View (mehrere Fahrzeuge):**
```yaml
type: horizontal-stack
cards:
  - type: picture-entity
    entity: image.audi_s6_avant_side_large
  - type: picture-entity
    entity: image.vw_golf_gte_side_large
```

> Die VIN eines Fahrzeugs findest du als Attribut auf jeder Image-Entity (Developer Tools → Zustände → Attribut `vin`).

---

## Empfohlene Lovelace-Cards / Recommended Lovelace Cards

Stand 2026-05-03. Diese Custom-Cards harmonieren gut mit unseren Sensor-/Image-/Switch-Entities. Wir recommendieren sie für deine Dashboards bis unsere eigene "Ultimate VAG Vehicle Card" released ist (geplant — siehe unten).

| Card | Wofür | Status | Repo |
|---|---|---|---|
| **flex-table-card** | Multi-Vehicle-Dashboards: Tabelle mit allen Fahrzeugen + Status (range, charge, locked, last_seen) als Spalten | ✅ aktiv (custom-cards Org) | [custom-cards/flex-table-card](https://github.com/custom-cards/flex-table-card) |
| **vehicle-info-card** | Single-Vehicle-Detailansicht mit Image + Charge + Climate + Doors | ⚠️ wenig Updates (war Mercedes-fokussiert) | [ngocjohn/vehicle-info-card](https://github.com/ngocjohn/vehicle-info-card) |
| **car-card** | Simple Charge-Status-Card mit visuellem Battery-Indicator (für EV-Schnellansicht) | ✅ aktiv | [flixlix/car-card](https://github.com/flixlix/car-card) |
| **Ultra-Vehicle-Card** | Polished Premium-Look (großes Render + animierte Details) — gute Inspiration für unser eigenes Card-Projekt | ✅ aktiv | [WJDDesigns/Ultra-Vehicle-Card](https://github.com/WJDDesigns/Ultra-Vehicle-Card) |

### 🚧 Geplant: Ultimate VAG Vehicle Card (eigenes Projekt)

Wir bauen eine **eigene HA Lovelace Card** speziell für VAG Connect. Inspiration aus den oberen drei Cards, aber:
- Volle Multi-Brand-Unterstützung (Audi/VW/Skoda/SEAT/CUPRA/Porsche/VW NA) mit brand-spezifischen Themes
- Direkte Integration mit unseren Service-Calls (lock, climate, send_destination, etc.)
- Battery + Range + Climate + Trip-Stats in einem zusammenhängenden View
- Optional: `browser_mod` Integration für interaktive Popups (z.B. Adress-Suche → `send_destination` Service)

**Status:** in Planung. Eigenes Repo (`vag-connect-lovelace-card`) wird in einer separaten Session aufgesetzt. Track-link bleibt hier sobald live.

### Browser-Mod Integration (optional)

[`thomasloven/hass-browser_mod`](https://github.com/thomasloven/hass-browser_mod) (1700+ stars, MIT, HACS Default) — bietet starke per-Browser-Steuerung. **Kein hard dependency** für VAG Connect, aber wenn du es nutzt, lassen sich coole Dinge bauen:

- **Vehicle-Alert-Popup** wenn 12V-Battery < 11.5V oder Wake-Budget exhausted
- **NFC-Tap → Quick-Command-Sheet** mit lock/unlock/climate buttons als Popup
- **Charging-Session-Screensaver** — Vehicle-Card auto-öffnet bei Lade-Start auf einem bestimmten Dashboard
- **Confirm-Popup** für `vag_connect.send_destination` ("Soll ich 'Office' an dein Auto senden?") bevor der Service aufgerufen wird

Recipe-Doc folgt in v1.18.0 unter `docs/recipes/browser-mod.md`.

---

## Services / Aktionen

| Service | Beschreibung | Parameter |
|---|---|---|
| `vag_connect.lock` | Fahrzeug verriegeln | `vin` |
| `vag_connect.unlock` | Entriegeln (S-PIN erforderlich) | `vin` |
| `vag_connect.start_climatisation` | Klimatisierung starten | `vin` |
| `vag_connect.stop_climatisation` | Klimatisierung stoppen | `vin` |
| `vag_connect.start_charging` | Laden starten | `vin` |
| `vag_connect.stop_charging` | Laden stoppen | `vin` |
| `vag_connect.start_window_heating` | Fensterheizung starten | `vin` |
| `vag_connect.stop_window_heating` | Fensterheizung stoppen | `vin` |
| `vag_connect.wake_vehicle` | Fahrzeug aufwecken | `vin` |
| `vag_connect.flash_lights` | Lichter blinken lassen | `vin` |
| `vag_connect.refresh_vehicle` | Sofortaktualisierung | — |
| `vag_connect.set_target_soc` | Ladziel setzen (20–100 %) | `vin`, `target_soc` |
| `vag_connect.set_climatisation_temperature` | Zieltemperatur (16–30 °C) | `vin`, `temperature` |
| `vag_connect.set_departure_timer` | Abfahrtstimer setzen | `vin`, `timer_id`, `enabled`, `time` |

---

## Installation

### HACS (empfohlen)

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/its-me-prash/vag-connect-ha` → Kategorie: Integration
3. **VAG Connect** installieren → Home Assistant neu starten
4. Einstellungen → Integrationen → **+ Integration** → **VAG Connect**

### Manuell

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Home Assistant neu starten.

---

## Konfiguration

| Feld | Pflicht | Beschreibung |
|---|---|---|
| Fahrzeugmarke | ✓ | Audi / VW EU / Škoda / SEAT / CUPRA / VW US/CA / Porsche |
| E-Mail | ✓ | Anmelde-E-Mail der Hersteller-App |
| Passwort | ✓ | App-Passwort |
| S-PIN | — | Nur für Verriegelung (unter Sicherheit in der App) |
| Abfrageintervall | — | Minuten (Standard: 5, Minimum: 5) |

**Welche App?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Bekannte Einschränkungen

- **S-PIN** für Verriegelung erforderlich — einmalig in der App unter Sicherheit eintragen
- **Polling** mindestens 5 Minuten — kürzere Intervalle riskieren temporäre Account-Sperren
- **2FA** — einmalig manuell in der App bestätigen, danach automatisch
- **VW EU Fahrzeugbilder** — kein bestätigter `vgql`-Endpoint bekannt; Audi-Bilder funktionieren
- **Alte Fahrzeuge** (kein CARIAD-Support, `GDC_MISSING`) — werden automatisch übersprungen
- **Warnleuchten** — derzeit nur VW EU / Audi; andere Marken in Arbeit
- **Nicht verfügbar:** Ladesäulen-Infos, Kennzeichen, WLTP-Reichweite, Akkukapazität, Fahrtrichtung (diese Daten liefert die CARIAD API generell nicht)

---

## Technischer Hintergrund

### Eigener CARIAD-Client

```
cariad/
  auth/idk.py        ← IDK PKCE/OIDC (VW, Audi, Škoda, SEAT, CUPRA, VW NA)
  auth/porsche.py    ← Auth0 PKCE (Porsche)
  api/vw_eu.py       ← VW EU (CARIAD BFF emea.bff.cariad.digital)
  api/audi.py        ← Audi: CARIAD BFF + AZS Token für Fahrzeugbilder
  api/skoda.py       ← Škoda (mysmob API)
  api/seat_cupra.py  ← SEAT / CUPRA (OLA API)
  api/porsche.py     ← Porsche (PPA API)
  api/vw_na.py       ← VW US/CA (NA Auth-Server)
  api/graphql.py     ← Fahrzeugbilder via vgql (Audi bestätigt)
  models.py          ← VehicleData, BrandConfig
  exceptions.py      ← Typisierte Fehlerhierarchie
```

- **Keine externen Abhängigkeiten** — `requirements: []`
- **Pure aiohttp** — HA-Session wird injiziert
- **Clean-room** — kein GPL-Code, Endpoints aus MIT/Apache-Projekten

---

## Roadmap

> 📍 **Single Source of Truth:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — komplette P0/P1/P2/P3 Priorisierung mit allen ~20 offenen Issues kategorisiert.

### Letzte Releases / Recent releases (2026-04-29 + 2026-04-30 + 2026-05-01)

| Version | Inhalt | Date |
|---|---|---|
| v1.8.6–v1.8.12 | Foundation-Sprint: Defensive Stabilität, Capability-Filter Phase 2, Multi-Brand Connection-State, alle Brand-Parser auf verifizierten Live-API-Pfaden | 2026-04-29 |
| v1.9.0 | 🛰️ Vehicle Data Scout + Error Reporter + Reporter Pipeline | 2026-04-29 |
| v1.9.1 | Audi/VW Lock + Wake Hotfix (#92) + Capability-Filter Phase 2 + Scout-Pfade #90/#91 | 2026-04-29 |
| v1.10.0–v1.10.2 | PHEV-Range-Triple (#94), Defensive Coding Phase 2 (#58), CUPRA Born 2026 Firmware (#53 Gerhard) | 2026-04-29/30 |
| v1.11.0–v1.11.1 | Issue #91 Closure (Light/Service/Number), Golf GTE Fuel-Range Fix (#96), Optimistic UI (3B-Part-3) | 2026-04-30 |
| v1.12.0 | 🔋💡⚡🧯🔒 5-in-1 Sprint: 12V (#23) + Per-Light + Writeable Number + Smart-Wake (#55) + Read-only Phase 1 (#63) | 2026-04-30 |
| v1.12.1 | Scout-Pfade #105/#106 + Gerhard's Born Fixture (#53 mit Consent) + #47 FAQ | 2026-04-30 |
| v1.12.2 | 🌟 **Erstes Community-Scout-Report** (Skoda #107 von tritanium73) | 2026-05-01 |
| **v1.12.3** | Scout-Pfade #111+#113+#114 bundled mit Wildcard-Strategie (`fuelStatus.rangeStatus.value.*` etc.) | **2026-05-01** |

### Nächste Sessions / Next sessions

| Version | Scope | Issues |
|---|---|---|
| **v1.13.0** ⭐ MINOR | Anonymized Diagnostics-Export + Capability-Filter Phase 3 + Read-only Phase 2/3 | #62, #56 Phase 3, #63 Phase 2/3 |
| **v1.14.0** MINOR | Trip Statistics aus Audi `tripstatistics/v1` | #24, #35 |
| **v1.15.0+** MINOR | PPC Climate (#29, #51), Theft/Alarm Binary (#33), Klima-Timer UI (#26) | various |
| **v1.18.0** MINOR | Push CUPRA/SEAT (Firebase FCM) + Push Skoda (mysmob MQTT) | #57, #27 |
| **v2.0.0** 🎉 MAJOR | HACS Default + Live-Tests alle Marken + EU Data Act ready (Sept 2026 Deadline) | #13, #59 |

> Reihenfolge ist **strikt P0 → P1 → P2**. Bug-Fixes haben immer Vorrang vor Features.

---

## Lizenz

Apache License 2.0 — [LICENSE](LICENSE)

Diese Integration ist ein unabhängiges Community-Projekt ohne Verbindung zu Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG oder anderen VAG-Tochtergesellschaften.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
