<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration für Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Lizenz-Apache%202.0-blue.svg?style=for-the-badge" alt="Lizenz"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue?style=for-the-badge" alt="Home Assistant"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-337%2F337-brightgreen?style=for-the-badge" alt="Tests"></a>
  <a href="custom_components/vag_connect/quality_scale.yaml"><img src="https://img.shields.io/badge/Quality%20Scale-Platinum%20%F0%9F%8F%86-gold?style=for-the-badge" alt="Platinum"></a>
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

**VAG Connect** verbindet Home Assistant direkt mit deinem Audi, VW, Škoda, SEAT, CUPRA, Porsche oder VW US/CA — ohne Middleware, ohne Docker, ohne extra Dienst. App-Zugangsdaten eingeben, fertig.

68 Entities über 7 Plattformen, 14 Services, cloud-push Architektur. Alle 7 VAG-Marken in einer Integration — kein separates Plugin pro Marke nötig.

Ab v0.14.1 spricht VAG Connect **direkt** mit der CARIAD-API über einen eigenen async-Client. Kein CarConnectivity, keine externe Abhängigkeit, kein Upstream-Blocker.

## Unterstützte Plattformen

```
sensor  |  binary_sensor  |  device_tracker  |  switch  |  button  |  climate  |  number
```

---

## Unterstützte Marken

| Marke | Auth-System | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK PKCE | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK PKCE | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK PKCE | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK PKCE | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK PKCE | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **Volkswagen US/CA** | IDK PKCE (NA) | b-h-s.spr.{cc}00.p.con-veh.net | ✅ Beta — Tester gesucht |
| **Porsche** | Auth0 PKCE | api.ppa.porsche.com | ✅ Beta — Tester gesucht |

> **Beta-Marken (VW US/CA + Porsche):** Die Integration ist vollständig implementiert und wurde gegen die dokumentierten APIs entwickelt — aber noch ohne echten Live-Test mit einem echten Fahrzeug. Feedback und Bug-Reports unter [Issues](https://github.com/its-me-prash/vag-connect-ha/issues) sehr willkommen.

---

## Features

### Alle Fahrzeuge

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA | VW US/CA | Porsche |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Tankstand / Akkustand | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reichweite | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Kilometerstand | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| GPS-Position | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Türen gesamt + einzeln | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fenster | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Motorhaube / Kofferraum | ✓ | ✓ | — | — | ✓ | ✓ |
| Klimatisierung start/stop | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Zieltemperatur setzen | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Verriegeln / Entriegeln | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lichter blinken | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fahrzeug aufwecken | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Servicefälligkeit km/Tage | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| Online-Status | ✓ | ✓ | ✓ | ✓ | ✓ | — |

### Elektro- & Hybridfahrzeuge

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA | VW US/CA | Porsche |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Akkustand % | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Elektrische Reichweite | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ladezustand | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ladeleistung kW | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Ladegeschwindigkeit km/h | ✓ | ✓ | ✓ | ✓ | — | — |
| Ladeende-ETA | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Stecker-Status | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Laden start/stop | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ladeziel % setzen | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fensterheizung | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Abfahrtstimer 1–3 | ✓ | ✓ | — | — | ✓ | ✓ |
| Akkutemperatur | ✓ | ✓ | — | — | — | — |
| AdBlue-Reichweite | ✓ | ✓ | — | — | — | — |

---

## Fahrzeugbilder in Lovelace

VAG Connect lädt automatisch bis zu 7 Render-Bilder pro Fahrzeug (PNG, transparenter Hintergrund).
Die Bilder werden lokal unter `/config/www/vehicles/` gecacht.

### Verfügbare Bildvarianten

| Entity-Suffix | MediaType | Ansicht | Größe | Empfehlung |
|---|---|---|---|---|
| `render_icon` | MS_MYP3 | 3/4-Ansicht | ~76 KB | Mini-Icons, Badges, Chip-Cards |
| `render_small` | MS_MYP4 | 3/4-Ansicht | ~117 KB | Kleine Karten, Sidebar |
| `render_medium` | MS_MYP5 | 3/4-Ansicht | ~196 KB | Standard-Karten, Grid |
| `render_side_sm` | MYAPN3NB | Seitenprofil | ~158 KB | Kompakte Seitenansicht |
| `render_side_lg` | MYAPN8NB | Seitenprofil | ~309 KB | ⭐ **Lovelace-Karten (empfohlen)** |
| `render_angle_hd` | MYAAN3NB | 3/4-Ansicht | ~1.7 MB | Hero-Banner, Vollbild |
| `render_angle_lg` | MYAAN8NB | 3/4-Ansicht | ~879 KB | Dashboard-Karten |

### Picture-Entity Card

```yaml
type: picture-entity
entity: sensor.audi_s6_avant_kilometerstand
image: /local/vehicles/WAUZZZF29MN0XXXXX_side_large.png
name: "S6 Avant"
```

### Button Card mit Fahrzeugbild

```yaml
type: custom:button-card
entity: sensor.audi_s6_avant_tankstand
show_icon: false
styles:
  card:
    - background-image: url('/local/vehicles/WAUZZZF29MN0XXXXX_side_large.png')
    - background-size: contain
    - background-position: center
    - background-repeat: no-repeat
    - height: 200px
```

### Mushroom Card

```yaml
type: custom:mushroom-entity-card
entity: sensor.audi_s6_avant_kilometerstand
icon: ''
picture: /local/vehicles/WAUZZZF29MN0XXXXX_icon.png
name: "S6 Avant"
```

### Garage-View (mehrere Fahrzeuge)

```yaml
type: horizontal-stack
cards:
  - type: picture-entity
    entity: sensor.audi_s6_avant_kilometerstand
    image: /local/vehicles/VIN1_side_large.png
  - type: picture-entity
    entity: sensor.vw_id4_kilometerstand
    image: /local/vehicles/VIN2_side_large.png
```

> **Tipp:** Die VIN findest du als Attribut auf jeder Image-Entity (`vin` in den Entitäts-Attributen) oder im Fahrzeugschein.


---

## Installation

### HACS (empfohlen)

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Kategorie: Integration
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
| E-Mail | ✓ | Anmelde-E-Mail aus der Hersteller-App |
| Passwort | ✓ | Passwort aus der App |
| S-PIN | — | Nur für Verriegelung (unter Sicherheit in der App) |
| Abfrageintervall | — | Minuten zwischen Aktualisierungen (Standard: 5) |

**Welche App?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Services / Aktionen

| Aktion | Beschreibung |
|---|---|
| `vag_connect.lock` | Fahrzeug verriegeln |
| `vag_connect.unlock` | Entriegeln (S-PIN erforderlich) |
| `vag_connect.start_climatisation` | Klimatisierung starten |
| `vag_connect.stop_climatisation` | Klimatisierung stoppen |
| `vag_connect.start_charging` | Laden starten |
| `vag_connect.stop_charging` | Laden stoppen |
| `vag_connect.set_target_soc` | Ladziel setzen (20–100 %) |
| `vag_connect.set_climatisation_temperature` | Zieltemperatur (16–30 °C) |
| `vag_connect.start_window_heating` | Fensterheizung starten |
| `vag_connect.stop_window_heating` | Fensterheizung stoppen |
| `vag_connect.flash_lights` | Lichter blinken lassen |
| `vag_connect.wake_vehicle` | Fahrzeug aufwecken |
| `vag_connect.set_departure_timer` | Abfahrtstimer setzen |
| `vag_connect.refresh_vehicle` | Sofortaktualisierung |

---

## Technischer Hintergrund

### Eigener CARIAD-Client (seit v0.10.0)

```
cariad/
  auth/idk.py      ← PKCE/OIDC für alle IDK-Marken (clean-room)
  api/vw_eu.py     ← Volkswagen EU
  api/audi.py      ← Audi (VW EU + AZS/MBB)
  api/skoda.py     ← Škoda
  api/seat_cupra.py← SEAT / CUPRA
  models.py        ← VehicleData (70 Felder), BrandConfig
  exceptions.py    ← Typisierte Fehlerhierarchie
```

- **Keine externen Abhängigkeiten** — `requirements: []`
- **Pure aiohttp** — HA's Session wird injiziert (`inject-websession` ✅)
- **Clean-room** — kein GPL-Code kopiert, alle Endpoints aus MIT/Apache-Projekten

### Platinum Quality Scale — alle 47 Regeln erfüllt

| Ebene | Status |
|---|---|
| Bronze (16) | ✅ |
| Silver (13) | ✅ |
| Gold (14) | ✅ |
| **Platinum (4)** | ✅ |

`strict-typing` · `async-dependency` · `inject-websession` · `test-coverage` (95 %, 342 Tests)

---

## Bekannte Einschränkungen

- **S-PIN** für Verriegelung notwendig — in der App unter Sicherheit eintragen
- **Polling-Intervall** mindestens 5 Minuten — zu kurz führt zur temporären Account-Sperre
- **2FA** — einmalig manuell in der App bestätigen, danach automatisch
- **Porsche** — eigenständiges Auth0-System, geplant für v0.15.0
- **VW North America** — separater Auth-Server, geplant für v0.16.0
- **VW China 2026+** — neue CEA/XPeng-Plattform, API nicht öffentlich, kein ETA

---

## Roadmap

| Version | Inhalt |
|---|---|
| ✅ v0.14.1 | Platinum, eigener CARIAD-Client |
| 🔜 v0.15.0 | Porsche (Auth0 + PPA-API) |
| 🔜 v0.16.0 | VW North America (US/CA) |
| 🎯 v1.0.0 | HACS Official |

---

## Lizenz

Apache License 2.0 — [LICENSE](LICENSE)

**VAG Connect™** ist ein Markenzeichen (™, nicht ®, nicht registriert). Forks sollten diesen Namen nicht verwenden, um Verwechslungen zu vermeiden.

Diese Integration ist ein unabhängiges Community-Projekt ohne Verbindung zu Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG oder anderen VAG-Tochtergesellschaften.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
