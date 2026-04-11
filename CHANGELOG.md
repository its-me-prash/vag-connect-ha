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
