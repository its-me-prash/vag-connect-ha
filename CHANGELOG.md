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

Geplant für 0.2.0:
- Porsche Connector (CARIAD-API, identisch zu Audi)
- Chinesische Region (CN-Endpoints)
- Fensterheizung als eigener Switch
- Abfahrtstimer (Departure Timer) für EVs




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
  **Autor:** @Prash1407

#### Mehrere Fahrzeuge — wie es funktioniert
- Ein Audi-Konto mit Q4 + A4: beide erscheinen als separate Geräte, automatisch
- Audi + Skoda: Integration zweimal hinzufügen (je ein Config Entry)
- Jedes Fahrzeug = ein HA-Gerät mit eigener VIN als Identifier (stabil)
  **Autor:** @Prash1407
## [0.2.1] - 2026-04-11

Hotfix: fehlende Service-Registrierungen nach Cross-Check entdeckt.

### Behoben

#### Services für Fensterheizung und Wake fehlten
- `vag_connect.start_window_heating` nicht in _register_services() registriert
- `vag_connect.stop_window_heating` nicht registriert
- `vag_connect.wake_vehicle` nicht registriert
- services.yaml fehlten die drei neuen Einträge
  **Entdeckt durch:** automatisierten Cross-Check (Coordinator-Actions vs. Services)
  **Autor:** @Prash1407
## [0.2.0] - 2026-04-11

Features aus Issue-Analyse des gesamten VAG-HA-Ökosystems.
Quellen: audiconnect/audi_connect_ha Issues, homeassistant-myskoda Issues,
CarConnectivity Issues, ioBroker VW-Connect Forum.

### Hinzugefügt

#### Fensterheizung Switch
- Neuer `switch.vag_*_fensterheizung` für alle Fahrzeuge mit Fensterheizfunktion.
  Nutzt `vehicle.window_heatings.commands`, Command `start-stop`.
  **Autor:** @Prash1407
  **Quelle:** [CarConnectivity WindowHeatingStartStopCommand](https://github.com/tillsteinbach/CarConnectivity)
  **Referenz-Issue:** [myskoda #929](https://github.com/skodaconnect/homeassistant-myskoda/issues/929) — Heizung Stop nicht möglich

#### Wake-Car Button
- Neuer `button.vag_*_fahrzeug_aufwecken` — weckt schlafende Fahrzeuge auf.
  Verbrenner-Fahrzeuge kommunizieren seltener; Wake erzwingt eine Status-Aktualisierung.
  Nutzt `vehicle.commands`, Command `wake-sleep`.
  **Autor:** @Prash1407
  **Quelle:** [CarConnectivity WakeSleepCommand](https://github.com/tillsteinbach/CarConnectivity)
  **Referenz-Issue:** [myskoda #762](https://github.com/skodaconnect/homeassistant-myskoda/issues/762) — Wake car Feature Request

#### Token-Persistenz
- CC-Tokens werden in `.storage/vag_connect_tokens_{entry_id}.json` gespeichert.
  Bei HA-Neustart ist kein Re-Auth mehr nötig — Tokens werden wiederverwendet.
  Reduziert Auth-Anfragen und Risiko von Account-Sperrungen.
  **Autor:** @Prash1407
  **Quelle:** [CarConnectivity tokenstore_file Parameter](https://github.com/tillsteinbach/CarConnectivity)

#### Bessere Fehlerbehandlung bei Login
Neue spezifische Fehlermeldungen statt generischem "cannot_connect":
- `terms_and_conditions` — Nutzungsbedingungen müssen in der App akzeptiert werden
- `marketing_consent` — Datenschutzzustimmung erforderlich (App → Profil → Zustimmungen)
- `two_factor_required` — 2FA muss einmalig manuell in der App bestätigt werden
- `too_many_requests` — Account temporär gesperrt, 15 Minuten warten
- `invalid_credentials` — E-Mail oder Passwort falsch
  **Autor:** @Prash1407
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
- **Autor:** @Prash1407
- **Referenz:** HA `DataUpdateCoordinator` Dokumentation — `coordinator.data` muss vor Platform-Setup befüllt sein.

#### Race Condition: CC-Thread vs. HA-Loop
- **Problem:** CC-Background-Thread schrieb `self.vehicles`, HA asyncio-Loop las es gleichzeitig ohne Synchronisation.
- **Fix:** `threading.Lock` (`self._vehicles_lock`) schützt alle Lese- und Schreibzugriffe auf `self.vehicles`. Observer-Callback macht `dict(self.vehicles)` für einen thread-safe Snapshot.
- **Autor:** @Prash1407

#### entity_base crash bei None coordinator.data
- **Problem:** `self.coordinator.data.get(self._vin, {})` warf `AttributeError` wenn `data` noch `None` war.
- **Fix:** `(self.coordinator.data or {}).get(self._vin, {})` — sicher gegen `None` zur Startup-Zeit.
- **Autor:** @Prash1407

#### manifest.json: falsche iot_class und ungepinnte Versionen
- **Problem:** `iot_class: "cloud_polling"` war falsch (wir pushen reaktiv). Package-Versionen nicht an installierte Versionen angepasst.
- **Fix:** `iot_class: "cloud_push"`. Versionen korrekt:
  - `carconnectivity>=0.11.8`
  - `carconnectivity-connector-audi>=0.3.0`
  - `carconnectivity-connector-volkswagen>=0.10.4`
  - `carconnectivity-connector-skoda>=0.12.4`
  - `carconnectivity-connector-seatcupra>=0.6.1`
- **Autor:** @Prash1407

#### _async_update_data machte bei jedem Aufruf einen CC-Fetch
- **Problem:** `_async_update_data` rief immer `cc.fetch_all()` auf — auch bei reaktiven Updates die bereits frische Daten in `self.vehicles` hatten. Doppelter Netzwerk-Traffic.
- **Fix:** `_async_update_data` gibt nur `dict(self.vehicles)` zurück. CC-Fetch passiert nur noch bei manuellem Refresh (Button/Service).
- **Autor:** @Prash1407

---

## [0.1.0] - 2026-04-11

Erste öffentliche Version.

### Hinzugefügt

#### Kern-Integration
- HA Custom Component Struktur (`config_flow`, `coordinator`, alle Plattformen)
  _Autor: @Prash1407_

- Reaktiver `DataUpdateCoordinator` mit CarConnectivity Observer-Pattern:
  CC-Background-Thread pollt VAG-API → `VALUE_CHANGED` Observer → `asyncio.run_coroutine_threadsafe` → `async_set_updated_data()` → Entities update sofort.
  `update_interval=None` — kein eigenes HA-Polling.
  _Autor: @Prash1407_
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
  _Autor: @Prash1407_
- `binary_sensor` — 6 Sensoren
  _Autor: @Prash1407_
- `device_tracker` — GPS-Position
  _Autor: @Prash1407_
- `switch` — Verriegelung, Klimatisierung, Laden
  _Autor: @Prash1407_
- `button` — Lichtsignal, Refresh
  _Autor: @Prash1407_
- `climate` — Vorklimatisierung mit Temperatursteuerung
  _Architektur-Referenz: [homeassistant-myskoda](https://github.com/skodaconnect/homeassistant-myskoda) — @skodaconnect_
  _Autor: @Prash1407_
- `number` — Ladziel-Slider, Klimatemperatur-Slider
  _Autor: @Prash1407_

#### Services
- `vag_connect.lock`, `unlock`, `start/stop_climatisation`, `start/stop_charging`, `flash_lights`, `refresh_vehicle`
  _Autor: @Prash1407_

#### Übersetzungen
- 8 Sprachen: DE, EN, FR, NL, ES, PL, CS, SV
  _Autor: @Prash1407_

#### Entwicklung
- 18 Unit-Tests (18/18 bestanden)
  _Autor: @Prash1407_
- Ruff-Linting, Diagnostics-Endpoint, Issue-Templates, HACS-Kompatibilität
  _Autor: @Prash1407_

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
  **Autor:** @Prash1407
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

**Autor:** @Prash1407

#### sensor.py: Runtime-Crash `is_electric` nicht definiert
- `is_electric` wurde nach Refactoring nicht mehr gesetzt → NameError beim Starten
- Behoben: `has_battery` und `has_combustion` direkt aus vehicle-Dict
  **Autor:** @Prash1407

#### Lade-Reichweite/h — Einheit aus HA-Konstante
- `native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR` statt hartcodiertem `"km/h"`
- `native_unit_of_measurement=UnitOfPower.KILO_WATT` für Ladeleistung statt `"kW"`
  **Autor:** @Prash1407

### Hinzugefügt

#### 7 neue Tests für EV/PHEV/Verbrenner-Logik (42 Tests gesamt)
- Pure EV: alle Flags korrekt, kein Tankstand
- PHEV: `has_battery=True` UND `has_combustion=True`, beides anzeigen
- Verbrenner: `has_battery=False`, kein Ladestand
- Fallback aus Drives wenn `vehicle.type = None`
  **Autor:** @Prash1407
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
  **Autor:** @Prash1407
## [0.3.1] - 2026-04-11

### Behoben

#### Ladegeschwindigkeit-Sensor falsch benannt
- **Vorher:** Name "Ladegeschwindigkeit", Einheit "km/h" → klang nach Fahrzeuggeschwindigkeit
- **Nachher:** Name "Lade-Reichweite pro Stunde", Einheit "km/h"
  Bedeutung: Wie viele km Reichweite werden pro Stunde geladen (z.B. 120 km/h = nach 1h Laden hat man 120 km mehr)
  Kein `SensorDeviceClass.SPEED` — das wäre falsch (Fahrzeuggeschwindigkeit)
  **Autor:** @Prash1407

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
  **Autor:** @Prash1407
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
  **Autor:** @Prash1407
  **Quell-Issue:** #2

#### Individuelle Tür-Sensoren (Issue #3)
- Dynamische `binary_sensor.*_tur_vorne_links/rechts/hinten_links/rechts` etc.
- `binary_sensor.*_kofferraum` + `binary_sensor.*_motorhaube`
- Werden automatisch angelegt basierend auf `vehicle.doors.doors`-Dict
- Deutsch: frontLeft, frontRight, rearLeft, rearRight, trunk, bonnet
  **Autor:** @Prash1407
  **Quell-Issue:** #3

#### Sitzheizung Switch (Issue #6)
- `switch.*_sitzheizung` — Sitzheizung Ein/Aus
- Nutzt `vehicle.climatization.settings.seat_heating`
  **Autor:** @Prash1407
  **Quell-Issue:** #6

#### force_enable_access Option (Issue #1)
- Neues optionales Feld im Config-Flow: "Türen erzwingen"
- Für ältere VW/Audi-Modelle die keine 'access' Capability melden
- Wird als `force_enable_access: true` an den CC-Connector weitergegeben
  **Autor:** @Prash1407
  **Quell-Issue:** #1
  **Referenz:** CarConnectivity-connector-volkswagen force_enable_access Option

### Behoben

#### Stale Data bei VAG-Server-Fehler (Issue #4)
- Wenn der VAG-Server nicht erreichbar ist oder einen Fehler zurückgibt,
  werden Entities jetzt als `unavailable` markiert statt veraltete Werte zu zeigen
- `_on_cc_update` übergibt `success=False` bei Exception
- `_async_push_update(data, success=False)` setzt `last_update_success=False`
  und ruft `async_update_listeners()` auf — HA rendert Entities als unavailable
  **Autor:** @Prash1407
  **Quell-Issue:** #4
  **Referenz:** myskoda#731 Wrong/old sensor info when server unavailable
