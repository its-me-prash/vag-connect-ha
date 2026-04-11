# Changelog

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
Versioning: [Semantic Versioning 2.0.0](https://semver.org/lang/de/)

---

## [Unreleased]

Geplant fuer 0.2.0:
- Porsche Connector (CARIAD-API, identisch zu Audi)
- MQTT Push-Updates statt reinem Polling
- Chinesische Region (CN-Endpoints)
- Fensterheizung als eigener Switch

---

## [0.1.0] - 2026-04-11

Erste oeffentliche Version.

### Hinzugefuegt

#### Kern-Integration
- Home Assistant Custom Component Struktur (`config_flow`, `coordinator`, alle Plattformen)
  _Autor: @prash1407_

- `DataUpdateCoordinator` mit vollstaendiger CarConnectivity-API-Integration
  _Implementiert nach Inspektion der echten CarConnectivity-Objekte:
  `vehicle.doors.lock_state.value`, `vehicle.charging.state.value`,
  `vehicle.drives.drives.values()` usw._
  _Autor: @prash1407 -- API-Quellen: @tillsteinbach (CarConnectivity)_

#### Unterstuetzte Marken
- **Audi** (myAudi / CARIAD `emea.bff.cariad.digital`)
  _Connector-Quelle: [CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi) von @acfischer42_
  _Endpoint-Recherche: [audi_connect_ha_q4](https://github.com/moritzwiechers/audi_connect_ha_q4) von @moritzwiechers_

- **Volkswagen EU** (WeConnect `emea.bff.cariad.digital`)
  _Connector-Quelle: [CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen) von @tillsteinbach_

- **Volkswagen US/CA** (VW Car-Net)
  _Connector-Quelle: [CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na) von @matpoulin / @zackcornelius_

- **Skoda** (MySkoda API)
  _Connector-Quelle: [CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda) von @tillsteinbach_
  _MQTT-Dokumentation: [myskoda](https://github.com/skodaconnect/myskoda) von @skodaconnect_

- **SEAT / CUPRA** (MyCupra API)
  _Connector-Quelle: [CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra) von @tillsteinbach_

#### HA-Plattformen
- `sensor` -- 14 Sensoren: Tankstand, Ladestand, Reichweite, Kilometerstand,
  Ladestatus, Steckerstatus, Ladziel, Klimastatus, Zieltemperatur,
  Aussentemperatur, Inspektionsdatum/-km, Oelservice-Datum/-km
  _Autor: @prash1407_

- `binary_sensor` -- 6 Sensoren: Tueren gesperrt/offen, Fenster offen,
  Ladekabel verbunden, Laedt, Klimatisierung aktiv
  _Autor: @prash1407_

- `device_tracker` -- GPS-Position auf HA-Karte
  _Autor: @prash1407_

- `switch` -- Tuerverriegelung, Klimatisierung, Laden (EV)
  _Autor: @prash1407_

- `button` -- Lichtsignal, Daten sofort aktualisieren
  _Autor: @prash1407_

- `climate` -- Vorklimatisierung mit Temperatursteuerung
  _HA-Architektur-Referenz: [homeassistant-myskoda](https://github.com/skodaconnect/homeassistant-myskoda) von @skodaconnect_
  _Autor: @prash1407_

- `number` -- Ladziel-Slider (10-100%), Klimatemperatur-Slider (16-30C)
  _Autor: @prash1407_

#### Services
- `vag_connect.lock` -- Tuer verriegeln
- `vag_connect.unlock` -- Tuer entriegeln (S-PIN erforderlich)
- `vag_connect.start_climatisation` -- Klimatisierung starten
- `vag_connect.stop_climatisation` -- Klimatisierung stoppen
- `vag_connect.start_charging` -- Laden starten (EV)
- `vag_connect.stop_charging` -- Laden stoppen (EV)
- `vag_connect.flash_lights` -- Lichtsignal (Honk & Flash)
- `vag_connect.refresh_vehicle` -- Sofortaktualisierung
  _Autor: @prash1407_

#### Uebersetzungen
- Deutsch (de) -- @prash1407
- Englisch (en) -- @prash1407
- Franzoesisch (fr) -- @prash1407
- Niederlaendisch (nl) -- @prash1407
- Spanisch (es) -- @prash1407
- Polnisch (pl) -- @prash1407
- Tschechisch (cs) -- @prash1407
- Schwedisch (sv) -- @prash1407

#### Entwicklung & Qualitaet
- 18 Unit-Tests (18/18 bestanden) mit echten CarConnectivity-Enums als Mocks
  _Autor: @prash1407_
- Ruff-Linting, vollstaendig clean
- GitHub Actions CI-Workflow (Ruff + Hassfest + HACS Validation)
- GitHub Actions Release-Workflow (automatisches ZIP bei `git tag v*`)
- Diagnostics-Endpoint (keine Passwoerter, keine GPS-Daten im Export)
  _HA-Vorlage: [HA Diagnostics Docs](https://developers.home-assistant.io/docs/diagnostics/)_
- Bug-Report und Feature-Request Issue-Templates

### Bekannte Einschraenkungen in 0.1.0

- Porsche noch nicht unterstuetzt (CARIAD-API vorhanden, kein Tester)
- China-Region (CN) nicht getestet, Endpoints moeglicherweise abweichend
- Kein MQTT Push -- nur Polling (geplant fuer 0.2.x)
- Fensterheizung noch kein eigener Switch

### Quellen und Recherche

Die API-Reverse-Engineering-Arbeit hinter dieser Integration stammt aus:

| Quelle | Relevanz |
|---|---|
| [ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect) von @TA2k | Breiteste VAG-API-Abdeckung, aktivste deutschsprachige Community |
| [myskoda MQTT-Dokumentation](https://myskoda.readthedocs.io/en/stable/mqtt/) | MQTT Push-Events fuer Skoda (auf Audi uebertragbar) |
| [audi_connect_ha](https://github.com/audiconnect/audi_connect_ha) | Urspruengliche Audi-HA-Integration, Pattern-Referenz |
| [vw-car-net-api](https://github.com/thomasesmith/vw-car-net-api) | Dokumentierter PKCE/OIDC Auth-Flow |
| [ioBroker VW-Connect Forum](https://forum.iobroker.net/topic/26438) | Aktivstes deutschsprachiges VAG-API-Forum |

---

## Format dieser Datei

Jeder Eintrag nennt:

1. **Was** wurde geaendert (konkret, kein Marketing)
2. **Wer** hat es gemacht (`@githubname`)
3. **Woher** kommt der Code/die Idee (Link zur Quell-Repo wenn vorhanden)

Kategorien: `Hinzugefuegt` / `Geaendert` / `Behoben` / `Entfernt` / `Sicherheit`
