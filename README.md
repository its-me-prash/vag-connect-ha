```
 _   _  ___  _____   _____                             _
| | | |/ _ \|  __ \ /  __ \                           | |
| | | / /_\ \ |  \/ | /  \/ ___  _ __  _ __   ___  ___| |_
| | | |  _  | | __  | |    / _ \| '_ \| '_ \ / _ \/ __| __|
\ \_/ / | | | |_\ \ | \__/\ (_) | | | | | | |  __/ (__| |_
 \___/\_| |_/\____/  \____/\___/|_| |_|_| |_|\___|\___|\__|

  Home Assistant Integration  |  Audi . VW . Skoda . SEAT . CUPRA
```

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/github/v/release/Prash1407/vag-connect-ha)](https://github.com/Prash1407/vag-connect-ha/releases)
[![Lizenz](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](LICENSE)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)
[![Tests](https://img.shields.io/badge/Tests-18%2F18-brightgreen)](tests/)

**[English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Ich wollte meinen Audi in Home Assistant steuern, ohne drei verschiedene Integrationen parallel zu pflegen oder einen extra MQTT-Broker zu betreiben. Also hab ich das hier gebaut.

**VAG Connect** verbindet Home Assistant direkt mit den offiziellen Apps von Audi, VW, Skoda, SEAT und CUPRA. Keine Zwischenschicht, kein Docker, kein separater Dienst. Integration installieren, Zugangsdaten eingeben, fertig.

Die technische Arbeit dahinter hat vor allem Till Steinbach mit seinem [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)-Framework erledigt. Diese Integration ist im Grunde ein sauberer Home Assistant-Wrapper darum.

---

## Unterstuetzte Plattformen

```
sensor  |  binary_sensor  |  device_tracker  |  switch  |  button  |  climate  |  number
```

---

## Features

### Alle Marken

| Feature | Audi | VW EU | VW US/CA | Skoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|:---:|
| Tankfuellstand / Ladestand | + | + | + | + | + |
| Reichweite | + | + | + | + | + |
| Kilometerstand | + | + | + | + | + |
| Position (GPS-Karte) | + | + | + | + | + |
| Tueren Status | + | + | + | + | + |
| Fenster Status | + | + | + | + | + |
| Aussentemperatur | + | + | + | + | + |
| Klimatisierung Status | + | + | + | + | + |
| Verriegeln / Entriegeln | + | + | + | + | + |
| Klimatisierung starten/stoppen | + | + | + | + | + |
| Lichtsignal (Honk & Flash) | + | + | + | + | + |

### Elektro- und Hybridfahrzeuge

| Feature | Audi e-tron | VW ID | Skoda Enyaq | CUPRA Born |
|---|:---:|:---:|:---:|:---:|
| Ladestand (%) | + | + | + | + |
| Laden starten / stoppen | + | + | + | + |
| Ladziel setzen (Slider) | + | + | + | + |
| Ladestatus | + | + | + | + |
| Stecker verbunden | + | + | + | + |

### Nur Verbrenner

| Feature | Verfuegbarkeit |
|---|---|
| Oelstand | Audi, VW |
| Inspektion faellig (km) | Audi, VW, Skoda |
| Inspektionsdatum | Audi, VW, Skoda |
| Oelservice faellig (km) | Audi, VW |

---

## Installation

### Via HACS (empfohlen)

1. HACS oeffnen -> Integrationen -> ... -> Benutzerdefinierte Repositories
2. URL: `https://github.com/Prash1407/vag-connect-ha` , Kategorie: Integration
3. Nach **VAG Connect** suchen, installieren, HA neu starten

### Manuell

Den Ordner `custom_components/vag_connect/` in dein `config/custom_components/`-Verzeichnis kopieren, dann Home Assistant neu starten.

---

## Einrichtung

**Einstellungen -> Geraete & Dienste -> + Integration -> "VAG Connect"**

| Feld | Beschreibung | Pflicht |
|---|---|:---:|
| Marke | Audi / VW EU / VW US-CA / Skoda / SEAT-CUPRA | ja |
| E-Mail | Zugangsdaten aus der App | ja |
| Passwort | Zugangsdaten aus der App | ja |
| S-PIN | Benoetigt fuer Verriegelung | nein |
| Intervall | Abfrageintervall in Minuten (min. 5) | ja |

---

## Abfrageintervall

Standard: 15 Minuten. Nicht unter 5 Minuten gehen. Die Hersteller-APIs sind nicht fuer hohe Abfragerate ausgelegt und koennen bei Missbrauch den Account temporaer sperren.

---

## Services (Automationen)

```yaml
# Tuer verriegeln
service: vag_connect.lock
data:
  vin: "WAUZZZ4G7EN123456"

# Klimatisierung starten
service: vag_connect.start_climatisation
data:
  vin: "WAUZZZ4G7EN123456"

# Laden starten
service: vag_connect.start_charging
data:
  vin: "WAUZZZ4G7EN123456"

# Laden stoppen
service: vag_connect.stop_charging
data:
  vin: "WAUZZZ4G7EN123456"

# Lichtsignal
service: vag_connect.flash_lights
data:
  vin: "WAUZZZ4G7EN123456"

# Daten sofort aktualisieren (kein VIN-Parameter)
service: vag_connect.refresh_vehicle
```

---

## Debugging

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.vag_connect: debug
```

Fuer Bug-Reports: Einstellungen -> Geraete & Dienste -> VAG Connect -> ... -> Diagnose herunterladen. Die Datei enthaelt keine Passwoerter und keine GPS-Koordinaten.

---

## Versioning

Dieses Projekt nutzt [Semantic Versioning 2.0.0](https://semver.org/lang/de/).

```
MAJOR.MINOR.PATCH

MAJOR  Breaking changes (Entities umbenennen, Plattform entfernen)
MINOR  Neue Features (neue Marke, neue Sensoren, neue Sprache)
PATCH  Bugfixes, Uebersetzungskorrekturen, Abhaengigkeitsupdates
```

Aktuell: `0.x.y` (pre-stable). Version `1.0.0` erscheint wenn Audi, VW und Skoda stabil getestet sind.

---

## Mitmachen

PRs und Issues sind willkommen. Besonders gesucht:

- Tester mit **Porsche** (nutzt dieselbe CARIAD-API wie Audi)
- Tester mit **chinesischem VAG-Account** (CN-Region, andere Endpoints)
- Weitere Uebersetzungen -- eine neue Sprachdatei ist in 20 Minuten fertig, siehe [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Danksagungen

Dieses Projekt steht auf den Schultern von:

| Projekt | Autor | Beitrag |
|---|---|---|
| [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) | @tillsteinbach | API-Engine fuer alle VAG-Marken |
| [CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi) | @acfischer42 | Audi CARIAD-Connector |
| [CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen) | @tillsteinbach | VW WeConnect-Connector |
| [CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda) | @tillsteinbach | Skoda MySkoda-Connector |
| [CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra) | @tillsteinbach | SEAT/CUPRA MyCupra-Connector |
| [audi_connect_ha](https://github.com/audiconnect/audi_connect_ha) | @audiconnect | Inspiration und HA-Integrationspattern |
| [homeassistant-myskoda](https://github.com/skodaconnect/homeassistant-myskoda) | @skodaconnect | MQTT-Architektur-Referenz |
| [ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect) | @TA2k | API-Endpoint-Recherche |

---

## Rechtliches

Diese Integration nutzt inoffizielle APIs -- dieselben, die die offiziellen Apps nutzen. Sie ist weder von Audi AG, Volkswagen AG, CARIAD, Skoda Auto, SEAT S.A. noch von Nabu Casa autorisiert oder unterstuetzt.

Alle Markennamen sind Warenzeichen ihrer jeweiligen Inhaber. Lizenzen und Attributionen: [NOTICE.md](NOTICE.md).

---

*Gebaut von [prash1407](https://github.com/Prash1407) -- MIT Lizenz -- 2026*
