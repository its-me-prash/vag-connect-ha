# Technische Changelog-Details (v1.8.6+)

Dieses Dokument enthält die vollständigen technischen Detail-Notes für
die Releases v1.8.6 und neuer — gedacht für Contributors, Issue-Reporter,
Reviewer und alle die wissen wollen *welche* Datei *welche* Zeile geändert
hat und *warum*.

**Für End-User-freundliche Release-Notes siehe [`CHANGELOG.md`](../CHANGELOG.md).**

Ältere Releases (v1.8.5 und davor) waren bereits kompakter und sind
weiterhin direkt in `CHANGELOG.md` zu finden.

---

## [1.10.0] - 2026-04-29

### PHEV Range Triple + Audi Diesel Range — Issue #94 + Scout-driven Entities aus #91

**Auslöser:** Issue #94 (PHEV-User wollen elektrische + Verbrennungs-Reichweite separat sehen), Issue #91 (Audi S6 C8 2021 Live-Test zeigt `measurements.rangeStatus.value.dieselRange = 190` als unbekannten Pfad). Erste MINOR-Release die die Vehicle Data Scout findings (v1.9.0) in echte HA-Entitäten überführt.

#### Neue Felder

**`custom_components/vag_connect/cariad/models.py`** — VehicleData um 3 Felder erweitert:

```python
electric_range_km: int | None = None     # batterie-only Reichweite
combustion_range_km: int | None = None   # Petrol/Diesel/CNG/LPG Reichweite
total_range_km: int | None = None        # kombinierte Reichweite (PHEVs)
```

`range_km` bleibt als "Headline-Number" für Backwards-Compat — existierende Dashboards / Automatisierungen brechen nicht.

#### Parser-Änderungen

**`custom_components/vag_connect/cariad/api/vw_eu.py:_parse_status`** — komplett umgebaute Range-Logik:

API-Pfade pro Drivetrain:

| Quelle | Pfad | Beispiel-Vehicle |
|---|---|---|
| Pure EV | `charging.batteryStatus.value.cruisingRangeElectric_km` | ID.4, e-tron GT |
| PHEV (modern) | `fuelStatus.rangeStatus.value.{primaryEngine,secondaryEngine}.{type,remainingRange_km}` | Golf 7 GTE 2015+ (#90) |
| Total (Hybrid) | `fuelStatus.rangeStatus.value.totalRange_km` | Golf 7 GTE |
| Diesel (Audi älter) | `measurements.rangeStatus.value.dieselRange` | S6 C8 2021 (#91, sample 190 km) |
| Benzin (Audi älter) | `measurements.rangeStatus.value.gasolineRange` | (proaktiv für ICE-Audis) |

Neue Logik:

1. **Iteration über beide Engine-Blöcke** (`primaryEngine` + `secondaryEngine`). Klassifizierung nach `engine.type` (`electric`/`ev` → `electric_range_km`, `gasoline`/`petrol`/`diesel`/`gas`/`cng`/`lpg` → `combustion_range_km`). Kein Hardcoding "primary == electric" — manche Firmwares vertauschen es.
2. **Fallback auf `measurements.rangeStatus`-Pfad** wenn kein `fuelStatus`-Block (Audi S6 C8 2021). Akzeptiert sowohl skalare `int`-Werte als auch `{distanceInKm: int}`-Wrapper.
3. **`total_range_km` separat** — nur gesetzt wenn `totalRange_km` explizit publiziert wird.
4. **Headline `range_km` Priorität:** elektrisch (für `has_battery=True`) → total → Verbrennung.

Pre-1.10.0 hatte 2 Bugs:
- `battery_range` von `cruisingRangeElectric_km` überschrieb manchmal den `total_range_km` (Reihenfolge im Code)
- `combustionRange` wurde nirgends in ein eigenes Feld geschrieben — verloren für PHEV-User

**`custom_components/vag_connect/cariad/api/skoda.py:get_status`** — Driving-Range Block:

Skoda mysmob hat dieselbe Per-Engine-Struktur, aber unter `electricRange.distanceInKm` + `combustionRange.distanceInKm` + `totalRangeInKm`. Pre-1.10.0 las nur `combustionRange` als Skalar — auf neueren Firmwares mit Wrapper-Form (Kodiaq iV) war das `None`. Fix: liest jetzt beide Formen (gewrappt als Default, flacher Skalar als Fallback) und befüllt alle 3 Felder.

#### Sensor-Definitionen

**`custom_components/vag_connect/sensor.py`** — 3 neue `VagSensorDescription`:

| Key | Translation Key | Icon | Condition | Unit |
|---|---|---|---|---|
| `electric_range_km` | electric_range_km | mdi:battery-charging-outline | electric | km |
| `combustion_range_km` | combustion_range_km | mdi:gas-station | combustion | km |
| `total_range_km` | total_range_km | mdi:map-marker-distance | (none) | km |

Alle drei: `device_class=DISTANCE`, `state_class=MEASUREMENT`, `suggested_display_precision=0`.

#### Phantom-Entity-Schutz (#94 acceptance criteria)

Neuer `_DATA_PRESENT_REQUIRED` Frozenset in `sensor.py`:

```python
_DATA_PRESENT_REQUIRED: frozenset[str] = frozenset({
    "electric_range_km",
    "combustion_range_km",
    "total_range_km",
})
```

`async_setup_entry` filtert pro VIN: wenn `vehicle.get(desc.data_key) is None` UND der Key im `_DATA_PRESENT_REQUIRED`-Set ist → Entity wird NICHT erstellt. Reine EVs bekommen also nicht den `combustion_range_km`-Sensor als "unknown", reine ICE keinen `electric_range_km`. Per-key opt-in — bestehende Sensoren behalten ihr "create-immer, populate-später" Verhalten.

Wichtig: das Set ist **additiv zur** `condition`-Filterung (`electric`/`combustion`). Beide müssen gleichzeitig "ja" sagen damit eine Entity entsteht. Verhindert double-trouble: ein PHEV mit `has_battery=True` + `has_combustion=True` aber ohne API-Daten für eines der beiden → richtige Filterung.

#### Translations

8 Sprachen (de/en/fr/es/nl/pl/cs/sv) mit konsistenten Begriffen:

| Sprache | Electric | Combustion | Total |
|---|---|---|---|
| DE | Elektrische Reichweite | Kraftstoff-Reichweite | Gesamtreichweite |
| EN | Electric Range | Fuel Range | Total Range |
| FR | Autonomie électrique | Autonomie carburant | Autonomie totale |
| ES | Autonomía eléctrica | Autonomía combustible | Autonomía total |
| NL | Elektrisch bereik | Brandstofbereik | Totaal bereik |
| PL | Zasięg elektryczny | Zasięg paliwa | Zasięg łączny |
| CS | Elektrický dojezd | Dojezd na palivo | Celkový dojezd |
| SV | Elektrisk räckvidd | Bränsleräckvidd | Total räckvidd |

#### Tests

**`tests/test_v1100_phev_ranges.py`** (neu, 13 Tests):

- `TestVehicleDataFields` (2): Defaults sind None, to_dict round-trips
- `TestVWEUParseRanges` (5): PHEV mit primary=electric/secondary=gasoline; vertauschte Engine-Positionen; Audi diesel-only Fallback; pure EV (kein combustion); wrapped `{distanceInKm: int}` form
- `TestSkodaParseRangesUnit` (1): Kodiaq PHEV shape mit allen 3 Werten
- `TestSensorGating` (5): `_DATA_PRESENT_REQUIRED` enthält die 3 Keys; alle 3 SensorDescriptions registriert; combustion hat gas-station icon + condition; electric hat battery icon + condition; total hat keine condition

#### Was NICHT in v1.10.0 ist

- **`vehicleHealthWarnings` als neue Binary-Sensors:** Parser + Felder existieren schon seit v1.0 (warning_engine/oil/tyre/brakes — gefüllt aus `vehicleHealthWarnings.warningLights.value`). Die Vehicle Data Scout Findings #90 + #91 hatten den Pfad nur als top-level `vehicleHealthWarnings` gemeldet (ungeparster wrapper) — v1.9.1 hat das `EXPECTED_KEYS` registriert, der Parser darunter funktioniert seit jeher.
- **`vehicleHealthInspection` als neuer Date-Sensor:** existiert schon als `service_due_at` (DATE-device-class, parsed aus `inspectionDue_days`), v1.9.1 hat den Top-Level-Pfad registriert.
- **`maxChargeCurrentAC_A` als Number-Entity:** Feld existiert bereits in VehicleData als `max_charge_current` (float). Das Number-Platform-Wiring kommt in v1.10.1 separat.
- **Defensive Coding Phase 2 (#58):** verschoben auf v1.10.1 — eigene Session, separater PR.
- **`automation` + `departureProfiles` Plattform:** Architekturarbeit, kommt in v1.11.0+.

#### Auswirkung auf Bestandsbenutzer

- **Reine EV-Besitzer (ID.4 etc.):** sehen jetzt `electric_range_km` zusätzlich zur bestehenden `range_km`. Kein neuer Verbrennungs-Sensor (Phantom-Schutz).
- **Reine ICE-Besitzer:** sehen jetzt `combustion_range_km`. Kein neuer Elektro-Sensor.
- **Audi S6 C8 2021 (TDI):** sieht jetzt korrekten `combustion_range_km` (z.B. 190 km) statt nichts.
- **PHEV-Besitzer (Golf GTE etc.):** sehen alle drei (45 elektrisch + 520 Sprit + 565 gesamt) statt nur eines.

#### Hard Rules eingehalten

- ✅ Nichts spekuliert — alle Pfade sind verifiziert (gegen #90 #91 Live-Daten + bestehende Skoda-Fixtures + audi_connect_ha source).
- ✅ Keine bestehenden Tests gebrochen — Backwards-Compat via `range_km`.
- ✅ Brand-localized Translations in 8 Sprachen.
- ✅ Strict-Semver — MINOR weil neue Sensoren (3 neue Entitäten).

---

## [1.9.1] - 2026-04-29

### Hotfix #92 (Audi S6 C8 2021 Lock + Wake) + Vehicle Data Scout Coverage (#90, #91) + Capability-Filter Phase 2 (#56)

Erste reale Bug-Reports an die v1.9.0 Vehicle Data Scout & Error Reporter
Pipeline. Maintainer Prash testete v1.9.0 sofort nach Release auf seinem
Audi S6 C8 (2021, MJ 2021) + VW Golf 7 GTE — beide Reports kamen via
1-Klick-Workflow ins Repo (#90, #91, #92), genau wie das v1.9.0 Design
es vorgesehen hatte. Erfolgs-Validierung für die ganze Reporter-Pipeline.

#### Änderungen

**`custom_components/vag_connect/cariad/api/vw_eu.py`** (2 Bug-Fixes):

- `command_lock(vin, spin="")` — Signatur erweitert. Pre-1.9.1 sandte
  immer `{"action": "lock"}` ohne S-PIN. Premium Audi-Modelle wie der
  S6 C8 antworten mit `403 spin_error` (Body:
  `{"error":{"message":"spin_error","spinState":"DEFINED","remainingTries":3}}`).
  Fix: gleiche S-PIN-Behandlung wie `command_unlock` — wenn die S-PIN
  konfiguriert ist, wird sie ins Payload aufgenommen sowohl beim
  combined `/access/lock-unlock`-Endpoint als auch beim separaten
  `/access/lock`-Fallback.
- `command_wake(vin)` — von bareem `self._post` auf `self._post_command`
  umgestellt. Pre-1.9.1 traf `vehicle/v1/.../vehicleWakeup` direkt; bei
  premium Audi-Modellen gibt's das nur unter `/vehicle/v2/...`. Der
  `_post_command`-Helper hat seit v1.8.5 (Session 3A) den v1→v2 Fallback,
  jetzt wird er auch für Wake genutzt.

**`custom_components/vag_connect/coordinator.py`**:

- `async_lock(vin)` — Brand-Erkennung erweitert: bei `audi`/`volkswagen`
  wird die S-PIN aus den Options/Data gelesen und an `command_lock(vin, spin=...)`
  übergeben. Bei SEAT/CUPRA bleibt der Pre-Check für fehlende S-PIN
  (raises `ServiceValidationError`); bei Audi/VW wird der Call ohne S-PIN
  zugelassen (für ältere Modelle ohne Premium-S-PIN-Anforderung) — schlägt
  er dann fehl, klassifiziert ihn die neue Phase-2-Pipeline automatisch
  als `SPIN_REQUIRED`.
- `_cariad_cmd` — komplett umgebaut für Phase 2:
  - Bei Erfolg: `record_command_success(vin, method)` — flippt
    `supported_by_vehicle` + `entitled_by_account` + `available_now`
    auf True und löscht `last_error`.
  - Bei Fehler: `classify_command_failure(err)` → ableitet
    `CommandFailureReason` aus Body + Status; `record_command_failure(...)`
    aktualisiert die FeatureState. Exception wird trotzdem propagiert.
  - Beide Calls in try/except — Bookkeeping darf nie das Command-Ergebnis
    beeinflussen.
- `is_command_known_unsupported(vin, command)` — neuer Helper.
  Konservativ: nur True wenn `supported_by_vehicle is False` ODER
  `entitled_by_account is False`. Transient errors (UNKNOWN, BACKEND_ERROR,
  VEHICLE_UNREACHABLE) lassen die Flags auf None und der Helper bleibt False.

**`custom_components/vag_connect/entity_base.py`**:

- `_command_id: str | None = None` — neues Class-Attribut. Subklassen
  setzen es auf z.B. `"command_lock"` um Phase-2-Gating zu aktivieren.
- `available` Property erweitert: zusätzlich zur per-VIN Verfügbarkeit
  prüft sie jetzt `coordinator.is_command_known_unsupported(vin, command)`
  wenn `_command_id` gesetzt ist. Sensoren ohne Command bleiben
  unverändert.

**`_command_id` Annotationen** in command-bound Entities:

- `lock.py:VagDoorLock` → `command_lock`
- `button.py:VagFlashButton` → `command_flash`
- `button.py:VagWakeButton` → `command_wake`
- `climate.py:VagClimate` → `command_start_climate`
- `switch.py:VagLockSwitch` → `command_lock`
- `switch.py:VagClimatisationSwitch` → `command_start_climate`
- `switch.py:VagChargingSwitch` → `command_start_charging`
- `switch.py:VagWindowHeatingSwitch` → `command_start_window_heating`

**`custom_components/vag_connect/cariad/exceptions.py`**:

- `classify_command_failure(exc)` — Body-Content-Sniffing vor
  Status-Code-Klassifikation:
  - `spin_error` / `spinState` (case-insensitive) → `SPIN_REQUIRED`
    (vorher fälschlich `NOT_ENTITLED` weil 403)
  - `subscription` + (`expired`|`lapsed`) → `SUBSCRIPTION_EXPIRED`
  - `not_entitled` / `not-entitled` / `license_required` /
    `license-required` / `entitlement` → `NOT_ENTITLED`
- Verifizierte Marker-Strings dokumentiert mit Issue-Quellen
  (#92 für spin_error, #47/#42 für subscription, #51 für not_entitled).

**`custom_components/vag_connect/cariad/_unexpected_keys.py`** —
`EXPECTED_KEYS["volkswagen"]["selectivestatus"]` (Audi inherits)
um 13 neue Pfade erweitert basierend auf Issues #90 + #91:

| Path | Quelle | Bemerkung |
|---|---|---|
| `measurements.rangeStatus.value.dieselRange` | #91 (S6 TDI) | sample 190km |
| `measurements.rangeStatus.value.gasolineRange` | proaktiv (Petrol-Pendant) | |
| `measurements.fuelLevelStatus.value.currentFuelLevel_pct` | #91 | sample 26% |
| `charging.chargingSettings.value.maxChargeCurrentAC_A` | #90 (Golf 7 GTE) | sample 16A |
| `charging.chargeMode` | #90 | top-level Block |
| `climatisation.climatisationSettings.value.targetTemperature_F` | #90 | sample 73°F |
| `climatisation.climatisationSettings.value.climatisationWithoutExternalPower` | #90 | bool |
| `vehicleLights.lightsStatus.value.carCapturedTimestamp` | #90+#91 | timestamp |
| `vehicleLights.lightsStatus.value.lights` | #90+#91 | array |
| `userCapabilities` | #90+#91 | top-level |
| `fuelStatus` | #90+#91 | top-level (verschieden von `measurements.fuelLevelStatus`) |
| `vehicleHealthInspection` | #90+#91 | service-due Block |
| `vehicleHealthWarnings` | #90+#91 | warning Block |
| `automation` | #90 | smart-charging Block |
| `departureProfiles` | #90 | Nachfolger von `departureTimers` |

#### Tests

**`tests/test_v191_hotfix.py`** (neu, 18 Tests):

- `TestAudiLockSpin` (4): no-spin omits field, spin kwarg → payload,
  client default spin, coordinator forwards Audi spin
- `TestVWEUWake` (2): wake → `_post_command` dispatch, v1 404 → v2
- `TestClassifyAndAutoRecord` (7): spin_error in body, subscription,
  not_entitled, status fallback, `is_command_known_unsupported`
  state machine (transient = False, missing-capability = True,
  subscription = True, success = back to False), `_cariad_cmd`
  auto-recording on failure
- `TestScoutKeyRegistration` (5): diesel range, max charge ampere,
  top-level diagnostic blocks, lights nested, audi == volkswagen
  inheritance smoke

#### Architektur-Notes

- **Warum kein "MISSING_CAPABILITY" auto-flip auf 404?** 404 kann auch
  ein Endpoint-Versions-Mismatch sein (Hauptgrund für den v1→v2
  Fallback). Wir bleiben bei `WRONG_API_PROFILE` für 404 und nur
  explizite Body-Marker (`missing-capability`, `missing_capability`)
  führen zu permanenter Hide.
- **Warum nicht alle Brand-Capabilities-IDs in button.py erweitern?**
  Wir haben verifizierte Capability-IDs nur für SEAT/CUPRA (OLA Vocab).
  Audi/VW EU haben eine andere Capability-Vokabular die wir noch nicht
  gegen Live-Vehicles abgeglichen haben — Phase 2 nutzt deshalb das
  Per-Command-FeatureState-System (lernt durch Beobachten von 403er),
  nicht Capability-Lookup-vor-Entity-Creation.
- **Warum Lock + Window-Heating-Switch + Climatisation-Switch _command_id
  haben aber nicht jeden Sensor?** Sensors haben kein Backend-Action;
  die Phase-2-Logik bringt nur Wert für Entitäten die ein Command auslösen.
  Read-only-Entities bleiben sichtbar solange `is_vehicle_available` True
  ist.
- **Warum keine UI-Texte für die Phase-2 "unavailable"-States?** HA's
  Standard-Mechanik ist gut: Entity wird ausgegraut, State zeigt
  "Unavailable". Eigene Repair-Issues für Subscription-Renewal kommen
  in v1.10.0 (Diagnostics + Smart-Wake Sprint).

#### Rückwärtskompatibilität

- Alle Änderungen sind additive Verhaltens-Verbesserungen.
- `_command_id` defaults to `None` → keine alte Subklasse bekommt
  unbeabsichtigtes Hide-Verhalten.
- `record_command_success` / `record_command_failure` existieren seit
  v1.8.2 — Phase 2 nutzt sie nur konsequenter.

---

## [1.9.0] - 2026-04-29

### Vehicle Data Scout + Error Reporter — Crowd-Sourced Bug-Discovery via 1-Klick Reporter Pipeline

**Versionssprung-Begründung:** Erste **MINOR-Release nach strikter Semver-Disziplin**
(siehe Roadmap-Sektion „Semver-Korrektur ab v1.9.0"). Zwei neue Sensoren = MINOR,
nicht PATCH. Folgereihen entsprechend verschoben (v1.9.1 Capability-Filter,
v1.9.2 Defensive Coding Phase 2, v1.9.3 Optimistic Lock/Climate, v1.10.0
Diagnostics + Smart-Wake + 12V).

**Pattern-Quelle:** `tillsteinbach/CarConnectivity-*` "Unexpected Keys found"
War unsere ergiebigste API-Erkenntnisquelle (CC-seatcupra #109 Rainer's CUPRA Born,
CC-skoda #50 Kodiaq iV 2026 Live-Dump). Wir bauen das gleiche Pattern in unsere
Integration ein — plus Error-Sammlung — und senken die Hürde von „Issue selbst
schreiben" auf „1 Klick auf vorausgefüllten GitHub-Link" oder „1 Klick auf Copy
für Forum/Facebook".

#### Neue Module (3, alle pure-Python — Unit-test-bar ohne HA)

**`custom_components/vag_connect/cariad/_unexpected_keys.py`** (neu, 392 Zeilen):

- `UnexpectedField` dataclass: `path`, `sample_masked`, `endpoint`, `first_seen_at`
- `EXPECTED_KEYS: dict[brand][endpoint] -> set[str]` — registrierte Felder pro
  Brand+Endpoint. SEAT inherits CUPRA, Audi inherits VW EU. 5 Brands aktiv,
  jeweils 5–7 Endpoints abgedeckt.
- `_path_matches(path, expected_paths)` — Wildcard-Matching mit `*` als Segment
  (z.B. `doors.*.locked` matcht `doors.frontLeft.locked`)
- `mask_value(value, max_len=80)` — anonymisiert: VIN-Regex (17-stellig) →
  `mask_vin`, Email → `***@***`, JWT-shape → `[token]`, UUID → `[uuid]`,
  Float → 1 Dezimalstelle (kills GPS-Präzision auf ~11 km)
- `detect_unexpected(brand, endpoint, response, max_depth=6)` — Generator,
  yieldet `UnexpectedField` für nicht-registrierte Pfade. Stoppt rekursiv
  bei `max_depth` (Schutz gegen pathologische Responses). Brand/endpoint
  ohne Registry-Eintrag → silent (keine false positives).

**`custom_components/vag_connect/cariad/_error_reporter.py`** (neu, 208 Zeilen):

- `ErrorRecord` dataclass — frozen, alle Felder maskiert
- `ErrorRingBuffer` mit `_MAX_ERRORS = 20` (begrenzt Memory + Diagnostics-Größe)
- 2 zusätzliche Regexes über `_unexpected_keys` hinaus:
  - `_BEARER_RE` — `Bearer\s+[A-Za-z0-9._-]+`
  - `_OPAQUE_TOKEN_RE` — `\b[A-Za-z0-9+/]{32,}={0,2}\b`
- `_redact(text, max_len=500)` — strippt VIN/Email/JWT/UUID/Bearer/opaque
- `record_error(buffer, *, exception, brand, vin, model_year, firmware, endpoint)` —
  **NEVER raises**. Außenliegender try/except baut bei Buffer-Failure einen
  minimal Fallback-Record `ErrorReporterFailure`. Hält letzte 12 Traceback-Zeilen
  (~3 Frames + Headers — genug zum Debuggen, klein genug für GitHub-URL-Limit)
- `serialise_for_diagnostics(buffer)` — JSON-safe Liste für HA-Diagnostics

**`custom_components/vag_connect/cariad/_reporter_pipeline.py`** (neu, 230 Zeilen):

- `build_unexpected_keys_report(findings, brand, model_year, firmware, integration_version)` —
  Markdown mit Tabelle (Path | Sample | Endpoint | First seen) + Privacy-Footer
- `build_error_report(records, brand, integration_version)` — Markdown mit Section
  pro Error, Tracebacks in fenced code blocks
- `github_issue_url(title, body, *, repo_url, labels, body_max=6500)` — baut
  pre-filled Issue-URL mit URL-encoded Query-Params, **truncates body bei 6500B**
  (GitHub URL limit ~8KB) und appendet Marker
- `ensure_unexpected_keys_issue(hass, *, entry_id, findings, brand, ...)` — `ir.async_create_issue`
  mit `translation_key="vehicle_data_scout_findings"`, `learn_more_url` zeigt auf
  pre-filled GitHub-URL. Empty findings → `ir.async_delete_issue` (cleanup).
- `ensure_error_reporter_issue(...)` — gleicher Aufbau, severity=ERROR statt
  WARNING, `translation_key="error_reporter_findings"`
- `clear_reporter_issues(hass, entry_id)` — wird beim Entfernen der Integration
  gerufen

#### Geänderte Dateien

**`custom_components/vag_connect/cariad/api/base.py`** (+9 Zeilen):

- `last_raw_responses: dict[str, dict[str, Any]] = {}` — opt-in Stash für
  Brand-Clients. Coordinator iteriert das nach jedem erfolgreichen Poll und
  füttert es in `detect_unexpected`. Brand-Client opt-in heißt: kein Forced-Change
  in Audi/Porsche/VW NA — die bleiben silent bis sie selbst Endpoints stashen.

**`custom_components/vag_connect/cariad/api/skoda.py`** (+15 Zeilen):

- Stash der 7 gefetcheten Endpoints (vehicle-status, charging, air-conditioning,
  parking, driving-range, maintenance, readiness) in `last_raw_responses`.
  Skipped wenn payload kein dict (Exception aus `asyncio.gather`).

**`custom_components/vag_connect/cariad/api/seat_cupra.py`** (+13 Zeilen):

- Stash der 5 wichtigsten Endpoints (mycar, status, charging, charging-info,
  climatisation). SEAT erbt automatisch über `EXPECTED_KEYS["seat"] = EXPECTED_KEYS["cupra"]`.

**`custom_components/vag_connect/cariad/api/vw_eu.py`** (+10 Zeilen):

- Stash von `selectivestatus` und `parkingposition`. Audi erbt über `AudiClient(VWEUClient)`
  und `EXPECTED_KEYS["audi"] = EXPECTED_KEYS["volkswagen"]`.

**`custom_components/vag_connect/coordinator.py`** (+125 Zeilen):

- Imports: `ErrorRingBuffer`, `record_error`, `ensure_error_reporter_issue`,
  `ensure_unexpected_keys_issue`, `UnexpectedField`, `detect_unexpected`
- Neue Felder im `__init__`:
  - `self.unexpected_findings: dict[str, dict[str, UnexpectedField]] = {}` —
    per-VIN, de-duped per Path (gleiche Drift bei jedem Poll = nur 1 Record)
  - `self.error_buffer: ErrorRingBuffer = ErrorRingBuffer()`
- `_poll_loop` — neue Hooks:
  - Nach erfolgreichem Poll für VIN: `self._scan_for_unexpected_keys(vin)` (try/except)
  - Nach Per-VIN-Exception: `record_error(buffer, exception=result, brand, vin,
    model_year, firmware, endpoint="get_status")` (try/except, NEVER raises)
  - Nach jedem Poll-Cycle: `self._refresh_reporter_issues()` (try/except)
  - Nach Outer-Exception: `record_error(buffer, exception=err, brand, endpoint="poll_loop")`
    + `_refresh_reporter_issues()`
- Neue Methoden:
  - `_scan_for_unexpected_keys(vin)` — iteriert `client.last_raw_responses`,
    de-duped per Path
  - `_refresh_reporter_issues()` — flatten + delegiert an pipeline-Funktionen,
    lazy-import um Circular zu vermeiden
  - `reporter_findings_count()` — sum von distinct paths über alle VINs
  - `reporter_error_count()` — `len(buffer)`

**`custom_components/vag_connect/sensor.py`** (+85 Zeilen):

- 2 neue `VagSensorDescription` mit `data_key=""`:
  - `api_observer_findings` (icon `mdi:radar`, EntityCategory.DIAGNOSTIC)
  - `error_reporter_count` (icon `mdi:alert-circle-outline`, EntityCategory.DIAGNOSTIC)
- `_REPORTER_KEYS` frozenset für Dispatch in `async_setup_entry`
- Neue Klasse `ReporterSensor(VagConnectSensor)`:
  - `native_value` reads from `coordinator.unexpected_findings[vin]` (per-VIN)
    bzw. `coordinator.reporter_error_count()` (account-wide)
  - `extra_state_attributes` zeigt Preview (max 5 Pfade / 3 Exception-Typen)
    + `report_url` Pointer auf GitHub Issues

**`custom_components/vag_connect/diagnostics.py`** (+22 Zeilen):

- Imports: `serialise_for_diagnostics`
- Neue Felder in der Diagnostics-Response:
  - `unexpected_findings`: `{masked_vin: [{path, sample, endpoint, first_seen_at}]}`
  - `error_buffer`: full `serialise_for_diagnostics(buffer)`
- Beide bereits in `mask_value` / `_redact` durchgelaufen — keine Doppel-Redaction nötig

**`custom_components/vag_connect/strings.json` + 8 translations** (de/en/fr/es/nl/pl/cs/sv):

- 2 neue Sensor-Namen (`api_observer_findings`, `error_reporter_count`),
  brand-localized:
  - DE: "API-Beobachter" / "Fehler-Berichter"
  - EN: "Vehicle Data Scout" / "Error Reporter"
  - FR: "Observateur d'API" / "Rapporteur d'erreurs"
  - ES: "Observador de API" / "Reportador de errores"
  - NL: "API-waarnemer" / "Foutmelder"
  - PL: "Obserwator API" / "Raporter błędów"
  - CS: "Pozorovatel API" / "Hlásič chyb"
  - SV: "API-spanare" / "Felrapportör"
- 2 neue Issue-Translations (`vehicle_data_scout_findings`, `error_reporter_findings`)
  pro Sprache mit Title + ausführlicher Markdown-Description (1-Klick-Anleitung
  + Facebook/Forum-Workflow + Privacy-Footer)

**`custom_components/vag_connect/manifest.json`**:

- `version`: `1.8.12` → `1.9.0`

#### Tests

**`tests/test_reporter.py`** (neu, 18 Tests):

- `TestUnexpectedKeys` (10 Tests): registered-keys not flagged, unknown-keys
  flagged, unregistered brand silent, SEAT==CUPRA inheritance, Audi==VW
  inheritance, mask_value redaction (VIN, GPS, JWT, UUID, Email), wildcard
  path matching
- `TestErrorReporter` (4 Tests): ring buffer evicts oldest, record_error
  masks all sensitive substrings, record_error never raises (BoomBuffer
  fixture), serialise_for_diagnostics is JSON-safe
- `TestReporterPipeline` (4 Tests): unexpected-keys report renders table,
  empty findings = empty string, error report renders fenced traceback,
  GitHub URL pre-filled and decodable, body truncation works,
  ensure_*_issue creates/deletes via mocked HA registry, error-issue
  severity is ERROR

#### Privacy-Audit

Jede der folgenden Substrings darf NICHT in der Diagnostics-Response landen:

- Voller VIN (17 chars)
- Bearer-Token, JWT, opaque base64 token (>=32 chars)
- userID (UUID v4)
- Email-Adresse
- GPS-Koordinaten mit > 1 Dezimalstelle (~11 km Bucket)

Verifiziert via `test_record_error_masks_sensitive_data` mit kombiniertem
String, der alle 5 Pattern-Typen enthält. Plus dedizierte `mask_value`
Unit-Tests für jeden Typ einzeln.

#### Architektur-Notes

- **Warum opt-in pro Brand-Client?** Audi inherits VW EU automatisch. Andere
  Brands (Porsche, VW NA) bleiben silent bis sie eine `EXPECTED_KEYS`-Tabelle
  und `last_raw_responses`-Stash haben. Verhindert false-positives für nicht-getunte Brands.
- **Warum Per-VIN für Vehicle Data Scout, Account-wide für Error Reporter?**
  Drift ist Vehicle-spezifisch (Firmware, Modelljahrgang). Errors sind oft
  Auth/Rate-Limit (account-wide). Trennung spiegelt die Ursachen.
- **Warum De-Dup per Path?** Drift bei jedem Poll → ohne De-Dup hätte der Buffer
  in 1 Stunde 720 identische Einträge. De-Dup hält ihn klein und den Report lesbar.
- **Warum NEVER-raises?** Error-Reporter ist Infrastruktur. Ein Bug im Reporter
  würde sonst die Integration killen — genau das Gegenteil von dem, was wir wollen.
- **Warum kein Auto-Push?** GDPR (Anwender muss aktiv konsentieren), HACS-Regeln
  (kein automatischer Telemetry-Send), GitHub ToS (Bot-Issues = Spam-Risiko).
  1-Klick + opt-in ist die Best Practice.

#### Was kommt NICHT in v1.9.0

- **Capability-Filter Phase 2** (#56) — separates Release v1.9.1
- **Defensive Coding Phase 2** (#58) — separates Release v1.9.2
- **Anonymized Diagnostics-Export Service** mit Reset-Button — Teil von v1.10.0
- **Push notifications** für neue Findings — bewusst nicht (nutzt schon HA Repair-System)

---

## [1.8.12] - 2026-04-29

### MVP-Move — Multi-Brand Connection-State (Helper-Extraction + Apply auf alle 4 CARIAD-Brands)

Erweitert das `carCapturedTimestamp` Pattern aus v1.8.11 (Skoda-only) auf
**alle vier CARIAD-basierten Brand-Clients**: VW EU, Audi, SEAT, CUPRA.
Macht uns zur **ersten VAG-HA-Integration mit centralisiertem
Multi-Brand Connection-State**.

**Methodik:** vor Implementation **3 parallele Recherche-Agents** losgeschickt
(CC-skoda Issues, myskoda Issues + recent merged PRs, volkswagencarnet
Issues + PRs). Plus laufender Agent für audi_connect_ha. Erkenntnisse alle
verifiziert gegen echte Live-API-Responses (Hard Rule #8 — keine Spekulation).

**Bestätigung aus volkswagencarnet Issue #921 (ID.4 2025 Live-Dump):**
VW EU CARIAD-BFF `selectivestatus` returns `carCapturedTimestamp` auf
JEDEM sub-object — aber **TIEFER geschachtelt** als Skoda mysmob:

```
access.accessStatus.value.carCapturedTimestamp
charging.batteryStatus.value.carCapturedTimestamp
charging.chargingStatus.value.carCapturedTimestamp
charging.chargingSettings.value.carCapturedTimestamp
charging.plugStatus.value.carCapturedTimestamp
climatisation.climatisationStatus.value.carCapturedTimestamp
climatisation.climatisationSettings.value.carCapturedTimestamp
measurements.rangeStatus.value.carCapturedTimestamp
measurements.odometerStatus.value.carCapturedTimestamp
measurements.fuelLevelStatus.value.carCapturedTimestamp
parkingposition.carCapturedTimestamp        ← separate endpoint
```

Format ist gemischt: ISO-Strings UND pre-parsed `datetime`-Objekte.

**`cariad/_util.py` — neuer Helper `compute_connection_state(*sub_objects)`:**

- **Rekursiver Walk** durch dicts und lists, sammelt jeden datetime
  unter `carCapturedTimestamp` (oder konfigurierbarem `timestamp_keys` Tupel)
- **Akzeptiert** sowohl ISO-Strings als auch pre-parsed `datetime`
- **Naive datetimes** werden als UTC interpretiert
- **Defensive** gegen: BaseException-Sub-Objects (asyncio.gather mit
  `return_exceptions=True`), corrupt ISO-Strings, missing fields
  (myskoda PR #565)
- **Returns** `(state, last_seen_at)` — `(None, None)` wenn nichts gefunden
- Thresholds: `<30 min → "online"`, `<24 h → "standby"`, `>=24 h → "offline"`

**Apply auf 4 Brand-Clients:**

1. `cariad/api/skoda.py` — Refactor: hardgekodeter v1.8.11-Block ersetzt
   durch `compute_connection_state(...)` Aufruf. Behavior identisch, Code 40
   Zeilen kürzer.
2. `cariad/api/seat_cupra.py` — Apply: am Ende von `get_status` mit den
   9 OLA-Sub-Objects.
3. `cariad/api/vw_eu.py` — Apply: in `get_status` direkt nach `_parse_status`.
   Helper handles die nested `.value.carCapturedTimestamp` Pfade durch
   den rekursiven Walk.
4. `cariad/api/audi.py` — Inheritance: `AudiClient(VWEUClient)` überschreibt
   `get_status` nicht, profitiert daher automatisch.

**Tests** (`tests/test_cariad.py::TestComputeConnectionState`, 12 neue):
top-level + nested patterns, freshest wins, datetime + str + naive, corrupt
strings, exception sub-objects, threshold boundaries, custom timestamp_keys.
Plus alle 10 v1.8.11 Skoda-Tests bleiben grün (Refactor-Garantie).

**`manifest.json`:** 1.8.11 → 1.8.12

**Bewusst NICHT in v1.8.12 enthalten** (eigene Sessions geplant):

- `readiness.connectionState.isOnline` als Master-Health-Sensor
- `InsufficientBatteryLevel` Stale-Cache-Verlängerung (volkswagencarnet #940)
- `devicePlatform: WCAR/MBB_ODP/PPC/PPE` Plattform-Routing
- `engineType.primaryEngineType` für saubere EV/PHEV/ICE-Detection
- `TermsAndConditionsError` spezifische Detection im Auth-Flow (volkswagencarnet PR #307)
- `windowHeatingStatus[]` Array-Pfad für Audi/VW EU
- Service Discovery Pattern (volkswagencarnet PR #314)

**Bestätigt unsere Strategie 1:1**: skodaconnect/myskoda PR #536
implementiert exakt dieselbe Logik intern (ältere Events ignorieren).
Wir machen das gleiche, exposen aber als User-facing Sensor.

**Quellen** (verifiziert):
- robinostlund/volkswagencarnet Issue #921 (ID.4 2025), #940 (12V),
  PRs #301 (Readiness), #307, #310, #314, #316/#317
- tillsteinbach/CC-skoda Issue #50, CC-seatcupra #109
- skodaconnect/myskoda PR #536, #565

## [1.8.11] - 2026-04-29

### Session 3S — Škoda `carCapturedTimestamp` connection-state + #50 Live-API-Erkenntnisse

Schließt **#54 (GitHobi)** "Standby vs Offline" und integriert die wichtigsten
Live-API-Erkenntnisse aus dem Kodiaq iV 2026 Komplettdump in
`tillsteinbach/CarConnectivity-connector-skoda` Issue **#50**. Plus: PRs aus
`skodaconnect/myskoda` (#503, #536, #565) wurden ausgewertet — **myskoda PR #536
fährt GENAU dieselbe `carCapturedTimestamp`-Strategie wie unsere v1.8.11**, was
unseren Ansatz unabhängig bestätigt.

**Methodisch (wichtig nach v1.8.9-Lerneinheit):** vor diesem PR wurden ZWEI
parallele Recherche-Agents losgeschickt — einer für CC-skoda Issues, einer für
myskoda Issues + recent merged PRs. Erst danach Code geschrieben, damit nichts
wichtiges verpasst wird.

**`cariad/api/skoda.py` — `_parse_status` erweitert:**

1. **Neuer `compute_connection_state(...)` Block:** sammelt
   `carCapturedTimestamp` aus allen 7 Status-Sub-Objects (status, charging,
   ac, parking, driving_range, maintenance, readiness), nimmt den
   freshesten Wert und mappt: `<30min` → `online`, `<24h` → `standby`,
   `>=24h` → `offline`. Defensive `try/except ValueError` für korrupte
   Backend-Timestamps. Wenn kein Timestamp gefunden → `None` (myskoda
   PR #565 Pattern: das Feld ist nicht garantiert).
2. **`vehicle-status.detail` Block:** parst `sunroof`, `trunk`, `bonnet`
   (CLOSED/OPEN/UNSUPPORTED). Pre-v1.8.11 für Škoda nie populiert.
   `UNSUPPORTED` lässt das Feld auf `None` (Karoq Diesel ohne Sunroof
   zeigt korrekt keine Entity).
3. **`overall.reliableLockStatus`** als bevorzugte Lock-Quelle vor
   `doorsLocked`/`locked` (Kodiaq 2026+).
4. **`charging.fullyChargedAt`** als ISO-Timestamp wird zuerst probiert
   (kein Drift durch Poll-Latency). Fallback auf
   `remainingTimeToFullyChargedInMinutes`.

**`cariad/models.py`** — neues Field `last_seen_at: Any | None` mit
Comment: "wann das AUTO zuletzt Daten geliefert hat" vs. das existierende
`last_updated_at` "wann WIR zuletzt gepollt haben".

**`sensor.py`** — neue `VagSensorDescription` für `connection_state`,
`EntityCategory.DIAGNOSTIC`, icon `mdi:car-connected`.

**Translations (9 Files)** — `connection_state` in EN/DE/FR/ES/NL/PL/CS/SV
+ strings.json.

**Tests** (`tests/test_cariad.py::TestSkodaGetStatus`, 10 neue):

1. `test_v1811_connection_state_online_when_recent`
2. `test_v1811_connection_state_standby_under_24h`
3. `test_v1811_connection_state_offline_over_24h`
4. `test_v1811_connection_state_none_when_no_timestamp` — defensive (myskoda PR #565)
5. `test_v1811_freshest_timestamp_across_subobjects` — multi-source (myskoda PR #536)
6. `test_v1811_detail_block_sunroof_trunk_bonnet`
7. `test_v1811_detail_unsupported_stays_none`
8. `test_v1811_reliable_lock_status_preferred`
9. `test_v1811_charging_fully_charged_at_iso_timestamp`
10. `test_v1811_charging_interrupted_state_not_charging` — myskoda #503 Regression-Test

Plus neuer helper `_url_routing_client(by_path)` für saubere Multi-Endpoint-Mocks.

**Bewusst NICHT in v1.8.11 enthalten** (eigene Sessions geplant):

- `/v3/garage` Fallback für #75 Kodiaq Mk2 — Hard Rule #8 (keine Spekulation,
  myskoda-Source bestätigt v3 existiert nicht)
- `specification` Felder (`trimLevel`, `engine.type`, `manufacturingDate`,
  `systemModelId`) → Device-Info-Erweiterung
- `renders` / `compositeRenders` (Light/Dark, 4 Auflösungen) → Image-Refactor v1.10
- `batteryProtectionLimitOn` / `batteryCareModeTargetValueInPercent` →
  Battery-Care eigene Session
- `seatHeatingActivated` Dict → Seat-Heating eigene Session
- `timers[]` / `runningRequests[]` → Departure-Timer eigene Session
- `/api/v1/trip-statistics/{vin}/single-trips` → Trip-Stats v1.10.x
- `/api/v1/charging/{vin}/history` mit Cursor-Pagination → eigene Session
- `/v2/widgets/vehicle-status/{vin}` als leichter Endpoint → Session 6 Smart-Wake
- `devicePlatform: MBB_ODP` vs `WCAR` Plattform-Routing → Capability-Filter Session
- AdBlue Range für Diesel (CC-skoda #24) → eigene kleine Session
- Token-Hardening / 429-Backoff → bereits in v1.8.7 Defensive Pass abgedeckt

**Quellen** (verifiziert während Recherche):
- `tillsteinbach/CarConnectivity-connector-skoda` Issue #50 (Kodiaq iV 2026
  Live-Dump), #44, #23, #24, #8, #41
- `skodaconnect/myskoda` Issue #503, #461, #495, #458, #416, #237, #207
- `skodaconnect/myskoda` PRs #536 (Pattern-Bestätigung), #565
  (Optional fields), #537 (MY26 Capabilities)
- `tillsteinbach/CarConnectivity-connector-skoda` PR #36 (Maintenance fields)

## [1.8.10] - 2026-04-29

### Hotfix — Legacy CARIAD-flat doors fallback Inversionsbug (Pre-v1.8.9-Bug)

Ein-Zeilen-Hotfix gegen einen latenten Bug der seit Einführung des
Legacy-Fallback-Pfads in v1.8.9 vorhanden war. Aufgedeckt durch den
v1.8.9 Regression-Test `test_v189_status_legacy_flat_fallback_still_works`,
der in CI im PR #82 als FAIL durchlief. Der PR wurde trotzdem gemerged
weil Branch-Protection auf required-checks im Repo nicht aktiviert ist —
das ist eine separate Process-Lücke die in einem eigenen Hotfix adressiert
wird.

**Bug:**

Im `cariad/api/seat_cupra.py` Legacy-Fallback-Block (für sehr alte
Firmware oder zukünftige API-Änderungen wo unsere neuen pycupra-Pfade
nichts liefern) stand:

```python
for key in ("doorClosedLeftFront", "doorClosedRightFront", ...):
    val = v(access_s, key)
    ...
    doors_legacy[door_id] = not val   # ❌ INVERSION-BUG
```

Das `not val` invertierte die Semantik: das CARIAD-BFF-Field heißt
`doorClosed*` — also `True` bedeutet "Tür IST geschlossen", was unserer
`doors_individual`-Konvention (True == closed) **direkt** entspricht.
Das `not val` war daher falsch, und Tür-Entities würden für jedes
Modell, das tatsächlich diese flachen Pfade liefert, die invertierte
Information melden.

**Fix:**

```python
doors_legacy[door_id] = bool(val)   # ✅ direkt, ohne Inversion
```

**Impact:** Aktuelle CUPRA Born / Formentor / Tavascan Modelle nutzen die
neuen `status.doors.{position}.{locked,open}` Pfade aus v1.8.9, also
trifft sie der Bug **nicht** in Praxis. Der Bug betrifft nur den
defensiven Fallback-Pfad — der nur fires wenn keine der neuen
strukturierten Pfade Daten liefert. Realistisch dürfte das auf keinem
heute aktiven SEAT/CUPRA-Modell passieren. Trotzdem wichtig zu fixen
weil:

1. Der bestehende Regression-Test (12. Test in v1.8.9) muss grün sein
2. Kommt eine zukünftige OLA-API-Änderung die uns auf den Fallback
   wirft, würden Tür-Entities silently invertierte Werte zeigen
3. CI auf main muss grün sein — `main` mit failing tests blockt jede
   nachfolgende PR

**Tests:** keine Änderungen nötig — der bestehende v1.8.9 Test
`test_v189_status_legacy_flat_fallback_still_works` testet das korrekte
Verhalten und passt jetzt mit dem gefixten Code.

### Hotfix — Legacy CARIAD-flat doors fallback inversion bug (English)

One-line hotfix for a latent bug present since the legacy-fallback path
was introduced in v1.8.9. Caught by the v1.8.9 regression test
`test_v189_status_legacy_flat_fallback_still_works` which failed in CI on
PR #82 but the PR was merged anyway because branch protection on
required checks is not enabled in the repo (separate process gap to be
addressed).

**Bug:** in `seat_cupra.py` legacy-fallback block, `doors_legacy[door_id]
= not val` inverted the semantics — the CARIAD-BFF field is named
`doorClosed*`, so `True` means "door IS closed", matching our
`doors_individual` convention (True == closed) directly. The `not val`
was wrong.

**Fix:** `doors_legacy[door_id] = bool(val)`.

**Impact:** current CUPRA Born / Formentor / Tavascan models use the new
`status.doors.{position}.{locked,open}` paths from v1.8.9, so the bug
doesn't hit them in practice. Only matters if a future OLA API change
forces us onto the fallback path. Still must be fixed because: (1)
existing regression test must pass, (2) silent inversion in fallback
would hide as a real bug later, (3) main with failing tests blocks
every subsequent PR.

**Tests:** no changes needed — the existing v1.8.9 test now passes with
the fixed code.

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

