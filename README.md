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
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-363%2F363-brightgreen?style=for-the-badge" alt="Tests"></a>
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

**80+ Entities** über **10 Plattformen**, **16 Services**. Alle 7 VAG-Marken in einer Integration — kein separates Plugin nötig.

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

### Bisher erreicht

| Version | Inhalt | Status |
|---|---|---|
| v1.0–v1.5 | 9 Plattformen, 7 Marken, Bugs & Entity-Audit | ✅ Done |
| v1.6.0 | SEAT/CUPRA 9 Endpoints, Škoda Fix, Audi PPC, Lock, Nachtabsenkung | ✅ Done |
| v1.7.0 | Škoda Komplett-Rewrite, Auto-Fachwörter alle Sprachen, Zuverlässigkeit | ✅ Done |

### Sessions-Plan (P0 → P2)

| Session | Version | Scope | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 | iot_class, per-VIN availability, S-PIN fail-fast, fake writables entfernt, Geocoding opt-in, Platforms-Sync | **#60** |
| **1.5 — Privacy & Auth Polish** | v1.8.1 | VIN-Maskierung in Logs/Diagnostics, ConfigEntryAuthFailed bei verlorenen Credentials, userPosition-Doku | — |
| **2 — Capabilities** | v1.8.2 | Capability-gated Entities, Subscription-Detection (2A→2B→2C) | #56, #68 |
| **3 — Command Profile** | v1.8.3 | Brand/Region/Plattform-Routing, RS e-tron GT Fix | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.4 | Anonymisierte Diagnostics, Regression-Tests | #62, #58 |
| **5 — Process & Governance** | — | Issue Forms, Brand Captains, CODEOWNERS, Privacy Guide | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Read-only Modus, Command Locking, Cloud vs Wake | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | MQTT Broker Integration | #57 |
| **9 — Feature Batch** | v1.10.0 | Verbrauchsdaten, Ladehistorie, Abfahrtstimer-UI, Alarm, Ladeprofile | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live-Tests alle Marken, Compatibility Matrix, EU Data Act ready | #13, #59 |

> Reihenfolge ist **strikt P0 → P1 → P2**. Sessions 1–4 sind nicht-verhandelbar bevor neue Features kommen.

---

## Lizenz

Apache License 2.0 — [LICENSE](LICENSE)

Diese Integration ist ein unabhängiges Community-Projekt ohne Verbindung zu Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG oder anderen VAG-Tochtergesellschaften.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
