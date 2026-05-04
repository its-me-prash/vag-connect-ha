# VAG Connect — Roadmap

> Single canonical source of truth for sessions, versions and issue mapping.
> The README ships an identical short version in 8 languages; this file
> mirrors it for archive/historical purposes and links the active GitHub
> issues for each session.

**Last updated:** 2026-05-04 — post v1.17.7 (Skoda outside_temp + preferred_workshop attrs als PATCH — beides nutzt EXISTIERENDE sensor + model fields, kein neuer Sensor → echter PATCH. Schließt #129 + #130 + #133. Plus voriges v1.17.6 = HomeRegion-Helper
Scaffolding, evcc port — `cariad/_home_region.py` mit per-VIN
7d-cache + `resolve_home_region()` async helper für
`mal-1a.prd.ece.vwg-connect.com` Discovery-Endpoint, defensiv
gegen alle Failure-Modi. SCAFFOLDING-ONLY: Helper gebaut +
14 Tests + Bruno-Doku, NICHT in `vw_eu.py` integriert weil
99%-EU-User vs 1%-Edge-Case Risk-Reward ungünstig — Wire-Up-
Plan im Modul-Header dokumentiert für späteren PATCH falls
Live-Tests bestätigen). Nächste P0 in laufender Sprint-Sequenz:
v1.18.0 (B = outside_temperature_c Skoda Sensor + workshop
attrs, MINOR weil neue Sensoren) → v1.19.0 (A = Push Bundle
FCM CUPRA/SEAT + MQTT Skoda, big architectural).

---

## Where to follow progress

- **Issues:** https://github.com/its-me-prash/vag-connect-ha/issues
- **PRs:** https://github.com/its-me-prash/vag-connect-ha/pulls
- **Releases:** https://github.com/its-me-prash/vag-connect-ha/releases
- **Live document for AI tools:** [`docs/SESSION_HANDOFF.md`](SESSION_HANDOFF.md)
- **Verified API facts archive:** [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md)

---

## Achieved (v1.0 → v1.8.12)

| Version | Content | Date |
|---|---|---|
| v1.0 – v1.5 | 9 platforms, 7 brands, bug fixes, entity audit | 2026-04 (early) |
| v1.6.0 | SEAT/CUPRA 9 endpoints, Škoda fix, Audi PPC, lock platform, nightly polling reduction | 2026-04-24 |
| v1.7.0 | Complete Škoda rewrite, car-friendly translations all 8 languages, reliability (rate-limit backoff, token-refresh lock, stale-data tracking) | 2026-04-25 |
| v1.8.0 | **Foundation Fix** — 7 P0 release blockers (#60); per-VIN availability; S-PIN fail-fast; reverse-geocoding opt-in | 2026-04-26 |
| v1.8.1 | Privacy & auth polish — VIN masking; ConfigEntryAuthFailed wiring | 2026-04-27 |
| v1.8.2 | **Session 2A** — error taxonomy + 3-state feature model + capabilities cache (#68) | 2026-04-27 |
| v1.8.3 | **Session 2B** — capability gating SEAT/CUPRA flash + wake | 2026-04-27 |
| v1.8.4 | **Session 2C** — SEAT/CUPRA SecToken lock fix (#53, #68) | 2026-04-27 |
| v1.8.5 | **Session 3A** — Command Profile foundation + v1/v2 fallback for 4 set-value commands (#51, #61, #74) | 2026-04-27 |
| **v1.8.6** | **Docs Truthfulness** — README + 8 translations + Multi-Brand-Successor positioning + dynamic CI badge | **2026-04-29** |
| **v1.8.7** | **Defensive Programming Pass** — 504 retry, transient-error retry, refresh storm guard, 3-failure tolerance, 6h stale-cache (12 new tests) | **2026-04-29** |
| **v1.8.8** | **Session 3B** — CARIAD v1/v2 + combined/separate dispatch for lock/unlock/climate/charging start+stop (4 new tests) | **2026-04-29** |
| **v1.8.9** | **Session 3C** — CUPRA OLA status JSON paths fix (Gerhard's 19 entities) + Live-API findings from CC-seatcupra #5/#8/#18/#21/#50/#51/#109 (12 new tests) | **2026-04-29** |
| **v1.8.10** | Hotfix — legacy CARIAD-flat doors fallback inversion (1-line) | **2026-04-29** |
| **v1.8.11** | **Session 3S** — Škoda `carCapturedTimestamp` connection-state + `detail` block + `reliableLockStatus` + `fullyChargedAt` from CC-skoda #50 Live-Dump (10 new tests, closes #54) | **2026-04-29** |
| **v1.8.12** | **MVP-Move** — Multi-Brand connection-state (Skoda + CUPRA + SEAT + VW EU + Audi via inheritance). Brand-agnostic helper `compute_connection_state` with recursive timestamp walk. Verified via volkswagencarnet #921 ID.4 2025 Live-Dump (12 new tests) | **2026-04-29** |
| **v1.9.0** | 🔬 **Vehicle Data Scout + Error Reporter** — 2 neue Diagnostik-Sensoren mit gemeinsamer 1-Klick Reporter Pipeline. Brand-localized in 8 Sprachen. HA Repair-Issues mit pre-filled GitHub-URL + Diagnostics-Export für Facebook/Forum-Community. Privacy: VIN/GPS/JWT/UUID/Email maskiert, NIE Auto-Push. Aktiv für Skoda + SEAT + CUPRA + VW EU + Audi (18 neue Tests) | **2026-04-29** |
| **v1.9.1** | 🔧 **Audi/VW Lock+Wake Hotfix + Capability-Filter Phase 2** — Issue #92: `command_lock` schickt jetzt S-PIN für Audi/VW (CARIAD BFF antwortete `403 spin_error`); `command_wake` nutzt v1→v2 Fallback. Issues #90+#91: 27 Vehicle Data Scout Findings vom Maintainer registriert (`dieselRange`, `currentFuelLevel_pct`, `maxChargeCurrentAC_A`, `userCapabilities`, `fuelStatus`, `vehicleHealthInspection`, `vehicleHealthWarnings`, `automation`, `departureProfiles`, etc.). Issue #56: Capability-Filter Phase 2 — `classify_command_failure` mit Body-Sniffing (spin_error/subscription/not_entitled), `_cariad_cmd` schreibt jedes Command-Ergebnis in FeatureState, command-bound Entities (Lock/Climate/Switch/Buttons) gehen automatisch unavailable bei definitivem Backend-No. (18 neue Tests) | **2026-04-29** |
| **v1.10.0** | 🔋⛽ **PHEV-Range-Triple + Audi-Diesel-Range** — Issue #94 + Scout-Entity-Implementierung aus #91: drei neue Sensoren `electric_range_km` / `combustion_range_km` / `total_range_km`. VW EU/Audi Parser klassifiziert nach Engine-Typ (nicht Position) aus `fuelStatus.rangeStatus.value.{primary,secondary}Engine`. Audi S6 C8 2021 Diesel-Fallback aus `measurements.rangeStatus.value.dieselRange`. Skoda mysmob `electricRange.distanceInKm` + `combustionRange.distanceInKm` + `totalRangeInKm`. Phantom-Entity-Schutz via `_DATA_PRESENT_REQUIRED` — keine "unknown"-Sensoren auf reinen EVs/ICEs. 8 Sprachen. (13 neue Tests) | **2026-04-29** |
| **v1.10.1** | 🛡️ **Defensive Coding Phase 2** — Issue #58: drei neue Helfer (`safe_int` / `safe_float` / `safe_enum`) in `cariad/_util.py`, NIE-raises Vertrag. An die heißesten Parsing-Stellen angewendet (Skoda `remainingTimeToFullyChargedInMinutes` als String "12.5", VW EU `maxChargeCurrentAC_A` als Enum "MAXIMUM", `model_year` int/string interop). Coordinator wrapped `to_dict()+_enrich()` per VIN in eigenes try/except — Parse-Failure landet in v1.9.0 Error Reporter Ring-Buffer statt Vehicle komplett unavailable zu machen. Forward-Kompatibilität: `safe_enum` loggt unbekannte Werte (myskoda #503 `CHARGING_INTERRUPTED` Pattern) statt zu crashen. (16 neue Tests) | **2026-04-30** |
| **v1.10.2** | 🚗 **CUPRA Born 2026 Firmware-Shapes** — Issue #53 Live-Test (Gerhard, 2026-04-30): Vehicle Data Scout meldete 19 neue Felder. Beim Audit zeigte sich: viele sind **umbenannte** Versionen unserer bekannten Felder (`battery.currentSocPercentage` statt `currentSOC_pct`, `plug.connection`/`plug.lock` kurz statt lang, lowercase enums). `seat_cupra.py` Parser liest jetzt alle drei Field-Namen-Varianten als Fallback-Kette + lowercase enum tolerance. Plus neue Born-2026-Felder genutzt: `battery.estimatedRangeInKm` als range fallback, `status.locked` + `status.hood.locked` als top-level overall fallback. **Erste echte Live-Validation der v1.9.0 Reporter Pipeline (~12h Bug-Report → Hotfix).** (16 neue Tests) | **2026-04-30** |
| **v1.11.0** | 🔆🔧 **Issue #91 Closure: Light-Status, Service-Days, Max-Charge-Current** — fünf neue Entitäten schließen Issue #91 vollständig: `lights_on` Binary-Sensor (any-light-on Aggregate), `lights_count` Sensor, `service_due_in_days` + `oil_service_due_in_days` als raw int Sensoren (komplementär zu den DATE-Sensoren), `max_charge_current_a` als Ampere-Sensor (read-only). Defensive Light-Parsing handhabt 3 bekannte Element-Shapes + Aggregate-Fallback bei unbekannter Shape. `_DATA_PRESENT_REQUIRED` Pattern jetzt auch in binary_sensor.py. 8 Sprachen. (15 neue Tests) | **2026-04-30** |
| **v1.11.1** | 🐛💨 **Golf 7 GTE Fuel-Range Fix (#96) + Optimistic UI (3B-Part-3)** — #96: VW Golf 7 GTE 2015 + Passat GTE B7/B8 zeigen endlich `fuel_level`/`combustion_range_km`/`total_range_km`. Root cause: `fuelStatus.rangeStatus = {error}` ließ Drivetrain-Detection False. Fix: 4 zusätzliche Pfade (`measurements.fuelLevelStatus.value.{primaryEngineType,secondaryEngineType}` + `carType="hybrid"` Substring) + `measurements.rangeStatus.value.totalRange_km` Fallback + engine-block `currentFuelLevel_pct` Fallback. Verifiziert via evcc-io/evcc#19045 + Audi Q4 + CarConnectivity Logs. 3B-Part-3: Optimistic UI (myskoda PR #832) — Lock/Climate/Charging/Window-Heating-Switches flippen sofort, revertieren bei Failure. (18 neue Tests) | **2026-04-30** |
| **v1.12.0** | 🔋💡⚡🧯🔒 **5-in-1 Feature-Sprint** — Issue #23 (12V Voltage-Sensor + Low-Warnung bei <11.5V via lvBattery job), #91 Welle 3 (Per-Light Binary-Sensors aus `lights_individual` dict), #91 follow-up (writeable Max-Charge-Current Number + neuer `command_set_max_charge_current` Command), #55 (Smart-Wake Counter + Soft-Cap auf 3/Tag + UTC-midnight reset), #63 Phase 1 (Read-only Mode Option — skip lock/switch/button(non-refresh)/climate/number platforms; refresh-button bleibt). 8 Sprachen. (~25 neue Tests) | **2026-04-30** |
| **v1.12.1** | 🛰️📚 **Scout-Pfade #105/#106 + Gerhard's Born Fixture (#53 consent) + #47 FAQ** — Welle 4 EXPECTED_KEYS Wildcards für `.error.*` + explizite `.value` Container. Erste Live-Validation des Privacy-Workflows aus PR #101: Gerhard hat Consent für Fixture gegeben, komplett redacted nach Hard Rule #18 + 7 Privacy-Audit-Tests. 6 Round-Trip-Tests verifizieren dass v1.10.2 Parser-Pfade aus der Fixture die Werte produzieren die Gerhard live sah. #47 FAQ-Sektion in CONTRIBUTING.md mit Subscription-vs-missing-capability-vs-spin-Diagnose-Tabelle. (19 neue Tests) | **2026-04-30** |
| **v1.12.2** | 🌟🛰️ **Erstes Community-Scout-Report (Skoda #107 von tritanium73)** — User `tritanium73` reichte am 2026-05-01 den ersten Vehicle Data Scout Report von einem Nicht-Maintainer ein. 14 neue Skoda mysmob Pfade über 4 Endpoints (`renders.{lightMode,darkMode}` 2-segment fix, 6× `air-conditioning`, 2× `driving-range` mit `carType`+`primaryEngineRange`, 4× `maintenance` meta-blocks). Volle v1.9.0 Pipeline funktioniert in der Wildbahn. (6 neue Tests) | **2026-05-01** |
| **v1.12.3** | 🛰️ **Scout-Pfade #111 (DnnsJp74) + #113 (Golf GTE) + #114 (Audi S6 C8)** — drei Scout-Reports zusammen. #111: 23 Audi-Pfade von Community-User DnnsJp74 (zweiter community Scout report nach #107). #113+#114: 14+20 Felder von Prash auf eigenen Vehicles (Golf GTE + Audi S6) — alle drei zeigen `.value` Container Children. Wildcards `fuelStatus.rangeStatus.value.*`, `vehicleHealthInspection.maintenanceStatus.value.*`, `departureProfiles.departureProfilesStatus.value.*`, `userCapabilities.capabilitiesStatus.value.*` decken alle Klassen future-proof ab. (8 neue Tests) | **2026-05-01** |
| **v1.13.0** | 🛡️ **Production Hardening Bundle** — drei P0-Themen aus dem Backlog (#56/#63/#62) plus Process-Docs (#64) in einem MINOR. Capability-Filter Phase 3 mit `cariad/_capabilities.py` Single-Source-of-Truth (`CAPABILITY_MAP[brand][command_id]→cap_id`, Audi/SEAT erben via Table-Alias) — gates PRE-Entity-Creation (Phase 1+2 waren post-failure). Read-only Phase 2 service-side: `_coord_writeable(vin)` raised `read_only_mode_active` ServiceValidationError. Read-only Phase 3 cloud_refresh vs wake distinction (`refresh_cloud_cache` neu, `refresh_vehicle` bleibt als Alias) + 5-min wake cooldown pro VIN + per-VIN-per-command-class asyncio.Lock mit timeout. Diagnostics: token-redaction expanded (access/refresh/id_token snake+camel + client_secret), Email partial-mask `u***@***.com`, GPS opt-in 1-decimal rounding wenn reverse-geocoding aus. Process: `.github/ISSUE_TEMPLATE/{scout_report,error_report}.yml` + `BRAND_CAPTAINS.md`. Pre-Research: `docs/RESEARCH_NOTES_2026-05-02.md` (423 Zeilen, 13 Issues über 3 Bundles). (31 neue Tests) | **2026-05-02** |
| **v1.17.3** | 🤖🛡️📚 **Bruno-CI Stufe 2 + Lovelace Cards + 3 Research-Docs + Tim Outreach** — MASSIVE PATCH-Release. (1) Bruno-CI Stufe 2: seat_cupra auf 100% coverage (35 .bru files) + strict gating ON in CI; 7 skoda + 10 cariad_bff .bru files (warn-mode bis v1.17.4); drift-check refactored mit multi-file-per-brand support + `_ENGINE_BASE` constant + `--strict-brands` per-brand graduation; placeholder-expansion dropped originals (no strict-mode false-positives). (2) Lovelace Cards README section: 4 community Cards reviewed (flex-table-card, vehicle-info-card, car-card, Ultra-Vehicle-Card) plus eigenes Card-Projekt teaser plus browser_mod integration hint. (3) 3 neue research-docs: migration-from-mitch-dc-2026-05-03 (deprecated repo deep-scan + entity-ID mapping table), browser-mod-integration-2026-05-03 (use-case-fit assessment + recipe-cookbook für v1.18.0), community-vag-ha-landscape-2026-05-03 (4 outreach targets + 6 reply drafts + competitor inventory + SEO harvest). (4) Reply auf Tim's Antwort auf Bruno-Collection Issue #1 — humanized German showing v1.17.0→v1.17.2 evolution + cross-review offer + endpoint-PRs angekündigt. | (no issues) |
| **v1.17.7** | 🌡️🔧 **Skoda outside_temperature + preferred_workshop attrs** — PATCH-Release. Wires-up zwei existing-but-not-Skoda-populated Datenpunkte aus den v1.17.5 Scout-Reports: (1) `outside_temp` Sensor (existiert seit early releases, von VW EU + SEAT/CUPRA populated) bekommt Skoda als zusätzliche Datenquelle aus `outsideTemperature.{temperatureValue,temperatureUnit}` mit defensiver FAHRENHEIT-Konversion (#129/#130/#133, drei konvergente Reports). (2) Neues Model-Field `preferred_workshop: dict` populated aus `preferredServicePartner` (alle Felder außer `openingHours`), surfaced als `extra_state_attributes` auf bestehendem `service_due_in_days` Sensor (Pattern wie v1.14.0 #24 recent_trips, v1.15.0 #35 recent_charging_sessions). Echter PATCH weil keine neuen Sensoren / Translations / Platforms — nur Datenquellen-Hookup. Schließt #129, #130, #133. (14 neue Tests, 13/13 lokal verifiziert) | **2026-05-04** |
| **v1.17.6** | 🌍 **HomeRegion-Helper Scaffolding (evcc port)** — PATCH-Release. Neuer Helper `cariad/_home_region.py` (155 Zeilen) mit `HomeRegionCache` (per-VIN dict + 7d TTL) + `resolve_home_region(client, vin, *, cache=None) -> str` async function. Discovery-Endpoint `https://mal-1a.prd.ece.vwg-connect.com/api/cs/vds/v1/vehicles/{vin}/homeRegion` (verifiziert gegen evcc-io/evcc `vehicle/vw/api.go:HomeRegion()`). Defensiv gegen 404, network error, malformed-response (9 variants getestet). `DEFAULT_BASE` matched `vw_eu._BASE` per Invariant-Test. **SCAFFOLDING ONLY** — nicht in URL-Buildern integriert; Wire-Up-Plan im Modul-Header dokumentiert (`self._vehicle_bases` dict + `_base_for_vin()` sync helper + 13 Call-Sites in vw_eu.py). Bruno-Doku in `tests/bruno/cariad_bff/22_GET_homeRegion.bru` (drift-check silent weil mal-1a anderer Host-Namespace). Hilft potentiell beim Lösen von #75 wenn Christian's Vehicle in non-EU-Region geroutet ist (zu verifizieren). (14 neue Tests) | **2026-05-04** |
| **v1.17.5** | 🛰️ **Scout-Welle 5 — 4 Community-Reports in 24h + 4 Verification-Pings** — PATCH-Release. Vehicle Data Scout Pipeline (v1.9.0) lieferte am 2026-05-03/04 vier neue Community-Reports von vier verschiedenen Usern: #129 rocksandclouds (3 Skoda outsideTemperature-Felder), #130 Chr1sDub (13 Skoda Felder — outsideTemperature + preferredServicePartner + customerService), #132 rborkenhagen (3 VW Felder — heaterSource + departureTimers + secondaryEngineType=electric), #133 christianmhz (15 Skoda Felder — gleiche wie #130 plus targetTemperature.unitInCar + parking errors[]). Plus Gerhard's parallele Cupra Born v1.17.4-Test-Reaktion auf #53 mit 8 weiteren Cupra Felder (services.charging/climatisation/windowHeating + settings.maxChargeCurrentAc/autoUnlockPlugWhenChargedAc/targetSoc + chargingCareSettings.batteryCareMode + chargingCareStatus.batteryCareTargetSoc). Total **42 neue Felder über 4 Brands** registriert in EXPECTED_KEYS — viele über Wildcards (`outsideTemperature.*`, `preferredServicePartner.*`, `customerService.*`, `errors.*`, `services.*`, `settings.*`, `chargingCareSettings.*`, `chargingCareStatus.*`, `departureTimers.*`). Plus Sprint-A Verification-Pings: #118 (eismarkt restart), #51 (Audi RS e-tron 404), #48 (all-actions-fail), #42 (migendi CUPRA Formentor v1.5.9). Plus Diagnostic-Pings: #131 (Chr1sDub Skoda Octavia subscription/S-PIN check), #53 (Gerhard Born Klima-Stop 404 — A/B fallback in v1.16.1 deckt 2 URLs, Born scheint dritten Pfad zu brauchen). NICHT in diesem Release (alle deferred zu v1.18.0+): outside_temperature_c Sensor, preferredServicePartner-attrs, 500-Klassifikation für Skoda mysmob (false-positive Risiko), HomeRegion-Helper. (16 neue Tests, alle 5 Scout-Reports + Inheritance verifiziert) | **2026-05-04** |
| **v1.17.4** | 🤖✅ **Bruno-CI Stufe 2 COMPLETE — Full Strict Coverage all 3 brands** — PATCH-Release. (1) Skoda Bruno coverage 7→**24** .bru files (17 neu via gen-agent: set-charge-limit, charging start/stop, lock/unlock/honk-and-flash, vehicleWakeup, 5× air-conditioning, connection-readiness, driving-range, parking, vehicle-maintenance). (2) CARIAD-BFF Bruno coverage 10→**21** .bru files (11 neu: audi engine_stop, vehicles list GET, climatisation_timers, windowheating combined, vehicleWakeup, plus 7 separate-route fallbacks für lock/unlock/charging start+stop/climate start+stop). (3) Drift-script erweitert: `{path_suffix}` placeholder expansion in `_ACTION_EXPANSIONS` + neuer `_is_skipped_template()` filter für `/vehicle/v2/vehicles/{vin}/{path_suffix}` v2 auto-fallback templates (sonst hätte placeholder-expansion strict-mode für v2-Pfade gebrochen). (4) CI workflow auf full `--strict --brand all` (kein `--strict-brands seat_cupra` whitelist mehr) — neue Endpoints in `cariad/api/*.py` ohne matching `.bru` File **failen sofort CI**. (5) Final coverage: **80/80 ALL STRICT PASS** (35+24+21). (6) Roadmap-Klarstellung: Vehicle Data Scout (v1.9.0) deckt 80% der Discovery-Cases (neue Felder in known endpoints) — mitmproxy/Frida-Capture-Stack ist P3 Edge-Case-Tool für komplett neue Endpoints / neue Brands / neue App-Features (Walk-Away-Lock-style discoveries). | **2026-05-03** |
| **v1.17.2** | 🧹🤖 **Stale-Cleanup + Bruno-CI Stufe 1** — PATCH-Release. (1) 17 Pointer auf 2 post-v1.17.0 entfernte research docs gefixt (canonical replacement → `vag-ha-integration-research.md`). (2) Bruno-CI Foundation: `tests/bruno/seat_cupra/` Scaffold mit 6 sample `.bru` files für hauptsächliche endpoints + dirs für skoda/cariad_bff. `scripts/check_bruno_url_drift.py` (stdlib only, <1s) walks Python `f"{_BASE}/..."` URLs vs `.bru` URLs und reports drift mit Normalize-Phase für `{{vin}}`/`{vin}` + `{action}` placeholder expansion. `.github/workflows/bruno-validation.yml` mit 2 jobs (collection-structure validation via `bru run --env mock` + url-drift warn-only). `docs/BRUNO-WORKFLOW.md` Contributor-Guide mit Capture-Methodology (mitmproxy + Frida) + Privacy rules. Foundation für Stufe 2 (Source-of-Truth) und Stufe 3 (Custom Claude Code Skill). | (no issues) |
| **v1.17.1** | 🚙🌬️🔥 **Bruno Quick-Wins Bundle** — MASSIVE PATCH-Release basierend auf Timwun's Cupra-WeConnect-Bruno-Collection deep-dive (53 .bru files crawled). 7 SEAT/CUPRA-Verbesserungen alle defensiv mit A/B-fallback: (1) Window Heating Endpoint A/B-Fix (war wahrscheinlich seit immer broken, analog #53 Climate). (2) Cabin Ventilation start/stop neu (Bruno seq 31/32). (3) Webasto Auxiliary Heating start/stop neu (Bruno seq 29/30 + pycupra) mit SecToken auf start, A/B URL-fallback zwischen Bruno-Pfad und Pycupra-Pfad. (4) #36 Navigation closer (`PUT /v1/users/vehicles/{vin}/destination` mit verbatim Bruno body shape — single-element JSON array mit address/geoCoordinate/destinationName). (5) Battery Care Sensors — 2 thin GET endpoints exponiert. (6) Generic `_post_with_ab_fallback` Helper extrahiert. (7) Capabilities path A/B-fallback (singular/plural). (8) Charging Actions A/B-fallback (newer non-/v1). Plus Cariad-Charging-Host research (`docs/research/cariad-charging-host-2026-05-02.md`) für v1.18.0 Charging Statistics prep. Closes #36. (~25 neue Tests) | **2026-05-02** |
| **v1.17.0** | 🛡️📚 **Operational Hardening Bundle** — Quality-of-life MINOR. Poll-Defaults quota-protective angehoben (5min→10min default, 3min→5min min) basierend auf community research dass MyCupra/MySeat ~1500 calls/day quota hat — alte 3min default frisst 32% des Budgets, neue 10min nur 10%. Vehicle-deactivated persistent_notification (analog pycupra v0.2.14) — User wissen warum Entities verschwinden. Year-rollover + DST + leap-year unit tests (pycupra issue #33 prevention). Plus zwei neue End-User-Docs: docs/FAQ.md (What wakes the car, Privacy Matrix, Quota explanation, Reauth-Flow, Entity-ID Stability Policy, Read-only Mode) + docs/HACS-CHECKLIST.md (Audit-Status pro Item für v2.0.0 HACS Default prep). Plus community research doc `vag-ha-integration-research.md` (Skoda + MQTT + extended HACS-Checklist + 8 upstream contributions). Plus 8 ready-to-post upstream issue drafts für WulfgarW/homeassistant-pycupra in docs/upstream-contributions/. Bonus: outreach an Timwun/Cupra-WeConnect-Bruno-Collection Repo (50+ verifizierte OLA-Endpoint-Specs entdeckt — closes #36 Navigation in v1.17.x). (~12 neue Tests) | **2026-05-02** |
| **v1.16.1** | 🐛 **SEAT/CUPRA Climate Fix + #122 Scout-Paths** — PATCH-Hotfix nach Gerhard's v1.16.0 Test (#53). Climate URL ``POST /v2/vehicles/{vin}/climatisation`` mit Body action gab 404, korrekt ist ``POST /v2/vehicles/{vin}/climatisation/start`` (Action im Pfad, verifiziert gegen pycupra). Defensive v1/v2 Fallback. Plus #122 SEAT Scout-Pfade von r1150gs (`engines.primary.*` wildcard). Phase 3 Phantom-Button Bug auf #53 wartet auf Gerhard's Diagnostics für Root-Cause. (6 neue Tests) | **2026-05-02** |
| **v1.16.0** | ⏰📍 **Cross-Brand UX + Skoda Charging Profiles** — Long-standing UX gap closed: HA `time` platform (10. Plattform) für `time.{auto}_departure_timer_X_time_set` Editing-Entities (#26). User editiert Abfahrtszeit direkt im Dashboard, integration ruft existierenden `set_departure_timer` Service. Plus Skoda mysmob Endpoint `GET /v1/charging/{vin}/profiles` (verifiziert myskoda chargingprofiles.py) für #25/#31 read-only Sensoren: `active_charging_profile_name` (aus `currentVehiclePositionProfile.name` — Backend wählt Profil basierend auf Vehicle-GPS automatisch, kein client-side GPS-Zone-Matching nötig!), `active_charging_profile_target_soc_pct`, `next_charging_time`, `charging_profiles_count`. Plus Profile-List als attrs. Plus Cross-Brand OTA Probe Plan dokumentiert (`docs/RESEARCH_NOTES_2026-05-02_OTA_PROBE.md`). Skoda vehicle-info bundle (renders/equipment/widget) + Charging-Profile Write-Side + Push Bundle deferred zu v1.17.0+. (~20 neue Tests) | **2026-05-02** |
| **v1.15.0** | 🛰️🔋 **Skoda Modernization Bundle** — komplette Adoption von 22 myskoda Upstream-PRs seit unserem Cutoff. (1) #35 Skoda Charging History via neuem mysmob `/v1/charging/{vin}/history` Endpoint — `total_charged_energy_kwh` mit `TOTAL_INCREASING` für HA Energy Dashboard plus 2 last-session Sensoren plus `recent_charging_sessions` als attrs. 1h-Cache + brand-restriction + capability-gate. (2) Skoda Software-Version + OTA via `/v1/vehicle-information/{vin}/software-version/update-status` (myskoda PR #541) — `sensor.software_version` + `binary_sensor.ota_update_available` mit `releaseNotesUrl` als attr. (3) 8 neue cap-ids in CAPABILITY_MAP["skoda"]: software_update, charging_history, charging_profiles, driving_score, readiness, plug_and_charge, route_planning, battery_charging_care. (4) Capability-Status Tolerance: top-level `errors[]` block (myskoda PR #543) + extended transient status enum values (INSUFFICIENT_BATTERY_LEVEL, LOCATION_DATA_DISABLED, VEHICLE_DISABLED). (5) Diagnostics Anonymize Hardening: `_mask_location_qs` für Query-String GPS scrubbing + `_stable_hash` SHA-256 für user_id/account_id (Pattern aus myskoda anonymize.py). Cross-Brand OTA + #26 Klima-Timer UI + #25/#31 read-only Sensoren deferred zu v1.16.0. (~30 neue Tests) | **2026-05-02** |
| **v1.14.0** | 🚗 **Audi Feature Pack Bundle** — Bundle 2 aus dem Pre-Research-Plan. (1) #24 Trip Statistics für VW EU + Audi via CARIAD-BFF `/vehicle/v1/vehicles/{vin}/tripstatistics?type={shortTerm\|longTerm}` — 4 neue Sensoren (`last_trip_distance_km`, `_avg_speed_kmh`, `_avg_fuel_consumption_l_100km`, `_avg_electric_consumption_kwh_100km`) + `recent_trips` als attributes. 1h-Cache-Cycle, brand-restriction, capability-gate (`tripStatistics`). Backend liefert consumption ×10 — Parser teilt. (2) #28 Audi ICE Remote Engine Start/Stop — zwei-Schritt S-PIN-Flow nach audi_connect_ha PR #717 (`PUT /vehicle/v1/engine/{VIN}/userpromptproof` → extract `userPromptProof` → `POST /engine/{VIN}/start` mit `securedActivationData`). Stop ohne S-PIN. Audi-only via `CAPABILITY_MAP["audi"]` Copy-and-Patch (verhindert Pollution VW EU Map). Service `vag_connect.engine_start`/`engine_stop`. (3) #29 PPE/PPC Klima-Body conditional — `force_ppe_climate` Option (User-overridable, Audi-only Effekt). `command_start_climate(ppe_mode=True)` schaltet auf neues Body-Format (climatisationMode mandatory, targetTemperature omitted). Plus #116 Skoda Scout-Pfade (MavericklCS) — 4× `primaryEngineRange.*` + `predictiveMaintenance.setting.*` Wildcard. (19 neue Tests) | **2026-05-02** |

**Sprint summary 2026-04-29:** 7 releases, ~50 new tests, branch
protection activated, CHANGELOG split into human + technical, 4 parallel
research agents producing the verified-source archive in
`docs/RESEARCH_NOTES_2026-04-29.md`.

---

## Session plan (next sessions, P0 → P1 → P2)

Strict order — P0 (next release) > P1 (planned MINOR) > P2 (later) > P3 (research / wait-on-user) > MAJOR.

### ✅ Done (v1.9.0 → v1.12.1, alle 2026-04-29/30 ausgeliefert)

| Version | Scope | Date |
|---|---|---|
| ~~v1.9.0~~ | Vehicle Data Scout + Error Reporter (Reporter Pipeline) | done |
| ~~v1.9.1~~ | Audi Lock+Wake Hotfix (#92) + Capability-Filter Phase 2 (#56) + Scout-Pfade #90/#91 registriert | done |
| ~~v1.10.0~~ | PHEV-Range-Triple + Audi-Diesel-Range (#94 + #91) | done |
| ~~v1.10.1~~ | Defensive Coding Phase 2 (#58) | done |
| ~~v1.10.2~~ | CUPRA Born 2026 Firmware-Shapes (#53 — Gerhard) | done |
| ~~v1.11.0~~ | Issue #91 Closure (Light-Status, Service-Days, Max-Charge-Current) | done |
| ~~v1.11.1~~ | Golf GTE Fuel-Range #96 + Optimistic UI 3B-Part-3 | done |
| ~~v1.12.0~~ | 5-in-1 Feature-Sprint: 12V #23 + Per-Light + Writeable Number + Smart-Wake #55 + Read-only #63-Phase-1 + Scout-Pfade #103/#104 | done |
| ~~v1.12.1~~ | Scout-Pfade #105/#106 + Gerhard's Born Fixture (#53 consent) + #47 FAQ | done |
| ~~v1.12.2~~ | Erstes Community-Scout-Report (Skoda #107 von tritanium73) | done |
| ~~v1.12.3~~ | Scout-Pfade #111/#113/#114 + Wildcard-Strategie für `.value.*` Container | done |
| ~~v1.13.0~~ | Production Hardening Bundle: Capability-Filter Phase 3 (#56) + Read-only Phase 2/3 (#63) + Anonymized Diagnostics-Export (#62) + Process & Governance Doc-PR (#64) | done |
| ~~v1.14.0~~ | Audi Feature Pack: Trip Stats #24 + Engine Start ICE #28 + PPE/PPC Klima-Body #29 + Skoda Scout-Pfade #116 | done |
| ~~v1.15.0~~ | Skoda Modernization: Charging History #35 + OTA + 8 cap-ids + capability tolerance + anonymize hardening | done |
| ~~v1.16.0~~ | Cross-Brand UX + Skoda Charging Profiles: HA time platform #26 + #25/#31 read-only via charging-profiles + Cross-Brand OTA Probe Plan | done |
| ~~v1.16.1~~ | SEAT/CUPRA Climate 404 fix (#53) + #122 SEAT scout-paths | done |
| ~~v1.17.0~~ | Operational Hardening: poll-defaults raised + deactivated notification + year-rollover tests + FAQ + HACS Checklist + 3 research docs + 8 upstream drafts + Bruno outreach | done |
| ~~v1.17.1~~ | Bruno Quick-Wins: window heating fix + ventilation + aux heating + battery care + #36 Navigation + 2× A/B-fallbacks + Cariad-Charging-Host research | done |
| ~~v1.17.2~~ | Stale-Cleanup (17 doc-refs) + Bruno-CI Stufe 1 (scaffold + drift-check + GH Actions workflow + contributor guide) | done |
| ~~v1.17.3~~ | Bruno-CI Stufe 2 + Lovelace Cards + 3 Research Docs + Tim Outreach Reply | done |
| ~~v1.17.4~~ | Bruno-CI Stufe 2 **COMPLETE** — 80/80 strict coverage all 3 brands (35 seat_cupra + 24 skoda + 21 cariad_bff) + drift-script `{path_suffix}` expansion + `_is_skipped_template()` v2 auto-fallback filter + CI full --strict no whitelist | done |
| ~~v1.17.5~~ | Scout-Welle 5 — 4 Community-Reports in 24h + Gerhard Born v1.17.4-Test (5 Reports total, 42 Felder über Skoda/VW/Audi/Cupra/Seat) + 4 Verification-Pings + 2 Diagnostic-Pings | done |
| ~~v1.17.6~~ | HomeRegion-Helper Scaffolding (evcc port) — `cariad/_home_region.py` mit per-VIN 7d-cache + Discovery-Endpoint async resolution, 14 Tests, NICHT wire-in (opt-in für späteren PATCH) | done |
| ~~v1.17.7~~ | Skoda outside_temperature + preferred_workshop attrs — Wires-up #129/#130/#133 Scout-Findings als ECHTE Datennutzung (kein neuer Sensor, nur neue Skoda-Datenquelle für existing outside_temp + extra_state_attributes auf service_due_in_days) | done |

### 🔴 P0 — Nächste Release (v1.18.0 ODER weitere v1.17.x)

| Session | Version | Scope | Issues |
|---|---|---|---|
| **Push Bundle (FCM CUPRA/SEAT + MQTT Skoda)** | **v1.18.0** ⭐ | MINOR (big session): Firebase FCM via `mqtt.messagehub.de` (CUPRA/SEAT) + mysmob MQTT broker (Škoda-only — myskoda PR #566). Eliminiert 12V-Wake-Cycle für Real-Time-Updates. Bisher P2 — durch Push-Konsens jetzt P0. 2-3 Wochen Arbeit. | #57, #27 |
| **Eigenes Lovelace-Card Repo** | parallel session | Standalone session: HACS-Plugin Skeleton (lit-element + ts-build via vite/esbuild), inspiriert von Ultra-Vehicle-Card + car-card. Stretch-goal: Designer-Mode für PHEV-Range-Triple + Charging-Profile-Picker + Aux-Heating-Switch. | (community) |
| **Pycupra-driven Hardening** | **v1.17.x** | PATCH aus pycupra source-reading: port `find_path()` als `cariad/_safe_path.py`, extend exception taxonomy mit `PyCupraThrottledException`-equivalent, surface `X-RateLimit-Remaining` als `requests_remaining_today` sensor. Notes in `docs/research/vag-ha-integration-research.md`. | (HACS-Checklist outstanding) |
| **Skoda Vehicle-Info Bundle + Cross-Brand OTA Live-Test** | **v1.18.0 oder eigenes Bundle** | MINOR: deferred aus v1.16.0 — `GET /v1/vehicle-information/{vin}` + `/renders` + `/equipment` + lightweight `/v2/widgets/vehicle-status/{vin}` für Skoda DeviceInfo Erweiterung. Plus Cross-Brand OTA Live-Test per `docs/RESEARCH_NOTES_2026-05-02_OTA_PROBE.md`. Plus Charging Profile Write-Side. | (Live-Test asks) |
| **Old-Bug Verify-Pings** | community | User-Comments auf #42 (CUPRA Formentor) + #48 (all-actions-fail) + #51 (Audi RS e-tron GT 404) — höchstwahrscheinlich gefixt durch v1.8.4 SecToken / v1.8.5 v1/v2 fallback / v1.9.1 Wake-Fix / v1.10.2 Born firmware fixes. Status-Bestätigung gefragt. | #42, #48, #51 |

### 🟠 P2 — Future MINOR Sprints (v1.16.0+)

| Session | Version | Scope | Issues |
|---|---|---|---|
| **Theft / Alarm Binary** | v1.16.0 | API-Endpoint research nötig — alarmStatus job in CARIAD selectivestatus? Feature-Discovery dann implementation. | #33 |
| **Navigation: Ziel ans Auto** | v1.16.x | MINOR: Service `vag_connect.send_destination` + payload research. | #36 |
| **Standort-spez. Ladeziel + Ladeprofile (Write-Side)** | v1.17.0 | MINOR: location-based charging (zone-aware target_soc) + multiple Ladeprofile pro Standort schreibbar. Verlängerung der read-only Implementierung aus v1.15.0. | #25, #31 |
| **Ladehistorie LTS** | v1.17.x | API-Discovery nötig — `chargedEnergy_kWh` Feld nicht in CARIAD selectivestatus verifiziert (Research v1.13.0). Wartet auf neuen Endpoint-Hinweis aus Live-Tests. | #35 |

### 🔵 P2 — Big Architectural

| Session | Version | Scope | Issues |
|---|---|---|---|
| **Push CUPRA/SEAT + Push Škoda** | v1.18.0 | MINOR: Firebase FCM via `mqtt.messagehub.de` (CUPRA/SEAT) + mysmob MQTT broker (Škoda-only — myskoda PR #566). Eliminiert 12V-Wake-Cycle für Real-Time-Updates. Big session, 2-3 Wochen Arbeit. | #57, #27 |

### ⚪ P3 — Wait on User / Community

| Session | Status | Action |
|---|---|---|
| **#13 Live-Tests gesucht** | ongoing community | Brand-Captains-Liste (Teil von #64) wird das organisieren |
| **#53 CUPRA Born Funktionstest** | active mit Gerhard | v1.12.1 hat Fixture committed; nächster Test-Cycle wartet auf Gerhard's nächste Antwort |
| **#74 VW Passat 2025 B9** | wait | Marco Debug-Log offen — needed für PPC platform routing |
| **#75 Skoda Kodiaq 2 Mk2** | wait | tester needed |
| **#76 VW T6 Multivan Legacy MBB** | wait | tester needed |

### 🛠️ Discovery-Tooling-Strategie (Scope-Klarstellung post v1.17.4)

| Tool | Coverage | Status |
|---|---|---|
| **Vehicle Data Scout (v1.9.0)** | **80%-Case** — neue Felder in **bekannten** Endpoints (z.B. neuer `temp_C` in `chargingStatus` beim Kodiaq iV 2026, Born-2026 firmware-shapes via #53) | ✅ Active in Production — Pull-Modell, User installiert → wir kriegen Reports passiv (siehe v1.12.2 #107 als erste Community-Validation) |
| **Bruno-Collection (v1.17.1-v1.17.4)** | **80/80 strict-coverage all 3 brands** — alle in `cariad/api/*.py` + `seat_cupra.py` + `skoda.py` referenzierten Endpoints sind dokumentiert. CI fängt URL-drift ab. | ✅ COMPLETE — Tim's upstream Collection (53 .bru CUPRA WeConnect) + unsere 80 .bru ergänzen sich. |
| **mitmproxy + Frida Capture-Stack** | **20%-Edge-Case** — komplett neue Endpoints / neue Brands / neue App-Features die App-only sind (z.B. "Walk Away Lock" wenn nur App es kennt) / Auth-Flow-Wechsel | 📋 P3 Documented-Recipe — `docs/BRUNO-WORKFLOW.md` Capture-Methodology Section. Nur für Discovery-Sprints, kein routine-Tool. Stretch-Goal: dedicated `docs/CAPTURE_STACK_RECIPE.md` falls nächster neuer Brand käme. |

### 🎯 v2.0.0 (MAJOR — distant)

| Session | Version | Scope | Issues |
|---|---|---|---|
| **HACS Default + v2.0.0** | **v2.0.0** 🎉 | MAJOR: HACS Default Repository, Live tests all brands compatibility matrix, EU Data Act ready (pycupra `EUDAConnection` ready to port — September 2026 EU deadline). | #13, #59 |

### Standalone enhancements (no version pin yet)

- **Diesel AdBlue Range** for Škoda (CC-skoda #24): field `adblue_range_km`
  exists in `models.py` but Skoda parser doesn't read it from
  `driving-range` endpoint. Small targeted session.
- **`/v2/widgets/vehicle-status/{vin}`** as lightweight Skoda endpoint
  (myskoda PR #557): for battery-friendly polling. Pairs well with Session 6.
- **Region-routing** `_get_cariad_url(region)` for US users (volkswagencarnet
  PRs #648/#676): hardcoded `emea.` breaks US-based VW EU users.
- **TermsAndConditionsError repair issue** (volkswagencarnet PR #307):
  HA `ir.async_create_issue` with deeplink to vehicle-account login portal
  when 401 with `terms_of_use` body is detected.
- **ICE Engine Start S-PIN flow** (audi_connect_ha PR #717): two-step
  PUT `/engine/{VIN}/userpromptproof` then POST `/engine/{VIN}/start`.
  ICE-only feature, capability-gated.
- **PPE Climate Body** (audi_connect_ha PR #644 + #677): `climatisationMode:
  "comfort"` mandatory, `targetTemperature*` must be omitted for PPE
  (Q6 e-tron, A6 e-tron, etc.). Conditional body shape.

---

## What will not be implemented

| Brand / feature | Reason |
|---|---|
| VW China (2026+) | CEA/XPeng platform — undocumented, near-zero HA user base |
| Lamborghini commands | No verified public API. Research only — see `research/LUXURY_BRANDS.md` |
| Bentley commands | No verified public API. Research only |
| Bugatti | Fleet too small, no API surfaced |
| Ducati | Motorcycles — out of scope |
| MAN / Scania | Commercial fleet APIs — different use case |
| Ford Explorer Electric | FordPass + Ford Auth + Ford API. Out of scope. Use [marq24/ha-fordpass](https://github.com/marq24/ha-fordpass). (#77 closed) |
| VW EU Vehicle Render Image API | No official render API exists. Marketing CDN URLs are not authenticated. (#37 closed) |
| Skoda `/v3/garage` Fallback for Kodiaq Mk2 #75 | Endpoint does not exist in mysmob — verified by grep on `skodaconnect/myskoda` (zero matches). Hard Rule #8 forbids speculation. |

---

## Process notes (current state of the practice)

- Every session = atomic PR + tagged release.
- **Branch protection ON** since 2026-04-29 — 5 required CI checks
  (Lint, Tests, Hassfest, HACS, CHANGELOG). Merging with failing tests
  is now impossible (lesson from v1.8.9 incident).
- Every command-sending entity must be capability-gated (#56) before
  reaching v2.0.0.
- Translation strings: English in `strings.json`, mirrored across
  `translations/{de,en,cs,es,fr,nl,pl,sv}.json`.
- CHANGELOG is now split: human-friendly in `CHANGELOG.md` (with emojis,
  for HACS browsers and end users), full technical with all source
  citations in `docs/CHANGELOG_TECHNICAL.md`.
- Research-Agent recipe documented in `docs/RESEARCH_NOTES_2026-04-29.md`
  section 7.

### Semver-Korrektur (going-forward strict, ab v1.9.0)

Historisch (v1.8.6 → v1.8.12) waren PATCH-Bumps auch für neue Features
üblich (z.B. v1.8.11 hatte einen neuen `connection_state` Sensor — wäre
nach strikter Lesart MINOR gewesen). Tags v1.8.11 + v1.8.12 sind released,
die rebasen wir nicht.

**Going forward — strict semver:**

- **PATCH** (`1.x.Y`) — nur Bug-Fixes, keine neuen Entities, keine API-Änderungen
- **MINOR** (`1.X.0`) — neue Sensoren, neue Services, neue Plattformen
- **MAJOR** (`X.0.0`) — Breaking Changes, Architektur-Wechsel

Konsequenz: `Vehicle Data Scout + Error Reporter` (zwei neue Sensoren)
wird **v1.9.0**, nicht v1.8.13. Folgereihe entsprechend verschoben.

---

## How an AI tool resumes this work

If a fresh AI session lands here without context:

1. Read [`docs/SESSION_HANDOFF.md`](SESSION_HANDOFF.md) — orientation
2. Read [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md) — verified API facts
3. Pick the next un-shipped session from this file
4. Follow the recipe at the bottom of `docs/SESSION_HANDOFF.md`
   ("How to start the next session")
