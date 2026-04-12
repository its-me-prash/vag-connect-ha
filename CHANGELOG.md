# Changelog

Alle wesentlichen Änderungen werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
Versioning: [Semantic Versioning 2.0.0](https://semver.org/lang/de/)

Commit-Konvention: [Conventional Commits](https://www.conventionalcommits.org/de/)
```
feat:     Neue Funktion
fix:      Bugfix
docs:     Nur Dokumentation
refactor: Kein neues Feature, kein Bug
test:     Tests hinzugefügt/geändert
chore:    Build-Prozess, Abhängigkeiten
ci:       CI/CD-Änderungen
```

---

## [Unreleased]

Geplant für 0.11.0+:
- `strict-typing` vollständig — mypy --strict ohne Upstream-Einschränkungen
- `test-coverage` >85% — HA Integration Test Framework Setup
- HACS offizieller Antrag wenn genug Tester

### Feature-Backlog (nach requests-Fix)

**Priorität 1 — Fehlende Sensoren aus CARIAD-API:**
- `adblue_level` — AdBlue-Stand für Diesel
- `hood_closed` — Motorhaube offen/zu
- `trunk_closed` / `trunk_locked` — Kofferraum separat
- `sunroof_closed` — Schiebedach-Status
- `parking_time` — Zeitstempel letztes Parken
- `hv_battery_min_temperature` / `hv_battery_max_temperature` — Akku-Temperaturbereich
- `gas_level` / `gas_range` — CNG/Erdgas-Fahrzeuge

**Priorität 2 — Trip-Statistiken (volkswagencarnet hat 424 Properties):**
- `last_trip_duration`, `last_trip_length`, `last_trip_average_speed`
- `last_trip_average_fuel_consumption`, `last_trip_average_electric_engine_consumption`
- `last_trip_average_recuperation` — Rekuperation pro Fahrt
- `longterm_trip_*` — Langzeit-Durchschnitte
- Benötigt: Prüfen ob CarConnectivity trip data exposed

**Priorität 3 — UX-Verbesserungen:**
- VIN-Auswahl im Config Flow (inspiriert von marksieczkowski/ha-volkswagen)
- Pre-Heater Support für Verbrenner (audiconnect hat das)
- Connector LED-Farbe wenn CC Issue #122 gefixt

**Strategisch (falls CC dauerhaft broken):**
- Eigene CARIAD-API direkt (`emea.bff.cariad.digital`) — beide konkurrierenden
  Integrationen nutzen dieselbe API. Fork von volkswagencarnet + Multi-Brand-Support.
  Aufwand: sehr hoch. Nur wenn @tillsteinbach langfristig inaktiv.

### Ecosystem-Analyse (Stand April 2026)

| Integration | API-Backend | Status | Stars | requests-OK |
|---|---|---|---|---|
| **vag-connect-ha** | CarConnectivity | 🟡 requests-Blocker | 0 | ❌ |
| audiconnect | CARIAD BFF direkt | 🟡 läuft, neue Modelle 2025 kaputt | 325 | ✅ |
| volkswagencarnet | CARIAD BFF direkt | 🟢 läuft, Stabilitäts-Bugs | 502 | ✅ |
| marksieczkowski/ha-volkswagen | CC + VW NA | 🟡 WIP, requests-Blocker | 0 | ❌ |
| skodaconnect | Eigene API | 🔴 archiviert (Skoda Connect abgeschaltet 2024) | 104 | ✅ |

**Warum skodaconnect archiviert:** Škoda hat skoda-connect.com Ende 2024 abgeschaltet
und Nutzer auf MyŠkoda migriert. Die alte API existiert nicht mehr.
Škoda ist jetzt über CarConnectivity (connector-skoda) erreichbar.

**Fallback-Entscheidung:** Kein Fallback auf volkswagencarnet/audiconnect solange
CarConnectivity verfügbar ist. Beide haben aktive API-Bugs (audiconnect: 502 bei
Klimatisierung, GPS-Probleme; volkswagencarnet: State-Detection falsch, Task-Exceptions).
Erst Phase 2/3 wenn CC langfristig inaktiv bleibt.
- `strict-typing` vollständig — mypy --strict ohne Upstream-Einschränkungen
- `test-coverage` >85% — HA Integration Test Framework Setup
- HACS offizieller Antrag wenn genug Tester

---

## [0.10.0] - 2026-04-12

### Fix: requests 2.33.x Dependency-Konflikt (HA 2026.x)

**Ursache:** CarConnectivity 0.11.8 verlangt `requests~=2.32.5`, aber HA 2026.x
hat `requests==2.33.1` installiert. Das ist ein Upstream-Problem bei @tillsteinbach.

**Was wir getan haben:**
- Erkennung des Konflikts in `async_setup_entry` eingebaut
- HA Repair-Issue unter Einstellungen → Reparaturen mit klarer Erklärung und Workaround
- Upstream Issue bei tillsteinbach/CarConnectivity gemeldet

**Temporärer Workaround** bis upstream gepatcht:
```bash
# In der HA-Shell (Einstellungen → System → Terminal)
pip install requests==2.32.5
# Dann HA neu starten
```

_Autor: @its-me-prash_

## [0.9.0] - 2026-04-12

### Fixes

**Python 3.11 Kompatibilität — Kritischer Bugfix**
- 500 Internal Server Error im Config Flow auf HA-Instanzen mit Python 3.11 behoben
- `type X = ...` (Python 3.12+ only) ersetzt durch `TypeAlias` aus `typing` (Python 3.10+)
- Betrifft alle Nutzer auf HA 2024.x — sofortiges Update empfohlen

**Username aktualisiert**
- Alle Repository-Referenzen von `Prash1407` → `its-me-prash` aktualisiert

**README**
- Letzte 3 Versionen in allen 8 Sprachen im README angezeigt
- HACS Update-Benachrichtigungen zeigen automatisch den Changelog-Abschnitt

_Autor: @its-me-prash_

---

## [0.8.0] - 2026-04-12

### Gold vollständig — icon-translations, stale-devices, 192 Tests

#### Gold (letzte offene Punkte geschlossen)

**`icon-translations`** — `icons.json` erstellt:
- 64 Icon-Definitionen für alle Platforms (sensor, binary_sensor, switch, button, number, device_tracker, climate)
- Icons zentral verwaltet statt hardcoded in Python

**`stale-devices`** — automatische Geräte-Bereinigung:
- `_async_remove_stale_devices()` im Coordinator vergleicht aktuelle VINs mit `coordinator.data`
- Fahrzeuge die nicht mehr im API-Account sind, werden automatisch aus dem HA Device Registry entfernt
- Implementiert bei jedem erfolgreichen Cloud-Push

#### Typing-Fixes
- `config_flow.py`: `FlowResult` → `ConfigFlowResult` (modernes HA-Pattern)
- `switch.py`: Null-Guard in `VagWindowHeatingSwitch.is_on` — kein AttributeError mehr wenn `_vehicle` None
- `button.py`: Korrekte Typannotation für entities-Liste
- `number.py`: `max_charge_current` Handler in `async_set_native_value` ergänzt

#### Testsuite massiv erweitert
- **+123 neue Tests** → **192/192 grün**
- `test_entities.py`: Alle Platforms vollständig abgedeckt (sensor, binary_sensor, switch, button, number, climate, device_tracker, diagnostics, repairs)
- `test_config_flow.py`: Reauth, Reconfigure, Error-Mapping, Options Flow
- Coordinator action methods: `_run_command`, alle async Actions, `_async_update_data`, stale devices

#### Coverage (72% — Ceiling ohne HA Integration Test Framework)
| Modul | Coverage |
|---|---|
| button, climate, diagnostics, entity_base, repairs, const | **100%** |
| binary_sensor | **98%** |
| number, sensor | **97-98%** |
| switch | **91%** |
| config_flow | **90%** |
| device_tracker | **97%** |
| coordinator | **56%** (CC-Startup-Code + _start_cc erfordern echte CC-Verbindung) |
| `__init__` | **24%** (async_setup_entry erfordert HA Integration Test Framework) |

#### quality_scale.yaml aktualisiert
- `icon-translations`: done
- `stale-devices`: done
- `strict-typing`: in progress (Upstream-Blocker dokumentiert)
- `test-coverage`: todo mit Begründung

_Autor: @its-me-prash_



## [0.7.0] - 2026-04-12

### Gold-Level — HA Quality Scale systematisch umgesetzt

#### Bronze (vervollständigt)
- **`entry.runtime_data`** — Alle Plattform-Files auf modernes HA-Pattern umgestellt (war: `hass.data[DOMAIN]`)
- **`unique-config-entry`** — `async_set_unique_id(f"{brand}_{username}")` + `_abort_if_unique_id_configured()` verhindert doppelte Einträge ✅ (war schon korrekt, jetzt dokumentiert)
- **`data_description`** — Config-Flow-Felder haben Beschreibungstexte in allen 8 Sprachen
- **`test-before-configure`** — `_validate_credentials()` prüft CC-Instantiierung vor Entry-Erstellung ✅

#### Silver (vervollständigt)
- **`parallel-updates`** — `_attr_parallel_updates = 0` auf `VagConnectEntity` Basisklasse (`cloud_push`, kein direkter API-Zugriff von Entities)
- **`reauthentication-flow`** — `async_step_reauth` + `async_step_reauth_confirm` in config_flow.py; wird automatisch ausgelöst wenn CC Auth fehlschlägt
- **`action-exceptions`** — Alle Service-Handler werfen `ServiceValidationError` (nicht `RuntimeError`) wenn VIN nicht gefunden; übersetzt in 8 Sprachen
- **`log-when-unavailable`** — `_was_available` Flag in Coordinator; loggt genau einmal bei Offline → Online Transition, nie wiederholend

#### Gold (vervollständigt)
- **`entity-disabled-by-default`** — 15 DIAGNOSTIC-Sensoren haben `entity_registry_enabled_default=False`: firmware, Kennzeichen, Akkutemp, Ladesäule-Details, Verbindung, Heading, WLTP-Reichweite, Ladetyp u.a.
- **`reconfiguration-flow`** — `async_step_reconfigure` erlaubt Änderung aller Einstellungen ohne Integration zu löschen
- **`exception-translations`** — `ServiceValidationError` mit `translation_key="vehicle_not_found"`, übersetzt in 8 Sprachen
- **`diagnostics`** — `diagnostics.py` auf `entry.runtime_data` umgestellt, `cloud_push_active` Status ergänzt
- **`docs-known-limitations`** — README: CC-Sync-Blocker, Live-Test-Hinweis, SEAT/CUPRA-404, Porsche-Status, Timer-Schreibzugriff
- **`docs-use-cases`** — README: 2 Beispiel-Automationen (Akku-Warnung + Klimatisierung vor Abfahrt)
- **`docs-removal-instructions`** — README: Schritt-für-Schritt-Anleitung zum Entfernen inkl. Token-Datei
- **`quality_scale.yaml`** — Vollständige Gold-Checkliste mit Status und Begründungen für alle Regeln; Platinum-Blocker dokumentiert

#### Infrastruktur
- **`config_flow.py`** — Komplett neu: saubere Typen, `_user_schema()` Fabrik für DRY Wiederverwendung, `_map_error()` für alle Fehlercodes
- **`entity_base.py`** — `sw_version` (Firmware) in `DeviceInfo`; vollständige Docstrings
- **`const.py`** — `CONF_FORCE_ACCESS` korrekt exportiert
- **8 Übersetzungen** — 114/114 Keys synchron (DE/EN/FR/NL/ES/PL/CS/SV)
- **10 neue Tests** → **79/79 grün** | Lint: sauber

#### Was noch fehlt (0.8.0)
- `strict-typing`, `icon-translations`, `stale-devices`, `test-coverage >95%`
- Platinum: upstream CarConnectivity muss async werden (nicht in unserer Hand)

_Autor: @its-me-prash_



---

## [0.6.0] - 2026-04-12

### Hinzugefügt

#### EntityCategory.DIAGNOSTIC — saubere Entity-Struktur
Technische Sensoren die nicht täglich gebraucht werden, erscheinen jetzt nur noch unter **Gerätediagnose** statt im Haupt-Dashboard:

- `firmware_version`, `license_plate`, `connection_state` → DIAGNOSTIC
- `battery_temp`, `battery_cap_kwh` → DIAGNOSTIC  
- `charging_type`, `charging_station_address/kw/operator` → DIAGNOSTIC
- `heading`, `parking_city`, `service_due_at`, `oil_service_at` → DIAGNOSTIC
- `is_online`, `connector_locked` (binary) → DIAGNOSTIC
- Number-Sliders (Ladeziel, Klimatemp, Ladestrom) → CONFIG

#### Neue Sensoren
- `sensor.{fahrzeug}_reichweite_bei_100_prozent` — geschätzte Reichweite bei vollem Akku (aus `drive.range_estimated_full`, CC-Core [@tillsteinbach](https://github.com/tillsteinbach/CarConnectivity))
- `sensor.{fahrzeug}_wltp_reichweite` — WLTP-Normreichweite (aus `drive.range_wltp`, CC-Core [@tillsteinbach](https://github.com/tillsteinbach/CarConnectivity), DIAGNOSTIC)
- `sensor.{fahrzeug}_akkuenergie_verfugbar` — verfügbare Akkuenergie in kWh (aus `battery.available_capacity`, CC-Core [@tillsteinbach](https://github.com/tillsteinbach/CarConnectivity))
- `sensor.{fahrzeug}_zuletzt_aktualisiert` — Timestamp letztes Fahrzeug-Update (DIAGNOSTIC)

#### Fixes
- Typo `Ladziel` → `Ladeziel` in number.py behoben
- `Max Ladestrom` → `Max. Ladestrom` (korrekte Abkürzung)

#### UX / Infrastruktur
- Config Flow: korrekter VAG-Hinweis — kein separater Account nötig, Secondary Users haben bei CARIAD eingeschränkte API-Rechte (Fernzugriff nur mit Hauptnutzer-Account)
- `hacs.json`: `iot_class` ergänzt für HACS Analytics-Tracking
- `docs/lovelace-example.yaml`: Fertiges Beispiel-Dashboard (mushroom + mini-graph-card)
- README: Analytics-Badge, Account-Empfehlung, Dashboard-Link, alle 8 Sprachen
- Alle 8 Übersetzungen auf 99/99 Keys synchronisiert
- 6 neue Tests → **69/69 grün**

_Autor: @its-me-prash_

## [0.5.0] - 2026-04-12

### Hinzugefügt

#### Abfahrtstimer (Departure Timer) — Issue #5
EVs und PHEVs mit CARIAD-Backend (Audi, VW, Škoda, SEAT/CUPRA) unterstützen jetzt Abfahrtstimer.

**Neue Entities (nur bei `has_battery`):**
- `sensor.{fahrzeug}_abfahrtstimer_1/2/3` — Timestamp-Sensor mit der geplanten Abfahrtszeit
- `switch.{fahrzeug}_abfahrtstimer_1/2/3` — Timer aktivieren / deaktivieren

**Neuer Service `vag_connect.set_departure_timer`:**
```yaml
service: vag_connect.set_departure_timer
data:
  vin: "WAUZZZ4G7EN123456"
  timer_id: 1          # 1, 2 oder 3
  enabled: true
  departure_time: "07:30"  # optional: "HH:MM" oder ISO-Datetime
```

**Technischer Hintergrund:**
- `AudiClimatization.Timers` (CC-Connector-Audi ≥0.3.0) war bereits vorhanden, aber nicht im HA-Layer exponiert. Die Timer-Klasse stammt aus [@acfischer42](https://github.com/acfischer42/CarConnectivity-connector-audi)'s Audi-Connector — wir haben sie lediglich in Entities und einen Service übersetzt.
- `_extract()` liest jetzt `vehicle.climatization.timers.timer_1/2/3` (enabled + target_datetime).
- `async_set_departure_timer()` setzt enabled-Flag und optionale Zielzeit direkt auf dem CC-Objekt.
- Bei fehlendem Timer-Objekt (API hat noch keinen Timer zurückgegeben) → alle Keys = `None`, kein Crash.

**Übersetzungen:** alle 8 Sprachen (DE/EN/FR/NL/ES/PL/CS/SV) — 93/93 Keys synchron.

**Tests:** 6 neue Unit-Tests → 63/63 bestanden.

_Autor: @its-me-prash_

## [0.4.6] - 2026-04-11

### Hinzugefügt
- Logo: Echtes VAG Connect Logo (VAG Connected, AI-generiert, Gemini-Wasserzeichen entfernt)
  icon.png (256×256), logo.png (512×512), icon@2x.png (512×512)

### Behoben
- `set_target_soc` und `set_climatisation_temperature` waren in services.yaml dokumentiert
  aber nicht in `_register_services()` registriert — jetzt vollständig verknüpft
- strings.json: 21 → 87 Keys (synchron mit de.json)
- CHANGELOG fehlte für Versionen 0.4.3–0.4.5

---

## [0.4.5] - 2026-04-11

### Geändert
- icon.png durch echtes AI-generiertes Logo ersetzt

---

## [0.4.4] - 2026-04-11

### Hinzugefügt
- Logo/Icon erstellt (Pillow, Platzhalter)
- strings.json auf 87 Keys synchronisiert
- services.yaml: set_target_soc + set_climatisation_temperature ergänzt
- README.en.md vollständig aktualisiert
- README.fr/nl/es/pl/cs/sv aktualisiert

---

## [0.4.3] - 2026-04-11

### Behoben
- Alle 6 Sprachen (FR/NL/ES/PL/CS/SV): von 10 auf 87 Keys aktualisiert
- README: 'separate Geräte' → 'separate Fahrzeuge'
- README EV/PHEV: konkrete Modelle aufgelistet

---

## [0.4.2] - 2026-04-11

### Hinzugefügt

#### Metrisch / Imperial — vollständige Einheitenunterstützung

VAG Connect nutzt HAs eingebautes Einheitensystem. Einstellung:
**Einstellungen → System → Allgemein → Einheitensystem**

| Sensor | Metrisch | Imperial |
|---|---|---|
| Reichweite | km | mi |
| Kilometerstand | km | mi |
| Nächste Inspektion | km | mi |
| Nächster Ölwechsel | km | mi |
| Außentemperatur | °C | °F |
| Zieltemperatur | °C | °F |
| Akkutemperatur | °C | °F |
| **Ladegeschwindigkeit** | km/h | mph |

Kein eigenes Konfigurations-Feld nötig — HA übernimmt die Umrechnung automatisch
für alle Entities mit korrektem `device_class`.

**Neu:** `charging_rate_kmh` bekommt `device_class=SensorDeviceClass.SPEED` →
automatische km/h → mph Konvertierung bei imperialem Einheitensystem.

Alle anderen Sensoren (Leistung kW, Prozent, kWh, Grad) haben keine imperiale
Entsprechung — bleiben unverändert.
  **Autor:** @its-me-prash

### Hinweis

**`sensor.*_ladesaule`** — Entity-IDs enthalten grundsätzlich keine Umlaute
(ä → a, ö → o, ü → u) — das ist normales HA-Verhalten bei allen Integrationen.
Der Anzeigename in HA bleibt korrekt: **Ladesäule**.

## [0.4.1] - 2026-04-11

### Sprachbereinigung — Umlaute, Terminologie, Ton

#### README.md
- Alle ae/oe/ue-Substitute durch echte Umlaute ersetzt: Türen, Außentemperatur,
  Tankfüllstand, Verfügbarkeit, fällig, Ölstand, Ölservice, Unterstützte, usw.
- Feature-Tabellen auf aktuellen Stand 0.4.0 gebracht
- Ton: sachlich, direkt, für normale Nutzer verständlich
  **Autor:** @its-me-prash

#### Sensor-Namen
- `Batterieladestand` → `Akkustand` (wie es Nutzer kennen — z.B. Handy-Akku)
- `Ladziel` → `Ladeziel` (Tippfehler behoben)
- `Tankfüllstand` → `Tankstand` (kürzer, genauso klar)
- `Ladestatus` → `Ladevorgang` (beschreibt was es ist)
- `Steckerstatus` → `Ladestecker` (konkreter)
- `Klimatisierungsstatus` → `Klimatisierung` (kein überflüssiges -status)
- `Fahrzeugstatus` → `Fahrzeugzustand` (präziser)
- `Verbindungsstatus` → `Verbindung` (kürzer)
- `Inspektion fällig in` → `Nächste Inspektion`
- `Ölservice fällig in` → `Nächster Ölwechsel`
- `Ölservicedatum` → `Ölwechseldatum`
- `Parkadresse` → `Standort` (natürlicher)
- `Firmware` → `Firmware-Version`
  **Autor:** @its-me-prash

#### Binary Sensor Namen
- `Fährt` → `In Fahrt` (natürlicheres Deutsch)
- `Ladekabel verbunden` → `Ladekabel steckt`
- `Klimatisierung aktiv` → `Klimatisierung läuft`
- `Online` → `Erreichbar` (was es für den Nutzer bedeutet)
  **Autor:** @its-me-prash

#### Switch-Namen
- `Stecker Auto-Entsperren` → `Stecker nach Laden entsperren`
- `Fensterheizung` → `Scheibenheizung` (automotive Standard-Begriff)
  **Autor:** @its-me-prash

#### Translations de.json + en.json
- Vollständig aktualisiert auf alle 0.4.0-Features (31 neue Entity-Keys)
- Repair-Issues: natürlicheres Deutsch, klare Handlungsanweisungen
- en.json: automotive Standard-Englisch (Battery Level statt State of Charge)
  **Autor:** @its-me-prash

## [0.4.0] - 2026-04-11

Features die kein anderes VAG Home Assistant Plugin hat.

### Hinzugefügt

#### Fahrzeugstatus (vehicle.state + connection_state)
- `sensor.*_fahrzeugstatus` — PARKED / DRIVING / IGNITION_ON / OFFLINE
- `sensor.*_verbindungsstatus` — ONLINE / REACHABLE / OFFLINE
- `binary_sensor.*_fahrt` — True wenn Fahrzeug fährt (DRIVING oder IGNITION_ON)
- `binary_sensor.*_online` — True wenn Fahrzeug erreichbar
  **Einzigartig:** Kein anderes VAG-HA-Plugin zeigt ob das Auto fährt.
  Nutzbar für Automationen: *„Wenn Auto fährt → Heizung runterdrehen"*
  **Autor:** @its-me-prash

#### Parkadresse als Text (position.location)
- `sensor.*_parkadresse` — vollständige Adresse direkt von der API (kein Geocoding)
- `sensor.*_parkstadt` — Stadt wo das Fahrzeug steht
  **Einzigartig:** myskoda Issue #824 offen seit 2025, nie implementiert.
  **Autor:** @its-me-prash

#### Fahrtrichtung (position.heading)
- `sensor.*_fahrtrichtung` — 0–360°, Einheit °
  Nutzbar für Karten-Dashboards mit Richtungspfeil.
  **Autor:** @its-me-prash

#### Akkutemperatur + Kapazität (battery.temperature, total_capacity)
- `sensor.*_akkutemperatur` — °C (erklärt Reichweitenverlust im Winter)
- `sensor.*_akkukapazitat` — kWh (für Degradations-Monitoring)
  **Einzigartig:** Tesla-Integration hat das — nie bei VAG gesehen.
  **Autor:** @its-me-prash

#### Ladeende-ETA (charging.estimated_date_reached)
- `sensor.*_ladeende` — Timestamp wann Akku voll (z.B. „heute 22:47 Uhr")
  Nutzbar für: *„Benachrichtige mich wenn Auto voll geladen"*
  **Einzigartig:** Alle anderen zeigen nur %-Stand, niemand den Zeitpunkt.
  **Autor:** @its-me-prash

#### Ladetyp AC/DC (charging.type)
- `sensor.*_ladetyp` — OFF / AC / DC
  **Autor:** @its-me-prash

#### Ladesäulen-Info (charging.charging_station)
- `sensor.*_ladestaule` — Name der Ladesäule (z.B. „IONITY A9")
- `sensor.*_ladestaule_adresse` — Adresse
- `sensor.*_ladestaule_max_leistung` — Max-kW
- `sensor.*_ladestaule_betreiber` — Betreibername
  **Einzigartig:** evcc zeigt das — kein HA-Plugin bisher.
  **Autor:** @its-me-prash

#### Auto-Unlock Switch (charging.settings.auto_unlock)
- `switch.*_stecker_auto_entsperren` — Stecker nach Ladeende automatisch öffnen
  **Einzigartig:** VW-App kann das — kein HA-Plugin bisher.
  **Autor:** @its-me-prash

#### Max Ladestrom Slider (charging.settings.maximum_current)
- `number.*_max_ladestrom` — 6–32A, Slider in HA
  Für schwache Hausinstallationen oder gesteuertes Laden.
  **Einzigartig:** Kein anderes VAG-HA-Plugin.
  **Autor:** @its-me-prash

#### Stecker-Verriegelung (charging.connector.lock_state)
- `binary_sensor.*_stecker_verriegelt` — True wenn Kabel mechanisch gesperrt
  **Autor:** @its-me-prash

#### Kennzeichen + Firmware (vehicle.license_plate, software.version)
- `sensor.*_kennzeichen` — Kennzeichen
- `sensor.*_firmware` — Firmware-Version für OTA-Tracking
  **Autor:** @its-me-prash

### Tests
- 57 Unit-Tests (vorher 42) — 15 neue Tests für alle Features
  **Autor:** @its-me-prash

## [0.3.4] - 2026-04-11

### Codebereinigung — kein Funktionsverlust

#### Kritische Bugs behoben
- `number.py`: `is_electric` → `has_battery` — PHEV-Fahrzeuge bekamen keine Number-Entities
- `_run_subsystem_command` entfernt — war identisch zu `_run_command`, beide hatten
  unterschiedliche sub_maps; jetzt eine einzige Methode mit vollständiger Map
  (doors, charging, climatization, lights, **window_heatings**)

#### Totes Gewicht entfernt
- `const.py`: 33 ungenutzte Konstanten gelöscht (PATH_*, ICON_*, REGIONS, CONF_REGION)
  — Reste aus alter API-Pfad-Architektur, nie von Entities verwendet
- `coordinator._extract()`: `nickname`-Key entfernt — gesetzt aber nie gelesen
- `from __future__ import annotations`: aus allen 13 Python-Dateien entfernt
  (Python 3.12 unterstützt native Union-Typen, kein Compat-Import nötig)

#### Konsistenz
- `CONF_FORCE_ACCESS`: war direkt als String `"force_enable_access"` im Coordinator,
  jetzt korrekt aus const.py importiert
- F821 Ruff: Forward-Reference `VagConnectOptionsFlow` mit String-Annotation gelöst

#### Zahlen
- const.py: 70 → 20 Zeilen (-71%)
- coordinator.py: -30 Zeilen (redundante Methode)
- Gesamt: ~80 Zeilen weniger bei gleicher Funktionalität
  **Autor:** @its-me-prash

## [0.3.3] - 2026-04-11

### Behoben

#### EV / PHEV / Verbrenner-Logik komplett überarbeitet
Das `is_electric`-Flag war zu simpel und führte zu falschen Sensor-Zuordnungen bei PHEVs.

**Neue Flags im Coordinator:**
| Flag | Wahr für | Bedeutung |
|---|---|---|
| `is_electric` | Nur reine EVs | `vehicle.type == ELECTRIC` |
| `has_battery` | EV + PHEV | Hat Akku und Lader |
| `is_hybrid` | PHEV | `vehicle.type == HYBRID` |
| `has_combustion` | Verbrenner + PHEV | Hat Verbrennungsmotor |

**Sensor-Conditions:**
- `condition="electric"` → prüft jetzt `has_battery` (EV + PHEV sehen Lade-Sensoren)
- `condition="combustion"` → prüft jetzt `has_combustion` (Verbrenner + PHEV sehen Tank/Öl)

**Fallback:** Wenn `vehicle.type = None` → Flags werden aus den Drive-Typen abgeleitet.

**Autor:** @its-me-prash

#### sensor.py: Runtime-Crash `is_electric` nicht definiert
- `is_electric` wurde nach Refactoring nicht mehr gesetzt → NameError beim Starten
- Behoben: `has_battery` und `has_combustion` direkt aus vehicle-Dict
  **Autor:** @its-me-prash

#### Lade-Reichweite/h — Einheit aus HA-Konstante
- `native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR` statt hartcodiertem `"km/h"`
- `native_unit_of_measurement=UnitOfPower.KILO_WATT` für Ladeleistung statt `"kW"`
  **Autor:** @its-me-prash

### Hinzugefügt

#### 7 neue Tests für EV/PHEV/Verbrenner-Logik (42 Tests gesamt)
- Pure EV: alle Flags korrekt, kein Tankstand
- PHEV: `has_battery=True` UND `has_combustion=True`, beides anzeigen
- Verbrenner: `has_battery=False`, kein Ladestand
- Fallback aus Drives wenn `vehicle.type = None`
  **Autor:** @its-me-prash

## [0.3.2] - 2026-04-11

### Hinzugefügt

#### Tests: 35 Unit-Tests (vorher 18)
17 neue Tests für alle Features seit v0.2.0:
- `charging_power_kw` + `charging_rate_kmh` Extraktion
- `doors_individual` — individuelle Türen inkl. Edge-Cases
- `_async_push_update(success=False)` — stale-data-Fix bestätigt
- `_tokenstore_path()` — Pfad korrekt + eindeutig pro Entry
- `force_enable_access` — Flag im coordinator-Code verifiziert
- `_device_name()` — alle Naming-Cases (Marke+Modell, Fallback VIN)
  **Autor:** @its-me-prash

## [0.3.1] - 2026-04-11

### Behoben

#### Ladegeschwindigkeit-Sensor falsch benannt
- **Vorher:** Name "Ladegeschwindigkeit", Einheit "km/h" → klang nach Fahrzeuggeschwindigkeit
- **Nachher:** Name "Lade-Reichweite pro Stunde", Einheit "km/h"
  Bedeutung: Wie viele km Reichweite werden pro Stunde geladen (z.B. 120 km/h = nach 1h Laden hat man 120 km mehr)
  Kein `SensorDeviceClass.SPEED` — das wäre falsch (Fahrzeuggeschwindigkeit)
  **Autor:** @its-me-prash

### Hinzugefügt

#### HA Repair-Issues für Auth-Fehler (2FA, T&C, gesperrter Account)
Statt stiller Fehler im Log erscheint jetzt eine sichtbare Meldung im HA UI
unter **Einstellungen → System → Reparaturen** mit konkreter Handlungsanweisung.

| Fehler | Reparatur-Anleitung |
|---|---|
| `two_factor_required` | App öffnen, einmalig 2FA bestätigen, HA neu starten |
| `terms_and_conditions` | App öffnen, T&C akzeptieren |
| `marketing_consent` | App → Profil → Zustimmungen |
| `too_many_requests` | 15 Minuten warten, Intervall erhöhen |
| `auth_failed` | Zugangsdaten prüfen, neu konfigurieren |

Nach erfolgreichem Login werden alle alten Repair-Issues automatisch gelöscht.
  **Autor:** @its-me-prash
  **Referenz Issue:** #7 (2FA upstream), myskoda#976, myskoda#934

#### Warum 2FA nicht vollständig automatisierbar ist
Der CarConnectivity-Connector hat keinen OTP-Eingabe-Schritt im Auth-Flow.
VW/Audi sendet den Code per E-Mail — das kann HA nicht abfangen.
Der **Token-Persistenz-Workaround** (seit v0.2.0) funktioniert so:
1. Einmal manuell in der App 2FA bestätigen
2. Tokens werden in `.storage/vag_connect_tokens_*.json` gespeichert
3. Bei HA-Neustarts werden gespeicherte Tokens wiederverwendet → kein Re-Auth

## [0.3.0] - 2026-04-11

Schließt Issues #1, #2, #3, #4, #6 aus der Ökosystem-Analyse.

### Hinzugefügt

#### Ladeleistung + Ladegeschwindigkeit (Issue #2)
- `sensor.*_ladeleistung` — aktuelle Ladeleistung in kW
- `sensor.*_ladegeschwindigkeit` — Ladegeschwindigkeit in km/h
- Datenquelle: `vehicle.charging.power.value` + `vehicle.charging.rate.value`
  **Autor:** @its-me-prash
  **Quell-Issue:** #2

#### Individuelle Tür-Sensoren (Issue #3)
- Dynamische `binary_sensor.*_tur_vorne_links/rechts/hinten_links/rechts` etc.
- `binary_sensor.*_kofferraum` + `binary_sensor.*_motorhaube`
- Werden automatisch angelegt basierend auf `vehicle.doors.doors`-Dict
- Deutsch: frontLeft, frontRight, rearLeft, rearRight, trunk, bonnet
  **Autor:** @its-me-prash
  **Quell-Issue:** #3

#### Sitzheizung Switch (Issue #6)
- `switch.*_sitzheizung` — Sitzheizung Ein/Aus
- Nutzt `vehicle.climatization.settings.seat_heating`
  **Autor:** @its-me-prash
  **Quell-Issue:** #6

#### force_enable_access Option (Issue #1)
- Neues optionales Feld im Config-Flow: "Türen erzwingen"
- Für ältere VW/Audi-Modelle die keine 'access' Capability melden
- Wird als `force_enable_access: true` an den CC-Connector weitergegeben
  **Autor:** @its-me-prash
  **Quell-Issue:** #1
  **Referenz:** CarConnectivity-connector-volkswagen force_enable_access Option

### Behoben

#### Stale Data bei VAG-Server-Fehler (Issue #4)
- Wenn der VAG-Server nicht erreichbar ist oder einen Fehler zurückgibt,
  werden Entities jetzt als `unavailable` markiert statt veraltete Werte zu zeigen
- `_on_cc_update` übergibt `success=False` bei Exception
- `_async_push_update(data, success=False)` setzt `last_update_success=False`
  und ruft `async_update_listeners()` auf — HA rendert Entities als unavailable
  **Autor:** @its-me-prash
  **Quell-Issue:** #4
  **Referenz:** myskoda#731 Wrong/old sensor info when server unavailable

## [0.2.2] - 2026-04-11

### Geändert

#### Entity-ID Schema: Marke + Modell statt VIN/Nickname
- **Vorher:** `sensor.wauzzz4g7en123456_kilometerstand` (unlesbar)
- **Nachher:** `sensor.audi_q4_e_tron_kilometerstand`

Schema: `{platform}.{marke}_{modell}_{sensor_key}`

Beispiele:
- `sensor.audi_q4_e_tron_batterieladestand`
- `binary_sensor.skoda_enyaq_iv_turen_offen`
- `device_tracker.volkswagen_id_4_pro_position`
- `switch.seat_cupra_born_verriegelung`

Bei zwei gleichen Modellen (z.B. Firmenwagen + Privat):
- `sensor.audi_q4_e_tron_kilometerstand` (erstes Fahrzeug)
- `sensor.audi_q4_e_tron_2_kilometerstand` (zweites — HA setzt _2 automatisch)

**BREAKING:** Wer bereits Automationen mit entity_id hatte, muss diese anpassen.
  **Autor:** @its-me-prash

#### Mehrere Fahrzeuge — wie es funktioniert
- Ein Audi-Konto mit Q4 + A4: beide erscheinen als separate Geräte, automatisch
- Audi + Skoda: Integration zweimal hinzufügen (je ein Config Entry)
- Jedes Fahrzeug = ein HA-Gerät mit eigener VIN als Identifier (stabil)
  **Autor:** @its-me-prash

## [0.2.1] - 2026-04-11

Hotfix: fehlende Service-Registrierungen nach Cross-Check entdeckt.

### Behoben

#### Services für Fensterheizung und Wake fehlten
- `vag_connect.start_window_heating` nicht in _register_services() registriert
- `vag_connect.stop_window_heating` nicht registriert
- `vag_connect.wake_vehicle` nicht registriert
- services.yaml fehlten die drei neuen Einträge
  **Entdeckt durch:** automatisierten Cross-Check (Coordinator-Actions vs. Services)
  **Autor:** @its-me-prash

## [0.2.0] - 2026-04-11

Features aus Issue-Analyse des gesamten VAG-HA-Ökosystems.
Quellen: audiconnect/audi_connect_ha Issues, homeassistant-myskoda Issues,
CarConnectivity Issues, ioBroker VW-Connect Forum.

### Hinzugefügt

#### Fensterheizung Switch
- Neuer `switch.vag_*_fensterheizung` für alle Fahrzeuge mit Fensterheizfunktion.
  Nutzt `vehicle.window_heatings.commands`, Command `start-stop`.
  **Autor:** @its-me-prash
  **Quelle:** [CarConnectivity WindowHeatingStartStopCommand](https://github.com/tillsteinbach/CarConnectivity)
  **Referenz-Issue:** [myskoda #929](https://github.com/skodaconnect/homeassistant-myskoda/issues/929) — Heizung Stop nicht möglich

#### Wake-Car Button
- Neuer `button.vag_*_fahrzeug_aufwecken` — weckt schlafende Fahrzeuge auf.
  Verbrenner-Fahrzeuge kommunizieren seltener; Wake erzwingt eine Status-Aktualisierung.
  Nutzt `vehicle.commands`, Command `wake-sleep`.
  **Autor:** @its-me-prash
  **Quelle:** [CarConnectivity WakeSleepCommand](https://github.com/tillsteinbach/CarConnectivity)
  **Referenz-Issue:** [myskoda #762](https://github.com/skodaconnect/homeassistant-myskoda/issues/762) — Wake car Feature Request

#### Token-Persistenz
- CC-Tokens werden in `.storage/vag_connect_tokens_{entry_id}.json` gespeichert.
  Bei HA-Neustart ist kein Re-Auth mehr nötig — Tokens werden wiederverwendet.
  Reduziert Auth-Anfragen und Risiko von Account-Sperrungen.
  **Autor:** @its-me-prash
  **Quelle:** [CarConnectivity tokenstore_file Parameter](https://github.com/tillsteinbach/CarConnectivity)

#### Bessere Fehlerbehandlung bei Login
Neue spezifische Fehlermeldungen statt generischem "cannot_connect":
- `terms_and_conditions` — Nutzungsbedingungen müssen in der App akzeptiert werden
- `marketing_consent` — Datenschutzzustimmung erforderlich (App → Profil → Zustimmungen)
- `two_factor_required` — 2FA muss einmalig manuell in der App bestätigt werden
- `too_many_requests` — Account temporär gesperrt, 15 Minuten warten
- `invalid_credentials` — E-Mail oder Passwort falsch
  **Autor:** @its-me-prash
  **Referenz:** [myskoda #976 MarketingConsentError](https://github.com/skodaconnect/homeassistant-myskoda/issues/976)
  **Referenz:** [myskoda #934 CSRFError](https://github.com/skodaconnect/homeassistant-myskoda/issues/934)
  **Referenz:** [Audi Connector T&C AuthenticationError](https://github.com/acfischer42/CarConnectivity-connector-audi)
  **Referenz:** [VW Connector 2FA README](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen)

### Bekannte Einschränkungen in 0.2.0
- Porsche noch nicht unterstützt
- CN-Region nicht getestet
- `force_enable_access` für ältere VW-Modelle noch nicht in Config-Flow
  Tracked: #5 (geplant für 0.2.1)
---

## [0.1.1] - 2026-04-11

Bugfix-Release. Alle Fehler die ein Live-HA-System verhindert hätten.

### Behoben

#### coordinator.data war None beim Entity-Start
- **Problem:** `async_setup_entry` befüllte `coordinator.data` nicht vor `async_forward_entry_setups`. Entities griffen direkt auf `None.get(vin)` zu → `AttributeError`.
- **Fix:** `coordinator.async_set_updated_data(vehicles)` wird jetzt explizit nach `async_setup()` aufgerufen, bevor Platforms initialisiert werden.
- **Autor:** @its-me-prash
- **Referenz:** HA `DataUpdateCoordinator` Dokumentation — `coordinator.data` muss vor Platform-Setup befüllt sein.

#### Race Condition: CC-Thread vs. HA-Loop
- **Problem:** CC-Background-Thread schrieb `self.vehicles`, HA asyncio-Loop las es gleichzeitig ohne Synchronisation.
- **Fix:** `threading.Lock` (`self._vehicles_lock`) schützt alle Lese- und Schreibzugriffe auf `self.vehicles`. Observer-Callback macht `dict(self.vehicles)` für einen thread-safe Snapshot.
- **Autor:** @its-me-prash

#### entity_base crash bei None coordinator.data
- **Problem:** `self.coordinator.data.get(self._vin, {})` warf `AttributeError` wenn `data` noch `None` war.
- **Fix:** `(self.coordinator.data or {}).get(self._vin, {})` — sicher gegen `None` zur Startup-Zeit.
- **Autor:** @its-me-prash

#### manifest.json: falsche iot_class und ungepinnte Versionen
- **Problem:** `iot_class: "cloud_polling"` war falsch (wir pushen reaktiv). Package-Versionen nicht an installierte Versionen angepasst.
- **Fix:** `iot_class: "cloud_push"`. Versionen korrekt:
  - `carconnectivity>=0.11.8`
  - `carconnectivity-connector-audi>=0.3.0`
  - `carconnectivity-connector-volkswagen>=0.10.4`
  - `carconnectivity-connector-skoda>=0.12.4`
  - `carconnectivity-connector-seatcupra>=0.6.1`
- **Autor:** @its-me-prash

#### _async_update_data machte bei jedem Aufruf einen CC-Fetch
- **Problem:** `_async_update_data` rief immer `cc.fetch_all()` auf — auch bei reaktiven Updates die bereits frische Daten in `self.vehicles` hatten. Doppelter Netzwerk-Traffic.
- **Fix:** `_async_update_data` gibt nur `dict(self.vehicles)` zurück. CC-Fetch passiert nur noch bei manuellem Refresh (Button/Service).
- **Autor:** @its-me-prash

---

## [0.1.0] - 2026-04-11

Erste öffentliche Version.

### Hinzugefügt

#### Kern-Integration
- HA Custom Component Struktur (`config_flow`, `coordinator`, alle Plattformen)
  _Autor: @its-me-prash_

- Reaktiver `DataUpdateCoordinator` mit CarConnectivity Observer-Pattern:
  CC-Background-Thread pollt VAG-API → `VALUE_CHANGED` Observer → `asyncio.run_coroutine_threadsafe` → `async_set_updated_data()` → Entities update sofort.
  `update_interval=None` — kein eigenes HA-Polling.
  _Autor: @its-me-prash_
  _API-Quelle: CarConnectivity @tillsteinbach — Observer-Pattern, `Observable.ObserverEvent`_

#### Unterstützte Marken
- **Audi** (myAudi / CARIAD `emea.bff.cariad.digital`)
  _Connector: [carconnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi) v0.3.0 — @acfischer42_
  _Endpoint-Recherche: [audi_connect_ha_q4](https://github.com/moritzwiechers/audi_connect_ha_q4) — @moritzwiechers_

- **Volkswagen EU** (WeConnect `emea.bff.cariad.digital`)
  _Connector: [carconnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen) v0.10.4 — @tillsteinbach_

- **Volkswagen US/CA** (VW Car-Net)
  _Connector: [CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na) — @matpoulin_

- **Skoda** (MySkoda MQTT + REST)
  _Connector: [carconnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda) v0.12.4 — @tillsteinbach_
  _MQTT-Doku: [myskoda](https://github.com/skodaconnect/myskoda) — @skodaconnect_

- **SEAT / CUPRA** (MyCupra REST)
  _Connector: [carconnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra) v0.6.1 — @tillsteinbach_

#### HA-Plattformen
- `sensor` — 14 Sensoren
  _Autor: @its-me-prash_
- `binary_sensor` — 6 Sensoren
  _Autor: @its-me-prash_
- `device_tracker` — GPS-Position
  _Autor: @its-me-prash_
- `switch` — Verriegelung, Klimatisierung, Laden
  _Autor: @its-me-prash_
- `button` — Lichtsignal, Refresh
  _Autor: @its-me-prash_
- `climate` — Vorklimatisierung mit Temperatursteuerung
  _Architektur-Referenz: [homeassistant-myskoda](https://github.com/skodaconnect/homeassistant-myskoda) — @skodaconnect_
  _Autor: @its-me-prash_
- `number` — Ladziel-Slider, Klimatemperatur-Slider
  _Autor: @its-me-prash_

#### Services
- `vag_connect.lock`, `unlock`, `start/stop_climatisation`, `start/stop_charging`, `flash_lights`, `refresh_vehicle`
  _Autor: @its-me-prash_

#### Übersetzungen
- 8 Sprachen: DE, EN, FR, NL, ES, PL, CS, SV
  _Autor: @its-me-prash_

#### Entwicklung
- 18 Unit-Tests (18/18 bestanden)
  _Autor: @its-me-prash_
- Ruff-Linting, Diagnostics-Endpoint, Issue-Templates, HACS-Kompatibilität
  _Autor: @its-me-prash_

### Bekannte Einschränkungen in 0.1.0 / 0.1.1
- Porsche nicht unterstützt (CARIAD-API vorhanden, kein Tester)
- CN-Region nicht getestet
- Fensterheizung kein eigener Switch

### API-Forschungsquellen
| Quelle | Relevanz |
|---|---|
| [ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect) @TA2k | Breiteste VAG-API-Abdeckung, aktivste deutschsprachige Community |
| [myskoda MQTT-Doku](https://myskoda.readthedocs.io/en/stable/mqtt/) | Push-Event-Spezifikation |
| [vw-car-net-api](https://github.com/thomasesmith/vw-car-net-api) | Dokumentierter PKCE/OIDC Auth-Flow |

---

## Changelog-Prozess

Jede Version folgt diesem Ablauf:

```
1. Feature/Fix entwickeln
2. CHANGELOG.md aktualisieren (Unreleased-Block)
3. Commit mit Conventional-Commit-Prefix:
   feat: / fix: / docs: / refactor: / test: / chore: / ci:
4. Bei Release:
   - Version in manifest.json bumpen
   - Unreleased → [x.y.z] - DATUM
   - git tag -a vX.Y.Z -m "Release X.Y.Z"
   - git push origin vX.Y.Z
   → GitHub Actions release.yml erstellt automatisch ZIP + Release
```
