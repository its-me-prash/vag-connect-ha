<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration für Audi · VW · Škoda · SEAT · CUPRA · Porsche · VW US/CA</strong><br>
  <em>Eine Integration für alle 7 VAG-Marken — direkter API-Zugriff, ohne Middleware</em>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="Lizenz"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.4%2B-blue" alt="Home Assistant"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/its-me-prash/vag-connect-ha/ci.yml?branch=main&label=CI" alt="CI"></a>
</p>

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

## 🚗 Was es kann

Verbindet Home Assistant **direkt** mit deinem Fahrzeug-Cloud-Account (myAudi, We Connect ID, MyŠkoda, MyCupra, MySeat, My Porsche, MyVW). **Keine Middleware, kein Docker, kein extra Dienst** — Anmeldung mit deinen App-Zugangsdaten, fertig.

- **80+ Entitäten** über **10 HA Plattformen** (Sensoren, Schalter, Klima, Lock, etc.)
- **14 Services** (Lock, Climate, Charging, Departure-Timer, etc.)
- **Vehicle-Bild als Device-Picture** + Custom-Lovelace-Card-Support
- **GPS-Position auf der HA-Map** als TrackerEntity
- **Multi-Vehicle-Support** pro Account
- **Read-only Modus** für sichere Anwendung in Automationen
- **HACS-Quality-Scale: Platinum** ⭐

> ✅ **Aktiv gepflegter Multi-Brand-Nachfolger** für [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archiviert 10/2025) und [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated 03/2025).

---

## 📋 Unterstützte Marken

| Marke | Backend | Status | Besonderheit |
|---|---|---|---|
| **Audi** (myAudi) | Cariad-BFF + MBB Legacy | ✅ Stable | PPC/PPE Klima, ICE Engine Start (#28) |
| **Volkswagen EU** (We Connect ID) | Cariad-BFF + MBB Legacy | ✅ Stable | PHEV Range-Triple, Tank-Level via MBB für Golf 7 GTE |
| **Škoda** (MyŠkoda mysmob) | Skoda mysmob | ✅ Stable | Charging-Profiles, OTA, Workshop-Attrs, Multi-Angle Renders |
| **SEAT** (MySEAT OLA) | OLA | ✅ Stable | OLA viewPoint Renders (4-7 Ansichten) |
| **CUPRA** (MyCupra OLA) | OLA | ✅ Stable | OLA viewPoint Renders, Born MY26 firmware shapes |
| **Porsche** (My Porsche) | PPA + Auth0 | ✅ Stable | Eigene HTTP-Hardening (retry/quota/storm-protection) |
| **VW US/CA** (myVW NA) | VW NA Cloud | 🟡 Beta | Charge ETA, Climate, Lock, Doors |

---

## 🚀 Installation (HACS)

### Option 1: One-Click Install (empfohlen)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=its-me-prash&repository=vag-connect-ha&category=integration)

### Option 2: HACS Custom Repository (manuell)

1. **HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories**
2. URL: `https://github.com/its-me-prash/vag-connect-ha`
3. Kategorie: **Integration**
4. **VAG Connect** suchen + installieren
5. **Home Assistant neu starten**

### Option 3: Manuelle Installation

```bash
cd /config/custom_components
git clone https://github.com/its-me-prash/vag-connect-ha.git
mv vag-connect-ha/custom_components/vag_connect .
rm -rf vag-connect-ha
# HA neu starten
```

---

## ⚙️ Konfiguration

**Settings → Devices & Services → Integration hinzufügen → "VAG Connect"**

| Feld | Beispiel | Beschreibung |
|---|---|---|
| Marke | `Audi`, `Volkswagen EU`, etc. | Welche Brand-App verwendest du? |
| E-Mail | `du@example.com` | Deine VAG-Account-Email |
| Passwort | `••••••••` | Dein Account-Passwort |
| S-PIN | `1234` *(optional)* | 4-stellige PIN für Lock/Unlock auf manchen Brands |

**Optionen** (Settings → Devices & Services → VAG Connect → ⋮ → Konfigurieren):

- **Polling-Intervall** (5-60 min) — Default 10 min. Niedriger = aktueller, frisst aber API-Quota schneller.
- **Read-only Modus** — wenn aktiv: nur Status-Sensoren, keine Schalter/Buttons die Befehle senden würden.
- **Reverse-Geocoding** (opt-in) — sendet GPS an OpenStreetMap für Adress-Auflösung.
- **Push-Toggles** (Skoda MQTT / CUPRA-SEAT FCM / Audi-VW FCM) — Foundation gelegt, Live-Activation pending Tester.

---

## 🎨 Was du bekommst

### Standard Entitäten pro Vehicle (alle Brands)

**Sensoren**: Battery SoC, Range (electric/combustion/total), Fuel Level, Odometer, Outside Temp, Battery Temp, 12V Voltage, Service Days, Oil Service Days, Charging Power/Rate/Type, Last Trip Stats, Charging History, Plug State, Lights Count, Equipment Count, Software Version, Quota Remaining, Connection State, Last Seen.

**Binary Sensors**: Doors Locked, Doors Open (per door), Windows Open (per window), Trunk/Hood/Sunroof, Plug Connected, Charging, OTA Update Available, 12V Low Warning, Lights On (per light), Vehicle Online.

**Steuerung**: Lock/Unlock, Climate Start/Stop, Charging Start/Stop, Window Heating, Window Heating Combined, Cabin Ventilation (CUPRA/SEAT), Aux Heating (Webasto, CUPRA/SEAT), Departure Timer (1-3 mit `time` platform), Set Target SoC, Set Target Temp, Set Max Charge Current, Set Charge Mode, Honk-and-Flash, Wake Vehicle, Refresh.

**Image Platform**: 1-7 Vehicle-Renders pro VIN (Audi/VW: GraphQL MediaService; CUPRA/SEAT: OLA viewPoints; Skoda: Widget + Multi-Angle Composites).

**Device Tracker**: GPS-Position als TrackerEntity (`source_type: gps`) für die HA Lovelace Map.

### Automatisches Vehicle-Bild

Das Auto erscheint als **Device-Picture** in HA, plus als `entity_picture` auf jedem Entity. Custom Lovelace Cards ([Ultra-Vehicle-Card](https://github.com/WJDDesigns/Ultra-Vehicle-Card), [vehicle-info-card](https://github.com/ngocjohn/vehicle-info-card), [Mushroom](https://github.com/piitaya/lovelace-mushroom) Templates) lesen `extra_state_attributes.image_url` automatisch.

---

## 🗺️ Lovelace-Beispiele

### Map Card

```yaml
type: map
title: Fuhrpark
default_zoom: 12
hours_to_show: 24
entities:
  - device_tracker.audi_a4_b9_position
  - device_tracker.vw_golf_7_gte_position
  - zone.home
```

### Picture-Entity Card mit Vehicle-Render

```yaml
type: picture-entity
entity: image.audi_a4_b9_render_side_lg
camera_view: live
show_state: false
show_name: false
```

### Vehicle-Info Card (Custom)

```yaml
type: custom:vehicle-info-card
entity: sensor.audi_a4_b9_battery_level
image: '[[ states.image.audi_a4_b9_render_side_lg.state ]]'
```

Mehr Beispiele in [`docs/FAQ.md#lovelace-examples`](docs/FAQ.md).

---

## 🔧 Häufige Fragen

| Frage | Antwort |
|---|---|
| **Wann wird mein Auto geweckt?** | Nur bei Service-Calls (Lock/Climate/Wake), niemals bei Status-Polls. Smart-Wake-Cap: max 3 Wakes/Tag pro Auto (Default), 5min Cooldown zwischen Wakes. |
| **Wie viel API-Quota?** | MyCupra/MySeat: ~1500 Calls/Tag. Bei 10min default Polling: ~144 Calls/Tag = 10% Budget. Sensor `requests_remaining_today` zeigt aktuellen Stand. |
| **Was wenn Tank-% bei Golf 7 GTE fehlt?** | v1.25.0 hat MBB VSR Phase 2 read-side fallback. Siehe [Golf 7 GTE Tank-Guide](docs/GOLF_7_GTE_TANK_GUIDE.md). |
| **Token bleibt nach HACS-Update?** | ✅ ja, seit v1.19.2 — Token-Persistence via HA `Store` (kein Re-Login mehr nach Updates). |
| **Wie melde ich Bugs?** | HA → Integration → 🔧 Reparieren → Bug-Report. Diagnostics werden anonymisiert (VINs gemaskt, GPS gerundet, Tokens gestrippt). |

Vollständige FAQ in [`docs/FAQ.md`](docs/FAQ.md).

---

## 🛡️ Privacy & Sicherheit

- **Keine externen Dienste** — alles geht direkt zwischen HA und Manufacturer-API
- **Token-Cache** lokal in HA's `.storage/` (per-config-entry, JSON, automatisch entfernt bei Integration-Removal)
- **Diagnostics anonymisiert**: VINs gemaskt (`***ABC123`), GPS auf 1 Decimal gerundet, Tokens/Passwörter komplett gestrippt
- **Reverse-Geocoding opt-in** — Default deaktiviert
- **VIN-Masking** durchgängig in allen Logs

Details in [`PRIVACY.md`](PRIVACY.md) und [`SECURITY.md`](SECURITY.md).

---

## 🛣️ Roadmap

**Aktueller Stand:** v1.25.0 (Sprint C — Cross-Brand Parity + UX/UI + MBB VSR Phase 2 für Golf 7 GTE Tank).

**Pending Tester** (siehe [`docs/EXTERNAL_BLOCKED_ROADMAP.md`](docs/EXTERNAL_BLOCKED_ROADMAP.md)):
- [#160 MBB Phase 2 write-side](https://github.com/its-me-prash/vag-connect-ha/issues/160) — Audi A4 B9 / Q5 2021 / Golf 7 / Passat B8 Owner
- [#161 Push Phase 2](https://github.com/its-me-prash/vag-connect-ha/issues/161) — Skoda Connect+ / MyCupra/MySeat / Audi+VW Cariad-modern Owner
- [#163 heaterSource](https://github.com/its-me-prash/vag-connect-ha/issues/163) — ID.4/7 / e-tron Heat-pump Owner

**Geplant für v1.26.0**: `device_action` + `device_trigger` (GUI-Automationen für Vehicles), `system_health.py`, `logbook.py`, CommandDispatcher Phase 2 refactor, weitere Translation-Coverage.

Vollständige Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## 🤝 Contributing

PRs willkommen — siehe [`CONTRIBUTING.md`](CONTRIBUTING.md).

**Vehicle Data Scout** (live seit v1.9.0): Wenn deine Integration unbekannte JSON-Felder erkennt, erstellt sie automatisch eine HA Repair-Notification mit pre-filled GitHub-Issue-Link. **1-Klick Bug-Report ohne dass du Code anschauen musst.**

Live-Tester gesucht für die external-blocked Tracks oben — Comment unter dem entsprechenden Issue mit `Brand + Modell + Jahr + Subscription-Status`.

---

## 📜 Lizenz

[Apache License 2.0](LICENSE) — siehe auch [`NOTICE.md`](NOTICE.md) für Attributions an Upstream-Projekte ([myskoda](https://github.com/skodaconnect/myskoda), [pycupra](https://github.com/WulfgarW/homeassistant-pycupra), [audi_connect_ha](https://github.com/audiconnect/audi_connect_ha), [volkswagencarnet](https://github.com/Trekky12/volkswagencarnet), [evcc](https://github.com/evcc-io/evcc)).
