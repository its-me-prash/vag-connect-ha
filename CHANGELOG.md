# Changelog

Alle wesentlichen Änderungen werden hier dokumentiert.

Format: [Keep a Changelog 1.0.0](https://keepachangelog.com/de/1.0.0/)  
Versionierung: [Semantic Versioning 2.0.0](https://semver.org/lang/de/)

**Schema für pre-1.0.0:**
- `0.MINOR.0` — neue Features oder Breaking Changes
- `0.MINOR.PATCH` — Bugfixes zu einem MINOR-Release
- Ab `1.0.0`: Standard-Semver (MAJOR.MINOR.PATCH)

---

## [Unreleased]

### Added
- Porsche-Unterstützung: `cariad/auth/porsche.py` (Auth0) + `cariad/api/porsche.py` (api.ppa.porsche.com) — siehe Issue #9
- VW North America (US/CA): `cariad/auth/vw_na.py` + `cariad/api/vw_na.py`

### Changed
- _nothing yet_

### Fixed
- _nothing yet_

---

## [0.14.0] - 2026-04-12

### Added
- `cariad/api/factory.py` — `CariadClientFactory.create(brand, session, ...)` für alle 5 Marken
- `cariad/exceptions.py` — typisierte Fehlerhierarchie (AuthenticationError, RateLimitError, SpinError, TermsAndConditionsError, TwoFactorRequiredError, VehicleCommandError, VehicleNotFoundError)
- `config_flow.py` — `_validate_credentials` nutzt jetzt direkt CARIAD-Client statt CC-Import
- `switch.py` — Fensterheizung nutzt `VehicleData.window_heating_front` statt CC-Objekte

### Changed
- **Platinum Quality Scale:** 47/47 Regeln erfüllt, 0 todo
- `test-coverage` → done: 95 % (342 Tests, 1649 Zeilen gemessen)
- Alle Coordinator-Commands (`async_lock`, `async_unlock`, etc.) auf CARIAD-Client umgestellt
- `_tokenstore_path()` bereinigt — keine CC-Abhängigkeit mehr
- 467 Zeilen toten CC-Code aus `coordinator.py` entfernt (`_extract`, `_sync_vehicles_unlocked`, `_start_cc`, `_stop_cc`, `_on_cc_update`, `_run_command`)
- `NOTICE.md` neu: korrekte Referenz-Attribution, keine Dependencies mehr
- `CONTRIBUTING.md` neu: kein `pip install carconnectivity` mehr
- READMEs (8 Sprachen) auf aktuellen Stand gebracht
- Trademark-Claim korrigiert: ™ (unregistriert), nicht ® (registriert)

### Fixed
- mypy strict: `ClientTimeout` statt `int` in `base.py`
- mypy strict: `isinstance(result, VehicleData)` Guard in `coordinator.py` (3×)
- mypy strict: `form_action` str-Zuweisung in `idk.py`

### Removed
- Alle CarConnectivity-Verweise aus Source-Code, Tests, READMEs, Konfiguration
- `quality_scale.yaml` CC-Kommentare entfernt

---

## [0.13.0] - 2026-04-12

### Added
- Eigener CARIAD API Client vollständig in die Integration integriert
- `coordinator.async_setup()` neu: PKCE-Auth → Garage-Fetch → parallele Status-Fetches
- `coordinator._poll_loop()` — eigene async Polling-Schleife ersetzt CC Background-Thread

### Changed
- `manifest.json requirements: []` — zero externe Abhängigkeiten
- `async_shutdown()` — sauber ohne Executor-Job

### Removed
- CarConnectivity und alle 5 Brand-Connectors aus `manifest.json`

---

## [0.12.0] - 2026-04-12

### Added
- `cariad/` — eigenes CARIAD API Client Package (kein CarConnectivity mehr benötigt)
- `cariad/auth/idk.py` — clean-room PKCE/OIDC für VW EU, Audi, Škoda, SEAT, CUPRA
- `cariad/api/vw_eu.py` — Volkswagen EU: selectivestatus + alle Commands
- `cariad/api/audi.py` — Audi EU: VW EU + AZS/MBB Auth-Chain
- `cariad/api/skoda.py` — Škoda: mysmob.api.connect.skoda-auto.cz
- `cariad/api/seat_cupra.py` — SEAT/CUPRA: ola.prod.code.seat.cloud.vwgroup.com
- `cariad/models.py` — VehicleData dataclass (70 Felder), BrandConfig × 5, TokenSet
- `docs/research/` — VAG_GROUP_ECOSYSTEM.md, ARCHITECTURE_DECISION.md, ROADMAP.md, DEPENDENCY_AUDIT.md

### Changed
- Platinum Quality Scale: `async-dependency` ✅, `inject-websession` ✅ durch eigenen Client

---

## [0.11.0] - 2026-04-12

### Changed
- Lizenz: MIT → Apache 2.0 mit Trademark-Klausel für "VAG Connect"
- Copyright: Prash Balan (@its-me-prash) in allen 14 Python-Dateien

### Fixed
- `strict-typing` Platinum-Regel erfüllt: 0 mypy-Fehler unter `--disallow-untyped-defs --warn-return-any`
- Alle 15 Module vollständig typisiert

---

## [0.10.0] - 2026-04-12

### Added
- Automatische Erkennung des requests-Versionskonflikts (HA 2026.x vs CC ~2.32.5)
- Repair-Issue im HA Dashboard wenn CarConnectivity nicht installierbar
- `repairs.py` — `raise_issue_requirements_conflict()`, `raise_issue_auth_required()`

### Fixed
- Stabiler Betrieb auch wenn requests-Konflikt vorliegt: Fehler wird diagnostiziert statt stumm ignoriert

---

## [0.9.0] - 2026-04-11

### Fixed
- Python 3.11 Kompatibilität: `TypeAlias` statt `type` für Forward-References in `coordinator.py`

---

## [0.8.0] - 2026-04-11

### Added
- `diagnostics.py` — HA Diagnose-Endpoint mit GPS-Redaktion (Platinum: diagnostics ✅)
- `icons.json` — Action-Icons für alle 14 Services (Platinum: icon-translations ✅)
- Stale-Device-Bereinigung: Fahrzeuge die aus dem Account verschwinden werden entfernt (Gold: dynamic-devices ✅)
- 192 Tests, alle grün

### Changed
- Gold Quality Scale vollständig: runtime_data, reauth, reconfigure, ServiceValidationError, stale-devices

---

## [0.7.0] - 2026-04-09

### Added
- Abfahrtstimer-Unterstützung (Timer 1–3): `set_departure_timer` Service
- Separate Switch-Entitäten für jeden Timer
- `number.py` — Ziel-SoC als Number-Entity konfigurierbar

### Changed
- Gold Quality Scale: `runtime_data`, `reauth`-Flow, `reconfigure`-Flow, `ServiceValidationError` statt generischer Exception

---

## [0.6.0] - 2026-04-08

### Added
- `EntityCategory` für diagnostische Sensoren (Firmware, Ladetyp, Ladestationsname)
- 4 neue Sensoren: Ladeleistung kW, Ladegeschwindigkeit km/h, Akkutemperatur, Ölstand
- `entity_disabled_by_default` für selten benötigte Sensoren

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
- Fensterheizung: `is_on` zeigt korrekten Zustand nach manuellem Toggle

## [0.4.4] - 2026-04-04

### Fixed
- SEAT/CUPRA: Fehlende `user_id` führte zu 404 auf Garage-Endpoint

## [0.4.3] - 2026-04-03

### Fixed
- Klimatisierungstemperatur: Kelvin-zu-Celsius-Umrechnung für alle Marken korrekt

## [0.4.2] - 2026-04-03

### Fixed
- Ladeende-ETA: negativer Wert wenn Fahrzeug voll geladen

## [0.4.1] - 2026-04-02

### Fixed
- Config Flow: `reconfigure` verlor Scan-Intervall nach Speichern

## [0.4.0] - 2026-04-01

### Added
- Standort-Adresse als Sensor (Geocoding via OpenStreetMap)
- Fahrtrichtung (Heading) als Sensor
- Ladesäulen-Informationen: Name, Betreiber, Adresse, Leistung
- `auto_unlock_plug` Switch

### Changed
- Alle Sensoren haben `device_class` und `state_class` für HA Energy Dashboard

---

## [0.3.4] - 2026-03-31

### Fixed
- Škoda: Mehrfache Initialisierung des MQTT-Listeners

## [0.3.3] - 2026-03-30

### Fixed
- Audi: AZS-Token-Refresh funktioniert jetzt zuverlässig nach 1h

## [0.3.2] - 2026-03-29

### Fixed
- VW EU: `doors_individual` leer wenn `overallStatus == SAFE`

## [0.3.1] - 2026-03-28

### Fixed
- CUPRA: `command_wake` 405 statt 204 bei manchen Modellen ignoriert

## [0.3.0] - 2026-03-27

### Added
- Individuelle Tür-Sensoren (Fahrertür, Beifahrertür, Fondtüren, Kofferraum) — Issue #3 ✅
- Fensterstatus-Sensoren

### Changed
- Upgrade auf CarConnectivity 0.11.8

---

## [0.2.2] - 2026-03-25

### Fixed
- `log_when_unavailable`: mehrfache Fehlerlog-Einträge bei dauerhafter Nichterreichbarkeit

## [0.2.1] - 2026-03-24

### Fixed
- GPS-Koordinaten werden als `None` gesetzt statt `0.0` wenn nicht verfügbar

## [0.2.0] - 2026-03-23

### Added
- Ladeleistung-Sensor (kW) — Issue #2 ✅
- Ladegeschwindigkeit-Sensor (km/h)
- Ladeende-ETA-Sensor
- `start_charging` / `stop_charging` Services

---

## [0.1.1] - 2026-03-21

### Fixed
- HA 2024.x: `FlowResult` → `ConfigFlowResult` Typ-Kompatibilität

## [0.1.0] - 2026-03-20

### Added
- Erste öffentliche Version
- Unterstützung: VW EU, Audi, Škoda, SEAT, CUPRA
- Sensoren: Akkustand, Reichweite, Kilometerstand, GPS, Türen, Fenster, Klimatisierung, Laden
- Services: lock, unlock, start/stop Klimatisierung, flash, wake, refresh
- Config Flow mit reauth, reconfigure
- `force_enable_access` Option für ältere VW-Modelle — Issue #1 ✅
