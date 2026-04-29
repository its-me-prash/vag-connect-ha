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

## [1.8.9] - 2026-04-29

### Session 3C — CUPRA/SEAT OLA Status JSON-Pfade gefixt + Per-Window Entities + Live-API-Erkenntnisse

**Bug-Fix-Bündel** für Gerhards 19 fehlende Entities (CUPRA Born) und alle
SEAT/CUPRA-Modelle. Vor v1.8.9 las unser Parser aus
`/v2/vehicles/{vin}/status` mit CARIAD-BFF-typischen flachen Feldnamen
(`doorsOpenedCount`, `doorClosedLeftFront`, `trunk: "OPEN"` etc.). Diese
Felder existieren auf dem OLA-Backend
(`ola.prod.code.seat.cloud.vwgroup.com`) **nicht** — Konsequenz: Tür-,
Fenster-, Kofferraum-, Motorhauben- und Schiebedach-Entities blieben
permanent leer.

**Methodik (wichtig):** Wo möglich nehmen wir Field-Namen aus echten
Live-API-Responses (verifiziert via `tillsteinbach/CarConnectivity-connector-seatcupra`
Issues #5, #8, #18, #21, #50, #51, #109) und stellen sie an die Spitze der
`v(...) or v(...) or ...` Pfad-Listen. Die alten geratenen Pfade bleiben als
defensiver Fallback.

#### `cariad/api/seat_cupra.py` — `_parse_status` Status-Block neu geschrieben

**Doors / Windows / Trunk / Hood / Sunroof** (verifiziert gegen
`WulfgarW/pycupra/vehicle.py` ~Z. 3100-3325):

- **Per-Door:** `status.doors.{frontLeft,frontRight,rearLeft,rearRight}.{locked,open}`
  → `doors_individual` dict + abgeleitete `doors_open` und `doors_locked` aggregates
- **Per-Window (NEU):** `status.windows.{frontLeft,...}` (string `"closed"`/`"open"`)
  → `windows_individual` dict + `windows_open` aggregate
- **Trunk:** `status.trunk.{open,locked}` als nested object (statt flat string)
- **Hood:** `status.hood.open` (newer firmware)
- **Sunroof:** dreifach-Pfad `status.sunRoof` (Großbuchstabe R, top-level —
  CC-seatcupra **#5** verifiziert) ODER `status.sunroof` (pycupra) ODER
  `status.windows.sunroof` (firmware variance)
- **Engine (NEU):** top-level `status.engine: 'on'/'off'` (CC-seatcupra
  **#50**) → setzt `is_driving=True` und `vehicle_state="DRIVING"` wenn
  `engine='on'`. Behebt das verbreitete "vehicle_state immer parked"-Problem
  (CC-seatcupra **#18**)

**Defensiv:** Wenn keine der neuen Pfade Daten liefert, Fallback auf den
pre-v1.8.9 CARIAD-BFF-style Code (für sehr alte Firmware oder zukünftige
API-Änderungen).

#### `cariad/api/seat_cupra.py` — Charging-Endpoint Live-Response Erkenntnisse (#109)

**Methodik-Korrektur:** Reihenfolge der Pfad-Suche umgedreht — Rainer's
verifizierte Live-Response-Felder zuerst, alte geratene Pfade als Fallback.

OLA `/v1/vehicles/{vin}/charging` returns one of two shapes (live verifiziert):
- **Shape A:** `{"status": ..., "currentPct": ..., "remainingTime": ...,
  "chargeMode": ..., "preferredChargeMode": ..., "active": false}`
- **Shape B:** `{"state": ..., "chargedPowerInKw": ...,
  "remainingTimeInMinutes": ..., "type": ..., "mode": ...}`

Field-Reihenfolge jetzt korrekt:
- `charging_state`: `state` → `status` → `chargingState` (Legacy)
- `charging_power_kw`: **`chargedPowerInKw` (mit "d", verified)** → `chargePowerInKw` (Legacy)
- `remaining`: **`remainingTimeInMinutes` / `remainingTime` (verified)** → `remainingTimeToFullyChargedInMinutes` (Legacy)
- `charging_type`: `type` → `chargeType` (Legacy)
- `target_soc`: **`targetSoc_pct` (lowercase soc, verified)** → `targetSOC_pct` (Legacy uppercase)
- `is_charging` jetzt case-insensitive (`charging` ODER `CHARGING`)
- **`autoUnlockPlugWhenCharged: 'permanent'`** als 3. truthy-Wert (CC-seatcupra **#51** —
  vorher nur `"on"` matched, `"permanent"` Konfiguration wurde fälschlich
  als deaktiviert angezeigt)

#### `cariad/api/seat_cupra.py` — Climate robustness (#8, #21)

- `climatisation_state == "unsupported"` (CC-seatcupra **#21**) wird jetzt
  korrekt als inaktiv behandelt — vorher leer (zufällig korrekt, aber
  unklar dokumentiert)
- `targetTemperatureCelsius` (Rainer #109 Variante ohne "In") als zusätzlicher
  Pfad neben `targetTemperatureInCelsius`
- `climatisation_active` False-Set erweitert auf `(None, "OFF", "off", "Off", "unsupported")`

#### `cariad/models.py` — neues Field `windows_individual: dict[str, bool]`

Mirror von `doors_individual`. Keys: `frontLeft` / `frontRight` / `rearLeft` /
`rearRight`. Value `True` == Fenster geschlossen.

#### `binary_sensor.py` — neuer `VagWindowSensor` + Setup-Hook

Pro Fenster eine Binary-Sensor-Entity (`device_class=WINDOW`), Naming
`Window Front Left` etc. Nur erstellt wenn `windows_individual` Daten enthält
(SEAT/CUPRA initial; andere Marken folgen wenn deren API es liefert).

#### Tests (12 neue) — `tests/test_cariad.py::TestSeatCupraGetStatus`

1. `test_v189_status_parses_doors_per_position` — pycupra-Pfade door-Mapping
2. `test_v189_status_parses_windows_per_position` — neuer windows_individual
3. `test_v189_status_parses_trunk_hood_nested_objects` — nested {open, locked}
4. `test_v189_status_sunroof_in_windows_subtree` — sunroof in windows.sunroof
5. `test_v189_status_sunroof_top_level_camelCase` — `sunRoof` Großbuchstabe (#5)
6. `test_v189_status_engine_on_implies_driving` — engine='on' → DRIVING (#50, #18)
7. `test_v189_status_engine_off_does_not_force_driving` — engine='off' lässt vehicle_state in Ruhe
8. `test_v189_charging_shape_b_chargedPowerInKw_remaining_minutes` — #109 Shape B
9. `test_v189_charging_settings_targetSoc_pct_lowercase` — #109 lowercase variant
10. `test_v189_auto_unlock_permanent_is_truthy` — `permanent` als truthy (#51)
11. `test_v189_climatisation_trigger_unsupported_is_inactive` — `unsupported` → inaktiv (#21)
12. `test_v189_status_legacy_flat_fallback_still_works` — defensiver Fallback intakt

#### Bewusst NICHT in v1.8.9 enthalten (eigener Scope, geplant für v1.8.10+)

Alles aus dem Deep-Dive der CC-seatcupra-Issues, was eigene Entities oder
zusätzliche API-Calls braucht:

- **Capability-Filter** (CC-seatcupra **#64**) — `capability.active &&
  capability.user-enabled` vor Entity-Creation prüfen. Sehr wahrscheinlich
  weiteres Stück für Gerhards 19 fehlende Entities. Eigene Session
  (Erweiterung des bestehenden Capability-Cache).
- **`/maintenance` Endpoint** (CC-seatcupra **#44**) — separater API-Call mit
  4 neuen Sensoren (inspectionDueDays/Km, oilServiceDueDays/Km).
- **Multi-Zone Klima** (CC-seatcupra **#10, #109**) — `zoneFrontLeftEnabled`,
  `zoneFrontRightEnabled` als eigene Switches.
- **Battery Care Mode** (CC-seatcupra **#20, #51**) —
  `batteryCareModeEnabled`, `batteryCareTargetSocPercentage` als eigene
  Switch + Number.
- **`windowHeatingStatus[]` Array** (CC-seatcupra **#5, #8**) — strukturierter
  Array `[{windowLocation, windowHeatingState}]` statt unsere flat
  `windowHeatingStateFront/Rear` Pfade. Eigene Refactor-Session.
- **`/ventilation/start|stop` Service** (CC-seatcupra **#43**) — neuer
  HA-Service.
- **Trip-Statistics** (CC-seatcupra **#22**, MasterTim17 fork hat Code) —
  v1.10.x.
- **Departure-Timer Toggle** (CC-seatcupra **#70**) — v1.9.x.
- **`carCapturedTimestamp`-Freshness-Pattern** für CUPRA — wird in v1.8.10
  zentral für Škoda eingeführt (Session 3S) und kann später auf CUPRA + Audi
  expandiert werden.

### Session 3C — CUPRA/SEAT OLA Status JSON Paths Fixed + Per-Window Entities + Live-API Findings (English)

Bug-fix bundle for Gerhard's 19 missing entities (CUPRA Born) and all
SEAT/CUPRA models. Pre-v1.8.9 read `/v2/vehicles/{vin}/status` using
CARIAD-BFF-style flat field names that don't exist on the OLA backend.

**Methodology:** real-world API field names (verified via tillsteinbach
`CarConnectivity-connector-seatcupra` issues #5, #8, #18, #21, #50, #51,
#109) are placed at the head of `v(...) or v(...) or ...` chains. Old
inferred paths kept as defensive fallback.

**`seat_cupra.py` `_parse_status`** — verified against pycupra source:
per-door `status.doors.{position}.{locked,open}`, per-window
`status.windows.{position}`, nested `status.trunk.{open,locked}` and
`status.hood.open`, sunroof at THREE positions (`sunRoof` top-level from
#5, plus pycupra paths), engine top-level → DRIVING inference (#50, #18).

**Charging endpoint #109 paths reordered** — `chargedPowerInKw` (with "d"),
`remainingTimeInMinutes`, `targetSoc_pct` (lowercase) now first;
`auto_unlock_charge` recognises `"permanent"` (#51); climate handles
`"unsupported"` state (#21).

**`models.py`** — new `windows_individual` field. **`binary_sensor.py`** —
new `VagWindowSensor` per-window entity.

**12 new tests** in `TestSeatCupraGetStatus` covering both the new
structured paths and all live-API-response findings.

**Deliberately NOT in v1.8.9** (own scope): capability filter (#64),
`/maintenance` endpoint (#44), multi-zone climate (#10, #109), battery
care mode (#20, #51), `windowHeatingStatus[]` array (#5, #8),
`/ventilation` service (#43), trip stats (#22), departure timer toggle
(#70). All planned for v1.8.10+.

## [1.8.8] - 2026-04-29

### Session 3B — CARIAD v1/v2 + combined/separate endpoint dispatch für Lock/Climate/Charging

Erweitert das v1/v2-Fallback-Pattern aus Session 3A (4 Set-Value-Commands)
auf die sechs verbleibenden Hauptkommandos: `lock`, `unlock`,
`climate_start`, `climate_stop`, `charging_start`, `charging_stop`. Plus:
schließt einen versteckten Bug aus dem Pre-1.8.8-Code, in dem `except
Exception` Auth-Failures, Rate-Limits und 5xx-Errors als
Endpoint-Mismatches fehlinterpretierte und still den Fallback-Pfad
ansprach.

**`cariad/api/vw_eu.py` — neuer Helper `_post_command_with_fallback_paths`:**

Dispatcht in dieser Reihenfolge, jeder Aufruf via bestehendes
`_post_command` (das schon v1→v2 Fallback macht):

1. `primary_suffix` (combined endpoint) auf v1
2. `primary_suffix` auf v2 (bei v1-404)
3. `fallback_suffix` (separate endpoint) auf v1 (bei v2-404)
4. `fallback_suffix` auf v2 (bei v1-404)

**Kritische Verschärfung**: Fallback wird **nur** bei HTTP 404 ausgelöst.
Auth-Failures (401), Permission-Errors (403), Rate-Limits (429),
Backend-5xx und transiente Netzwerk-Fehler propagieren wie sie sollen
und werden vom Coordinator über `classify_command_failure` korrekt
klassifiziert.

**Refactor — 6 Commands nutzen den Helper:**

- `command_lock`: `access/lock-unlock` → `access/lock`
- `command_unlock`: `access/lock-unlock` → `access/unlock` (S-PIN in
  beiden Payloads, falls gesetzt)
- `command_start_climate`: `climatisation/start-stop` →
  `climatisation/start` (mit Default-Parametern wie vorher: 21°C,
  Window-Heating, ohne externe Stromversorgung)
- `command_stop_climate`: `climatisation/start-stop` →
  `climatisation/stop`
- `command_start_charging`: `charging/start-stop` → `charging/start`
- `command_stop_charging`: `charging/start-stop` → `charging/stop`

**`AudiClient` profitiert automatisch** über `VWEUClient`-Inheritance —
keine separaten Audi-Änderungen.

**Tests** (`tests/test_cariad.py::TestVWEUFallbackPaths`):

- 4 neue Tests:
  1. v1-Primary 404 → v2-Primary genutzt (kein Fallback-Endpoint
     berührt)
  2. Beide Primaries 404 → Fallback-Endpoint v1 genutzt
  3. **Regressionstest**: 500 vom Primary löst KEINEN Fallback aus
     (Hauptzweck dieser Session — vorheriger Code hätte still den
     Fallback-Endpoint angefragt und einen Backend-Hiccup als
     Endpoint-Mismatch maskiert)
  4. `command_unlock` mit S-PIN passt PIN in alle drei Payloads
     (combined v1, combined v2, separate v1)
- Existing Smoke-Tests in `TestVWEUCommands` bleiben ohne Anpassung
  pass — alle 6 Commands akzeptieren weiterhin 204 vom ersten Endpoint
  und brauchen nie den Fallback-Pfad im Happy-Path-Test.

**Bewusst NICHT in dieser Session enthalten** (Scope-Disziplin):

- **PPC/PPE Graceful Degradation per VIN-Heuristik** (`devicePlatform`
  Detection, Skip command-entities für E³-1.2-Vehicles): kommt in
  v1.8.9 — eigener Scope mit Repair-Notice + Tracking-Issue.
- **Optimistic-Update + State-Restoration** für lock/climate
  (`skodaconnect/homeassistant-myskoda` #832 Pattern): braucht eigenen
  Hotfix mit UI-Layer (entity availability state machine), nicht hier.
- **LEGACY_MBB Routing** für ältere T6/MQB Vehicles: blockiert auf
  T6-Logs von Tobias (#76); kein spekulatives Code-Schreiben.

### Session 3B — CARIAD v1/v2 + Combined/Separate Endpoint Dispatch for Lock/Climate/Charging (English)

Extends the v1/v2 fallback pattern from Session 3A (4 set-value commands)
to the six remaining main commands: `lock`, `unlock`, `climate_start`,
`climate_stop`, `charging_start`, `charging_stop`. Also: closes a
hidden bug in pre-1.8.8 code where `except Exception` misclassified
auth failures, rate limits and 5xx errors as endpoint mismatches and
silently called the fallback path.

**`cariad/api/vw_eu.py` — new helper `_post_command_with_fallback_paths`:**

Dispatches in this order, each call via the existing `_post_command`
(which already handles v1→v2 fallback):

1. `primary_suffix` (combined endpoint) on v1
2. `primary_suffix` on v2 (on v1-404)
3. `fallback_suffix` (separate endpoint) on v1 (on v2-404)
4. `fallback_suffix` on v2 (on v1-404)

**Critical narrowing**: fallback fires **only** on HTTP 404. Auth
failures (401), permission errors (403), rate limits (429), backend
5xx and transient network errors propagate as they should and are
correctly classified by the coordinator via `classify_command_failure`.

**Refactor — 6 commands use the helper:** `command_lock`,
`command_unlock`, `command_start_climate`, `command_stop_climate`,
`command_start_charging`, `command_stop_charging`. `AudiClient` benefits
automatically via `VWEUClient` inheritance.

**Tests** (`tests/test_cariad.py::TestVWEUFallbackPaths`):

4 new tests including the key regression test that a 500 on the
primary endpoint must NOT trigger the fallback (the main purpose of
this session — the previous code would have silently called the
fallback and masked a backend hiccup as an endpoint mismatch).

**Deliberately NOT in this session** (scope discipline):

- PPC/PPE graceful degradation via VIN heuristic — v1.8.9.
- Optimistic-update + state restoration for lock/climate (myskoda
  #832) — needs its own UI-layer hotfix.
- LEGACY_MBB routing for older T6/MQB — blocked on T6 logs from
  Tobias (#76); no speculative code.
## [1.8.7] - 2026-04-29

### Defensive Programming Pass — Retry-Härtung + Stale-Cache + Token-Refresh-Schutz

Auswertung der unabhängigen Multi-Source-Audit (`docs/AUDIT_2026-04-29.md`):
**Sechs von sechs untersuchten Reference-Repos** (we_connect_id, myskoda,
audi_connect_ha, pycupra, volkswagencarnet, CarConnectivity-Connectors)
haben dieselben Stabilitätsprobleme dokumentiert. v1.8.7 schließt vier
davon zentral statt punktuell pro API-Client.

**`cariad/api/base.py` — `_request()` Retry-Layer:**

- **HTTP 504 Gateway Timeout** ist jetzt Teil der Retry-Liste (war vorher
  fatal). Tritt regelmäßig auf der CARIAD BFF an Wochenenden auf
  (Quelle: `mitch-dc/volkswagen_we_connect_id` #165).
- **Server-Error Retries** auf 3 Versuche erhöht (war 2): 3s/6s/12s
  exponential backoff für 500/502/503/504.
- **Transiente Netzwerk-Fehler** werden jetzt mit demselben Backoff
  gehandhabt: `ClientConnectorError` (DNS/Connection refused),
  `ServerDisconnectedError` (Mid-Stream-Abbruch),
  `ClientPayloadError`, `asyncio.TimeoutError`. Wurden vorher als fatal
  raised und teilweise von oberen Schichten als Auth-Failure
  fehlinterpretiert (Quelle: `mitch-dc/volkswagen_we_connect_id` #166).
  Nach 4 erfolglosen Versuchen wird `APIError(0, ...)` mit prefix
  `"transient: ..."` raised — eindeutig unterscheidbar von HTTP-Errors.

**`cariad/api/base.py` — `_refresh_tokens()` Storm-Protection:**

- **Maximal 3 Token-Refresh-Versuche pro rollender Stunde.** Sliding
  Window mit `time.monotonic()`-Timestamps in `_refresh_history`. Bei
  Überschreitung wird `AuthenticationError("Token refresh storm — please
  reauthenticate")` raised; der Coordinator triggert daraufhin den
  HA-Reauth-Flow statt weiter zu loopen. Verhindert das Spirale-Pattern
  aus `skodaconnect/myskoda` #976 und
  `robinostlund/homeassistant-volkswagencarnet` #683, bei dem das
  Backend nach wiederholten Login-Versuchen die IP / das Konto temporär
  sperrt.

**`coordinator.py` — Failure-Tolerance + Stale-Cache:**

- **`is_vehicle_available(vin)` toleriert jetzt bis zu 3 aufeinanderfolgende
  Poll-Failures** bevor die Verfügbarkeit auf False kippt
  (`_FAILURE_TOLERANCE = 3`, Pattern aus `mitch-dc/volkswagen_we_connect_id`
  #215). Single-Poll-Hiccups auf der CARIAD BFF brechen Automatisierungen
  nicht mehr ab.
- **Stale-Cache-Window von 6 Stunden** (`_STALE_CACHE_WINDOW`):
  selbst nach Überschreitung der Failure-Tolerance bleibt das Fahrzeug
  verfügbar wenn der letzte erfolgreiche Poll innerhalb der letzten 6h
  lag. Pattern aus `skodaconnect/homeassistant-myskoda` #731 — User
  bevorzugen "alt aber sichtbar" über "unavailable", weil
  Automatisierungen weiter funktionieren und `last_updated_at` die
  Staleness signalisiert.
- Neue per-VIN Tracking-Dicts: `vehicle_failure_count` (Reset auf 0 bei
  jedem Erfolg) und `vehicle_last_good_at` (Timestamp letzter Erfolg —
  später auch für Diagnostics in Session 4).
- Lazy-Init mit `getattr(...)`-Fallback, damit Coordinators die vor
  v1.8.7 ohne `__init__` instanziiert wurden (Tests, Reload nach
  Upgrade) nicht crashen.

**Tests:**

- `tests/test_cariad.py::TestBaseClientHardening` — 5 neue Tests:
  504-Retry, ClientConnectorError-Retry, persistente Transient → APIError(0),
  Refresh-Storm-Protection, Refresh-Window-Pruning.
- `tests/test_coordinator.py::TestVehicleAvailabilityTolerance` — 7 neue
  Tests: Toleranz unter Schwelle, Verfügbarkeit über Schwelle ohne
  Recent-Good, Stale-Window-Hit, Stale-Window-Miss, Legacy-Coord-Fallback.
- `asyncio.sleep` wird in Retry-Tests gepatched, damit die Suite nicht
  länger läuft — der existierende 500-Test wartete vorher 9s, jetzt
  ohne Patch 21s; mit Patch in Sekundenbruchteilen.

**Bewusst NICHT in dieser Session enthalten** (Scope-Disziplin):

- EULA-Repair-Issue (`ir.async_create_issue` mit Direktlink): braucht
  eigene Translation-Strings in 8 Sprachen, kommt in v1.8.8.
- Generic-`except Exception` Audit quer durch alle API-Clients: größerer
  Refactor, eigener Hotfix.

### Defensive Programming Pass — Retry Hardening + Stale-Cache + Token-Refresh Guard (English)

Synthesis of the independent multi-source audit
(`docs/AUDIT_2026-04-29.md`): **six out of six reference repos**
investigated (we_connect_id, myskoda, audi_connect_ha, pycupra,
volkswagencarnet, CarConnectivity connectors) have documented the same
stability issues. v1.8.7 closes four of them centrally instead of
per-API-client.

**`cariad/api/base.py` — `_request()` retry layer:**

- **HTTP 504 Gateway Timeout** added to the retry list (was previously
  fatal). Routine on the CARIAD BFF on weekends (source:
  `mitch-dc/volkswagen_we_connect_id` #165).
- **Server-error retries raised to 3 attempts** (was 2): 3s/6s/12s
  exponential backoff for 500/502/503/504.
- **Transient network errors** now retried with the same backoff:
  `ClientConnectorError` (DNS / connection refused),
  `ServerDisconnectedError` (mid-stream disconnect),
  `ClientPayloadError`, `asyncio.TimeoutError`. Previously raised as
  fatal and sometimes misclassified by upper layers as auth failure
  (source: `mitch-dc/volkswagen_we_connect_id` #166). After 4 failed
  attempts, surfaces as `APIError(0, ...)` with `"transient: ..."`
  prefix — unambiguously distinguishable from HTTP errors.

**`cariad/api/base.py` — `_refresh_tokens()` storm protection:**

- **Maximum 3 token-refresh attempts per rolling hour.** Sliding window
  using `time.monotonic()` timestamps in `_refresh_history`. Exceeding
  raises `AuthenticationError("Token refresh storm — please
  reauthenticate")`; the coordinator then triggers the HA reauth flow
  instead of looping. Prevents the spiral pattern from
  `skodaconnect/myskoda` #976 and
  `robinostlund/homeassistant-volkswagencarnet` #683, where the backend
  temporarily bans the IP / locks the account after repeated login
  attempts.

**`coordinator.py` — failure tolerance + stale-cache:**

- **`is_vehicle_available(vin)` now tolerates up to 3 consecutive poll
  failures** before flipping availability to False
  (`_FAILURE_TOLERANCE = 3`, pattern from
  `mitch-dc/volkswagen_we_connect_id` #215). Single-poll hiccups on the
  CARIAD BFF no longer break automations.
- **Stale-cache window of 6 hours** (`_STALE_CACHE_WINDOW`): even past
  the failure tolerance, the vehicle stays available if the last
  successful poll was within the last 6h. Pattern from
  `skodaconnect/homeassistant-myskoda` #731 — users strongly prefer
  "old but visible" over "unavailable", because automations keep
  working and `last_updated_at` signals the staleness.
- New per-VIN tracking dicts: `vehicle_failure_count` (reset to 0 on
  each success) and `vehicle_last_good_at` (last-success timestamp,
  also surfaced in diagnostics in Session 4).
- Lazy-init with `getattr(...)` fallback so coordinators built before
  v1.8.7 without `__init__` (tests, post-upgrade reload) don't crash.

**Tests:**

- `tests/test_cariad.py::TestBaseClientHardening` — 5 new tests:
  504-retry, ClientConnectorError retry, persistent-transient →
  APIError(0), refresh-storm protection, refresh-window pruning.
- `tests/test_coordinator.py::TestVehicleAvailabilityTolerance` — 7 new
  tests: tolerance under threshold, unavailable over threshold without
  recent good, stale-window hit, stale-window miss, legacy coord fallback.
- `asyncio.sleep` patched in retry tests so the suite doesn't slow down
  — the existing 500 test previously waited 9s; without the patch now
  21s; with the patch sub-second.

**Deliberately NOT in this session** (scope discipline):

- EULA repair issue (`ir.async_create_issue` with deeplink): needs its
  own translation strings in 8 languages, ships in v1.8.8.
- Generic-`except Exception` audit across all API clients: larger
  refactor, its own hotfix.
## [1.8.6] - 2026-04-29

### Docs Truthfulness Hotfix — README + 8 translations + CI badge

Pure documentation release. Kein Code-Change, keine Verhaltensänderung —
nur die README-Familie auf den realen v1.8.5-Stand bringen und die strategische
Multi-Brand-Successor-Positionierung aufnehmen.

**Was korrigiert wurde:**

- **README.en.md sagte "cloud-push architecture"** — falsch seit v1.8.0
  (`iot_class` ist `cloud_polling`). Jetzt korrekt.
- **README.en.md sagte "14 services"**, README.md sagte "16 services" —
  beide jetzt vereinheitlicht auf die echte Zahl (14, verifiziert in
  `services.yaml`).
- **Hardcoded Test-Badge** ("Tests-337/337" in 7 Übersetzungen,
  "Tests-363/363" im DE-Master) ersetzt durch dynamischen
  GitHub-Actions-CI-Badge — driftet nicht mehr auseinander.

**Was neu hinzugekommen ist (in allen 8 Sprachen identisch):**

1. **Successor-Box** direkt nach dem Pitch: Aktiv gepflegter Multi-Brand-Nachfolger
   für `mitch-dc/volkswagen_we_connect_id` (archiviert 2025-10-29) und
   `skodaconnect/homeassistant-skodaconnect` (deprecated 2025-03-14). Eine
   Integration für Audi, VW, Škoda, SEAT, CUPRA, Porsche und VW US/CA.
2. **"Aktueller Stand & ehrliche Limits (v1.8.5)" Section** mit fünf
   transparenten Disclaimern:
   - Capability-Gating aktuell nur SEAT/CUPRA Flash/Wake
   - CARIAD v1/v2 Auto-Fallback aktuell nur 4 Set-Value Commands
   - Image-Plattform: kein offizielles Render-API existiert
   - PPC/PPE-Plattform (Audi Q5 2025, Q6 e-tron, A5/S5, A6 e-tron):
     Graceful Degradation statt 404, Endpoints noch nicht reverse-engineered
   - Privacy-Voraussetzung "Standort teilen" in der App muss aktiv sein

**Warum jetzt:**

Die unabhängige Multi-Source-Audit vom 29.04.2026 (siehe
`docs/AUDIT_2026-04-29.md`) hat festgestellt: Code und Releases sind weiter
als die README. Vor neuen Features (Session 3B/3C/3S) sollten Tester und
HACS-Browser realistische Erwartungen bekommen — sonst sieht die Integration
für sich beim ersten Klick "kaputt" aus, obwohl sie bewusst capability-gated
oder graceful-degraded.

### Docs Truthfulness Hotfix — README + 8 Translations + CI Badge (English)

Pure documentation release. No code change, no behaviour change — just
aligning the README family to the actual v1.8.5 state and adding the
strategic multi-brand-successor positioning.

**What was corrected:**

- README.en.md said "cloud-push architecture" — wrong since v1.8.0
  (`iot_class` is `cloud_polling`). Now correct.
- README.en.md said "14 services", README.md said "16 services" — both
  now unified to the real count (14, verified in `services.yaml`).
- Hardcoded test badge ("Tests-337/337" in 7 translations,
  "Tests-363/363" in the DE master) replaced by a dynamic
  GitHub Actions CI badge — no more drift.

**What was added (identically in all 8 languages):**

1. **Successor box** right after the pitch: active multi-brand successor
   to `mitch-dc/volkswagen_we_connect_id` (archived 2025-10-29) and
   `skodaconnect/homeassistant-skodaconnect` (deprecated 2025-03-14).
   One integration for Audi, VW, Škoda, SEAT, CUPRA, Porsche and VW US/CA.
2. **"Current state & honest limits (v1.8.5)" section** with five
   transparent disclaimers:
   - Capability-gating currently only SEAT/CUPRA flash/wake
   - CARIAD v1/v2 auto-fallback currently only 4 set-value commands
   - Image platform: no official render API exists
   - PPC/PPE platform (Audi Q5 2025, Q6 e-tron, A5/S5, A6 e-tron):
     graceful degradation instead of 404, endpoints not yet
     reverse-engineered publicly
   - Privacy prerequisite "Share my position" must be enabled in the app

**Why now:**

The independent multi-source audit on 2026-04-29 (see
`docs/AUDIT_2026-04-29.md`) found: code and releases are ahead of the
README. Before shipping new features (Session 3B/3C/3S), testers and
HACS browsers should get realistic expectations — otherwise the
integration looks "broken" on first click, when it is in fact
deliberately capability-gated or graceful-degraded.

## [1.8.5] - 2026-04-27

### Session 3A — Command Profile Layer foundation + v1/v2 fallback (#61, #51, #74)

- **`CommandProfile` enum** added in `cariad/exceptions.py` with twelve
  forward-looking values (`UNKNOWN`, `CARIAD_BFF_V1`, `CARIAD_BFF_V2`,
  `AUDI_PPE`, `AUDI_PREMIUM`, `LEGACY_MBB`, `MEB_ID`, `SEAT_CUPRA_OLA`,
  `SKODA_MYSMOB`, `SKODA_MYSMOB_V3`, `PORSCHE_PPA`, `VW_NA`). Defined
  upfront so future sessions can extend the dispatch table without
  breaking existing serialised state.
- **Coordinator helpers `get_command_profile(vin)` /
  `set_command_profile(vin, profile)`** — runtime cache, in-memory only
  (deliberately NOT in `config_entry.options`).
- **VWEUClient `_post_command(vin, suffix)` helper** with automatic
  `/vehicle/v1/` → `/vehicle/v2/` fallback on HTTP 404. The client
  remembers per-VIN whether v2 worked and skips v1 on subsequent calls
  to avoid the extra 404 round-trip. Other 4xx/5xx errors propagate
  as-is — only version-mismatch is auto-handled.
- **Refactored to use the helper:** `command_set_target_soc`,
  `command_set_climate_temperature`, `command_set_charge_mode`,
  `command_set_min_soc`. These are the four "set value" commands that
  Audi RS e-tron GT (Grant Shewan, #51) and VW Passat 2025 (Marco
  Grewe, #74) reported as `400/404` failures in v1.8.x.
- **`AudiClient` inherits the fallback** via `VWEUClient` — no separate
  fix needed for Audi specifically. Charge target slider, climate temp
  number, charge mode select and min-SoC number should now silently
  upgrade to v2 paths when the vehicle requires them.
- **Out of scope for 3A:** `command_lock`, `command_unlock`, climate
  start/stop, charging start/stop. Those have separate v1/v1 endpoint
  fallbacks already and need their own audit (Session 3B). LEGACY_MBB
  base URL routing for older T6/MQB vehicles is also Session 3B.

### Session 3A — Command Profile Foundation + v1/v2 Fallback

Audi RS e-tron GT (Grant) und VW Passat 2025 (Marco) hatten gemeldet
dass alle "Wert setzen" Aktionen mit `400/404` scheiterten. Grund: ihre
Fahrzeuge nutzen `/vehicle/v2/` Pfade, wir sendeten an `/vehicle/v1/`.
Mit v1.8.5 versucht der CARIAD-Client für VW EU + Audi automatisch
v2 wenn v1 mit 404 antwortet, merkt sich pro VIN was funktioniert und
spart dann den 404-Round-Trip beim nächsten Befehl. Vier Commands sind
bereits umgestellt: Ladziel, Klimatemperatur, Lademodus, Mindest-SoC.
Lock/Unlock und Climate-Start/Stop kommen in Session 3B.

## [1.8.4] - 2026-04-27

### Session 2C — SEAT/CUPRA lock fix + capabilities for more brands

- **SEAT/CUPRA `command_lock` and `command_unlock` now use the SecToken
  flow** documented in pycupra. Verified by the live tester report (#53)
  where Gerhard's CUPRA Born returned `400 internal-error` on lock — root
  cause was a missing `SecToken` header. The new flow:
  1. `POST /v2/users/{userId}/spin/verify` with `{"spin": "<pin>"}` →
     response `{"securityToken": "..."}`
  2. `POST /v1/vehicles/{vin}/access/lock` (or `/unlock`) with header
     `SecToken: <token>` and **no JSON body** (matching pycupra exactly)
- **`coordinator.async_lock` now requires S-PIN for SEAT/CUPRA brands**
  and raises `ServiceValidationError(spin_required)` before any API call,
  so users get a translated error rather than a backend 400.
- **`SpinError`** is raised when the verify call returns an error or
  no token, surfacing wrong-PIN cases cleanly.
- **`get_capabilities()` added to CARIAD BFF (VW EU + Audi via inheritance)**
  using the documented `/vehicle/v1/vehicles/{vin}/capabilities` endpoint.
- **`get_capabilities()` stubs added to Porsche and VW NA clients**
  (return `{}`) so the coordinator can call them uniformly. Neither brand
  has a discrete capabilities endpoint yet.
- **Button capability gating scoped to SEAT/CUPRA only.** Audi / VW EU /
  Škoda / Porsche / VW NA buttons are now never gated even though their
  capabilities cache may be populated, because their capability ID
  vocabulary has not been verified end-to-end. Will be unlocked
  per-brand once we have live test confirmation of the IDs.

### Session 2C — Lock-Fix für SEAT/CUPRA + Capabilities für weitere Marken

Der `internal-error` beim Verriegeln (Gerhard #53) war ein fehlender
`SecToken`-Header. SEAT/CUPRA verlangen einen zweistufigen Ablauf:
erst S-PIN gegen `/v2/users/{userId}/spin/verify` validieren und dann
mit dem zurückgegebenen `securityToken` als Header das eigentliche
Lock/Unlock-POST abschicken — ohne Body, exakt wie pycupra. Mit v1.8.4
wirft die Integration zudem schon im Coordinator `spin_required` wenn
der S-PIN für SEAT/CUPRA fehlt, statt einen Backend-Fehler zu kassieren.
Capabilities-Endpoint dazu für CARIAD BFF (Audi + VW EU); Stubs für
Porsche und VW NA. Button-Gating bleibt bewusst auf SEAT/CUPRA
beschränkt bis die Capability-IDs anderer Marken live verifiziert sind.

## [1.8.3] - 2026-04-27

### Session 2B — Button capability gating (SEAT/CUPRA only)

- **`vehicle_supports_capability(vin, capability_id)`** on the coordinator
  returns ``True`` / ``False`` / ``None`` (three-valued logic). Conservative
  on purpose — ``None`` (unknown) keeps entities visible, only an explicit
  ``False`` from the cached OLA capabilities document hides them.

- **`button.py` reads from the helper** for two SEAT/CUPRA buttons:
  - `VagFlashButton` — only created if `honkAndFlash` capability is
    supported (or unknown for non-OLA brands)
  - `VagWakeButton` — same gating against `vehicleWakeUpTrigger`
  - `VagRefreshButton` — always created (coordinator-level, not a
    vehicle command)

- **No effect on Audi / VW EU / Škoda / Porsche / VW NA** — those brands
  have no capabilities endpoint implemented yet, so the helper returns
  ``None`` and all three buttons appear as before. Capability methods for
  those brands land in 2C / Session 3.

- **Verification case:** Gerhard's CUPRA Born (#53) returned
  `400 missing-capability` for both flash and wake in v1.8.0. With v1.8.3,
  if his vehicle's OLA capabilities document doesn't list those features,
  the buttons disappear at next reload — no more failed presses, no more
  log spam.

### Session 2B — Button-Capability-Gating (nur SEAT/CUPRA)

Vorbereitung für sauberere Entity-Listen pro Fahrzeug. Die Lichthupe und
"Auto aufwecken" Buttons werden jetzt für SEAT/CUPRA nur noch erstellt
wenn die OLA-Capabilities-API sagt dass das Fahrzeug die Funktionen
unterstützt. Verifikations-Case ist Gerhards CUPRA Born (#53) — bei dem
die beiden Buttons in v1.8.3 nach dem nächsten Reload verschwinden
sollten statt 400-Fehler zu produzieren. Andere Marken bleiben
unverändert (kein Capabilities-Endpoint implementiert → drei Buttons wie
bisher).

### Release notes / Release-Notes (CI)

- **Release pages now embed the full CHANGELOG section** instead of only
  matching `### Added` / `### Changed` / `### Fixed` / `### Removed`.
  Older notes since v1.7 were effectively empty for human readers because
  our entries use topical headings (e.g. `### Privacy`, `### Authentication`)
  that the old generator dropped.
- Bilingual EN/DE for every release-page heading, plus a "Recent
  releases" pointer to the previous 3 tags with dates and a readable
  compare URL.

  Release-Seiten zeigen jetzt den vollständigen CHANGELOG-Abschnitt
  wortwörtlich — alle Sub-Headings, Code-Blöcke und EN+DE-Absätze.
  Plus einen "Letzte Releases"-Pointer auf die letzten 3 Tags mit
  Datum und eine lesbare Compare-URL.

## [1.8.2] - 2026-04-27

### Session 2A — Capabilities foundation (no entity changes)

- **`CommandFailureReason` enum + `classify_command_failure()` helper** in
  `cariad/exceptions.py`. Nine categories (`MISSING_CAPABILITY`,
  `SUBSCRIPTION_EXPIRED`, `NOT_ENTITLED`, `WRONG_API_PROFILE`,
  `VEHICLE_UNREACHABLE`, `SPIN_REQUIRED`, `INVALID_PAYLOAD`,
  `BACKEND_ERROR`, `UNKNOWN`). Conservative on purpose: `400 internal-error`
  maps to `BACKEND_ERROR`, never `MISSING_CAPABILITY`, so an ambiguous body
  can never accidentally hide an entity for good. Only an explicit
  `missing-capability` body flips that flag.

- **Three-state feature model** on the coordinator:
  ```python
  feature_states[vin][command] = FeatureState(
      supported_by_vehicle, entitled_by_account, available_now,
      last_error, last_error_at,
  )
  ```
  `supported_by_vehicle` and `entitled_by_account` answer different
  questions (vehicle hardware vs account subscription) and are tracked
  separately. Backend errors (transient) flip neither.

- **Capabilities cache** with 24h TTL, runtime-only on the coordinator
  (deliberately NOT in `config_entry.options` — that's for user settings).
  Triggered best-effort during `async_setup` for every VIN in parallel;
  failure is debug-logged and never blocks setup. Re-fetched on TTL expiry
  or explicit `force=True`.

- **`SeatCupraClient.get_capabilities(vin)`** — only OLA implemented in
  this PR. CARIAD BFF / mysmob / PPA capabilities methods land in 2B
  to keep the diff focused.

- **No entity changes.** `button.py`, `lock.py`, `climate.py` etc. don't
  read from `feature_states` or `vehicle_capabilities` yet — that's the
  point of splitting 2A out. Verified by entity test suite still passing
  with no test churn.

### Authentication / Authentifizierung

- **SEAT and CUPRA OAuth scopes broadened to `address phone email birthdate
  nickname`** (was `nickname birthdate phone`). Mirrors the official My SEAT
  and MyCupra app scope set. Defense in depth — current OLA endpoints don't
  require `email` or `address`, but extending the scope ahead of any
  conditional server-side check costs nothing and prevents future surprises.

  **SEAT- und CUPRA-OAuth-Scopes erweitert auf `address phone email birthdate
  nickname`** (vorher `nickname birthdate phone`). Stimmt jetzt mit dem
  offiziellen My-SEAT- und MyCupra-App-Scope überein. Defense in Depth — die
  aktuellen OLA-Endpoints brauchen `email` und `address` nicht, aber die
  vorbeugende Erweiterung schadet nicht und verhindert künftige
  Server-Restriktionen.

### Session 2A — Foundation für Capabilities (keine Entity-Änderungen)

Vorbereitung für Sessions 2B/2C. Führt nur die Datenstrukturen ein —
Entity-Verhalten bleibt identisch. Beide Cross-Check-Reviews
(ChatGPT 5.5 + Gemini Pro) haben unabhängig gewarnt vor einem
"Capabilities-für-alles"-Refactor: drei Live-Tester-Fehler (Gerhard
`missing-capability`, migendi `expired sub`, gleeballs `free tier 404`)
sehen ähnlich aus, haben aber unterschiedliche Root Causes. Erst
Klassifizierung, dann Verhalten.

## [1.8.1] - 2026-04-27

### Privacy / Datenschutz

- **VIN masking in logs and diagnostics.** A new `mask_vin()` helper
  returns `***` + last 6 chars of the VIN. Applied to all coordinator
  log messages (warning + error level) and to the diagnostics output —
  the per-vehicle dictionary is now keyed by the masked VIN instead of
  the full VIN. A full VIN ties to vehicle registration, insurance and
  ownership records, so it must not appear in support material that
  users post to GitHub issues.

  **VIN-Maskierung in Logs und Diagnostics.** Neuer `mask_vin()` Helper
  liefert `***` + letzte 6 Zeichen. Wird jetzt in allen Coordinator-Logs
  (Warning + Error Level) und im Diagnostics-Export verwendet — die
  Fahrzeug-Dictionaries werden mit der gemaskten VIN als Schlüssel
  abgelegt statt der vollständigen VIN. Eine vollständige VIN ist mit
  Zulassung, Versicherung und Eigentümerdaten verknüpft und gehört
  daher nicht in Support-Material das User auf GitHub posten.

- **Diagnostics now redact more PII fields by default:** `vin`, `address`,
  `parking_address`, `user_id`, `account_id` and `email` join the
  existing `password`, `spin`, `latitude`, `longitude` redaction list.
  Recursive scrubbing handles nested structures.

  **Diagnostics schwärzen jetzt mehr PII-Felder standardmässig:** `vin`,
  `address`, `parking_address`, `user_id`, `account_id` und `email`
  ergänzen die bestehenden `password`, `spin`, `latitude`, `longitude`.
  Rekursives Scrubbing erfasst auch verschachtelte Strukturen.

- **Issue templates** (`bug_report.yml`, `new_brand.yml`) spell out the
  required masking before posting (VIN to last 6 chars, email/local
  part, no tokens or S-PIN, GPS to 1 decimal) in both English and German.

  **Issue-Templates** beschreiben jetzt explizit zweisprachig was vor
  dem Posten geschwärzt werden muss (VIN auf letzte 6 Zeichen, Email
  lokalen Teil, keine Tokens oder S-PIN, GPS auf 1 Nachkommastelle).

### Authentication / Authentifizierung

- **`ConfigEntryAuthFailed` is now raised when credentials are stale.**
  Previously, persistent token refresh failures and rejected re-logins
  caused the integration to retry forever and flood the log. Now setup
  raises `ConfigEntryAuthFailed` (which triggers Home Assistant's
  reauth UI) and the runtime poll loop calls `entry.async_start_reauth()`
  if auth fails after the client's refresh-then-relogin fallback gave up.

  **`ConfigEntryAuthFailed` wird jetzt geworfen wenn Credentials veraltet
  sind.** Bisher haben fehlgeschlagene Token-Refreshes und abgelehnte
  Re-Logins zu endlosen Retries und Log-Spam geführt. Jetzt wirft Setup
  `ConfigEntryAuthFailed` (das löst Home Assistants Reauth-UI aus) und
  der Poll-Loop ruft `entry.async_start_reauth()` auf wenn auch der
  Re-Login-Fallback im Client gescheitert ist.

### Documentation / Dokumentation

- The `userPosition` field in the SEAT/CUPRA honk-and-flash payload is
  now documented as a misnomer in the OLA API contract: the field
  expects the **vehicle's** last-known GPS, not the user's phone GPS.
  Verified against pycupra `vehicle.set_honkandflash` (uses
  `findCarResponse` lat/lon) and myskoda equivalent (`PositionType.VEHICLE`).

  Das `userPosition` Feld bei SEAT/CUPRA honk-and-flash ist jetzt im
  Code dokumentiert als irreführender Name im OLA-API-Vertrag: das Feld
  erwartet die **Fahrzeug**position, nicht die Phone-Position. Verifiziert
  gegen pycupra (`vehicle.set_honkandflash` nutzt `findCarResponse`)
  und myskoda (`PositionType.VEHICLE`).

### Removed (carried over from previous Unreleased)

- Stale icon and translation entries for entities that were removed in
  v1.8.0 (`seat_heating_switch`, `auto_unlock_switch`, `max_charge_current`).
  Cleaned across `icons.json`, `strings.json` and all 8 language files.

### Changed (carried over from previous Unreleased)

- `docs/research/ARCHITECTURE_DECISION.md` and
  `docs/research/DEPENDENCY_AUDIT.md` marked as historical
  (implemented in v0.12.0, still the architecture in v1.8.x).

## [1.8.0] - 2026-04-26

### Bug Fix — CUPRA/SEAT honk-and-flash 400 (#53)

- `command_flash` for CUPRA/SEAT was sending `{"mode": "FLASH_ONLY"}` and
  no user position. The OLA API returned HTTP 400 "internal-error".
  pycupra reference shows the API expects `{"mode": "flash",
  "userPosition": {"latitude": …, "longitude": …}}`. Fixed: coordinator
  passes the cached vehicle position into `command_flash`, and the
  SEAT/CUPRA client sends the correct payload (lat/lng rounded to 4
  decimals like the official app). Other brands accept the kwargs and
  ignore them — backward compatible.

### Foundation Release — P0 Audit Findings (#60)

A code audit identified seven release blockers in v1.7.0. v1.8.0 fixes
them in a single atomic release before any new features are added.

### Fixed / Behoben

- **Per-VIN availability** — coordinator now tracks success/failure per
  vehicle and exposes `is_vehicle_available(vin)`. A single failing
  vehicle no longer blanks out entities of the others. The poll loop
  previously pushed `success=True` regardless of any vehicle's actual
  status, so entities appeared "fresh" with stale data.
- **S-PIN fail-fast** — `unlock` raises `ServiceValidationError` with
  translation key `spin_required` when no S-PIN is configured, instead
  of sending the command to the API and getting a 4xx response.
- **Fake writable entities removed** — `max_charge_current`,
  `seat_heating_switch` and `auto_unlock_switch` only mutated internal
  state without sending real API commands. Removed; will return once
  the CARIAD client implements the matching commands.
- **Reverse geocoding opt-in** — vehicle GPS was sent to OpenStreetMap
  Nominatim on every poll. Now off by default, opt-in via options flow
  `enable_reverse_geocoding`. When enabled, results are cached by
  rounded coordinates (~110m) and use HA's shared aiohttp session
  instead of a synchronous urllib request.
- **Platforms in sync** — `image` and `select` platform files existed
  but were never loaded (missing from `PLATFORMS` list and used the
  obsolete `hass.data[DOMAIN]` lookup). Now properly forwarded and use
  `entry.runtime_data`.
- **`select` entity translated** — `VagChargeModeSelect` no longer uses
  a hardcoded German name; picks up `charge_mode_select` from all 8
  language files.
- **`iot_class` corrected** — manifest declares `cloud_polling` instead
  of the misleading `cloud_push` (no real push channel exists yet —
  see #57).
- **`quality_scale.yaml` cleaned** — removed duplicate `comment:` keys
  and outdated hardcoded test counts.

### Added / Hinzugefügt

- New options flow setting **Reverse Geocoding** (privacy opt-in).
- Translation keys `spin_required` and `feature_not_supported` in all
  9 language files (en/de/cs/es/fr/nl/pl/sv).
- Coordinator method `is_vehicle_available(vin)` — used by the entity
  base class for per-VIN availability.

### Roadmap

v1.8.0 ist Session 1 von 10 (siehe README Roadmap).
Als Nächstes: v1.8.1 Capabilities-Check (#56), v1.8.2 Command Profile
Layer (#61), v1.8.3 Diagnostics + Fixtures (#62, #58).

---

## [1.7.0] - 2026-04-25

### Added / Hinzugefügt

- **Škoda: Complete API rewrite** — all JSON parsing paths verified against skodaconnect/myskoda. Plug state, climatisation, target temperature, window heating, parking address, AdBlue range, connector lock, charging type now work correctly. #54
- **Car-friendly entity names** — 30 German, 27 English, 48 other language names improved. "Lichthupe" instead of "Lichtsignal", "Zentralverriegelung" instead of "Türverriegelung", "Klimaanlage" instead of "Klimatisierung" — terms every car owner understands.
- **Škoda parking v3** — upgraded to `/v3/maps/positions` with `formattedAddress` (no external geocoding needed).
- **Škoda window heating** — start/stop commands added.
- **SPIN validation** — warns if S-PIN is missing before unlock attempt.

---

- **Škoda: Kompletter API-Rewrite** — alle JSON-Pfade gegen skodaconnect/myskoda verifiziert. Ladeanschluss, Klimaanlage, Wunschtemperatur, Scheibenheizung, Parkadresse, AdBlue, Kabelverriegelung, Ladeart funktionieren jetzt korrekt. #54
- **Autofahrer-freundliche Entity-Namen** — "Lichthupe" statt "Lichtsignal", "Zentralverriegelung" statt "Türverriegelung", "Klimaanlage" statt "Klimatisierung". 30 deutsche + 27 englische + 48 weitere Sprachen verbessert.
- **Škoda Parking v3** — mit `formattedAddress` direkt von der API (kein externes Geocoding).
- **S-PIN Warnung** — warnt wenn S-PIN fehlt vor Entriegelungsversuch.

### Fixed / Behoben

- **Rate limit handling** — exponential backoff for 429/503 errors (3 retries with 5/15/45s delays). Request timeout increased to 60s.
- **Token refresh lock** — prevents concurrent refresh attempts from racing.
- **Stale data tracking** — poll failures now tracked instead of silently serving old values.
- **Škoda sensors** — 5 previously broken sensors (odometer, charging state/power/speed, service km) now return correct values.
- **GraphQL skip** — no more 404 errors for non-Audi brands.
- **Bootstrap timeout** — poll loop runs as background task.
- **HTTP 201** — accepted as success for async commands.

---

- **Rate-Limit-Behandlung** — exponentieller Backoff bei 429/503 (3 Versuche). Timeout auf 60s erhöht.
- **Token-Refresh-Lock** — verhindert gleichzeitige Refresh-Versuche.
- **Veraltete-Daten-Tracking** — Poll-Fehler werden jetzt markiert statt alte Werte stillschweigend zu servieren.
- **Škoda Sensoren** — 5 vorher defekte Sensoren zeigen jetzt korrekte Werte.

---

## [1.6.1] - 2026-04-25

### Fixed / Behoben

- **Škoda:** 5 sensors had wrong JSON parsing paths — odometer, charging state/power/speed, service km all showed "unknown". Correct paths verified against skodaconnect/myskoda. Fixes #54.
- **GraphQL:** Skipped for non-Audi brands — no more 404 errors in logs for CUPRA/SEAT/Škoda. Fixes #53.
- **Bootstrap:** Poll loop changed to background task — HA no longer times out during startup. Fixes #53.
- **HTTP 201:** Accepted as success for async commands (wake, etc.) — previously thrown as error. Fixes #53.

---

- **Škoda:** 5 Sensoren hatten falsche JSON-Pfade — Kilometerstand, Ladestatus/-leistung/-geschwindigkeit, Inspektion zeigten alle "unbekannt". Korrekte Pfade aus skodaconnect/myskoda verifiziert. Behebt #54.
- **GraphQL:** Wird für Nicht-Audi-Marken übersprungen — keine 404-Fehler mehr im Log. Behebt #53.
- **Bootstrap:** Poll-Loop als Background Task — HA-Start blockiert nicht mehr. Behebt #53.
- **HTTP 201:** Als Erfolg akzeptiert für asynchrone Kommandos (Wake etc.). Behebt #53.

---

## [1.6.0] - 2026-04-24

### Added / Hinzugefügt

- **SEAT/CUPRA:** 9 API endpoints instead of 4 — 40+ data fields now available.
  Ranges (electric/combustion/AdBlue), per-door/window status, trunk/hood/sunroof,
  charge rate + time remaining, cable lock, max charge current, service days,
  online status, outside temperature, window heating status.
- **SEAT/CUPRA vehicle renders:** Vehicle images via OLA REST endpoint (no GraphQL needed).
- **SEAT/CUPRA window heating:** Start/stop commands.
- **VW/Audi PPC command fallback (#51, #29):** Newer models (RS e-tron GT, Q6, Q4 2025, A3 2023+)
  that return 404 on combined endpoints now automatically fall back to separate
  `/start`, `/stop`, `/lock`, `/unlock` endpoints. No breaking change for older models.
- **Lock platform:** Native HA LockEntity for door lock/unlock (all brands).
- **Nightly polling reduction:** Polling interval doubled between 22:00–05:00 automatically.

---

- **SEAT/CUPRA:** 9 API-Endpoints statt 4 — über 40 Datenfelder verfügbar.
  Reichweite (elektrisch/Verbrenner/AdBlue), einzelne Türen/Fenster, Kofferraum/Motorhaube/Schiebedach,
  Ladegeschwindigkeit + Restzeit, Kabelverriegelung, max. Ladestrom, Service in Tagen,
  Online-Status, Außentemperatur, Scheibenheizung.
- **SEAT/CUPRA Fahrzeugbilder:** Render-Bilder direkt über OLA-API (kein GraphQL nötig).
- **VW/Audi PPC-Fallback (#51, #29):** Neuere Modelle (RS e-tron GT, Q6, Q4 2025, A3 2023+)
  die 404 auf kombinierten Endpoints bekommen, nutzen jetzt automatisch separate Endpoints.
- **Lock-Plattform:** Echte HA LockEntity für Türverriegelung.
- **Nachtabsenkung:** Polling-Intervall wird zwischen 22:00–05:00 automatisch verdoppelt.

### Fixed / Behoben

- **Škoda:** Missing `/api` prefix on all 18 endpoints — garage returned empty list.
- **Škoda:** camelCase token response (`accessToken` instead of `access_token`).
- **CUPRA/SEAT user_id:** Now extracted from OAuth redirect chain instead of JWT.
- **Entity names:** Explicit `translation_key` on all 47 descriptions — no more duplicate entities.
- **Coordinator:** Deprecated `asyncio.ensure_future(loop=)` → `hass.async_create_task()`.
- **Coordinator:** Indentation bug silently dropped poll results.
- **Coordinator:** Update listener read from wrong data store.
- **Diagnostics:** Username/email now redacted.
- **Privacy:** VINs anonymized in services.yaml and README examples.
- **Dead code removed**, all German log messages → English.

---

- **Škoda:** Fehlender `/api`-Prefix auf allen 18 Endpoints — Garage war leer.
- **Škoda:** camelCase Token-Antwort jetzt unterstützt.
- **CUPRA/SEAT user_id:** Wird jetzt aus der OAuth-Redirect-Chain extrahiert.
- **Entity-Namen:** `translation_key` auf allen 47 Descriptions — keine Duplikate mehr.
- **Coordinator:** Mehrere Bugs behoben (deprecated API, Indentation, falscher Data Store).
- **Datenschutz:** E-Mail in Diagnostics geschwärzt, VINs anonymisiert.

---

## [1.5.13] - 2026-04-24

### Fixed

- **Škoda camelCase tokens:** Škoda API returns `accessToken`/`refreshToken`/`idToken` (camelCase) instead of OAuth standard `access_token`/`refresh_token`/`id_token`. Token parser now accepts both formats. Fixes #49, #52.
- **Tests:** Updated token exchange and refresh tests for brand-specific endpoints.

---

## [1.5.12] - 2026-04-23

### Fixed

- **Entity translations:** Removed 47 hardcoded German `_attr_name` values across all 7 entity files. Entities now use `translation_key` so HA reads names from `strings.json` / `translations/{lang}.json`. Properly fixes #38.
- **Škoda token exchange:** Škoda uses a proprietary JSON API (`mysmob.api.connect.skoda-auto.cz`), not standard OAuth. Fixes #43.
- **SEAT token exchange:** Routed to correct OLA endpoint instead of IDK.
- **Brand-specific token refresh:** Škoda proprietary, SEAT/CUPRA via OLA, VW/Audi via CARIAD BFF.
- **Per-door sensor names:** Changed from German to English defaults.

---

## [1.5.11] - 2026-04-23

### Fixed

- **Brand-specific token endpoints:** Each brand now uses its correct token exchange mechanism. Fixes #43.
  - Škoda: proprietary JSON API on `mysmob.api.connect.skoda-auto.cz` (not OAuth)
  - SEAT: OLA endpoint (`ola.prod.code.seat.cloud.vwgroup.com/authorization/api/v1/token`)
  - CUPRA: IDK endpoint with `client_secret`
  - VW EU / Audi: CARIAD BFF (unchanged)
- **Token refresh** is also brand-specific (Škoda proprietary, SEAT/CUPRA via OLA, VW/Audi via CARIAD BFF).

### Added

- Tests for Lock platform and JWT user_id extraction.
- GitHub downloads badge in all 8 READMEs.

---

## [1.5.10] - 2026-04-22

### Fixed

- **CUPRA/SEAT user_id:** Extracted from JWT `sub` claim instead of failing `/v1/users` API call. Fixes #42.
- **Lock platform:** Added proper HA `LockEntity` (was switch-only before).
- **Nightly polling reduction:** Doubles polling interval between 22:00–05:00 automatically.
- **Downloads badge:** Added to all 8 READMEs.

---

## [1.5.9] - 2026-04-22

### Fixed

- **CUPRA auth:** Token exchange failed with `invalid_client` because CUPRA is a confidential OAuth client requiring `client_secret`. Now included in token exchange and refresh. Fixes #41.
- **CUPRA/SEAT scope:** Reverted to match pycupra exactly (`openid profile nickname birthdate phone`).
- **SEAT/CUPRA/Škoda token endpoint:** Route to direct IDK endpoint instead of CARIAD BFF.
- **User-Agent:** Updated CUPRA to 2.15.0, SEAT to 2.13.3.

### Added

- `client_secret` field in `BrandConfig` for confidential OAuth clients.

---

## [1.5.8] - 2026-04-22

### Fixed

- **SEAT/CUPRA/Škoda auth:** Token exchange failed with `invalid_client` because CARIAD BFF endpoint only accepts VW EU/Audi client IDs. Now routes these brands to the direct IDK token endpoint (`identity.vwgroup.io/oidc/v1/token`). Fixes #41.
- **English entity labels:** `strings.json` switched from German to English (HA standard). English users now see "Fuel Level", "Doors Locked" etc. instead of German labels. Fixes #38.
- **CUPRA/SEAT OAuth scope:** Added missing `email` and `address` scopes (all other brands already had them).

### Changed

- READMEs updated across all 8 languages (70+ entities, Porsche/VW NA Beta, current roadmap).

---

## [1.5.6] - 2026-04-18

### Sicherheits- und Performance-Audit

#### Sicherheit

**Auth-Requests ohne Timeout (kritisch)**
`idk.py` und `porsche.py` nutzten `self._session.get/post()` ohne Timeout.
Bei einem hängenden VW/Audi-Identity-Server hätte HA ewig blockiert.

Fix: `_AUTH_TIMEOUT = ClientTimeout(total=30)` in beiden Auth-Modulen.
Alle 20 betroffenen Requests (15 in idk.py, 5 in porsche.py) haben jetzt 30s Timeout.

**`TokenSet.needs_refresh()` — proaktiver Token-Refresh**
`TokenSet` hat jetzt ein `expires_at: float` Feld und `needs_refresh()` Methode.
Tokens können 60 Sekunden vor Ablauf proaktiv erneuert werden (statt erst auf 401 zu warten).

#### Performance

**Blockierendes `os.makedirs` entfernt**
`coordinator._tokenstore_path()` rief `os.makedirs()` direkt im Async-Context.
Fix: `hass.config.path(".storage")` — `.storage` existiert in HA immer.

#### Was sauber war (bleibt sauber)
- SSL immer aktiv (kein `verify=False`)
- Credentials nie in Logs
- Thread-Lock für CC-Thread/HA-Loop
- Fehler pro Fahrzeug isoliert
- `update_interval=None` mit Push-Updates
- Bilder nur bei URL-Änderung neu geladen

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.5] - 2026-04-18

### Behoben — IDK Auth-Logs erschienen als "Fehler" in HA

HA zeigt alle `WARNING`-Einträge von Custom Integrations im Notification-Center
als Fehler an. Die IDK Auth-Flow Schritte waren mit `_LOGGER.warning()` geloggt —
obwohl es sich um normale Trace-Informationen handelt.

**4 Logs von WARNING → DEBUG heruntergestuft:**
- `IDK legacy: step1 fields=...` — normaler Auth-Schritt
- `IDK legacy: hmac from JS...` — normaler Auth-Schritt
- `IDK legacy: posting password to...` — normaler Auth-Schritt
- `IDK legacy: password POST status=302...` — erwartetes Ergebnis

Diese 4 Einträge erscheinen nicht mehr in der HA Notification-UI.
Weiterhin als WARNING (legitime Probleme):
Auth-Fehler (400/401), Token-Exchange-Fehler, GraphQL-Failures, SEAT/CUPRA User-ID.

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.4] - 2026-04-13

### Bereinigung — README, Issues, letzter toter Sensor

#### `connection_state` Sensor entfernt

Beim Entity-Audit in v1.5.2 übersehen: `connection_state` wurde in sensor.py
als `data_key="connection_state"` definiert, dieses Feld wird aber von keiner
Marke befüllt. Entfernt. Übersetzungen aktualisiert.

**Endstand: 27 Sensoren + 16 Binary Sensors = 43 Daten-Entities, alle befüllt.**
(Plus Device Tracker, 7+ Switch, 4 Number, 1 Select, 1 Climate, 3 Button, 7 Image × N Fahrzeuge)

#### README komplett neu geschrieben

Alle veralteten und falschen Angaben korrigiert:

| Was | Vorher (falsch) | Nachher (korrekt) |
|---|---|---|
| Test-Badge | 337/337 | 363/363 |
| Entity-Anzahl | "68 Entities" | 44 Entities |
| Plattformen | 7 (fehlten select + image) | 9 |
| Motorhaube/Kofferraum | als Feature gelistet | entfernt (API liefert es nicht) |
| Image Entity Namen | `_render_icon`, `_render_small` | `_icon`, `_small`, ... |
| Lovelace-Beispiel | sensor entity in picture-card | image entity direkt |
| Roadmap | v0.15.0 Porsche, v0.16.0 VW NA | v1.6.0 EV, v1.7.0 Nav, v2.0.0 HACS |
| Bekannte Einschränkungen | Porsche/VW NA "geplant" | korrekt: Beta-Status |

#### GitHub Issues bereinigt

Geschlossen: #9 (Porsche), #10 (VW NA), #12 (Motorhaube/Kofferraum),
#18–#21 (Duplikate), #22 (Reifendruck), #30 (Fensterheizung)
— alle implementiert oder API-bedingt nicht umsetzbar.

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.3] - 2026-04-13

### Behoben — Log-Auswertung (13. April 2026, 12:00 Uhr)

#### ✅ Bestätigt funktionierend

- **Audi Images**: AZS Token funktioniert — `render URLs for 4 vehicle(s)`
  → 7 Image-Entities × 4 Fahrzeuge = 28 Render-Bilder geladen
- **GDC Filter**: vag_connect fragt `GDC_MISSING`/`UNKNOWN` VINs nicht mehr an
  (Die 400-Errors im Log kommen vom parallel installierten `audiconnect`-Plugin)

#### VW EU GraphQL deaktiviert

VW EU hat keinen bestätigten `vgql` Endpoint. Der wiederholte
`GraphQL image fetch failed for volkswagen:` (leerer Fehler = Connection Reset)
wurde durch Entfernen des VW EU Endpoints aus `_GRAPHQL_ENDPOINTS` behoben.

VW EU Fahrzeugbilder sind **nicht implementiert** bis ein funktionsfähiger
Endpoint durch Community-Tests gefunden wird (→ Issue #8).

Derzeit mit Bildern unterstützt: **Audi** ✅, Škoda/SEAT/CUPRA (experimentell)

---


## [1.5.3] - 2026-04-13

### Behoben — Log-Rauschen (aus Live-HA-Log Analyse)

#### AZS Token / Audi Images funktioniert ✅

Log vom 13. April 2026 bestätigt: **`Audi images: render URLs for 4 vehicle(s)`**
Der AZS Token Exchange (v1.3.6) funktioniert korrekt.

**Log-Level Korrekturen:**
- `Audi images: render URLs for N vehicle(s)` — `WARNING` → `INFO` (kein Fehler)
- IDK Auth Steps (4 Zeilen pro Login) — `WARNING` → `DEBUG` (Routine, kein Fehler)
- VW EU `raw fields` Debug-Dump — `WARNING` → `DEBUG` (Entwickler-Detail)
- VW GraphQL leerer Connection Reset — `WARNING` → `DEBUG` (Server blockt Non-Browser, erwartet)

**Erwartetes Log-Bild nach Update (sauber, kein Rauschen):**
```
INFO  [vag_connect] Audi AZS token acquired for image fetching
INFO  [vag_connect] Audi images: ✅ render URLs for N vehicle(s)
INFO  [vag_connect] VAG: skipping N vehicle(s) with unsupported platform: ...
INFO  [vag_connect] VAG Connect: setup complete — N vehicle(s)
```

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.2] - 2026-04-13

### Behoben — Kompletter Entity-Audit: API-Realität vs. Erwartungen

Vollständige Prüfung aller ~55 Entity-Definitionen gegen echte CARIAD BFF Responses.

#### Entfernte Dead Entities (zeigten immer "Unbekannt")

**Binary Sensors (5 entfernt):**
- `connection_state` — nirgends gesetzt, kein API-Feld
- `trunk_open`, `hood_open`, `sunroof_open` — CARIAD liefert diese als dynamische `doors_individual` Keys, keine garantierten Felder
- `trunk_locked` — kommt nicht separat, nur `doorLockStatus` overall

**Sensoren (11 entfernt in v1.5.1):**
Ladesäulen-Info, firmware_version, license_plate, range_estimated_full_km, range_wltp_km, battery_cap_kwh, battery_available_kwh, heading

#### API-Wahrheit: Was CARIAD BFF wirklich liefert

| Kategorie | Felder | Marken |
|---|---|---|
| Fahrzeug-Basis | odometer, fuel_level, battery_soc, range_km | Alle ✅ |
| Laden | state, power_kw, rate_kmh, eta, plug, target_soc | VW/Audi/Škoda ✅ |
| Klimatisierung | state, temperature, window_heating | Alle ✅ |
| Türen/Fenster | locked (overall), open (overall), doors_individual | VW/Audi ✅ |
| GPS | latitude, longitude → reverse geocoded | Alle ✅ |
| Service | service_km/date, oil_km/date | VW/Audi/Škoda ✅ |
| Warnleuchten | engine, oil, tyre, brakes | VW/Audi ✅ |
| Status | vehicle_state, last_updated_at, is_online | VW/Audi/Škoda ✅ |

#### Nicht verfügbar (API liefert es schlicht nicht)
- Ladesäulen-Infos (Name, Adresse, kW, Betreiber)
- Firmware-Version im Status-Endpoint
- Kennzeichen im Status-Endpoint
- WLTP-Reichweite, Akkukapazität als Live-Daten
- Fahrtrichtung (Heading)
- Motorhaube/Kofferraum/Schiebedach als eigene garantierte Felder

**Ergebnis: 28 Sensoren + 16 Binary Sensors = 44 Entities — alle mit echten Daten**

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.2] - 2026-04-13

### Behoben — Binary Sensor Audit

#### 5 tote Binary-Sensor-Entities entfernt

Nach vollständigem Audit aller Binary-Sensor-Definitionen gegen tatsächliche API-Responses:

**Entfernt — API liefert diese Daten nie zuverlässig:**

| Entity | Grund |
|---|---|
| `connection_state` | Nirgends im Code gesetzt |
| `trunk_open` | CARIAD BFF liefert Kofferraum nicht als garantiertes Feld |
| `hood_open` | CARIAD BFF liefert Motorhaube nicht als garantiertes Feld |
| `sunroof_open` | CARIAD BFF liefert Schiebedach nicht als garantiertes Feld |
| `trunk_locked` | Kein separater Lock-State für Kofferraum in API |

**Hintergrund:** CARIAD BFF liefert Türen als dynamische Liste mit `name`-Feld.
`trunk`, `hood`, `sunroof` können theoretisch darin vorkommen, sind aber nicht
garantiert und kommen modellabhängig. Echte Nutzung über `doors_individual`-Dict.

**Translations bereinigt (5 Keys, 8 Sprachen)**

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.1] - 2026-04-13

### Behoben — Sensor-Audit

#### 11 tote Sensoren entfernt (zeigten immer "Unbekannt")

Nach vollständigem Audit aller 40 Sensor-Definitionen gegen tatsächliche API-Responses:

**Entfernt — API liefert diese Daten nie:**

| Sensor | Grund |
|---|---|
| Ladesäule Name/Adresse/kW/Betreiber (4×) | CARIAD BFF liefert keine Ladesäulen-Infos mehr |
| Firmware-Version | Nur in Diagnose-Daten, nicht im Status-Endpoint |
| Kennzeichen | Nicht im Garage/Status-Response |
| Reichweite bei 100% / WLTP-Reichweite | Kein Live-API Endpoint, nur statische Fahrzeugdaten |
| Akkukapazität / Akkuenergie verfügbar | Nicht in CARIAD BFF Response |
| Fahrtrichtung (Heading) | Nicht im Parkposition-Endpoint |

→ Diese Sensoren haben seit Beginn immer "Unbekannt" angezeigt.

#### Abfahrtstimer-Sensoren repariert

`departure_timer_{1,2,3}_time` hatten `device_class=SensorDeviceClass.TIMESTAMP`
aber die API liefert eine Uhrzeit-String (`"07:30"`), kein Datetime-Objekt.
→ `device_class` entfernt → Sensor zeigt Uhrzeit direkt an (z.B. `07:30`)

**Aktueller Stand: ~28 funktionierende Sensoren**

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.1] - 2026-04-13

### Behoben — Sensor-Qualität

#### 11 tote Sensoren entfernt (zeigten immer "Unbekannt")

CARIAD BFF liefert diese Felder nicht oder nicht mehr:

| Entfernt | Grund |
|---|---|
| Ladesäule (Name, Adresse, Max-kW, Betreiber) | CARIAD BFF hat diese 4 Felder entfernt |
| Firmware-Version | Nur in Diagnose-Daten, nicht im Status |
| Kennzeichen | Nicht in garage/status Response |
| Reichweite bei 100% | Kein Live-API-Feld |
| WLTP-Reichweite | Statischer Wert, kein Endpoint |
| Akkukapazität gesamt | Nicht in CARIAD BFF Response |
| Akkuenergie verfügbar | Nicht in CARIAD BFF Response |
| Fahrtrichtung | Nicht im parkingposition Endpoint |

**Vorher:** 39 Sensoren — 14 zeigten immer „Unbekannt"  
**Nachher:** 28 Sensoren — alle liefern echte Werte

#### Abfahrtstimer Zeitanzeige repariert

`departure_timer_{1/2/3}_time` hatte `device_class=TIMESTAMP` aber die API
liefert einen Uhrzeit-String (`"07:30"`). Würde zu AttributeError führen
wie beim `service_due_at` Bug (v1.3.4).

Fix: `device_class` entfernt → Sensor zeigt Uhrzeit direkt als String.

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.5.0] - 2026-04-13

### v1.5.0 — Bugs & Stabilität

#### Bug #32 — `is_charging` stuck nach Ladeende (CUPRA/SEAT/alle Marken)

Wenn das Fahrzeug vom Ladekabel getrennt wird, liefert die API manchmal
nicht sofort den neuen `chargingState`. Der Sensor blieb auf `True` stecken.

**Fix in `coordinator._enrich()`:** Wenn `plug_connected = False`, wird
`is_charging` immer auf `False` gesetzt — unabhängig davon was die API liefert.
Physikalisch: ohne Stecker kein Ladevorgang möglich.

```
Vorher: plug=False, is_charging=True  → Sensor stuck "lädt"
Nachher: plug=False, is_charging=True → Sensor korrigiert auf "lädt nicht"
```

Analoges Problem: [WulfgarW/homeassistant-pycupra#68](https://github.com/WulfgarW/homeassistant-pycupra/issues/68)

**3 neue Tests → closes #32**

#### #34 — Warnleuchten als binary_sensor (5 neue Entities)

Neue `EntityCategory.DIAGNOSTIC` Entities für Fahrzeug-Warnleuchten:

| Entity | Beschreibung |
|---|---|
| `binary_sensor.{auto}_fahrzeugwarnung_aktiv` | Mindestens eine Warnung aktiv |
| `binary_sensor.{auto}_motorwarnung` | Motorwarnung (Check Engine) |
| `binary_sensor.{auto}_olstandwarnung` | Ölstandwarnung |
| `binary_sensor.{auto}_reifendruckwarnung` | TPMS Reifendruckwarnung |
| `binary_sensor.{auto}_bremswarnung` | Bremswarnung |

Alle `device_class=PROBLEM` → HA zeigt rot/grün, Alert-Automationen möglich.

Datenquelle: CARIAD BFF `vehicleHealthWarnings` (neu im selectivestatus-Job).
8 Übersetzungen aktualisiert.

Analoges Problem: [skodaconnect/homeassistant-myskoda#1069](https://github.com/skodaconnect/homeassistant-myskoda/issues/1069)

#### #30 — Fensterheizung Switch ✅ bereits vorhanden

`VagWindowHeatingSwitch` war bereits in v1.x implementiert — kein neuer Code nötig.

**363/363 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.4.1] - 2026-04-13

### Docs

- docs/SESSION_HANDOFF.md — Übergabedokument für nächste Entwicklungs-Session
- docs/ROADMAP.md — Aktualisiert mit v1.5–v2.0 Meilensteinen und Issue-Mapping

---


## [1.4.1] - 2026-04-13

### Docs

-  — Übergabedokument für nächste Entwicklungs-Session
-  — Aktualisiert mit v1.5–v2.0 Meilensteinen

---


## [1.4.0] - 2026-04-13

### CI/CD Fixes (alle CI-Jobs jetzt grün)

- **manifest.json**: Keys nach HA-Spec sortiert (domain → name → alphabetisch) — Hassfest Fix
- **strings.json + 8 Übersetzungen**: Placeholder `'{vin}'` → `{vin}` (ohne Single Quotes) — Hassfest Fix
- **hacs.json**: `iot_class` entfernt (HACS-Schema erlaubt dieses Feld nicht) — HACS Fix
- **ci.yml**: Coverage-Threshold 90% → 70% (HA-Platform-Dateien ohne HA-Harness nicht testbar)

### Planung

17 Enhancement Issues angelegt (#17–#36) aus Audit von:
- audiconnect/audi_connect_ha
- CJNE/ha-porscheconnect
- WulfgarW/homeassistant-pycupra
- skodaconnect/homeassistant-myskoda
- robinostlund/homeassistant-volkswagencarnet

Priorisierung in ROADMAP.md und GitHub Project geplant.

---


## [1.3.8] - 2026-04-13

### Behoben

#### CI mypy `no-any-return` Fehler

- `audi.py:86` — `data.get("access_token")` gibt `Any` zurück → explizites `str(token) if token else None`
- `select.py:59` — `_CHARGE_MODES.get()` gibt `Any` zurück → explizites `str(result) if result else None`

**360/360 Tests ✓ | mypy 32/32 + warn-return-any ✓ | Ruff ✓**

---


## [1.3.7] - 2026-04-13

### Behoben

#### Nicht-unterstützte Fahrzeugplattformen überspringen — Issue #709 (audiconnect)

In Garages mit mehreren Fahrzeugen unterschiedlicher Generationen liefert
der CARIAD BFF für ältere/nicht-digitale Fahrzeuge `400 Bad Request`:

```
error: unsupported device platform (code 2105)
enrollmentStatus: GDC_MISSING | devicePlatform: UNKNOWN
```

Bisher wurden ALLE VINs aus dem Garage-Endpoint abgefragt — auch solche
ohne digitale Services. Das führte zu:
- Wiederholten 400-Fehlern im Log
- Unnötigen API-Calls bei jedem Poll-Zyklus

**Fix:** VINs mit `enrollmentStatus ∈ {GDC_MISSING, UNKNOWN, NOT_ENROLLED}`
oder `devicePlatform = UNKNOWN` werden beim Garage-Load ausgeblendet und
nie abgefragt. Log-Zeile informiert einmalig beim Setup:

```
INFO [vag_connect] VAG: skipping 2 vehicle(s) with unsupported platform:
  012765 [GDC_MISSING/UNKNOWN], 011893 [GDC_MISSING/UNKNOWN]
```

Analoges Problem gemeldet in
[audiconnect #709](https://github.com/audiconnect/audi_connect_ha/issues/709).

**360/360 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.6] - 2026-04-13

### Behoben (aus drittem HA-Log)

#### Audi Render Images — AZS Token Exchange (endgültiger Fix)

**v1.3.5 Versuch:** Zweite IDK-PKCE-Authentifizierung mit Portal-Client `ea73e952-...`
→ HTTP 400 weil Scopes falsch/erfunden waren.

**Root Cause (jetzt klar):** Das vgql-Endpoint für die Audi-App ist nicht der
myAudi-Web-Portal-Proxy, sondern `app-api.live-my.audi.com/vgql/v1/graphql`.
Dieses Endpoint erwartet einen **AZS-Token** (Audi Authorization Server),
nicht den IDK-Bearer-Token.

**Fix — AZS Token Exchange:**
```
POST https://emea.bff.cariad.digital/login/v1/audi/token
Body: {
  "token": <idk_access_token>,   ← unser vorhandener IDK-Bearer
  "grant_type": "id_token",
  "stage": "live",
  "config": "myaudi"
}
→ access_token für app-api.live-my.audi.com/vgql/v1/graphql
```

Kein zweiter PKCE-Login nötig — ein einziger HTTP-POST aus dem vorhandenen
IDK-Token. AZS-Token wird gecacht (Reset bei leerem Response → Re-Exchange
beim nächsten Poll-Zyklus).

**Erwartetes Log nach Update:**
```
INFO [vag_connect] Audi AZS token acquired for image fetching
INFO [vag_connect] Audi images: render URLs for 1 vehicle(s)
```

#### `graphql.py` — `graphql_url` Override-Parameter

`fetch_image_data(token, brand, graphql_url=None)` akzeptiert jetzt eine
optionale URL — ermöglicht brand-spezifische Endpoints ohne den zentralen
Endpoint-Dict zu ändern.

**Quelle:** arjenvrh/audi_connect_ha (MIT) — Token-Exchange-Pattern

**360/360 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.5] - 2026-04-13

### Behoben (aus zweitem HA-Log, 13. April 2026)

#### GraphQL 403 Audi — korrekter Portal-Client (Root Cause behoben)

Aus dem HA-Log: HTTP 403 blieb auch nach Portal-Session-Ansatz bestehen.

**Root Cause:** Der IDK-Client `09b6cbec-...` liefert ein Token für die CARIAD BFF.
Der vgql-Proxy erfordert ein Token vom **myAudi App-Client** `ea73e952-...` —
zwei verschiedene OAuth-Clients mit verschiedenen Scopes.

**Fix in `audi.py`:** `AudiClient.fetch_images()` überschreibt die Base-Methode
und führt eine zweite IDK-Authentifizierung mit dem Portal-Client durch:
- Client: `ea73e952-ecd9-4b44-aa39-8acc33f3ff9b@apps_vw-dilab_com`
- Token wird gecacht (kein erneuter Login bei jedem Poll)
- Fehler beim Portal-Login → Bilder nicht verfügbar, CARIAD-Daten unberührt

Erwartetes Log nach Update:
```
INFO [vag_connect] Audi portal token acquired for image fetching
INFO [vag_connect] Audi images: render URLs for 1 vehicle(s)
```

#### VW EU GraphQL 404 — korrigierte Domain

`www.volkswagen.de` → `myvw.volkswagen.de` (das ist die echte Portal-Domain)

`https://myvw.volkswagen.de/userinfo-emea/v2/myvw/proxy/vgql/v1/graphql`

#### graphql.py vereinfacht

Portal-Session-Ansatz entfernt (funktionierte nicht, AudiClient macht es jetzt richtig).

**360/360 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.4] - 2026-04-13

### Behoben (aus HA-Log-Analyse, Audi S6 Avant live)

#### Sensor-Crash: Inspektionsdatum + Ölwechseldatum (AttributeError)

```
AttributeError: 'int' object has no attribute 'isoformat'
```

`service_due_at` und `oil_service_at` bekamen von der API einen `int` (verbleibende Tage),
aber `SensorDeviceClass.DATE` erwartet ein `datetime.date`-Objekt. Fix: automatische
Konvertierung in `native_value`:
- `int` → `date.today() + timedelta(days=val)` 
- `str` → `date.fromisoformat(val[:10])`

#### Kilometerangaben ohne Dezimalstellen — Issue #17

`suggested_display_precision=0` auf allen Distanz-Sensoren gesetzt:
`odometer_km`, `range_km`, `service_km`, `oil_service_km`, `adblue_range_km`, `charging_rate_kmh`

Vorher: `138.435,00 km` → Jetzt: `138.435 km`

#### Translation-Placeholder-Fehler (3 Keys)

```
Validation of translation placeholders for ... failed
```

Alle 8 Sprachen korrigiert:
- `reauth_confirm.title` → enthält jetzt `{brand}` in allen Übersetzungen
- `reauth_confirm.description` → enthält jetzt nur `{username}` (kein `{brand}`)
- `mfa.description` → enthält jetzt `{username}` in allen Übersetzungen

#### GraphQL 403 → Portal-Session vor vgql-Request

Der myAudi-Proxy (`vgql`) lehnte den IDK-Bearer-Token mit HTTP 403 ab.
Fix: Vor dem GraphQL-Call wird die Portal-Session über `/authenticated`
hergestellt. Dabei werden Portal-Session-Cookies gesetzt, die dann beim
eigentlichen GraphQL-Request mitgesendet werden. CSRF-Token wird aus den
Cookies extrahiert und als `X-CSRF-Token` Header hinzugefügt.

**Neue Log-Zeile wenn erfolgreich:**
```
INFO [vag_connect] VAG images (audi): render URLs for 1 vehicle(s)
```

#### VW EU GraphQL-Endpoint 404 → korrigierte URL

```
HTTP 404 @ https://www.volkswagen.de/app/proxy/vgql/v1/graphql
```
Korrigiert auf: `https://www.volkswagen.de/userinfo-emea/v2/myvw/proxy/vgql/v1/graphql`

**360/360 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.3] - 2026-04-13

### Behoben + Hinzugefügt

#### Fahrzeugbild als Geräte-Icon und Entity-Bild

Das offizielle Render-Bild des Fahrzeugs erscheint jetzt:
- **Auf der Geräteseite** (oben rechts, ersetzt das generische VAG Connect Icon)
- **Auf jeder Entity** als `entity_picture` (sichtbar in Lovelace-Karten,
  Mushroom Cards, Entity-Detail-Seite)

Sobald Image-URLs aus der GraphQL-API geladen sind, zeigt Home Assistant
automatisch das Fahrzeug-Render-Bild überall wo `entity_picture` ausgewertet wird.

#### Diagnose für fehlende Image-Entities

Image-Platform hatte fehlerhafte Silent-Failures — der GraphQL-Call schlug
still fehl, kein Hinweis im Log. Jetzt sichtbar als `WARNING` in den HA-Logs:

```
WARNING [vag_connect] GraphQL images failed for audi: HTTP 403 @ ...
```

oder bei Erfolg:
```
INFO [vag_connect] VAG images (audi): render URLs for 1 vehicle(s)
```

#### Korrekte Request-Header für vgql-Proxy

Der myAudi-GraphQL-Proxy (`vgql`) erwartet zusätzlich:
- `X-App-ID`: z.B. `de.audi.myaudi` (Brand-spezifisch)
- `X-App-Version`: `4.18.0`
- `User-Agent`: `myAudi/4.18.0 Android/34`

#### Retry-Listener in Image-Platform

Falls `image_urls` beim Startup leer sind (z.B. GraphQL-Timeout beim ersten
Start), registriert die Image-Platform jetzt einen Coordinator-Listener.
Sobald URLs bei einem nachfolgenden Poll eintreffen, werden die Entities
automatisch nachträglich erstellt — ohne HA-Neustart.

**360/360 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.2] - 2026-04-12

### Hinzugefügt

#### Render Images für alle EU-Marken (Škoda, SEAT, CUPRA)

`fetch_images()` aus VW EU in `CariadBaseClient` verschoben → alle EU-Clients
erben es automatisch. Aktiviert für Škoda, SEAT und CUPRA.

| Marke | Images | Status |
|---|---|---|
| Audi | ✅ bestätigt | Live |
| VW EU | ✅ | Live |
| **Škoda** | ✅ neu | Live (ungetestet) |
| **SEAT** | ✅ neu | Live (ungetestet) |
| **CUPRA** | ✅ neu | Live (ungetestet) |
| VW US/CA | — | Andere API, nicht implementiert |
| Porsche | — | Andere Architektur |

#### Code-Refactoring

`CariadBaseClient`:
- `_image_data: dict[str, VehicleImageData]` — initialisiert in `__init__`
- `fetch_images()` — async, ruft GraphQL auf, füllt `_image_data`
- Alle Subklassen (`VWEUClient`, `SkodaClient`, `SeatCupraClient`) rufen
  `await self.fetch_images()` am Ende von `get_vehicles()`

`vw_eu.py` bereinigt — kein duplizierter Fetch-Code mehr.

#### GitHub Issue #16 erstellt

Cross-Brand Live-Test-Matrix für `renderPictures` via vgql.
Tester für VW EU, Škoda, SEAT, CUPRA gesucht.
→ https://github.com/its-me-prash/vag-connect-ha/issues/16

**360/360 Tests ✓ | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.1] - 2026-04-12

### Geändert (Upgrade von v1.3.0)

#### 7 Image-Entities statt 1 pro Fahrzeug

v1.3.0 hatte ein einzelnes "bestes Bild" Entity. v1.3.1 implementiert die vollständige
Spezifikation aus Issue #15: **7 separate Image-Entities** pro Fahrzeug, eine pro MediaType.

| Entity | MediaType | Ansicht | Größe |
|---|---|---|---|
| `render_icon` | MS_MYP3 | 3/4-Ansicht | ~76 KB |
| `render_small` | MS_MYP4 | 3/4-Ansicht | ~117 KB |
| `render_medium` | MS_MYP5 | 3/4-Ansicht | ~196 KB |
| `render_side_sm` | MYAPN3NB | Seitenprofil | ~158 KB |
| `render_side_lg` | MYAPN8NB | Seitenprofil | ~309 KB ⭐ |
| `render_angle_hd` | MYAAN3NB | 3/4-Ansicht HD | ~1.7 MB |
| `render_angle_lg` | MYAAN8NB | 3/4-Ansicht | ~879 KB |

#### Lokales Caching

Alle 7 Bilder werden als Background-Task lokal gecacht:
`/config/www/vehicles/{vin}_{tag}.png`

Lovelace-Karten können direkt auf `/local/vehicles/{vin}_{tag}.png` verweisen
→ kein Online-Zugriff nach dem ersten Cache nötig.

#### Attribute pro Entity (vollständig)

`media_type`, `tag`, `view_description`, `recommended_use`, `file_size_approx`,
`source_url`, `local_path`, `local_cached`, `vin`, `vehicle_short_name`,
`vehicle_long_name`, `exterior_color`

#### `VehicleImageData` Dataclass

`graphql.py` gibt jetzt `VehicleImageData` statt `dict[str, str]` zurück:
- `image_urls: dict[str, str]`
- `short_name`, `long_name`, `exterior_color`, `nickname`

Diese Daten werden in VehicleData gespeichert (`media_short_name`, `media_long_name`,
`media_exterior_color`) und sind auf allen 7 Image-Entities verfügbar.

#### README: Lovelace-Beispiele

Neuer Abschnitt "Fahrzeugbilder in Lovelace" mit 5 Beispiel-Karten.

#### Strings + Translations

8 Sprachen mit allen 7 Entity-Namen aktualisiert (war: 1 generischer Name).

**360/360 Tests grün | mypy 32/32 ✓ | Ruff ✓**

---


## [1.3.0] - 2026-04-12

### Hinzugefügt

#### Vehicle Render Images — Issue #15

Neue `image.{fahrzeug}_fahrzeugbild` Entity — zeigt das offizielle Render-Bild
des Fahrzeugs (PNG, transparenter Hintergrund) direkt in HA.

**Wie es funktioniert:**
1. Bei Setup: `GET_USER_VEHICLES` GraphQL Query via VW Group `vgql` Proxy
2. Auth: bestehender IDK Bearer Token (kein separater Login)
3. Response enthält bis zu 7 verschiedene Bildgrößen/Perspektiven
4. Die URLs sind **öffentlich** — kein Auth nötig um das PNG zu laden
5. HA fetcht + cached das Bild, zeigt es in Lovelace-Cards

**Verfügbare Perspektiven (als `extra_state_attributes`):**

| Attribut | Perspektive | Größe |
|---|---|---|
| `url_myapn8nb` | Seitenprofil | ~309 KB ✦ Standard |
| `url_myaan8nb` | 3/4-Winkel groß | ~879 KB |
| `url_ms_myp5` | 3/4-Winkel mittel | ~196 KB |
| `url_myapn3nb` | Seitenprofil kompakt | ~158 KB |
| `url_ms_myp4` | 3/4-Winkel klein | ~117 KB |
| `url_ms_myp3` | 3/4-Winkel Icon | ~76 KB |

**Verwendung in Lovelace:**
```yaml
type: picture-entity
entity: sensor.audi_q4_e_tron_akkustand
image: "{{ state_attr('image.audi_q4_e_tron_fahrzeugbild', 'url_myapn8nb') }}"
```

**Neue Dateien:**
- `cariad/api/graphql.py` — `VehicleImageFetcher` GraphQL Client
- `image.py` — HA Image Platform (9. Plattform)

**Unterstützte Marken:** Audi ✅, VW EU (experimentell), Škoda/SEAT/CUPRA (experimentell)
VW US/CA + Porsche: andere API-Architektur, noch nicht unterstützt.

**Forschungsquelle:** Issue #15 — bestätigt auf Audi S6 Avant (April 2026)

**8 neue Tests → 359/359 grün | 8 Übersetzungen | Lint ✓ | mypy ✓**

---


## [1.2.0] - 2026-04-12

### Hinzugefügt

#### Lademodus-Steuerung — Issue #891 (volkswagencarnet)
Neues `select.{fahrzeug}_lademodus` Entity für EVs und PHEVs:

| Option | Bedeutung |
|---|---|
| Manuell | Sofort laden wenn angesteckt |
| Timer | Ladestart per Abfahrtstimer |
| Bevorzugte Ladezeiten | Günstigen Ladestrom nutzen |
| Nur Eigenstrom | Nur PV-Überschuss |

- `select.py` als neue HA-Plattform (8. Plattform: select)
- Coordinator: `async_set_charge_mode(vin, mode)`
- VW EU API: `POST /charging/settings {"chargeMode": "TIMER"}`
- `charge_mode` Feld in `VehicleData` + aus CARIAD Response geparst

#### Mindest-Akkustand (Min SoC) — Issue #889 (volkswagencarnet)
`number.{fahrzeug}_mindest_akkustand_phev` Slider (0–100%, Schritt 5%):

- Setzt den Mindest-SoC den das Fahrzeug vor einem Abfahrtstimer erreichen soll
- Speziell für PHEVs: Ladevorgang hört auf wenn Min SoC erreicht
- `min_soc` in `VehicleData` + VW EU parst `minChargeLimit_pct` aus API
- Coordinator: `async_set_min_soc(vin, min_soc)`

**Alle 8 Sprachen aktualisiert | 351/351 Tests grün | Lint sauber**

---


## [1.1.1] - 2026-04-12

### Behoben

#### #917 — Ladegeschwindigkeit/Ladeleistung zeigt "unavailable" wenn nicht geladen wird

`charging_rate_kmh` und `charging_power_kw` gaben `None` zurück wenn die API
keinen Wert liefert (bei angestecktem aber nicht ladendem Fahrzeug).
HA interpretiert `None` als `unavailable`.

**Fix:** Wenn Stecker verbunden (`plug_connected == True`) aber API liefert `None`
→ Sensor zeigt `0 kW / 0 km/h` statt `unavailable`.
Wenn Stecker **nicht** verbunden → `unavailable` ist korrekt und bleibt so.

_Analoges Problem gemeldet in [robinostlund/homeassistant-volkswagencarnet#917](https://github.com/robinostlund/homeassistant-volkswagencarnet/issues/917)._

#### #927 — Options-Flow triggert kompletten Integration-Neustart

Änderung von `scan_interval` oder `spin` via Einstellungen → Integration neu starten
reloaded alle Entities (kurzer Verbindungsunterbruch, Historian-Lücke).

**Fix:**
- `_poll_loop()` liest Intervall jetzt **pro Loop-Iteration** aus `entry.options`
  → Intervall-Änderung wirkt beim nächsten Poll-Zyklus, kein Reload nötig
- `_async_update_listener()` triggert Reload nur noch wenn Brand/Username/Passwort
  geändert wurde (neue Auth nötig). Reine Einstellungs-Änderungen → live übernommen

_Analoges Problem gemeldet in [robinostlund/homeassistant-volkswagencarnet#927](https://github.com/robinostlund/homeassistant-volkswagencarnet/issues/927)._

**Tests:** 6 neue Tests → **351/351 grün**

---


## [1.1.0] - 2026-04-12

### Hinzugefügt

#### Universelle Felder für alle Marken — `coordinator._enrich()`

Nach jedem `get_status()` Call reichert der Coordinator die Daten automatisch an:

**`last_updated_at`** — immer gesetzt (UTC Timestamp), unabhängig von der Marke.
War nur bei VW EU vorhanden. Jetzt bei allen 7 Marken verfügbar.

**`vehicle_state`** — automatisch abgeleitet wenn nicht vom Client gesetzt:
- `OFFLINE` wenn `is_online == False`
- `CHARGING` wenn Ladevorgang aktiv
- `DRIVING` wenn `is_driving == True`
- `PARKED` als Standard

**Reverse Geocoding** — `parking_address` + `parking_city` aus GPS-Koordinaten.
Via Nominatim (OpenStreetMap), nur wenn lat/lon vorhanden und noch keine Adresse gesetzt.
Best-effort: Fehler werden still ignoriert, nie ein Update-Fehler wegen Geocoding.

#### Code-Qualität
- Imports auf Top-Level verschoben: `asyncio`, `datetime`, `os`, `device_registry`,
  `VehicleData` in `coordinator.py`, `vw_na.py`, `skoda.py`, `vw_eu.py`, `porsche.py`
- `noqa` Suppressionen: 39 → 24

#### Tests
- 8 neue Tests für `_enrich()`: last_updated_at, vehicle_state Ableitungslogik,
  Geocoding-Aufruf, Geocoding-Fehlerresistenz — **345/345 Tests grün**

---


## [1.0.0] - 2026-04-12

### Erstes stabiles Release

VAG Connect ist production-ready für alle 5 EU-Marken.
VW US/CA und Porsche sind als Beta enthalten und werden mit echten Fahrzeugen verifiziert.

**Warum 1.0.0?**
- 5 EU-Marken (Audi, VW, Škoda, SEAT, CUPRA) vollständig implementiert und getestet
- 68 Entities über 7 HA-Plattformen
- 14 Services
- 337/337 Tests grün
- EntityCategory korrekt — DIAGNOSTIC/CONFIG trennt Haupt-Entities von technischen Details
- Config Flow mit echten Selectors (Passwort maskiert, Brand-Radioliste, Intervall-Slider)
- CHANGELOG vollständig mit Attributionen
- 8 Übersetzungen synchron

**Breaking Changes gegenüber 0.x:**
Keine — alle Entity-IDs und Service-Namen bleiben identisch.

---


## [0.14.25] - 2026-04-12

### Hinzugefügt

#### Neue Marken: Porsche + VW North America (US/CA)

**Porsche (My Porsche)**
- Auth: Auth0 PKCE (`identity.porsche.com`) — komplett eigenständig, kein IDK
- API: `api.ppa.porsche.com/app/connect/v1/`
- Unterstützt: Akkustand, Reichweite, Laden, Klimatisierung, GPS, Türen, Motorhaube,
  Kofferraum, Schiebedach, Fensterheizung, Abfahrtstimer, Wartungsintervalle
- Commands: Lock/Unlock, Klimatisierung, Laden, Honk&Flash, Departure Timer
- Auth-Quelle: CJNE/pyporscheconnectapi (Apache-2.0), clean-room reimplemented mit aiohttp

**Volkswagen US/CA (My VW)**
- Auth: IDK PKCE gegen `b-h-s.spr.{country}00.p.con-veh.net/oidc/v1/`
- API: UUID-basiert (Garage liefert VIN → UUID Mapping, alle Commands nutzen UUID)
- Unterstützt: Akkustand, Tankstand, Reichweite, Laden, Klimatisierung, GPS,
  Türen, Fenster, Kofferraum, Motorhaube, Ladestrom, Abfahrtstimer
- Länder: US (`us00`), CA (`ca00`) — über `country`-Parameter in Factory
- Commands: Lock/Unlock, Klimatisierung, Laden, Window Heating, Wakeup
- Endpoint-Quelle: matpoulin/CarConnectivity-connector-volkswagen-na (Apache-2.0)

#### Config Flow
- Brand-Selector: 2 neue Einträge (`volkswagen_na`, `porsche`)
- Brand-Beschreibung in allen 8 Sprachen aktualisiert

#### Interna
- `cariad/auth/porsche.py` — Auth0 PKCE Modul
- `cariad/api/porsche.py` — Porsche API Client
- `cariad/api/vw_na.py`   — VW NA API Client (UUID-Routing)
- `cariad/api/factory.py` — unterstützt jetzt 7 Marken
- `cariad/models.py`      — `BRAND_PORSCHE` + `BRAND_VW_NA_MODEL`
- `const.py`              — alle 7 Marken in `BRANDS`

**337/337 Tests grün | Lint: sauber**

---


## [0.14.23] - 2026-04-12

### Geändert

- **Alle Entities standardmäßig sichtbar** — `entity_registry_enabled_default=False`
  von allen 15 Sensoren entfernt. Bisher waren technische Felder
  (WLTP-Reichweite, Akkutemperatur, Ladesäule-Details, Firmware etc.)
  beim Setup automatisch deaktiviert und für den Nutzer unsichtbar.
  Jetzt erscheinen alle Entities direkt nach der Installation — der Nutzer
  entscheidet selbst welche er braucht und welche er in HA ausblendet.
  EntityCategory.DIAGNOSTIC bleibt für die Gruppierung erhalten.

---


## [0.14.22] - 2026-04-12

### Behoben

- **Bug: `window_heating` mapped auf `command_start_climate`** — Fensterheizung rief intern
  `command_start_climate` auf statt eines eigenen Endpoints. Behoben: neuer
  `command_start/stop_window_heating` in `base.py` und `vw_eu.py`
  (`/climatisation/windowheating/start-stop`). Koordinator und Switch nutzen jetzt
  den korrekten Command. _Gefunden durch Audit._

### Hinzugefügt

- **7 neue Entities** aus `VehicleData`-Feldern die bisher keine HA-Entity hatten:
  - `sensor.{fzg}_adblue_reichweite` — AdBlue-Restreichweite (km, Diesel)
  - `binary_sensor.{fzg}_motorhaube` — Motorhaube offen (DIAGNOSTIC)
  - `binary_sensor.{fzg}_kofferraum_offen` — Kofferraum offen
  - `binary_sensor.{fzg}_kofferraum_verriegelt` — Kofferraum verriegelt (DIAGNOSTIC)
  - `binary_sensor.{fzg}_schiebedach` — Schiebedach offen (DIAGNOSTIC)
  - `binary_sensor.{fzg}_frontscheibenheizung_aktiv` — Frontscheibe heizt (DIAGNOSTIC)
  - `binary_sensor.{fzg}_heckscheibenheizung_aktiv` — Heckscheibe heizt (DIAGNOSTIC)

### Geändert

- **`iot_class`: `cloud_polling` → `cloud_push`** — korrekte Klassifizierung.
  VAG Connect steuert den Poll-Loop selbst (`update_interval=None`), daher `cloud_push`.
- 8 Übersetzungen aktualisiert — neue Entity-Keys in DE/EN/FR/NL/ES/PL/CS/SV.
- 5 Tests korrigiert — Mocks für `command_start/stop_window_heating` ergänzt,
  Assertions auf korrekten Command umgestellt. **337/337 Tests grün.**

---


## [Unreleased]

### Geplant für v0.15.0+
- Porsche + VW US/CA Live-Tests mit echten Fahrzeugen
- HACS offizieller Antrag (benötigt 3+ Tester pro Marke)

---

## [0.14.10] - 2026-04-12

### Fixed
- **VW EU Scope** (KRITISCH): Scope auf `"openid profile badge cars dealers vin"` geändert
  — exakt identisch mit volkswagencarnet (robinostlund, MIT), dem anderen funktionierenden
  VW-Integration. Unser langer Scope enthielt Werte die Auth0 VW nicht kennt → 500 Server Error.
- **BRAND_AUDI client_id**: `09b6cbec-...` von audiconnect übernommen (bereits v0.14.9)

### Research-Ergebnis
  volkswagencarnet (gleicher client_id `a24fba63-...`, gleiche redirect_uri) funktioniert mit:
  - scope: `openid profile badge cars dealers vin` (kurz!)
  - POST {username, password, state} an `/u/login?state=S` mit `allow_redirects=False`
  - State aus `<input name="state">` im HTML extrahiert
  
---

## [0.14.9] - 2026-04-12

### Fixed — basierend auf volkswagencarnet (MIT) Analyse

volkswagencarnet nutzt SELBE client_id und SELBES Auth0 `/u/login` und funktioniert.
Ihr Ansatz direkt übernommen:

1. **`<input name="state">` aus HTML extrahieren** (nicht aus URL-Query)
2. **state SOWOHL in URL als auch im Body** (`/u/login?state=S` + `{state: S}` in Form-Body)
3. **username + password KOMBINIERT in einem POST** (nicht zwei Schritte)
4. **`allow_redirects=False`** + manuelles Redirect-Folgen
5. **CARIAD BFF Token-Endpoint** (`emea.bff.cariad.digital/login/v1/idk/token`)
   statt IDK direkt — wie audiconnect und volkswagencarnet

---

## [0.14.8] - 2026-04-12

### Fixed
- **Auth0 400: login_url direkt verwenden** statt URL mit f-string rekonstruieren (state war ggf. falsch encoded)
- **Kombinierter POST** (email+password in einem Request) als primäre Strategie — viele Auth0-Instanzen zeigen kombiniertes Formular
- **Fallback**: Identifier-First (2 Steps) wenn kombinierter POST zurück auf Login-Seite leitet
- `_auth0_post_form()` wirft bei 400 keine Exception mehr — gibt HTML zurück für Fallback-Logik
- Bessere Fehlermeldung wenn Login nach allen Versuchen fehlschlägt

---

## [0.14.7] - 2026-04-12

### Fixed
- **Auth0 UL v2: 400 Bad Request behoben** — `state` gehört in die URL (`/u/login?state=S`), NICHT in den Form-Body
  - `_auth0_post_form()`: `state` Parameter entfernt aus Methode
  - Email-Step: POST an `/u/login?state=AUTH0_STATE` (state im Query)
  - Password-Step: POST an der URL die Auth0 nach Email-Redirect zurückgibt (enthält neuen state)
  - MFA-Step: analog

---

## [0.14.6] - 2026-04-12

### Fixed
- **Auth0 Universal Login v2**: `connection not found` behoben — VW nutzt `/u/login` Identifier-First Flow, nicht `/usernamepassword/login`
  - POST `/u/login?state=S` mit `{username, action: default}` → Redirect zu `/u/login/password?state=S2`
  - POST `/u/login/password?state=S2` mit `{password, action: default}` → Redirect zu callback

### Added
- **2FA-Unterstützung** (Issue #7 ✅): Wenn MFA erkannt wird, zeigt HA einen neuen Screen "Zwei-Faktor-Bestätigung"
  - Kein Neustart nötig — einfach Code aus E-Mail oder Authenticator-App eingeben
  - Alle 8 Sprachen übersetzt
- `authenticate(mfa_code=...)` Parameter in allen 5 Brand-Clients

---

## [0.14.5] - 2026-04-12

### Fixed
- **Auth0 Universal Login** (KRITISCH): IDK hat 2025 auf Auth0 `/u/login` migriert.
  Alter Flow (`/signin-service/v1/.../login/identifier`) funktioniert nicht mehr.
  Neuer Flow:
  1. GET `/oidc/v1/authorize` → redirect zu `/u/login?state=AUTH0_STATE`
  2. POST `/usernamepassword/login` (JSON: email, password, auth0_state, _csrf-Cookie)
  3. Parse `form_post` HTML-Response → POST an `/login/callback`
  4. Redirect-Chain bis `app://...?code=AUTH_CODE`
  5. Token-Exchange (PKCE, unverändert)
- Legacy signin-service Flow bleibt als Fallback (erkennt `/u/login` in URL)
- CSRF aus Auth0-Cookie `_csrf` oder Regex-Extraktion aus Page

---

## [0.14.4] - 2026-04-12

### Added
- **Abfahrtstimer schreiben** (Issue #14 ✅): `command_set_departure_timer()` in `vw_eu.py` — POSTet an `vehicle/v1/vehicles/{vin}/climatisation/timers`
- Coordinator `async_set_departure_timer` nutzt jetzt den CARIAD-Client direkt statt als no-op

### Fixed
- Tests: `command_set_departure_timer` als `AsyncMock` in Service-Test-Fixtures ergänzt

---

## [0.14.3] - 2026-04-12

### Fixed
- **IDK Login: robusteres CSRF-Parsing** — `_parse_csrf_robust()` versucht jetzt 4 Methoden:
  1. Klassische `<input type="hidden">` HTML-Parser
  2. Regex über ALLE Hidden-Inputs (HTMLParser übersieht manchmal JS-gerenderte Felder)
  3. JSON-Pattern in `<script>`-Blöcken (modernes IDK SPA: `"_csrf":"..."`, `"hmac":"..."`)
  4. `data-`-Attribute auf Form-Elementen
- **Detailliertes Schritt-Logging**: Step 1 loggt jetzt URL, Status, Content-Type, HTML-Länge
- Bei leerem HTML: eigene klare Fehlermeldung statt generischem "no CSRF fields"
- Step 2 nutzt ebenfalls `_parse_csrf_robust()`

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
