# Changelog

Alle wesentlichen Änderungen werden hier dokumentiert.

Format: [Keep a Changelog 1.0.0](https://keepachangelog.com/de/1.0.0/)  
Versionierung: [Semantic Versioning 2.0.0](https://semver.org/lang/de/)

## Semver-Regeln für dieses Projekt (pre-1.0.0)

| Was | Version | Beispiel |
|---|---|---|
| Breaking Change, Architekturwechsel | `0.MINOR.0` | 0.10.0 → 0.11.0 |
| Neue Features, neue Sensoren/Services | `0.MINOR.0` | 0.10.0 → 0.11.0 |
| Bugfix, kleine Enhancement | `0.MINOR.PATCH` | 0.11.0 → 0.11.1 |
| Ab v1.0.0 | Standard `MAJOR.MINOR.PATCH` | 1.0.0 → 1.1.0 |

> **Hinweis:** Die Versionen 0.9.0–0.14.0 wurden am 2026-04-11/12 mit falschen
> Semver-Typen vergeben. Retroaktive Korrektur:
> `0.9.0→0.8.1`, `0.10.0→0.8.2`, `0.11.0→0.9.0`,
> `0.12.0→0.10.0`, `0.13.0→0.10.1`, `0.14.0→0.11.0`

---

## [Unreleased]

### Added
- Porsche-Unterstützung: `cariad/auth/porsche.py` (Auth0) + `cariad/api/porsche.py` — geplant v0.15.0, Issue #9
- VW North America (US/CA): separates Auth-System — geplant v0.16.0, Issue #10

---

## [0.14.2] - 2026-04-12

### Fixed
- **Audi/VW Login**: `_validate_credentials` nutzt jetzt eigene `aiohttp.ClientSession` mit frischem `CookieJar` — IDK-Auth-Flow ist stateful (Cookies zwischen den Steps), darf nicht die shared HA-Session verwenden
- **AZS Token Exchange (Audi)**: `id_token` statt `access_token` an AZS-Endpoint gesendet — `grant_type: id_token` erwartet das JWT `id_token`
- **VW US/CA aus Brand-Liste entfernt**: War in UI sichtbar obwohl noch nicht implementiert (wirft bei Konfiguration Exception)

### Changed
- Auth-Fehler werden jetzt mit `WARNING`/`ERROR` statt nur `DEBUG` geloggt — sichtbar in HA-Logs unter Einstellungen → System → Protokolle
- `idk.py`: Step-by-step Debug-Logging (Step 1: CSRF, Step 3: Redirect, Step 4: Token)

---

## [0.14.1] - 2026-04-12

### Changed
- Semver retroaktiv korrigiert: 0.9.0–0.14.0 → 0.8.1–0.11.0 (Dokumentation/Tags, intern)
- `iot_class`: `cloud_push` → `cloud_polling` (wir pollen, kein Push-Protokoll)
- CI: CarConnectivity-Dependencies entfernt, mypy + coverage-threshold hinzugefügt
- `icons.json`: Service-Icons für alle 14 Actions ergänzt
- `RELEASE_PROCESS.md`: aktuelle Semver-Tabelle und Checkpoints

### Fixed
- HACS-Update-Erkennung: Version war durch Retroaktiv-Korrektur unter installiertem Stand

---

## [0.11.0] - 2026-04-12

> Früher fälschlicherweise als `0.14.0` getaggt.

### Added
- 342 Tests, 95 % Coverage (1649 Zeilen gemessen)
- `CariadClientFactory` public export aus `cariad/__init__.py`
- `config_flow._validate_credentials` nutzt CARIAD-Client direkt

### Changed
- **Platinum Quality Scale:** 47/47 Regeln done, 0 todo, 2 exempt
- Coordinator-Commands vollständig auf CARIAD-Client umgestellt
- 467 Zeilen toten CC-Code aus `coordinator.py` entfernt
- `switch.py` Fensterheizung: `VehicleData.window_heating_front` statt CC-Objekte
- `NOTICE.md` neu: Referenz-Attribution, keine Dependencies
- READMEs (8 Sprachen) und Trademark-Claim (™, nicht ®) korrigiert

### Fixed
- mypy: `ClientTimeout` statt `int` in `base.py`
- mypy: `isinstance(result, VehicleData)` Guard in `coordinator.py` (3×)
- mypy: `form_action` str-Zuweisung in `idk.py`

### Removed
- Alle CarConnectivity-Verweise aus Source, Tests, READMEs

---

## [0.10.1] - 2026-04-12

> Früher fälschlicherweise als `0.13.0` getaggt.

### Removed
- CarConnectivity und alle 5 Brand-Connectors aus `manifest.json`
- `manifest.json requirements: []` — zero externe Abhängigkeiten bestätigt

---

## [0.10.0] - 2026-04-12

> Früher fälschlicherweise als `0.12.0` getaggt.

### Added
- `cariad/` — eigenes CARIAD API Client Package
- `cariad/auth/idk.py` — clean-room PKCE/OIDC für VW EU, Audi, Škoda, SEAT, CUPRA
- `cariad/api/vw_eu.py` — Volkswagen EU
- `cariad/api/audi.py` — Audi EU (VW EU + AZS/MBB Auth-Chain)
- `cariad/api/skoda.py` — Škoda (mysmob.api.connect.skoda-auto.cz)
- `cariad/api/seat_cupra.py` — SEAT/CUPRA (ola.prod.code.seat.cloud.vwgroup.com)
- `cariad/models.py` — `VehicleData` (70 Felder), `BrandConfig` × 5, `TokenSet`
- `docs/research/` — Ecosystem-Analyse, Architecture Decision Record, Dependency Audit

### Changed
- `inject-websession` ✅ — aiohttp Session wird per `async_get_clientsession(hass)` injiziert
- `async-dependency` ✅ — kein requests, kein Threading mehr

---

## [0.9.0] - 2026-04-12

> Früher fälschlicherweise als `0.11.0` getaggt.

### Changed
- Lizenz: MIT → **Apache 2.0** mit Trademark-Klausel für "VAG Connect"
- Copyright: Prash Balan (@its-me-prash) in allen Dateien

### Fixed
- `strict-typing` Platinum-Regel: 0 mypy-Fehler (`--disallow-untyped-defs --warn-return-any`)
- Alle 15 Module vollständig typisiert

---

## [0.8.2] - 2026-04-12

> Früher fälschlicherweise als `0.10.0` getaggt.

### Added
- Automatische Erkennung des requests-Versionskonflikts (HA 2026.x vs CC ~2.32.5)
- `repairs.py` — Repair-Issue im HA Dashboard

### Fixed
- Stabiler Betrieb auch bei requests-Konflikt

---

## [0.8.1] - 2026-04-11

> Früher fälschlicherweise als `0.9.0` getaggt.

### Fixed
- Python 3.11 Kompatibilität: `TypeAlias` statt `type` für Forward-References

---

## [0.8.0] - 2026-04-11

### Added
- `diagnostics.py` — HA Diagnose-Endpoint mit GPS-Redaktion
- `icons.json` — Action-Icons für alle 14 Services
- Stale-Device-Bereinigung bei Fahrzeugwechsel

### Changed
- Gold Quality Scale vollständig: `runtime_data`, `reauth`, `reconfigure`, `ServiceValidationError`

---

## [0.7.0] - 2026-04-09

### Added
- Abfahrtstimer (Timer 1–3): `set_departure_timer` Service — Issue #5 ✅
- `number.py` — Ziel-SoC als Number-Entity

### Changed
- Gold Quality Scale: `runtime_data`, `reauth`-Flow, `reconfigure`-Flow

---

## [0.6.0] - 2026-04-08

### Added
- `EntityCategory` für diagnostische Sensoren
- Sensoren: Ladeleistung kW, Ladegeschwindigkeit km/h, Akkutemperatur, Ölstand

---

## [0.5.0] - 2026-04-06

### Added
- Abfahrtstimer-Sensor (read-only): zeigt nächsten aktiven Timer

---

## [0.4.6] - 2026-04-05

### Fixed
- Coordinator-Crash wenn GPS-Daten `None` zurückgeben

## [0.4.5] - 2026-04-04

### Fixed
- Fensterheizung: `is_on` nach manuellem Toggle korrekt

## [0.4.4] - 2026-04-04

### Fixed
- SEAT/CUPRA: fehlende `user_id` → 404 auf Garage-Endpoint

## [0.4.3] - 2026-04-03

### Fixed
- Klimatisierungstemperatur: Kelvin→Celsius für alle Marken

## [0.4.2] - 2026-04-03

### Fixed
- Ladeende-ETA: negativer Wert wenn Fahrzeug voll geladen

## [0.4.1] - 2026-04-02

### Fixed
- Config Flow `reconfigure` verlor Scan-Intervall nach Speichern

## [0.4.0] - 2026-04-01

### Added
- Standort-Adresse als Sensor (OpenStreetMap Geocoding)
- Fahrtrichtung (Heading) als Sensor
- Ladesäulen-Informationen: Name, Betreiber, Adresse, Leistung
- `auto_unlock_plug` Switch

### Changed
- Alle Sensoren mit `device_class` und `state_class`

---

## [0.3.4] - 2026-03-31

### Fixed
- Škoda: Mehrfache Initialisierung des MQTT-Listeners

## [0.3.3] - 2026-03-30

### Fixed
- Audi: AZS-Token-Refresh nach 1h zuverlässig

## [0.3.2] - 2026-03-29

### Fixed
- VW EU: `doors_individual` leer wenn `overallStatus == SAFE`

## [0.3.1] - 2026-03-28

### Fixed
- CUPRA: `command_wake` 405 bei manchen Modellen ignoriert

## [0.3.0] - 2026-03-27

### Added
- Individuelle Tür-Sensoren (Fahrertür, Beifahrertür, Fond, Kofferraum) — Issue #3 ✅
- Fensterstatus-Sensoren

---

## [0.2.2] - 2026-03-25

### Fixed
- Mehrfache Fehlerlog-Einträge bei dauerhafter Nichterreichbarkeit

## [0.2.1] - 2026-03-24

### Fixed
- GPS: `None` statt `0.0` wenn nicht verfügbar

## [0.2.0] - 2026-03-23

### Added
- Ladeleistung-Sensor kW — Issue #2 ✅
- Ladegeschwindigkeit-Sensor km/h
- Ladeende-ETA-Sensor
- `start_charging` / `stop_charging` Services

---

## [0.1.1] - 2026-03-21

### Fixed
- HA 2024.x: `FlowResult` → `ConfigFlowResult` Kompatibilität

## [0.1.0] - 2026-03-20

### Added
- Erste Version: VW EU, Audi, Škoda, SEAT, CUPRA
- Sensoren: Akkustand, Reichweite, Kilometerstand, GPS, Türen, Fenster, Klimatisierung, Laden
- Services: lock, unlock, start/stop Klimatisierung, flash, wake, refresh
- `force_enable_access` für ältere VW-Modelle — Issue #1 ✅
