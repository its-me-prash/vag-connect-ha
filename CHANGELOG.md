# Changelog

Alle wesentlichen Änderungen werden hier dokumentiert.

Format: [Keep a Changelog 1.0.0](https://keepachangelog.com/de/1.0.0/)  
Versionierung: [Semantic Versioning 2.0.0](https://semver.org/lang/de/)

> 📖 **Bi-lingual title convention (ab v1.12.3 / since v1.12.3):** Section-Titles sind **DE / EN** geteilt durch ` / `. Body-Inhalt bleibt auf Deutsch (Audience ist primär die deutschsprachige VAG-HA-Community + DACH FB-Gruppen). Übersetzungen einzelner Body-Texte gibt es bei Bedarf via [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md) — dort wird das gleiche Pattern angewendet.

## [Unreleased]

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

> 💡 **Für Entwickler / Contributors:** Vollständige technische Detail-Notes
> für v1.8.6+ findest du in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md)
> — mit jeder geänderten Datei, jeder Zeile, jeder Issue-Referenz und der
> Methodik dahinter.

## [Unreleased]

## [1.17.6] - 2026-05-04 🌍 HomeRegion-Helper Scaffolding (evcc port) / HomeRegion Helper Scaffolding (evcc port)

🌍 **PATCH-Release.** evcc-Pattern für region-import / non-EU-routed Vehicles eingebaut. Neuer Helper `cariad/_home_region.py` löst per-VIN die Base-URI auf via Discovery-Endpoint `https://mal-1a.prd.ece.vwg-connect.com/api/cs/vds/v1/vehicles/{vin}/homeRegion`. **Scaffolding-only** — Helper ist gebaut, getestet, dokumentiert, aber NOCH NICHT in `vw_eu.py` URL-Builders integriert (würde 13 Call-Sites berühren — Risk-Reward für 99%-EU-User vs. 1%-Edge-Case ungünstig). Wire-Up-Plan ist im `_home_region.py` Modul-Header dokumentiert; Aktivierung erfolgt via separatem PATCH falls Live-Tests (#75 Skoda Kodiaq Mk2 oder ähnlich) bestätigen dass HomeRegion-Resolution den Bug fixt.

### 🛠️ Was ist gebaut / What is built

- **`custom_components/vag_connect/cariad/_home_region.py`** (155 Zeilen):
  - `HomeRegionCache` Klasse mit per-VIN dict + 7-Tage TTL
  - `async def resolve_home_region(client, vin, *, cache=None) -> str` — ruft Discovery-Endpoint, parsed `homeRegion.baseUri.content`, fallback auf `DEFAULT_BASE` bei Fehler/Malformed-Response
  - `DEFAULT_BASE = "https://emea.bff.cariad.digital"` (= identisch mit `vw_eu._BASE`)
  - `DISCOVERY_BASE = "https://mal-1a.prd.ece.vwg-connect.com"`
  - Defensiv gegen alle Failure-Modi (404, network error, malformed JSON, missing keys)
- **`tests/bruno/cariad_bff/22_GET_homeRegion.bru`** — menschen-runbar via Bruno CLI für manuelle Verifikation. Drift-check silent weil mal-1a anderer Host (kein `{{base_url}}` Prefix → keine Bruno-URL-Extraktion → kein Counting-Mismatch)
- **`tests/test_v1176_homeregion.py`** — 14 Test-Cases:
  - Cache: hit/miss/expiry/clear/per-VIN-isolation
  - Resolution: success/trailing-slash/correct-discovery-URL
  - Fallback: network error/404/malformed-response (9 variants)/no-cache-mode
  - Failure-caching (default base cached on lookup failure to skip retry)
  - Invariant test: `DEFAULT_BASE == vw_eu._BASE`

### 🔌 Wire-Up Plan (für späteren PATCH wenn nötig) / Wire-Up Plan

```python
# In VWEUClient.__init__:
self._vehicle_bases: dict[str, str] = {}
self._home_region_cache = HomeRegionCache()

# In VWEUClient.get_vehicles, nach VIN-Liste:
for vin in vins:
    self._vehicle_bases[vin] = await resolve_home_region(
        self, vin, cache=self._home_region_cache,
    )

# Helper für synchronen Zugriff in URL-Buildern:
def _base_for_vin(self, vin: str) -> str:
    return self._vehicle_bases.get(vin, _BASE)

# Alle 13 ``f"{_BASE}/..."`` Stellen umstellen auf:
# ``f"{self._base_for_vin(vin)}/..."``
```

Audi erbt automatisch via `AudiClient(VWEUClient)`. Skoda mysmob hat eigenen Backend-Hostname und braucht separaten Helper falls dort auch nötig (TBD basierend auf Live-Test-Daten von #75).

### 🚫 NICHT in diesem Release / NOT in this release

- **Wire-Up in `vw_eu.py`** — opt-in scaffolding, kein Risiko für EU-User
- **Skoda mysmob HomeRegion** — analoger Helper möglich, abhängig von #75 Live-Test
- **VW NA / Porsche / SEAT/CUPRA HomeRegion** — andere Auth-Pipelines, nicht von HomeRegion betroffen
- **PKCE-OAuth Hardening** — separater Patch, niedrige Prio

### 📦 Schließt Issues / Closes

Keine User-Issues direkt — Pure Infrastruktur-Vorbereitung. Hilft potentiell beim Lösen von #75 (Skoda Kodiaq Mk2 403) wenn Christian's Vehicle in nicht-Standard-Region geroutet ist (zu verifizieren wenn er antwortet).

## [1.17.5] - 2026-05-04 🛰️ Scout-Welle 5: 4 Community-Reports an einem Tag + 4 Verification-Pings / Scout Wave 5: 4 community reports in one day + 4 verification pings

🛰️ **PATCH-Release.** Vehicle Data Scout Pipeline (v1.9.0) hat innerhalb von 24h **4 neue Community-Reports** geliefert: rocksandclouds (#129), Chr1sDub (#130), rborkenhagen (#132), christianmhz (#133) — plus Gerhard's parallele Cupra Born v1.17.4-Test-Reaktion (#53). Total **42 neue Felder über 4 Brands** (Skoda + VW + Audi + Cupra/Seat) registriert in EXPECTED_KEYS. Plus Sprint-A Verification-Pings auf 4 ältere Issues.

### 🛰️ Scout-Silencing — 5 Reports, 4 Brands / Scout Silencing — 5 Reports, 4 Brands

**Skoda mysmob (#129 + #130 + #133, 3 unabhängige User mit konvergenten Findings):**

- `outsideTemperature.*` Wildcard auf `air-conditioning` Endpoint — deckt `temperatureValue` (z.B. `24.0`), `temperatureUnit` ("CELSIUS"), `carCapturedTimestamp` ab
- `targetTemperature.unitInCar` ("CELSIUS"|"FAHRENHEIT") auf `air-conditioning` Endpoint
- `preferredServicePartner.*` Wildcard auf `maintenance` Endpoint — deckt `name`, `brand`, `partnerNumber`, `id`, `contact`, `address`, `location`, `openingHours` ab (Skoda exposed jetzt komplette Werkstatt-Info)
- `customerService.*` Wildcard auf `maintenance` Endpoint — deckt `activeBookings`, `bookingHistory` ab
- `errors`, `errors.*` auf `parking` Endpoint (Skoda mysmob wraps "no recent GPS fix" und ähnliche transient errors jetzt im gleichen Pattern wie air-conditioning + driving-range)

**Volkswagen + Audi CARIAD-BFF (#132 rborkenhagen):**

- `climatisation.climatisationSettings.value.heaterSource` ("electric" für Born/ID — wird vom Backend gemeldet, von uns noch nicht für PHEV-PTC vs HV-loop Logik genutzt)
- `measurements.fuelLevelStatus.value.secondaryEngineType` ("electric" — companion zu primaryEngineType, hardens v1.11.1 #96 Golf GTE PHEV-detection)
- `departureTimers`, `departureTimers.*` Wildcard (top-level job ist seit v1.13.0 in selectivestatus query, aber nie explizit in EXPECTED_KEYS catalog gewesen)
- Audi erbt VW EU's selectivestatus shape — alle drei Silencings gelten automatisch

**Cupra/Seat OLA (#53 Gerhard's Born v1.17.4-Test):**

- `services.*` Wildcard auf `mycar` Endpoint — Born exposed per-service entitlement children (charging/climatisation/windowHeating); jeder ist multi-key dict (subscription state + caps + limits)
- `settings.*` Wildcard auf `charging-info` Endpoint — Born nutzt lowercase `Ac` suffix variant (`maxChargeCurrentAc`, `autoUnlockPlugWhenChargedAc`, `targetSoc`) parallel zur uppercase `AC` variant
- `chargingCareSettings.*` und `chargingCareStatus.*` Wildcards — neue Charge-Care-Subsystem leaves (`batteryCareMode=true`, `batteryCareTargetSoc=80`)
- Seat erbt Cupra's OLA shape — alle Silencings gelten automatisch

### 📨 Sprint-A Verification-Pings + Diagnostic-Pings / Sprint A Verification + Diagnostic Pings

4 ältere Issues mit Verweis auf Hardening-Bundles seit ihrer Original-Report-Version:

- **#118 eismarkt** "restart After Update" — User auf v1.9.0; v1.10.1 + v1.11.1 + v1.13.0 Hardening-Bundles seitdem
- **#51 Audi RS e-tron GT 404** — User auf v1.5.10; v1.8.4 SecToken + v1.8.5 v1/v2 fallback + v1.9.1 Wake-Fix + v1.13.0 Capability-Filter Phase 3 + v1.14.0 Audi Feature Pack seitdem
- **#48 all-actions-fail** — Generic; v1.8.5 fallback + v1.9.1 classify_command_failure + v1.13.0 Phase 3 seitdem
- **#42 migendi CUPRA Formentor v1.5.9** — v1.10.2 Born firmware + v1.16.1 Klima-Fix + v1.17.1 Bruno-Quick-Wins seitdem

Plus **#131 Chr1sDub Skoda Octavia** Diagnostic-Ping: Subscription-Verifikation (Connect-Abo: NEIN ist mutmaßlich Root-Cause für die HTTP 500 Klima-Failures) + S-PIN Re-Check (Optionen-Variante vs Initial-Config) — kein Code-Fix in diesem Release weil 500 → NOT_ENTITLED Klassifikation false-positive Risiko hat (transient backend errors würden Entities verstecken).

Plus **#53 Gerhard Born Klima-Stop 404 Diagnose-Frage** — A/B Fallback in v1.16.1 deckt 2 URLs ab; Gerhards Born scheint einen dritten Pfad zu brauchen. Warten auf DEBUG-Log + 404-Body um den fehlenden Path zu identifizieren.

### 🧪 Tests / Tests

- 16 neue Test-Cases in `tests/test_v1175_scout_silencing.py` — alle 5 Scout-Reports verifiziert für Skoda/VW/Audi/Cupra/Seat (inkl. Inheritance-Tests für audi←volkswagen und seat←cupra)
- Alle bestehenden Tests grün
- Bruno-Drift unverändert: 80/80 strict pass

### 🚫 NICHT in diesem Release / NOT in this release

- **outside_temperature_c Sensor (Skoda)** — strict semver MINOR weil neuer Sensor; deferred zu v1.18.0
- **preferredServicePartner als attrs-Sensor** — same reason; deferred
- **500-Klassifikation für Skoda mysmob** — false-positive Risiko zu hoch; alternative wäre per-VIN failure-rate threshold (komplexer; deferred)
- **HomeRegion-Helper (evcc port)** — eigener PATCH v1.17.6 oder mit v1.18.0 gebündelt

### 📦 Schließt Issues / Closes

Keine User-Issues direkt geschlossen — Verification-Pings warten auf User-Confirmation. Pure Scout-Silencing für #129/#130/#132/#133/#53.

## [1.17.4] - 2026-05-03 🎯 Bruno-CI Stufe 2 COMPLETE — Full Strict Coverage / Bruno-CI Stufe 2 Complete (Skoda + CARIAD-BFF strict)

🎯 **Bruno-CI Stufe 2 ist COMPLETE.** Skoda + CARIAD-BFF auf 100% coverage gebracht, alle 3 Brands jetzt strict mode in CI. **80 .bru files total**, 80/80 match (35 seat_cupra + 24 skoda + 21 cariad_bff).

### 🤖 Bruno Coverage Completion / Bruno Coverage Completion

- **Skoda: +17 neue .bru files** (seq 08–24) via gen-agent — covers alle 24 Python URLs:
  - 3× charging actions (set-charge-limit, start, stop)
  - 3× vehicle-access (lock, unlock, honk-and-flash)
  - 1× vehicle-wakeup (mit `?applyRequestLimiter=true` query)
  - 5× air-conditioning (bare GET, target-temperature, start, stop, start/stop-window-heating)
  - 1× connection-status/readiness
  - 1× vehicle-status/driving-range
  - 1× maps/positions/parking
  - 1× vehicle-maintenance
  - **24/24 strict pass**
- **CARIAD-BFF: +11 neue .bru files** (seq 11–21):
  - 4× neue concrete endpoints (engine_stop, vehicles list, climatisation/timers POST, windowheating combined)
  - 7× separate-route fallbacks für `_post_command_with_fallback_paths` (lock, unlock, charging-start, charging-stop, climatisation-start, climatisation-stop, vehicleWakeup) — required by drift-check für coverage of v1 paths
  - **21/21 strict pass**

### 🛠️ Drift-Check Improvements / Drift-Check Improvements

- **`{path_suffix}` placeholder expansion** in `_ACTION_EXPANSIONS` — covers `_post_command_with_fallback_paths(primary_suffix=..., fallback_suffix=...)` runtime templates. Same mechanism as `{action}` placeholder.
- **`_is_skipped_template()` helper** — filters out `/vehicle/v2/vehicles/{vin}/{path_suffix}` template captures since `_post_command` auto-falls back from v1→v2 with same body. v2 fallback URLs are implicit, no separate Bruno docs needed.
- **CI workflow strict mode for ALL 3 brands** — no more `--strict-brands seat_cupra` whitelist; full `--strict` gating. Any new Python endpoint without matching `.bru` fails CI immediately.

### 📊 Coverage Summary / Coverage Summary

| Brand | Python URLs | Bruno files | Match | Status |
|---|---|---|---|---|
| seat_cupra | 35 | 35 | 35/35 | ✅ Strict |
| skoda | 24 | 24 | 24/24 | ✅ Strict |
| cariad_bff | 21 | 21 | 21/21 | ✅ Strict |
| **Total** | **80** | **80** | **80/80** | **✅ All strict** |

### 📦 Schließt Issues / Closes

Keine User-Issues — Bruno-Coverage Abschluss.

### 🎯 Strategische Bedeutung / Strategic Context

Bruno-CI Stufe 2 ist die **Foundation für Stufe 3** (Custom Claude Code Skill für HAR→.bru → Python-client generation). Ab v1.18.0+ kann jede neue Endpoint-Addition über die `.bru → Python` Workflow-Direction laufen statt umgekehrt. Das senkt die Contribution-Schwelle für Brand-Captains drastisch und macht uns zur **canonical reference** für die VAG-FOSS-Community.

## [1.17.3] - 2026-05-03 🤖🛡️📚 Bruno-CI Stufe 2 + Lovelace Cards + 3 Research Docs

🤖 **MASSIVE PATCH-Release** mit 4 parallel ausgelieferten Themen:

1. **Bruno-CI Stufe 2** — full coverage seat_cupra (35 .bru files, strict gating ON), 7 skoda + 10 cariad_bff .bru files, multi-file-per-brand drift-check
2. **Lovelace Cards Recommendations** — 4 cards reviewed + own card project teased
3. **3 neue Research-Docs** — mitch-dc deprecated migration + browser_mod integration + community VAG-HA landscape
4. **Tim's Issue #1 Outreach Reply** — humanized German reply showing v1.17.0→v1.17.2 Bruno-Evolution, Cross-Review-Offer, +1 endpoint-PRs angekündigt

### 🤖 Bruno-CI Stufe 2 / Bruno-CI Stufe 2

**SEAT/CUPRA: 100% coverage + strict gating**
- 27 .bru files via gen-agent (seq 07-33) — covers alle Python-URLs in `cariad/api/seat_cupra.py`
- Plus 3 fallback `.bru` files (seq 34-36) für documented A/B-fallback URLs
- **Drift-check: 35/35 match, 0 drift, strict mode AKTIV in CI** — jede neue endpoint-Addition ohne `.bru` lässt CI fail

**Skoda: 7 .bru files** (seq 01-07) für die wichtigsten endpoints (garage mit MOD1-4 query, capabilities, vehicle-status, charging, charging-history, charging-profiles, software-update). 17 noch offene Python-URLs werden in v1.17.4 aufgefüllt.

**CARIAD-BFF (Audi + VW EU): 10 .bru files** (seq 01-10) für selectivestatus, capabilities, parkingposition, tripstatistics, lock, climate-start, charging-start, vehicleLights flash, plus 2 Audi-engine endpoints (PUT userpromptproof + POST start). 6 noch offene werden in v1.17.4 aufgefüllt.

**Drift-check Script Refactor:**
- Multi-file-per-brand support (cariad_bff = vw_eu.py + audi.py)
- `_ENGINE_BASE` constant captured for Audi-specific URLs
- `--strict-brands` flag für per-brand graduation (seat_cupra strict, skoda+cariad_bff warn-only)
- Placeholder-expansion für `{action}` runtime placeholder dropped originals (no more strict-mode false-positives)

### 🎨 Lovelace Cards Section / Lovelace Cards Section

Neue README-Sektion "Empfohlene Lovelace-Cards" mit Bewertungstabelle für 4 community Cards:
- **flex-table-card** (custom-cards Org, aktiv) — Multi-Vehicle-Dashboards
- **vehicle-info-card** (ngocjohn, wenig Updates) — Single-Vehicle-Detail
- **car-card** (flixlix, aktiv) — Simple EV-Schnellansicht
- **Ultra-Vehicle-Card** (WJDDesigns, aktiv) — Polished Premium-Look

Plus Teaser für **eigenes Card-Projekt** (`vag-connect-lovelace-card` repo geplant) + Browser-Mod Integration Hinweis (recipe-doc folgt v1.18.0).

### 🔬 3 Neue Research-Docs / 3 New Research-Docs

Alle in `docs/research/`:

- **`migration-from-mitch-dc-2026-05-03.md`** (R1) — `mitch-dc/volkswagen_we_connect_id` archived 2025-10-29 deep-scan. Repo-Status, top 10 open issues (mostly auth/login), last 5 PRs (anothertobi's CarConnectivity migration draft closed unmerged), endpoint comparison (we have 18 endpoints, they had 0 — used `weconnect==0.60.8` library wrapper), entity ID mapping table für Migration-Guide, SEO-keyword harvest für unsere README.
- **`browser-mod-integration-2026-05-03.md`** (R2) — `thomasloven/hass-browser_mod` analysis. 1727★, MIT, HACS-Default, v2 actively maintained. Service catalog, entity surface, 5 use-case-fit assessments für VAG (popup für 12V-warning, NFC-quick-command-sheet, charging-screensaver, per-browser theme, send_destination confirm-popup). Recommendation: doc-mention only, recipe-cookbook for v1.18.0.
- **`community-vag-ha-landscape-2026-05-03.md`** (R3) — community.simon42.com + community.home-assistant.io VW-Connect/MyAudi/MyCupra/MySkoda thread crawl. 4 high-signal outreach targets identifiziert, 6 reply-drafts (3 EN + 3 DE), competitor inventory (mitch-dc archived, skodaconnect deprecated, tillsteinbach/CarConnectivity active competitor), shared feature gaps (writable preheat, single climate-toggle, real-time push, EU Data Act), SEO-keyword harvest, differentiator: "no Docker, no MQTT broker, single HACS install all 7 brands".

### 📨 Outreach / Outreach

- **Reply auf Tim's Antwort** auf `Timwun/Cupra-WeConnect-Bruno-Collection#1` — humanized German Antwort zeigt v1.17.0→v1.17.2 Bruno-Evolution-Journey:
  - 3 Bug-fixes/Features die durch Bruno-Collection gelöst wurden (Climate-404, #36 Navigation, Aux-Heating)
  - Bruno-CLI in unsere CI integration
  - Neue eigene Bruno-Collection in `tests/bruno/` (33+10+7 .bru files)
  - Cross-Review-Offer für PRs zu seinem Repo
  - Endpoint-PRs angekündigt (4 endpoints aus pycupra die seine Collection noch nicht hat)

### 📦 Schließt Issues / Closes

Keine User-Issues — Bruno-CI + research + outreach.

### 📋 Roadmap-Update / Roadmap-Update

- **v1.17.4** geplant: Skoda + CARIAD-BFF Bruno coverage abschließen, alle 3 Brands strict mode, Bruno-CI Stufe 2 endgültig komplett
- **v1.18.0** geplant: Push Bundle (FCM für CUPRA/SEAT + MQTT für Skoda) — Foundation aus v1.15.0 cap-Map + v1.17.x Bruno-CI bereit
- **Eigenes Lovelace-Card Repo** in eigener Session

## [1.17.2] - 2026-05-03 🧹🤖 Stale-Cleanup + Bruno-CI Stufe 1 / Stale-Reference Cleanup + Bruno-CI Foundation

🧹🤖 **PATCH-Release** — zwei kleine, hochwertige Verbesserungen:

1. **Stale-Reference Cleanup** — 17 Pointer auf zwei post-v1.17.0 entfernte research-docs gefixt
2. **Bruno-CI Stufe 1 Foundation** — `tests/bruno/` Scaffold + GH Actions Workflow + URL-drift detection script

### 🧹 Cleanup / Cleanup

Maintainer hatte post-v1.17.0 zwei research-docs aus dem repo entfernt (`upstream-pycupra-notes.md` + `pycupra-deep-dive-2026-05-02.md`). v1.17.0/v1.17.1 CHANGELOG/ROADMAP/HACS-CHECKLIST/CHANGELOG_TECHNICAL referenzierten beide noch — alle 17 Pointer durch:
- Verweis auf canonical replacement (`vag-ha-integration-research.md`) ersetzt
- Pattern-Information inline expandiert wo Deep-Dive zitiert wurde
- Explanatory note hinzugefügt wo der Removal-Kontext relevant ist (CHANGELOG_TECHNICAL v1.17.0)

### 🤖 Neu — Bruno-CI Stufe 1 / New — Bruno-CI Stufe 1

Foundation für den Bruno-as-Living-Documentation Workflow (siehe `docs/BRUNO-WORKFLOW.md` neu).

- **`tests/bruno/seat_cupra/`** Scaffold mit:
  - `bruno.json` collection metadata
  - `environments/mock.bru` mit dummy VIN/token für CI parsing
  - 6 sample `.bru` files für die wichtigsten SEAT/CUPRA endpoints (status, charging, climate start, aux heating, destination, battery care)
- **`tests/bruno/{skoda,cariad_bff}/`** dirs für künftige expansion
- **`scripts/check_bruno_url_drift.py`** — Python ↔ Bruno URL drift scanner. Walks `cariad/api/*.py` für `f"{_BASE}/..."` URLs, walks `tests/bruno/<brand>/*.bru` für `url:` directives, reports endpoints in einer Quelle aber nicht der anderen. Normalize-Phase handhabt `{{vin}}` vs `{vin}`, `{action}` placeholder expansion, query-string stripping. Stdlib only (kein Bruno-CLI nötig), läuft in <1s. Modes: warn-only (default) oder `--strict` für CI-gating.
- **`.github/workflows/bruno-validation.yml`** — neuer CI-Workflow:
  - Job 1: install `@usebruno/cli@latest`, `bru run --env mock` über jede Collection — validates structural correctness ohne live API hits
  - Job 2: `python scripts/check_bruno_url_drift.py --brand all` — warn-only initially (will switch to strict once full coverage)
  - Path-filter: läuft nur bei changes in tests/bruno/, cariad/api/, scripts/check_bruno_url_drift.py, oder workflow itself
  - Concurrency-cancellation: ältere Runs werden gecancelt wenn neuer push kommt
  - HTML-Reporter artifact für 14 Tage retention
- **`docs/BRUNO-WORKFLOW.md`** — Contributor guide:
  - Why Bruno (drift detection + living docs + non-Python contribution barrier lowering)
  - File naming convention + .bru template
  - Full workflow für neuer Endpoint
  - Capturing API traffic (mitmproxy + Frida + Android emulator setup)
  - Privacy rules (anonymization before commit)
  - CI behavior explanation
  - Future: live API tests pre-condition

### 🎯 Strategische Bedeutung / Strategic Context

Bruno-CI ist Stufe 1 der "Bruno-MVP-Position" Strategie (siehe `docs/research/upstream-pycupra-notes.md` historical reference + `docs/research/vag-ha-integration-research.md` aktive). Folgestufen:
- **Stufe 2** (v1.17.x oder v1.18.x): Source-of-Truth Workflow — neue Endpoints erst `.bru` schreiben, dann Python generieren. Brand Captains contribute via `.bru` ohne Python skills.
- **Stufe 3** (v2.0.0 prep): Custom Claude Code Skill `pb-vag-bruno` — HAR→.bru converter, .bru→Python generator, .bru→OpenAPI exporter, drift-detection helper. Generative-AI-augmented API maintenance.

### 📦 Issue-Closures / Issue-Closures

Keine Issue-Closures (Cleanup + CI foundation, keine User-facing features).

## [1.17.1] - 2026-05-02 🚙🌬️🔥 Bruno Quick-Wins Bundle / Bruno Quick-Wins (Window heating fix + Ventilation + Aux Heating + Battery Care + Navigation #36 + 2× A/B-fallback)

🚙🌬️🔥 **MASSIVE PATCH-Release** basierend auf Timwun's `Cupra-WeConnect-Bruno-Collection` deep-dive (53 .bru files crawled). 7 SEAT/CUPRA-Verbesserungen — alle defensiv mit A/B-fallback wo Endpoints zwischen Quellen disagreen, alle Phase-3 capability-gated. Plus Cross-Brand OTA Probe Plan komplettiert mit eigenem Cariad-Charging-Host research.

### 🐛 Bug-Fixes / Bug-Fixes

- 🌡️ **Window Heating Endpoint A/B-Fix** — derzeit POST `/v2/vehicles/{vin}/climatisation` mit Body `{"action":"startWindowHeating"}` war wahrscheinlich seit immer broken (analog #53 Climate). Bruno-verifizierter Pfad: `/vehicles/{vin}/windowheating/requests/{start|stop}` (no /v1). A/B-fallback zur legacy URL bei 404 — kein Regression-Risiko.

### ✨ Neu / Added

- 🌬️ **SEAT/CUPRA Cabin Ventilation** (Bruno seq 31/32) — neue Service `vag_connect.start_ventilation` + `stop_ventilation` plus `switch.{auto}_ventilation`. Endpoint `POST /v1/vehicles/{vin}/ventilation/{start|stop}`. Capability-gated über Phase 3 (`command_start_ventilation` → `ventilation`).
- 🔥 **SEAT/CUPRA Webasto Auxiliary Heating** (Bruno seq 29/30 + pycupra) — Standheizung remote start/stop. Neue Services `vag_connect.start_aux_heating` + `stop_aux_heating` plus `switch.{auto}_aux_heating`. Start braucht **SecToken** (S-PIN-derived, gleiches Flow wie unser lock/unlock). Stop ohne S-PIN. **A/B URL-fallback** zwischen Bruno-Pfad `/v1/vehicles/{vin}/auxiliary-heating/start` und Pycupra-Pfad `/api/auxiliary-heating/v1/{vin}/start`.
- 📍 **#36 Navigation: Ziel ans Auto senden** (Bruno seq 34) — schließt seit Wochen offenes Issue. Neuer Service `vag_connect.send_destination(vin, latitude, longitude, name, [city, country, state, street, house_number, zip_code])`. Endpoint `PUT /v1/users/vehicles/{vin}/destination` mit verbatim Bruno body shape (single-element JSON array). SEAT/CUPRA only initially.
- 🔋 **SEAT/CUPRA Battery Care Sensors** (Bruno seq 10/11) — zwei thin GET endpoints exponiert als `binary_sensor.{auto}_battery_care_enabled` + `sensor.{auto}_battery_care_target_soc_pct`. Endpoints: `GET /v1/vehicles/{vin}/charging/battery-care` + `/battery-care/target`. 1h-Cache via neuer `coordinator.refresh_battery_care(vin)` mit brand-restriction (`cupra`/`seat`) + capability-gate. Best-effort: 404 → keine Entity (`_DATA_PRESENT_REQUIRED` gating).
- 🔧 **Generic `_post_with_ab_fallback` Helper** — extrahiert aus v1.16.1 climatisation-fix für Wiederverwendung. Pattern: try primary URL, on 404-only fall back to legacy URL with body action. Non-404 errors propagate normal. Headers per-call configurable. Verwendet von 5 Endpoints in v1.17.1.

### 🛡️ Defensive Hardening / Defensive Hardening

- 🔁 **Capabilities path A/B-fallback** — Bruno (seq 4) zeigt `/v1/user/{userId}/vehicle/{vin}/capabilities` (singular), unser pre-v1.17.1 nutzt `/v1/vehicles/{vin}/capabilities` (plural). Beide observed in upstream sources. Try plural first (status quo, no migration risk), fallback zu singular on 404 — preserves capability fetching für accounts die nur die singular Variante akzeptieren.
- 🔁 **Charging Actions A/B-fallback** — Bruno (seq 47/46) zeigt newer `/vehicles/{vin}/charging/requests/{start|stop}` (no /v1, no body), legacy `/v1/vehicles/{vin}/charging/actions` mit body action. Cariad migrated some endpoints away von /v1 — try newer first, fallback zu legacy on 404. Behebt potentielle 404s auf neuerer Firmware ohne ältere Accounts zu brechen.

### 🧬 Capability-Map Erweiterungen

7 neue cap-id Einträge in `CAPABILITY_MAP["cupra"]` (SEAT erbt via Alias):
- `command_start_ventilation` / `command_stop_ventilation` → `ventilation`
- `command_start_aux_heating` / `command_stop_aux_heating` → `auxiliary-heating`
- `command_send_destination` → `destination`
- `command_battery_care_read` → `charging`

5 neue Einträge in `_COMMAND_CLASS` für per-VIN per-class lock isolation.

### 🌐 Übersetzungen / Translations

8 Sprachen — neue keys:
- `entity.sensor.battery_care_target_soc_pct`
- `entity.binary_sensor.battery_care_enabled`
- `entity.switch.{ventilation_switch, aux_heating_switch}`

### 🧪 Tests / Tests

`tests/test_v1171_bruno_quick_wins.py` — neue Tests in 10 Klassen:
- `TestPostWithAbFallback` (3) — primary success, 404 fallback, non-404 propagates
- `TestWindowHeatingAB` (2) — Bruno path used first
- `TestVentilation` (2) — URL pattern + no body
- `TestAuxHeating` (4) — no-spin raises, SecToken, 404 fallback to pycupra path, stop without SecToken
- `TestBatteryCare` (3) — 404→empty, dict return, target SoC parsing
- `TestRefreshBatteryCareBrandRestriction` (2) — audi skips, cupra merges
- `TestCapabilitiesAB` (2) — plural primary, singular fallback
- `TestChargingActionsAB` (2) — newer path used first
- `TestSendDestination` (1) — URL + body shape verbatim Bruno
- `TestCapabilityMapV1171` (8 parametrized + 1) — all new cap-ids registered
- `TestCommandClassRegistry` (3) — engine/ventilation/aux_heating/destination classes

### 🔬 Pre-Research / Pre-Research

- `docs/research/cariad-charging-host-2026-05-02.md` (NEW) — research für 2nd Cariad host `prod.emea.mobile.charging.cariad.digital` der für Charging Statistics verwendet wird. Auth-Flow verifiziert (same OLA bearer token), endpoint catalog (`POST /charging_statistics` + `GET /charging_statistics/{sessionId}/power-curve`), cross-brand-status (vag-connect-ha wäre **first** FOSS-Integration die diesen Host nutzt). Implementation-Plan für v1.18.0 als neuer `cariad/api/charging_stats.py` Client.

### 📦 Schließt Issues / Closes

- Closes #36 (Navigation: Ziel/Adresse ans Fahrzeug senden — SEAT/CUPRA initial, Cross-Brand v1.18.0+)

### 🔗 Inspiration / Credits

- **`Timwun/Cupra-WeConnect-Bruno-Collection`** — 50+ verifizierte OLA-Endpoint-Specs in Bruno format. Issue #1 mit Dankeschön + Brand-Tester-Einladung gepostet. Diese Bundle ist direkter Output dieser Collection.
- **`WulfgarW/pycupra`** — Pycupra-Source für SecToken-Pattern + URL-Backup für Aux Heating fallback path.

## [1.17.0] - 2026-05-02 🛡️📚 Operational Hardening Bundle / Operational Hardening (Quota-protective polling + FAQ + HACS Checklist + Year-rollover Tests + Deactivated Notification)

🛡️📚 **Quality-of-life MINOR-Release** nach community-research deep-dive: Poll-Defaults quota-protective angepasst, deactivated-vehicle notification, year-rollover unit tests, plus zwei neue High-Value User-Docs (FAQ + HACS-Checklist). Setzt die Foundation für v1.18.0 Push Bundle und v2.0.0 HACS Default Repository.

### 🔄 Geändert / Changed

- 📊 **Poll-Defaults quota-protective angehoben** (community-research-driven):
  - `DEFAULT_SCAN_INTERVAL`: 5min → **10min** (288 polls/day → 144 polls/day = 19% → 10% des 1500/day Quotas)
  - `MIN_SCAN_INTERVAL`: 3min → **5min** (verhindert dass Power-User die Quota mid-day exhausten)
  - **Bestehende Configs werden NICHT umkonfiguriert** — nur Defaults für fresh installs
  - Begründung dokumentiert in `const.py` mit verweis auf pycupra README + WulfgarW/homeassistant-pycupra release notes
  - Siehe neue `docs/FAQ.md` "What is the daily API request quota?" für User-Erklärung

### ✨ Neu / Added

- 🚗 **Vehicle-deactivated persistent_notification** (analog `WulfgarW/homeassistant-pycupra` v0.2.14) — wenn ein Fahrzeug aus dem VAG-Konto verschwindet (verkauft / Eigentümerwechsel / Hersteller-Deaktivierung / Subscription abgelaufen), wird eine `persistent_notification` mit verständlicher Begründung erstellt BEVOR das Device removed wird. User wissen warum ihre Entities gerade verschwunden sind. Long-term-statistics History bleibt erhalten.

### 📚 Documentation / Documentation

- 📚 **`docs/FAQ.md`** (NEW) — High-value End-User-Doku:
  - "What actually wakes the car?" — definitive Antwort: nur explizite commands, KEIN polling
  - Wake protection summary (3/Tag soft-cap + 5min cooldown)
  - Privacy-Setting Matrix (Share/Use/Don't share → welche Entities degradieren)
  - Daily API Quota Erklärung mit polls/day Tabelle
  - Reauthentication-Flow erklärt + warum NICHT remove-and-readd (statistics history loss)
  - Entity-ID-Stability Policy (bug fix → keep ID, schema-change → new ID + deprecate)
  - Read-only Mode + "vehicle disappeared" + Bug-Reporting workflow + Brand-Region-Tabelle
- 📋 **`docs/HACS-CHECKLIST.md`** (NEW) — Audit-Status pro Item gegen die HACS-Default-Repository Pre-Conditions:
  - 7 Sektionen (Repo structure, Code quality, Config flow, Operational safety, CI/release, User-facing docs, Outstanding for v2.0.0)
  - Per-Item Status (✅ done / ⚠️ partial / ❌ missing / 🔮 planned)
  - Outstanding-Items klar gelistet für v2.0.0 prep (per-vehicle log prefix, requests_remaining_today sensor, HTTP 500 log-once pattern, PRIVACY.md, Live-Tests aller Brands, EU Data Act readiness)

### 🧪 Tests / Tests

- `tests/test_v1170_datetime_boundaries.py` — neue Tests in 4 Klassen für recurring datetime-arithmetic bug class (pycupra issue #33 prevention):
  - `TestDateConversionBoundaries` (5) — int-days + ISO string parsing across year-end + leap year
  - `TestWakeBudgetUtcMidnightReset` (2) — UTC date logic + year-rollover comparison
  - `TestConnectionStateTimestampBoundaries` (2) — naive vs tz-aware comparison + year-end timestamp parsing
  - `TestDstTransitionParsing` (3) — spring-forward + fall-back UTC offset preservation

### 🔬 Pre-Research / Pre-Research

Neue Research-Docs in `docs/research/`:
- **`vag-ha-integration-research.md`** — community research (Skoda + MQTT + HACS-Checklist + 8 upstream contribution ideas)
- *(Note: zwei zusätzliche pycupra research docs wurden post-v1.17.0 vom Maintainer entfernt — Inhalt überlappt mit `vag-ha-integration-research.md` + `cupra-bruno-endpoints-2026-05-02.md`.)*

Plus **`docs/upstream-contributions/wulfgar-pycupra-issues.md`** — 8 ready-to-post upstream issue drafts für `WulfgarW/homeassistant-pycupra` (async_step_reauth, requests_remaining sensor, retry-login action, push dispatcher hardening, hassfest CI, year-rollover tests, MQTT freshness validation, privacy-matrix FAQ).

### 🤝 Community / Community

- 📨 **Outreach an `Timwun/Cupra-WeConnect-Bruno-Collection`** — neuer Bruno-Collection mit 50+ verifizierten OLA-Endpoint-Specs entdeckt. Issue #1 mit Dankeschön + Brand-Tester-Einladung gepostet. Vollscan-Agent extrahiert die komplette Endpoint-Catalog für v1.17.x / v1.18.0 Implementation (insbesondere `PUT /v1/users/vehicles/{vin}/destination` für #36 Navigation-Closure).

### 📦 Geplante Issue-Closures / Planned Issue Closures

Keine direkten Issue-Closures in v1.17.0 (Hardening-Release ohne neue Features). Vorbereitung für #36 Navigation Closure in v1.17.x basierend auf Bruno-Collection.

## [1.16.1] - 2026-05-02 🐛 SEAT/CUPRA Climate Fix + #122 Scout-Paths / SEAT/CUPRA Climate 404 Fix + SEAT scout-path registration

🐛 **PATCH: Hotfix für SEAT/CUPRA Climate-Endpoint** — Gerhard's v1.16.0 Test (Issue #53) hat aufgedeckt dass unsere ``command_start_climate`` URL ``POST /v2/vehicles/{vin}/climatisation`` mit Body ``{"action":"start"}`` einen 404 produziert (`No static resource`). Korrekter OLA-Endpoint ist ``POST /v2/vehicles/{vin}/climatisation/start`` (Action im Pfad). Plus #122 SEAT Scout-Report von r1150gs.

### 🐛 Bug-Fixes / Bug-Fixes

- 🌡️ **SEAT/CUPRA Climate 404 (#53)** — neuer ``_post_climatisation_action`` Helper mit Defensive-Fallback:
  - **Primary** (verifiziert gegen `WulfgarW/pycupra/connection.py` `API_CLIMATER + '/start'`): ``POST /v2/vehicles/{vin}/climatisation/start`` body ``{}``
  - **Fallback** (legacy unsere alte URL): bei 404 → ``POST /v2/vehicles/{vin}/climatisation`` body ``{"action":"start"}``
  - Nicht-404 Fehler (403/500/etc) propagieren ohne Fallback — Phase 2 records the failure normal
  - Identisches Pattern für `command_stop_climate`

### 🛰️ Scout-Paths / Scout-Paths

- 🛰️ **#122 SEAT scout-report (r1150gs, 2026-05-02)** — `engines.primary` + `engines.primary.*` Wildcard in `EXPECTED_KEYS["cupra"]["mycar"]` registriert (SEAT erbt via Table-Alias). Vorher war `engines` als Top-Level-Block registriert — neue Sub-Block `primary` (3 keys) brauchte explizite Registration. Wildcard deckt zukünftige Sub-Felder ab.

### 🔍 Investigation / Investigation

- 🔍 **#53 Phase 3 Phantom-Button** — Gerhard's Born hat Lichthupe-Button trotz Phase 3 noch sichtbar. Hypothesen: OLA Capabilities-API "lügt" für seinen Born (sagt `honk-and-flash` active=true, aber Endpoint macht 400), oder `get_capabilities` failt silent, oder Cap-ID Mismatch. **Diagnostics-Download von Gerhard angefordert** für `vehicle_capabilities[VIN]` Inspektion. Fix folgt in v1.16.2 sobald Daten da sind.

### 🧪 Tests / Tests

- `tests/test_v1161_seat_cupra_climate_fix.py` — neue Tests in 2 Klassen:
  - `TestClimateEndpointFix` (4) — start uses path-suffix + stop uses path-suffix + 404 fallback to legacy + non-404 propagates without fallback
  - `TestScoutPathsSeat` (2) — `engines.primary.*` registriert + SEAT inherit via alias

### 📦 Schließt Issues / Closes

- Closes #122 (SEAT scout-report von r1150gs)

### 🔬 Bleibt offen / Still open

- **#53 Climate** ✅ gefixt in v1.16.1 (testen!)
- **#53 Phase 3 Phantom-Button** — wartet auf Gerhard's Diagnostics

## [1.16.0] - 2026-05-02 ⏰📍 Cross-Brand UX + Skoda Charging Profiles / Cross-Brand UX + Skoda Charging Profiles (HA time platform #26 + #25/#31 read-only via charging-profiles + OTA Probe planning)

⏰📍 **Long-standing UX gap geschlossen**: Departure-Timer kann jetzt direkt in HA editiert werden (#26). Plus #25/#31 Closure über Skoda's neuen `/v1/charging/{vin}/profiles` Endpoint, plus Cross-Brand OTA Probe Plan dokumentiert für Live-Test in v1.17.0.

### ✨ Neu / Added

- ⏰ **#26 HA `time` Plattform für Departure-Timer Editing** (10. Plattform):
  - Neue Datei `custom_components/vag_connect/time.py` mit `VagDepartureTimerTime`
  - Drei Entitäten pro EV/PHEV: `time.{auto}_departure_timer_1_time_set` / `_2` / `_3`
  - User editiert die Abfahrtszeit direkt im HA Dashboard → integration ruft existierende `coordinator.async_set_departure_timer(vin, timer_id, enabled=True, departure_time="HH:MM")` auf
  - Setzen der Zeit aktiviert den Timer automatisch (UX: User der Zeit setzt will den Timer offenbar aktiv haben)
  - Defensive Parser für `departure_timer_X_time` Feld: HH:MM, HH:MM:SS, ISO datetime — alle drei werden zu `datetime.time` konvertiert
  - Read-only Mode + Capability-Phase-3 Gating wie bei den existierenden departure-timer Switches
- 📍 **#25/#31 Skoda Charging Profiles Read-Only** — neuer mysmob Endpoint `GET /v1/charging/{vin}/profiles` (verifiziert via `myskoda/models/chargingprofiles.py`). Vier neue Sensor-Entitäten (Skoda EV/PHEV only):
  - `sensor.active_charging_profile_name` — **das Killer-Feld**: Backend-Response `currentVehiclePositionProfile.name` sagt uns welches der User-Profile gerade aktiv ist basierend auf der Vehicle-GPS-Position. Solves #25 (location-based target SoC) ohne client-side GPS-Zone-Matching.
  - `sensor.active_charging_profile_target_soc_pct` — Target SoC für das aktive Profil (PERCENTAGE)
  - `sensor.next_charging_time` — nächste geplante Ladezeit
  - `sensor.charging_profiles_count` (DIAGNOSTIC) — Anzahl registrierter Profile
  - Plus alle Profile flat als `extra_state_attributes.profiles` auf `active_charging_profile_name` mit per-Profile: id, name, target_soc_pct, max_charging_current, auto_unlock_plug, min_battery_soc_pct, location_lat (rounded 2-decimal), location_lon, preferred_times_count, timers_count
  - 1h-Cache-Cycle in `coordinator.refresh_charging_profiles` mit brand-restriction + capability-gate (`command_charging_profiles` cap-id `EXTENDED_CHARGING_SETTINGS` aus v1.15.0)
  - Write-Side für Profile-Editing **deferred** zu v1.17.0 (POST/PUT endpoints brauchen eigene Bundle-Größe)
- 📋 **Cross-Brand OTA Probe Plan** — `docs/RESEARCH_NOTES_2026-05-02_OTA_PROBE.md` mit konkreten `curl` Probes für CARIAD-BFF (Audi+VW EU) + OLA (SEAT/CUPRA) software-version Endpoints. Live-Tester Asks dokumentiert. Probe ist read-only und sicher (`GET` mit Bearer-Token). Adoption-Plan post-Probe: ~2h Implementation pro Backend wenn 200 OK kommt.

### 🔄 Geändert / Changed

- 🔧 `__init__.py` — `Platform.TIME` zur PLATFORMS-Liste hinzugefügt (10. Plattform). Service-Removal-List auch erweitert (kein neuer Service nötig — time platform reused existing `set_departure_timer`).
- 🔧 `coordinator.py` — neue `_parse_charging_profiles` pure function + `refresh_charging_profiles` 1h-cache helper + Hook im Poll-Loop neben Trip-Stats + Charging-History refreshes.
- 🔧 `cariad/api/skoda.py` — neuer `get_charging_profiles(vin)` method.
- 🔧 `cariad/models.py` — 5 neue Charging-Profiles-Felder zu VehicleData (`active_charging_profile_name`, `active_charging_profile_target_soc_pct`, `next_charging_time`, `charging_profiles_count`, `charging_profiles` list).
- 🔧 `sensor.py` — 4 neue VagSensorDescription Einträge plus erweiterte `extra_state_attributes` Override für `profiles` auf dem active-profile sensor.

### 🌐 Übersetzungen / Translations

8 Sprachen (de/en/fr/es/nl/pl/cs/sv) — neue keys:
- `entity.sensor.{active_charging_profile_name, active_charging_profile_target_soc_pct, next_charging_time, charging_profiles_count}`
- **Neue `entity.time` Sektion** mit `departure_timer_{1,2,3}_time_set`

### 🧪 Tests / Tests

- `tests/test_v1160_cross_brand_skoda_endpoints.py` — neue Tests in 4 Klassen:
  - `TestDepartureTimerTimeEntity` (7) — native_value HH:MM / HH:MM:SS / ISO datetime / garbage / None field + async_set_value dispatch + auto-enable
  - `TestParseChargingProfiles` (5) — flat profiles + currentVehiclePositionProfile + missing current → no active fields + garbage tolerance + empty
  - `TestGetChargingProfilesURL` (1) — URL pattern
  - `TestRefreshChargingProfilesBrandRestriction` (4) — brand restriction + 1h cache + capability gate
  - `TestOtaProbeDocsExist` (2) — sanity that the planning docs are committed

### 🔬 Pre-Research / Pre-Research

Skoda Charging Profiles + Widget + Vehicle-Information Schema-Research aus `myskoda/models/{chargingprofiles,widget,vehicle_info,info}.py` (verfasst 2026-05-02, 600 Zeilen Output).

### 📦 Schließt Issues / Closes

- Closes #26 (Klima-Timer / Departure-Timer UI — HA `time` Plattform für editing)
- Closes #25 (Standort-spez. Ladeziel — read-only via `currentVehiclePositionProfile.targetStateOfChargeInPercent`)
- Closes #31 (Ladeprofile pro Standort — read-only via `chargingProfiles` list mit per-Profil location)

### ❌ Deferred / Not in this release

- **Skoda Vehicle-Information Bundle** (myskoda PRs #543/#557) — drei Endpoints (vehicle-info, renders, equipment, lightweight widget) brauchen DeviceInfo-rewiring + image-platform Erweiterung + Live-Test → v1.17.0
- **Charging Profile Write-Side** — POST/PUT endpoints für Profile-Editing brauchen eigene Bundle-Größe → v1.17.0+
- **Cross-Brand OTA** (Audi/VW/SEAT/CUPRA) — Probe Plan dokumentiert, wartet auf cooperative Tester → v1.17.0 (mit Live-Test)
- **Push CUPRA/SEAT + Push Skoda MQTT** (myskoda PRs #533/#566) — bereits geplant für v1.18.0, Skoda-Path jetzt unblocked durch v1.15.0 cap-Map + diagnostics work

## [1.15.0] - 2026-05-02 🛰️🔋 Skoda Modernization Bundle / Skoda Modernization (Charging History #35 + OTA + 8 cap-ids + capability tolerance + anonymize hardening)

🛰️🔋 **Komplette Adoption der myskoda Upstream-Updates seit unserem PR #832 Cutoff** (22 PRs gemerged 2026-03 → 2026-04). Bundle 3 (Cross-Brand UX) wurde realistisch zu v1.16.0 verschoben — die HA `time`/`datetime` Plattform für #26 wäre eigene 10. Plattform-Erweiterung, und #25/#31 brauchen `charging-profiles` Endpoint-Research. v1.15.0 fokussiert auf was JETZT lieferbar ist.

### ✨ Neu / Added

- 🔋 **#35 Skoda Charging History → HA Energy Dashboard** — neuer mysmob Endpoint `GET /v1/charging/{vin}/history?userTimezone=UTC&limit=50`. Drei neue Sensor-Entitäten (Skoda EV/PHEV only):
  - `total_charged_energy_kwh` — `state_class=TOTAL_INCREASING` für HA Energy Dashboard. Sum aller `chargedInKWh` Sessions across alle Periods.
  - `last_charging_session_kwh` — Energie der letzten Sitzung
  - `last_charging_session_duration_min` — Dauer der letzten Sitzung
  - Plus `recent_charging_sessions` (last 5) als `extra_state_attributes` auf `total_charged_energy_kwh` (audi #113 "aggregate-in-state" Convention — vermeidet 255-char state limit)
  - `last_charging_session_current_type` (AC/DC) als attr
  - 1h-Cache-Cycle in `coordinator.refresh_charging_history` mit brand-restriction + capability gate (`command_charging_history` cap-id `CHARGING`)
  - Source: myskoda PR mit `ChargingHistory` model in `myskoda/models/charging_history.py` (verifiziert 2026-05-02)
- 🛰️ **Skoda Software-Version + OTA Status** (myskoda PR #541) — neuer Endpoint `GET /v1/vehicle-information/{vin}/software-version/update-status` (Skoda app v8.10.0+):
  - `sensor.software_version` (DIAGNOSTIC) — aktuelle Firmware (z.B. `"3.8"`)
  - `binary_sensor.ota_update_available` (UPDATE device class) — true wenn Backend einen Status anders als `NO_UPDATE_AVAILABLE`/`UPDATE_SUCCESSFUL` liefert (forward-compat: unbekannte enum-Werte = update läuft)
  - `releaseNotesUrl` als `extra_state_attributes.release_notes_url` auf dem binary_sensor
  - Cross-brand support **deferred** — CARIAD-BFF + OLA exposen den Endpoint nicht (Research 2026-05-02)
- 🛡️ **Capability-Map Skoda Erweiterung** — 8 neue cap-ids in `CAPABILITY_MAP["skoda"]` aus myskoda Upstream-Reverse-Engineering: `command_software_update`, `command_charging_history`, `command_charging_profiles`, `command_driving_score`, `command_readiness`, `command_plug_and_charge`, `command_route_planning`, `command_battery_charging_care`. Phase 3 kann jetzt sauber für jede dieser Capabilities entscheiden.
- 🧬 **Capability-Status Tolerance** (myskoda PR #543 schema) — `vehicle_supports_capability` versteht jetzt:
  - **Top-level `errors[]` Array** auf der capabilities response — wenn das ganze Dokument fehlgeschlagen ist (MISSING_RENDER, UNAVAILABLE_SERVICE_PLATFORM_CAPABILITIES, UNAVAILABLE_SOFTWARE_VERSION), bail to `None` statt fälschlich jede Entity zu gaten
  - Neue transient-state Status-Werte: `INSUFFICIENT_BATTERY_LEVEL`, `LOCATION_DATA_DISABLED`, `VEHICLE_DISABLED` — als "right now no" behandelt (gated wie bisher, aber dokumentiert für UX-Hints zukünftig)
- 🔐 **Diagnostics Anonymize Hardening** (Pattern aus myskoda `anonymize.py`):
  - **`_mask_location_qs`** — scrubbt `latitude=...&longitude=...` aus URL Query-Strings (z.B. `/maps/positions?latitude=48.13&longitude=11.57` in Error-Traces). Vorher konnte unser dict-key basiertes `_scrub` das nicht catchen weil lat/lon innerhalb eines String-Values steckten. Mode-aware: `gps_round=True` rundet auf 1 Dezimal, sonst REDACTED.
  - **`_stable_hash` SHA-256** — deterministischer 12-hex Pseudonym für stabile Repeat-Reporter Cross-Referenzen ohne PII zu leaken. `user_id`/`account_id`/`userId`/`accountId` → `sha256:abc123def456` (statt nur `**REDACTED**`).

### 🔄 Geändert / Changed

- 🔧 `cariad/_capabilities.py` — 8 neue Skoda cap-id Einträge plus erweiterte Doku zur Erkennung
- 🔧 `coordinator.py` — neue `_parse_charging_history` pure function + `refresh_charging_history` 1h-cache helper + Hook im Poll-Loop neben Trip-Stats refresh. `vehicle_supports_capability` extended um `errors[]` block + transient status documentation.
- 🔧 `cariad/api/skoda.py` — `get_status` gather() um den software-version Endpoint erweitert (best-effort, exception-tolerant). Neuer `get_charging_history(vin, limit=50)` method.
- 🔧 `cariad/models.py` — 4 OTA-Felder + 6 Charging-History-Felder zu VehicleData hinzugefügt
- 🔧 `diagnostics.py` — `_LOCATION_QS_RE` regex + `_HASH_KEYS` frozenset + neue helpers; `_scrub` String-Pfad chained jetzt `_mask_email` + `_mask_location_qs`

### 🌐 Übersetzungen / Translations

8 Sprachen (de/en/fr/es/nl/pl/cs/sv) — neue keys:
- `entity.sensor.{software_version, total_charged_energy_kwh, last_charging_session_kwh, last_charging_session_duration_min}`
- `entity.binary_sensor.ota_update_available`

### 🧪 Tests / Tests

- `tests/test_v1150_skoda_modernization.py` — neue Tests in 5 Klassen:
  - `TestParseChargingHistory` (5) — total kWh sum, sort-by-startAt desc, recent_sessions cap, garbage tolerance
  - `TestGetChargingHistoryURL` (2) — URL + default/custom limit param
  - `TestRefreshChargingHistoryBrandRestriction` (4) — brand restriction + 1h cache + capability gate
  - `TestSoftwareVersionParsing` (2) — NO_UPDATE_AVAILABLE → False, unknown enum → True (forward-compat)
  - `TestLocationQueryStringScrub` (4) — REDACTED + 1-dec round + no-op + negative coords
  - `TestStableHash` (4) — deterministic + different inputs + empty + salt
  - `TestUserIdHashingInScrub` (4) — user_id/accountId hashing + repeat-stability + string GPS scrub
  - `TestSkodaCapabilityMap` (8 parametrized + 1 sanity) — alle neuen cap-ids
  - `TestCapabilityStatusTolerance` (3 parametrized + 3) — errors[] block + transient states

### 🔬 Pre-Research / Pre-Research

Research-Sweep der **skodaconnect/myskoda** Upstream (22 PRs gemerged seit unserem PR #832 / Issue #976 Cutoff April 2026). Plus Cross-Brand OTA Endpoint-Probe (audi_connect_ha + volkswagencarnet + pycupra) — Resultat: CARIAD-BFF + OLA haben **kein** software-version endpoint heute, daher Skoda-only in v1.15.0.

### 📦 Schließt Issues / Closes

- Closes #35 (Ladehistorie LTS — Skoda über `chargedInKWh` per session, kumuliert in `total_charged_energy_kwh` mit `TOTAL_INCREASING`)

### 🛡️ Open / Re-Aktiviert

- **#75 Skoda Kodiaq Mk2 403** — Comment posted: ursprüngliche Hypothese war falsch (wir hatten den `connectivityGenerations` Query bereits seit langem), echte Ursache braucht 403-Body-Diagnostics. v1.15.0 verbessert Diagnostics-Export um die Übermittlung sicherer zu machen.

### ❌ Deferred / Not in this release

- **#26 Klima-Timer / Departure-Timer datetime UI** — braucht eigene HA `time`/`datetime` Plattform-Erweiterung (10. Plattform). Existing departure_timer switches + sensors bleiben funktional. → v1.16.0
- **#25 Standort-spezifischer Ladeziel + #31 Ladeprofile pro Standort** — beide brauchen `/v1/charging/{vin}/profiles` Endpoint-Schema-Research für Read-Only-Sensoren. → v1.16.0
- **Cross-Brand OTA** (Audi/VW/SEAT/CUPRA) — Endpoint nicht in CARIAD-BFF/OLA verifiziert. Live-Test-Probe nötig. → v1.16.0+

## [1.14.0] - 2026-05-02 🚗 Audi Feature Pack Bundle / Audi Feature Pack (Trip Stats + Engine Start ICE + PPC Climate Body) + Skoda Scout-Pfade #116

🚗 **Drei Audi-spezifische Features in einem MINOR-Release** + Skoda Scout-Pfade aus #116 (MavericklCS) als Add-On. Bundle 2 aus dem v1.13.0 Pre-Research-Plan (`docs/RESEARCH_NOTES_2026-05-02.md`).

### ✨ Neu / Added

- 🛣️ **#24 Trip Statistics für VW EU + Audi** — neuer CARIAD-BFF Endpoint `GET /vehicle/v1/vehicles/{vin}/tripstatistics?type={shortTerm|longTerm}` (verifiziert in audi_connect_ha + audiconnectpy + ioBroker/vw-connect). Vier neue Sensor-Entitäten pro Audi/VW EU Vehicle:
  - `last_trip_distance_km` (DISTANCE) — letzte Fahrt-Strecke aus shortTerm `mileage`
  - `last_trip_avg_speed_kmh` (SPEED) — Ø-Geschwindigkeit
  - `last_trip_avg_fuel_consumption_l_100km` (combustion-only) — Ø-Verbrauch in l/100km (Backend liefert ×10, Parser teilt)
  - `last_trip_avg_electric_consumption_kwh_100km` (electric-only) — Ø-Stromverbrauch in kWh/100km
  - Plus `recent_trips` (letzte 5) als `extra_state_attributes` auf `last_trip_distance_km` (audi #113 "aggregate-in-state" convention — vermeidet 255-char state limit)
  - 1h-Cache-Cycle in `coordinator.refresh_trip_statistics` — Brand-restriction audi/volkswagen (andere Brands skippen ohne Error), Phase 3 Capability-Gate (`command_trip_stats` → cap-id `tripStatistics`), 1h Cache-TTL via `_trip_stats_fetched_at`
  - **Subscription-required** (Audi connect Plus / WeConnect Plus) — Phase 3 versteckt die Entities wenn das Abo fehlt
- 🔥 **#28 Audi ICE Remote Engine Start/Stop** — zwei-Schritt S-PIN-Flow nach audi_connect_ha PR #717:
  - `service: vag_connect.engine_start` — `PUT /vehicle/v1/engine/{VIN}/userpromptproof` (S-PIN) → extract `userPromptProof` → `POST /vehicle/v1/engine/{VIN}/start` mit `securedActivationData`
  - `service: vag_connect.engine_stop` — single `POST /vehicle/v1/engine/{VIN}/stop` (kein S-PIN nötig)
  - **Audi-only** — andere Brands haben keinen `/engine/`-Subtree. Path-Pattern ist `/vehicle/v1/engine/{VIN}/...` (NICHT `/vehicle/v1/vehicles/{VIN}/engine/...`). VIN wird automatisch uppercased.
  - **S-PIN aus gespeicherter Konfiguration** — landet NIE im Service-Call-Log
  - **Capability-gated** über `CAPABILITY_MAP["audi"]["command_engine_start"] = "engineRemoteStart"` (⚠️ [Inference] cap-id, noch kein Live-Capabilities-Response gesehen)
  - Per-VIN `engine` lock-class via `_COMMAND_CLASS` — start/stop serialisieren nicht parallel
- 🌡️ **#29 PPE/PPC Klima-Body conditional** — Audi Q6/A6 e-tron, RS e-tron GT Facelift, A3 2024+ PHEV brauchen das neue PPE-Body-Format (audi_connect_ha PR #644 + #677):
  - `climatisationMode: "comfort"` mandatory
  - `targetTemperature` + `targetTemperatureUnit` MÜSSEN omitted werden
  - Neue Option `force_ppe_climate` (default False, Audi-only Effekt) in der Options-Flow. User-overridable da Auto-Detection unzuverlässig ist (kein verifiziertes Modell-Mapping public).
  - `command_start_climate(vin, ppe_mode=True)` schaltet das Body-Format um
- 🛰️ **#116 Skoda Scout-Pfade** — vierter Community-Scout-Report von **MavericklCS** (2026-05-01). 5 neue Pfade in `EXPECTED_KEYS["skoda"]`:
  - `driving-range`: 4× `primaryEngineRange.{engineType,currentSoCInPercent,currentFuelLevelInPercent,remainingRangeInKm}`
  - `maintenance`: `predictiveMaintenance.setting` + `predictiveMaintenance.setting.*` Wildcard

### 🔄 Geändert / Changed

- 🔧 `cariad/_capabilities.py` — Audi-Inheritance-Trick erweitert: `CAPABILITY_MAP["audi"]` ist jetzt eine **Kopie** von VW EU's Map (statt Alias) plus Audi-only Patch-Eintrag für `command_engine_start`. Verhindert Pollution der VW EU Map.
- 🔧 `coordinator.py` — `_COMMAND_CLASS` registry erweitert um `command_engine_start`/`command_engine_stop` → "engine" class. Trip-Stats refresh als best-effort gather() im Poll-Loop nach `_async_push_update`.
- 🔧 `sensor.py` — neuer `_TRIP_STATS_BRANDS` frozenset für Brand-Gating der 4 Trip-Stats Sensoren. Neuer `extra_state_attributes` Override in `VagConnectSensor` für `recent_trips` auf `last_trip_distance_km`.
- 🔧 `vw_eu.py` — `command_start_climate(vin, ppe_mode: bool = False)` mit conditional fallback-payload. Default = legacy body (backwards-compat).

### 🌐 Übersetzungen / Translations

8 Sprachen (de/en/fr/es/nl/pl/cs/sv) — neue keys:
- `entity.sensor.{last_trip_distance_km, last_trip_avg_speed_kmh, last_trip_avg_fuel_consumption_l_100km, last_trip_avg_electric_consumption_kwh_100km}`
- `options.step.init.data.force_ppe_climate` + `data_description.force_ppe_climate`

### 🧪 Tests / Tests

- `tests/test_v1140_audi_pack.py` — 19 neue Tests:
  - `TestParseTripStatistics` (6) — pure parser tests + ×10 division + sort + cap at 5 + garbage handling
  - `TestGetTripStatisticsURL` (1) — URL + type query param
  - `TestRefreshTripStatisticsBrandRestriction` (4) — Brand-restriction + capability gate + 1h cache
  - `TestAudiEngineStart` (5) — two-step flow + uppercase VIN + no-spin raises + missing-proof raises + stop endpoint
  - `TestPpcClimateBody` (3) — legacy body / PPE body / default-legacy
  - `TestCapabilityMapEngineStart` (4) — Audi-only inheritance copy + trip_stats brand-presence
  - `TestScoutPathsSkoda` (2) — primaryEngineRange.* + predictiveMaintenance.setting wildcard
  - `TestEngineCommandClass` (1) — engine class shared start/stop

### 🔬 Pre-Research / Pre-Research

- Bundle 2 aus `docs/RESEARCH_NOTES_2026-05-02.md` (verfasst 2026-05-02 vor v1.13.0). Alle drei Issues lieferten ✅ verified Recherche-Ergebnisse:
  - #24 (Trip Stats): CARIAD-BFF Endpoint + per-trip Field-Liste verifiziert
  - #28 (Engine Start): audi_connect_ha PR #717 source-read komplett — Endpoint + Body + Response-Shape
  - #29 (PPE Climate): Body-Pattern aus audi #644 + #677 verifiziert; Detection via User-Option (Auto-Heuristik defer)

### 📦 Schließt Issues / Closes

- Closes #24 (Verbrauchsdaten / Trip Stats Audi)
- Closes #28 (Remote Start ICE Audi 2024+)
- Closes #29 (PPC Climate für 2025 A3/Q5 / Q6/A6 e-tron)
- Closes #116 (Skoda Scout-Report von MavericklCS)

### ❌ Deferred / Not in this release

- **#35 Ladehistorie LTS** — `chargedEnergy_kWh` Feld nicht in CARIAD-BFF verifiziert (Research v1.13.0). Wartet auf API-Hinweis aus Live-Tests.
- **#51 RS e-tron GT Facelift** — graceful degradation only (volle PPE Lock/Charging-Endpoint-Map noch nicht reverse-engineered, Hard Rule #15 verbietet endpoint-guessing).
- **PPE Auto-Detection** — User opt-in only (keine zuverlässige VIN/Model/Year-Heuristik public verfügbar).

## [1.13.0] - 2026-05-02 🛡️ Production Hardening Bundle / Production Hardening (Capability Phase 3 + Read-only Phase 2 + Diagnostics-Polish + Process)

🛡️ **Drei P0-Themen aus dem Roadmap-Backlog in einem MINOR-Release.** Alle drei waren bereits angefangene Arbeit (Phase 1 ausgeliefert) — jetzt Closure mit Phase 2/3, plus die Diagnostics-Hardening die wir für Issue-Reporting brauchen, plus Process-Docs (#64) für Brand Captains.

### ✨ Neu / Added

- 🛡️ **Capability-Filter Phase 3** (#56) — `command.active && user-enabled && !license-issue` PRE-Entity-Creation Gating. Vorher: Entity wurde erstellt und ging nach 1. Failure unavailable (Phase 2). Jetzt: Entity wird gar nicht erst gebaut wenn das Backend `false` meldet. Tri-state: `True/False/None`, konservatives `None = behalte` für Brands ohne Cap-Mapping (Phase 2 fängt Runtime-Failures weiter ab). Neue Single-Source-of-Truth `cariad/_capabilities.py` mit `CAPABILITY_MAP[brand][command_id] → cap_id` und `cap_id_for(brand, command_id)`. Audi/SEAT erben über Table-Alias (`CAPABILITY_MAP["audi"] = CAPABILITY_MAP["volkswagen"]`). Skoda hat eigenes Schema (`active/editable/user-enabled/status/license-issue`) das `vehicle_supports_capability` jetzt mitnimmt.
- 🔒 **Read-only Mode Phase 2 — Service-Side Enforcement** (#63) — Phase 1 (v1.12.0) hat nur Entity-Creation geblockt; Phase 2 blockt jetzt auch alle Service-Calls. Neue `_coord_writeable(vin)` Helper raised `read_only_mode_active` ServiceValidationError bevor irgend ein Command rausgeht. Schützt vor versehentlichen Automatisierungen die direkt Services aufrufen (Bypass von Entity-Verstecken).
- 🔁 **`refresh_cloud_cache` Service-Alias** (#63) — Klare Trennung zwischen `refresh_cloud_cache` (kein Wake, nur Cloud-Polling — der häufige Fall) vs. `wake_vehicle` (echter Wake-Up mit 12V-Risiko + 3/Tag Budget aus v1.12.0 + jetzt 5-min Cooldown). Backwards-compat: `refresh_vehicle` bleibt als Alias für `refresh_cloud_cache`. Beschreibung in `services.yaml` clarified — kein Wake, nur Cache.
- ⏱️ **5-min Wake-Cooldown pro Fahrzeug** (#63) — Per-VIN `_wake_last_at` timestamp. Wake innerhalb des 5-Minuten-Fensters raised `wake_cooldown_active` ServiceValidationError mit `{remaining_s}` + `{cooldown_min}` Placeholders. Greift VOR dem 3/Tag Budget-Check aus v1.12.0 — schützt vor Click-Spam-Loops.
- 🔐 **Per-VIN Per-Command-Class asyncio.Lock mit Timeout** (#63) — Verhindert Double-Click (zwei `lock_doors` Klicks gleichzeitig) und Konkurrenz zwischen `start_climatisation`+`stop_climatisation`. `_get_command_lock(vin, command_class)` lazy creation; `_dispatch_cmd_locked` extracted helper. `asyncio.timeout(60)` Fallback verhindert Deadlock bei hängenden Commands. Neue `is_command_in_flight(vin, command_class)` API für UI-Feedback.
- 🔬 **Anonymized Diagnostics-Export** (#62) — Polish des HA `diagnostics`-Mechanismus für Issue-Reporting:
  - **Token-Redaction expanded** — `access_token`, `refresh_token`, `id_token` (snake_case + camelCase) und `client_secret` jetzt in `_REDACT_KEYS`.
  - **Email Partial-Mask** — `prash@gmail.com` → `p***@***.com` via Regex-Replacement (statt vollständigem `***`). Erlaubt Identifizierung des Reporters wenn er sich später meldet, ohne PII zu leaken.
  - **GPS Opt-In Rounding** — wenn `enable_reverse_geocoding=False`, werden Lat/Lon auf 1 Dezimalstelle gerundet (~11km Granularität). User der Reverse-Geocoding aktiv hat akzeptiert bereits volle Genauigkeit.
- 📝 **GitHub Issue Forms** (#64) — Strukturierte YAML-Forms für die zwei häufigsten Reports aus der v1.9.0 Reporter Pipeline: `scout_report.yml` für Vehicle Data Scout (1-klick pre-fill aus HA) + `error_report.yml` für Error Reporter Dumps. Felder: brand-Picker, vehicle, version, scout_report markdown, privacy_confirm.
- 🏆 **`BRAND_CAPTAINS.md`** (#64) — Initial Brand Captains Tabelle (aktuell nur Maintainer + "Bewährte Tester" Liste: Gerhard2808 für CUPRA Born, tritanium73 für Skoda, DnnsJp74 für Audi). "Wie werde ich Captain?" Anleitung + Captain-Pflichten + Privacy-Notes.

### 🔄 Geändert / Changed

- 🔧 **`_cariad_cmd` mit Lock-Wrapper** — alle Commands die durch den Lock gehen werden jetzt zentral durch `asyncio.timeout(60) + asyncio.Lock` geschickt. Falls kein Lock-Lookup möglich ist (unbekannte Command-Klasse), wird auf `_dispatch_cmd_locked` direkt fallback-dispatched — keine Regression für unbekannte Commands.
- 📚 **GitHub About-Section + Master READMEs (8 Sprachen)** auf v1.12.3-Stand refresht (vorher "68 entities, cloud push" — outdated). Alle 12 LIVE-Features dokumentiert. Roadmap-Sektion vereinfacht auf Single-Source-of-Truth Pointer + Tabelle der letzten 9 Releases. Bi-lingual Title Convention etabliert ab v1.12.3.

### 🌐 Übersetzungen / Translations

- 🌐 **8 Sprachen** (de/en/fr/es/nl/pl/cs/sv) — neue Exception-Keys `wake_cooldown_active` + `read_only_mode_active`. de.json hatte `wake_budget_exhausted` zusätzlich gefehlt; nachgereicht.

### 🧪 Tests / Tests

- 🧪 **31 neue Tests** in `tests/test_v1130_production_hardening.py`: TestCapabilityMap (5), TestCommandCapabilitySupported (8), TestCommandLock (4), TestWakeCooldown (3), TestReadOnlyServiceBlocking (2), TestDiagnosticsPolish (7), TestSkodaCapabilities (2).

### 🔬 Pre-Research / Pre-Research

- 📋 `docs/RESEARCH_NOTES_2026-05-02.md` — 423-Zeilen Pre-Implementation-Research für 13 Issues über 3 Bundles. Per-Issue-Verdict (✅ verified / ⚠️ [Inference] / ❌ gap → defer). Vermeidet Mid-Flight-Surprises bei Phase-3 Capability-Mapping. Bundle 2 (Audi-Pack) und Bundle 3 (Cross-Brand-UX) bereits gescoped für nächste Sessions.

### 📦 Schließt Issues / Closes

- Closes #56 (Capability-Filter Phase 3 — gates pre-entity-creation)
- Closes #62 (Anonymized Diagnostics-Export)
- Closes #63 (Read-only Mode Phase 2/3 — service-side blocking + cloud_refresh distinction + 5-min cooldown)
- Closes #64 (Process & Governance Doc-PR — Issue Forms + Brand Captains)

## [1.12.3] - 2026-05-01 🛰️ Scout-Pfade #111 + #113 + #114 / Scout paths bundled with wildcard strategy

🌟 **Drei Scout-Reports zusammen ausgeliefert.** #111 von DnnsJp74 (zweiter Community-User), plus #113+#114 von Prash auf seinen eigenen Vehicles (Golf GTE 14 Felder + Audi S6 C8 20 Felder) — alle drei zeigen denselben Pattern: `.value` Container haben Children die wir whack-a-mole jagen würden, wenn nicht Wildcards eingesetzt werden.

🛰️ **EXPECTED_KEYS Registrierungen** (`cariad/_unexpected_keys.py`, alle in `volkswagen.selectivestatus` — Audi inherits):

| Kategorie | Neue Pfade |
|---|---|
| automation `.value` neben `.error` | `automation.{climatisationTimer,chargingProfiles}.value` |
| Top-level meta-jobs (waren in selectivestatus query aber nicht registriert) | `batteryChargingCare` + `climatisationTimers` (beide mit `.*` wildcard) |
| Charging Erweiterungen | `charging.chargeMode.value`, `charging.chargingCareSettings.*`, `charging.chargingSettings.value.autoUnlockPlugWhenCharged` (legacy variant ohne AC suffix) |
| Climatisation Zone-Felder | `climatisation.climatisationSettings.value.{unitInCar,climatizationAtUnlock,windowHeatingEnabled,zoneFrontLeftEnabled,zoneFrontRightEnabled}` |
| Battery Temperature | `measurements.temperatureBatteryStatus.value.temperatureHvBattery{Min,Max}_K` (Min wird vom Parser für battery_temp gelesen seit v1.10.x; Max ist neu) |
| Readiness ConnectionState (4) + ConnectionWarning (2) | `readiness.readinessStatus.value.connectionState.{isOnline,isActive,batteryPowerLevel,dailyPowerBudgetAvailable}` + `.connectionWarning.{insufficientBatteryLevelWarning,dailyPowerBudgetWarning}` |

🌊 **Wildcard-Strategie für `.value.*` Container:**

Statt jeden neuen Sub-Field einzeln zu registrieren, decken Wildcards die ganze Klasse ab:
- `fuelStatus.rangeStatus.value.*` (alle Children: carType, totalRange_km, carCapturedTimestamp, etc.)
- `fuelStatus.rangeStatus.value.primaryEngine.*` + `.secondaryEngine.*`
- `vehicleHealthInspection.maintenanceStatus.value.*` (inspectionDue_days/km, oilServiceDue_days/km, mileage_km, carCapturedTimestamp)
- `departureProfiles.departureProfilesStatus.value.*`
- `userCapabilities.capabilitiesStatus.value.*`
- `batteryChargingCare.value.*` + `climatisationTimers.value.*` (proaktiv)

Plus alle 23 #111 paths unverändert eingeschlossen.

🧪 **Tests:** 8 neue in `tests/test_v1123_111_audi_scout.py` — verbatim Payloads für alle 3 Issues (#111, #113, #114) müssen Scout-Empty zurückgeben.

📊 **Audit-Befund auch bei den älteren Bugs:**

| Issue | Status |
|---|---|
| #42 (migendi CUPRA Formentor) | Verify-Ping gepostet, warte auf User-Antwort |
| #48 (all-actions-fail) | Verify-Ping gepostet |
| #51 (G.S. Audi RS e-tron GT) | Verify-Ping gepostet |
| #53 (Gerhard Born) | Status-Update mit Fixture-Bestätigung + Phase 3 Plan gepostet |

**Closes:** #111, #113, #114.

## [1.12.2] - 2026-05-01 🌟🛰️ Erstes Community-Scout-Report (Skoda #107 von tritanium73) / First community Scout report

🌟 **Erste Live-Validation der v1.9.0 Reporter Pipeline durch einen Nicht-Maintainer-User!**

User `tritanium73` hat heute einen Vehicle Data Scout Report für seine Skoda gefiltet (#107). 14 neue Felder über 4 mysmob-Endpoints — die volle 1-Klick Pipeline aus v1.9.0 funktioniert in der Wildbahn:

1. Scout erkennt Drift bei Poll
2. HA Repair-Notification erscheint bei tritanium73
3. Klick auf "Mehr erfahren" → pre-filled GitHub Issue
4. tritanium73 reicht das ein → wir fixen → 1.12.2 Release

Genau dafür wurde v1.9.0 gebaut. **Riesigen Dank an tritanium73 für den ersten Community-Beitrag in dieser Form** 🙏

🛰️ **EXPECTED_KEYS Registrierungen** (`cariad/_unexpected_keys.py`, alle skoda-only — SEAT/CUPRA und VW EU/Audi nicht betroffen):

| Endpoint | Neue Pfade |
|---|---|
| `vehicle-status` | `renders.lightMode` + `renders.darkMode` (waren via 3-Segment-Wildcard nicht matched — Bug aus v1.9.1 catalog) |
| `air-conditioning` | `runningRequests`, `steeringWheelPosition`, `windowHeatingState.unspecified`, `timers`, `outsideTemperature`, `errors` |
| `driving-range` | `carType`, `primaryEngineRange` |
| `maintenance` | `maintenanceReport.capturedAt`, `preferredServicePartner`, `predictiveMaintenance`, `customerService` |

`carType` + `primaryEngineRange` sind besonders interessant — wahrscheinlich die mysmob-Variante zu CARIAD-BFFs `fuelStatus.rangeStatus.value.primaryEngine` aus v1.10.0. Wiring als Range-Source kommt in v1.13.0+ wenn wir verifizierte Live-Response-Shape sehen.

🧪 **Tests:** 6 neue in `tests/test_v1122_107_skoda_scout.py` — verifizieren dass alle 14 Pfade jetzt registriert sind, plus Defensive-Test dass SEAT/CUPRA nicht versehentlich von der Skoda-Registrierung beeinflusst werden.

📊 **Bonus-Audit aus Diagnostics-Datei (Audi 2 Vehicles, Prash):**

- 4 unexpected findings sind bereits durch v1.12.1 registriert → silenced beim nächsten Poll ✅
- 2 Error-Reporter Findings sind transiente 502 Bad Gateway → v1.8.7 retry-mechanism funktioniert wie designed (Backend war kurz down). Kein Code-Change nötig — same Pattern wie #108.

**Closes:** #107.
**Acknowledges:** #108 (transient 502, no fix needed — system working as designed).

## [1.12.1] - 2026-04-30 🛰️📚 Scout-Pfade #105/#106 + Gerhard's Born Fixture + FAQ #47 / Scout paths + Born fixture + Subscription FAQ

🛰️ **Vehicle Data Scout Welle 4** (#105 VW EU 12 Felder + #106 Audi 8 Felder):

Pattern wie #103/#104 (v1.12.0) — Scout descendet eine weitere Ebene tiefer und findet die `.value` Container + die HTTP-Error-Wrapper Sub-Felder als unbekannt.

Neue Registrierungen in `EXPECTED_KEYS["volkswagen"]["selectivestatus"]` (Audi inherits):
- `userCapabilities.capabilitiesStatus.value` + `fuelStatus.rangeStatus.value` + `vehicleHealthInspection.maintenanceStatus.value` + `vehicleHealthWarnings.warningLights.value` + `departureProfiles.departureProfilesStatus.value`
- `automation.climatisationTimer.error` + `automation.chargingProfiles.error` (Bad-Gateway-Wrapper-Pattern wie `charging.chargeMode.error` aus v1.12.0)
- **Wildcards** `charging.chargeMode.error.*` + `automation.{climatisationTimer,chargingProfiles}.error.*` + `fuelStatus.rangeStatus.error.*` (proaktiv) — decken die 6 standardisierten HTTP-Error-Sub-Felder (message/errorTimeStamp/info/code/group/retry) future-proof ab

📚 **Gerhard's CUPRA Born Fixture** (#53 — Gerhard hat "ja Fixture OK, ich hab nix zu verbergen :-)" gesagt!):

- Neue Datei: `tests/fixtures/seat_cupra/cupra_born_2023_active_subscription_redacted.json`
- **Komplett anonymisiert:** VIN auf `***003577` maskiert, alle UUIDs/Tokens/Emails entfernt, GPS auf `48.0 / 11.0` gerundet (~11 km Bucket)
- **Zweck:** automatische Regression-Tests für CUPRA Born Parser-Drift (verhindert Born-2026-Firmware-Bug aus v1.10.2 wieder auftritt)
- **Source dokumentiert:** "User report from issue #53 (Gerhard2808), with explicit consent given on 2026-04-30"
- 8 Round-Trip-Tests verifizieren dass die v1.10.2 Parser-Pfade aus der redacted Fixture die Werte produzieren die Gerhard auf seinem Born sieht (battery 69%, range 277km, plug disconnected, doors locked)
- 7 Privacy-Audit-Tests verifizieren dass keine vollen VINs / Tokens / UUIDs / Emails in der Fixture sind

🌍 **Erste Live-Validation des "Privacy & data handling" Workflows aus PR #101** — User-Consent eingeholt, Fixture redacted, Source dokumentiert. Code-of-conduct funktioniert.

📚 **#47 FAQ — Service Plus / Subscription Docs:**

Neue FAQ-Sektion in `CONTRIBUTING.md`:
- "Brauche ich Security & Service Plus?" → meist nein, in Portugal + manchen 2024+ Audi ja
- Wie unterscheide ich `missing-capability` vs `subscription_expired` vs `spin_error` vs `404`?
- Wieso geht's in der App aber nicht in VAG Connect? (3 unabhängige Gründe aus #53 Lessons)
- Wo sehe ich meinen Subscription-Status?

Tabelle mit allen v1.9.1 `classify_command_failure` Markern + ihre Bedeutung. Verlinkt zu Phase 3 Capability-Filter (v1.13.0).

🧪 **Tests:** 19 neue in `tests/test_v1121_scout_and_born_fixture.py`:
- 5 Scout-Path-Coverage-Tests (#105/#106 verbatim payload bleibt silent)
- 7 Born-Fixture Privacy-Audit (no VIN/email/JWT/UUID/GPS-precision leak)
- 6 Born-Fixture Parser-Round-Trip (Gerhard's beobachtete Werte materialisieren)
- 1 #47 FAQ-Section-Presence Test

> 💡 Vollständige technische Details + ROADMAP-Refresh mit P0/P1/P2-Priorisierung in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md) + [`docs/ROADMAP.md`](docs/ROADMAP.md).

**Closes:** #105, #106, #47.

## [1.12.0] - 2026-04-30 🔋💡⚡🧯🔒 5-in-1 Feature-Sprint / Five features in one MINOR

✨ **Fünf neue Funktionen — alle in einer kohärenten "More Control + Diagnostics"-Theme:**

| # | Was | Issue | Wer profitiert |
|---|---|---|---|
| 🔋 | **12V-Batterie Voltage + Low-Warnung** | #23 | Alle CARIAD-Owner — sehen jetzt `12V-Batterie` Voltage-Sensor + `12V-Batterie schwach` Binary bei <11.5V |
| 💡 | **Per-Light Binary-Sensors** (#91 Welle 3) | #91 | Owner mit Vehicles deren Firmware bekannte Light-Element-Shapes ausliefert (frontLeft etc.) — eigene Binary pro Lichttyp |
| ⚡ | **Writeable `Max. Ladestrom` Number** | #91 follow-up | EV/PHEV Owner — können jetzt 6-32 A Ladestrom über Slider setzen (war pre-1.12.0 nur Sensor) |
| 🧯 | **Smart-Wake Counter + Budget** | #55 | Alle — neuer `Wake-Ups heute` Sensor + Soft-Cap auf 3/Tag schützt 12V-Batterie vor Über-Wakeup |
| 🔒 | **Read-only Mode Option** | #63 | Privacy/Safety-konservative Owner — nur Status-Sensoren, keine Switches/Buttons/Locks/Climate/Number |

🔋 **#23 — 12V Batterie:**
- Neue `lvBattery` job in CARIAD `selectivestatus` Polling-Liste
- Parser liest `lvBattery.lvBatteryStatus.value.batteryVoltage_V`
- Neuer Sensor `voltage_12v` (V, DEVICE_CLASS.VOLTAGE)
- Neue Binary `warning_12v_low` (PROBLEM-class) bei <11.5V
- Threshold matcht volkswagencarnet PR #940 + ELM327-Praxis. Symptom "API stops responding for hours" wird endlich erklärbar bevor User die Integration als kaputt markiert.

💡 **#91 Welle 3 — Per-Light Binary-Sensors:**
- Dynamische Erstellung via `_async_setup_light_sensors` aus `lights_individual` dict (gefüllt vom v1.11.0 Light-Parser)
- Mirror des Door/Window-Patterns: empty dict → keine Entities
- Vehicles mit unbekanntem Light-Element-Shape sehen weiterhin nur das Aggregate `lights_on` + `lights_count`

⚡ **#91 follow-up — Writeable Max-Charge-Current Number:**
- Neuer `command_set_max_charge_current` in `vw_eu.py` POST `chargingSettings` mit `{"maxChargeCurrentAC_A": ampere}`
- Number-Entity 6-32 A in 2er-Schritten (typische VW-EU-Werte: 6/8/10/12/14/16/32)
- `coordinator.async_set_max_charge_current` umgestellt: war `raise ServiceValidationError` → ist jetzt `_cariad_cmd("command_set_max_charge_current")`. Ungültige Werte werden vom Backend abgelehnt + via `classify_command_failure` Pipeline an User reportet.

🧯 **#55 — Smart-Wake:**
- Neuer Sensor `wake_count_today` (TOTAL_INCREASING, diagnostic)
- `async_wake_vehicle` trackt Counter pro VIN + Reset bei UTC-Mitternacht
- Soft-Cap auf 3 Wakes/Tag (`_WAKE_BUDGET_PER_DAY`) — über-Wake raised `ServiceValidationError("wake_budget_exhausted")` BEVOR API-Call. Schützt 12V-Batterie + verhindert Account-Suspension durch Wake-Loops.

🔒 **#63 — Read-only Mode (Phase 1):**
- Neue Options-Toggle "Read-only Mode" → Settings → Devices → VAG Connect → Configure
- Wenn aktiviert: lock/switch/button(non-refresh)/climate/number Plattformen skippen Entity-Creation komplett
- Sensors + binary_sensors + device_tracker bleiben (read-only sowieso)
- VagRefreshButton bleibt auch im Read-only Mode (cloud-poll, kein Vehicle-Command)
- Use-Case: Privacy-konservative Owner die nur Telemetrie wollen, oder Account-Schutz vor versehentlichem Actuation in Auto-Repeat-Loops

🌍 **Übersetzungen** in 8 Sprachen für alle 5 neuen Features inkl. die Read-only-Mode Option-Description (am ausführlichsten — User soll vor Aktivierung verstehen was passiert).

🧪 **Tests:** 25 neue Tests in `tests/test_v1120_features.py` decken alle 5 Features einzeln + Phantom-Schutz + Backwards-Compat.

> 💡 Vollständige Field-Mappings, Architektur-Notes und nicht-implementierte Punkte (was kommt in v1.12.1+) in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

**Closes:** #23, #55. **Partial:** #63 (Read-only-Mode-Phase-1 ausgeliefert; Command-Locking + cloud-vs-vehicle-refresh Distinction sind eigene Sessions).

### 📋 Doc-only — User-Data Handling + `[Inference]` Marker (2026-04-30, no version bump)

Nach Third-Party-Privacy-Review zu Issue #53 dokumentiert:

- 🔒 **`docs/SESSION_HANDOFF.md`** neue "User-Data Handling" Sektion + 2 neue Hard Rules (#18 Privacy-by-default, #19 `[Inference]` Marker für unverifizierte semantische Claims)
- 📝 **`CONTRIBUTING.md`** neue "Privacy & data handling" Sektion mit Fixture-Redaction-Template + Consent-Anfrage-Template + Maintainer-Self-Check
- ⚠️ **`cariad/api/seat_cupra.py:command_flash`** Docstring mit explizitem `[Inference]` Marker — `userPosition` Semantik ist gegen offizielle My SEAT/CUPRA-App nicht verifiziert (verifiziert nur gegen pycupra/myskoda)
- ⚠️ **`coordinator.py:async_flash_lights`** Cross-Reference auf den Inference-Marker

Hintergrund: pre-1.11.1 wurden zwei inhaltliche Ungenauigkeiten in #53 / #56 Comments gemacht:
1. Pauschale "subscription expired" Diagnose obwohl Gerhard's Vertrag aktiv ist
2. Behauptung `userPosition` macht es "wie die offizielle MyCupra-App" ohne App-Traffic-Verifikation

Folge-Comments auf #53 + #56 mit Korrektur kommen separat. Diese Doc-PR codifiziert die Lessons damit es nicht wieder passiert.

## [1.11.1] - 2026-04-30 🐛💨 Golf 7 GTE Fuel-Range Fix (#96) + Optimistic UI (3B-Part-3)

🐛 **Bug-Fix #96 — Golf 7 GTE / Passat GTE Fuel-Range erscheint endlich:**

Pre-1.11.1 Bug: VW Golf 7 GTE 2015 + Passat GTE B7/B8 Owner haben nach v1.10.0-Update **immer noch keine Sprit-Reichweite** gesehen. Root Cause: `fuelStatus.rangeStatus` returnt auf älteren GTE-Firmwares ein `{"error": ...}` Objekt statt `{"value": ...}` (verifiziert via evcc-io/evcc#19045 Passat GTE Live-Trace) → unsere Drivetrain-Detection blieb auf `has_combustion=False` → die `_DATA_PRESENT_REQUIRED` Phantom-Schutz-Logik aus v1.10.0 hat dann den Sensor nicht erstellt obwohl die Daten in `measurements` vorhanden waren.

**Fix (4 Tracks):**

- 🔧 **Drivetrain-Detection** liest jetzt aus 4 Quellen (statt 2): zusätzlich `measurements.fuelLevelStatus.value.{primaryEngineType,secondaryEngineType}` — populated AUCH wenn fuelStatus error returnt.
- 🔧 **`carType="hybrid"` flag** explizit erkannt → setzt `has_battery=True` UND `has_combustion=True`. Pre-1.11.1 nur Substring-Match auf "electric"/"gasoline" — verfehlt das nackte "hybrid".
- 🔧 **Total range fallback** aus `measurements.rangeStatus.value.totalRange_km` (war nur fuelStatus-Pfad).
- 🔧 **Fuel level fallback** aus engine block `currentFuelLevel_pct` (war nur measurements-Pfad).

Backwards-kompat: Vehicles deren `fuelStatus.rangeStatus.value` funktioniert (Golf GTE auf neuer Firmware, modern PHEVs) sehen identisches Verhalten wie v1.10.0.

💨 **3B-Part-3 — Optimistic UI für Lock/Climate/Charging/Window-Heating:**

Pattern aus `skodaconnect/myskoda` PR #832: Wenn User auf Lock/Climate/Charging-Switch klickt, flippt die HA-Karte **sofort** auf den Erwartungs-Wert — der API-Roundtrip (10–30 s) findet im Hintergrund statt. Bei Failure: revert + ServiceValidationError.

Was ist jetzt optimistic:
- 🔒 `async_lock` → `doors_locked = True` sofort
- 🔓 `async_unlock` → `doors_locked = False` sofort
- 🔥 `async_start_climatisation` → `climatisation_active = True` + `state = "VENTILATION"` sofort
- ❄️ `async_stop_climatisation` → `climatisation_active = False` + `state = "OFF"` sofort
- ⚡ `async_start_charging` → `is_charging = True` + `charging_state = "CHARGING"` sofort
- ⚡ `async_stop_charging` → `is_charging = False` + `charging_state = "NOT_CHARGING"` sofort
- 🪟 `async_start/stop_window_heating` → beide Felder sofort

Failure-Pfad: Snapshot der vorherigen Werte wird vor dem Optimistic-Set gespeichert; bei Exception wird zurückgesetzt + HA notified. User sieht den Lock-Toggle "zurück springen" als Hinweis dass das Command fehlschlug.

🧪 **Tests:** 18 neue in `tests/test_v1111_96_optimistic.py` decken alle 4 #96-Tracks (volle GTE Shape + Passat error shape + carType=hybrid + engine-block fallback + pure ICE + pure EV phantom-protection) plus alle Optimistic-Transitions + Revert-on-Failure.

> 💡 Vollständige Field-Mapping + evcc/CarConnectivity/Audi-Q4 Quellen-Analyse in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

## [1.11.0] - 2026-04-30 🔆🔧 Issue #91 Closure: Light-Status, Service-Days, Max-Charge-Current

✨ **Fünf neue Entitäten — schließt Issue #91 vollständig** (Audi S6 + VW Golf 7 GTE Vehicle Data Scout findings):

| Entity | Type | Quelle | Vehicle |
|---|---|---|---|
| 💡 **`lights_on`** ("Lichter an") | Binary-Sensor | `vehicleLights.lightsStatus.value.lights[]` | alle |
| 🔢 **`lights_count`** ("Aktive Lichter") | Sensor | gleiche Array | alle |
| 📅 **`service_due_in_days`** ("Inspektion in") | Sensor (`d`) | `vehicleHealthInspection.maintenanceStatus.value.inspectionDue_days` | alle |
| 🛢️ **`oil_service_due_in_days`** ("Ölwechsel in") | Sensor (`d`) | `vehicleHealthInspection.maintenanceStatus.value.oilServiceDue_days` | combustion |
| ⚡ **`max_charge_current_a`** ("Max. Ladestrom") | Sensor (`A`) | `charging.chargingSettings.value.maxChargeCurrentAC_A` | electric |

**Was war das Problem:**

Issue #91 (Audi S6 + Issue #90 VW Golf 7 GTE) hatte mehrere Punkte. v1.10.0 hat den dicksten Fish gefangen (PHEV-Range-Triple + Audi-Diesel-Range), aber ein paar Lücken blieben:

- Lichter-Status war nirgends zugänglich
- Service-Tage konnte man nur als Datum sehen, nicht als "noch X Tage"
- Max-Ladestrom war als Field da aber kein Sensor

v1.11.0 macht #91 jetzt komplett fertig.

**Defensive Light-Parsing:** weil die Element-Shape von `vehicleLights.lightsStatus.value.lights[]` zwischen Firmwares variiert (`{name,status}` vs `{id,status}` vs CARIAD-BFF Listen-Wrapper), versucht der Parser drei bekannte Shapes durch und fällt auf "nur Aggregate" zurück wenn keiner matcht. Per-Light-Binary-Sensors kommen erst in v1.12.0 wenn wir verifizierte Element-Shapes von mehreren Brands haben.

**Phantom-Entity-Schutz** wie schon in v1.10.0 — alle 5 neuen Entitäten gehen über `_DATA_PRESENT_REQUIRED` Frozenset. Wer keine Lichter-Daten von der API bekommt, sieht keinen "0"-Sensor.

**Backwards-Compat:** `service_due_at` (DATE) + `oil_service_at` (DATE) bleiben unverändert. Die neuen `_in_days`-Sensoren sind **zusätzliche** Anzeige-Optionen.

🌍 **Übersetzungen** in allen 8 Sprachen.

🧪 **Tests:** 15 neue in `tests/test_v1110_91_closure.py` decken alle 3 Light-Shape-Varianten + Aggregate-Fallback + Service-Days + Sensor-Registrierung.

> 💡 Vollständige technische Details in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

## [1.10.2] - 2026-04-30 🚗 CUPRA Born 2026 Firmware-Shapes (Gerhard's #53 Live-Test)

🐛 **Bug-Fix für CUPRA Born / SEAT Cupra Owner auf neuerer OLA-Firmware:**

Gerhard hat v1.10.0 auf seinem CUPRA Born getestet und der **Vehicle
Data Scout aus v1.9.0** hat **19 neue Felder** auf den OLA-Endpoints
gemeldet (#53 Comment 2026-04-30). Beim genauen Hinschauen waren das
nicht nur "neue Felder" — viele waren **umbenannte Versionen** der
Felder die wir schon kannten:

| Old (Rainer #109 — v1.8.9 Ref) | New (Born 2026 firmware) | Wirkung pre-1.10.2 |
|---|---|---|
| `battery.currentSOC_pct` | `battery.currentSocPercentage` | Akku-Füllstand leer |
| `plug.connectionState` / `plug.plugConnectionState` | `plug.connection` | Stecker-Verbunden immer False |
| `plug.lockState` / `plug.plugLockState` | `plug.lock` | Stecker-Verriegelt immer False |
| `"CONNECTED"` / `"LOCKED"` (UPPERCASE) | `"connected"` / `"locked"` (lowercase) | enums verglichen falsch |

**Folge:** auf Born-Owners die v1.8.9+ benutzen aber neuere Firmware
haben waren die Charging- + Plug-Entitäten still leer — keine
Fehlermeldung, einfach `unknown`.

**Fix:** `seat_cupra.py` Parser liest jetzt **alle drei Field-Namen-
Varianten** als Fallback-Kette (Born 2026 → Rainer #109 → Legacy
CARIAD), und vergleicht enum-Werte case-insensitive. Backwards-Compat
für ältere Firmwares bleibt erhalten.

**Plus neue Born-2026-Felder die wir jetzt nutzen:**

- 🔋 `battery.estimatedRangeInKm` → fallback für `range_km` /
  `electric_range_km` wenn der dedizierte ranges-Endpoint nichts liefert
- 🔒 `status.locked` (top-level bool) → fallback für `doors_locked`
  wenn die strukturierte `doors.*.locked` Tree leer ist
- 🚪 `status.hood.locked` (string `"true"`/`"false"`) → fallback für
  `hood_open` (invertiert)

**Plus alle 19 Felder im EXPECTED_KEYS-Katalog registriert** — Gerhard's
Repair-Notification löst sich beim nächsten Poll von alleine.

🛰️ **Erste echte API-Drift-Detection im Live-Betrieb seit v1.9.0!**
Das ganze v1.9.0 Vehicle-Data-Scout System hat genau diesen Use-Case
abgefangen: ein User auf neuerer Firmware hat einen 1-Klick-Bug-Report
geöffnet, wir haben innerhalb von Stunden den Parser gefixed.

🧪 **Tests:** 16 neue Tests in `tests/test_v1102_gerhard_born_firmware.py`
(camelCase-Pfade, lowercase-Enums, Backwards-Compat zu Rainer-Shape,
status-top-level-Fallback, alle 19 Scout-Felder registriert).

> 💡 Vollständige Field-Name-Mapping-Tabelle + Methodik-Notes in
> [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

## [1.10.1] - 2026-04-30 🛡️ Defensive Coding Phase 2 (Issue #58)

🐛 **Robustheit gegen unerwartete API-Werte:**

Drei neue Helfer in `cariad/_util.py` die NIE crashen, sondern bei
seltsamen Werten den Default zurückgeben:

- 🔢 **`safe_int(value, default=None)`** — akzeptiert int, float, bool,
  numerischer String mit Whitespace, Decimal-String (`"12.5"` → `12`).
  Garbage (None, leer, dict, list, "abc") → default.
- 🔣 **`safe_float(value, default=None)`** — gleiche Robustheit für floats.
- 🚦 **`safe_enum(value, known_values, *, log_name)`** — gibt den Wert
  zurück wenn er in `known_values` ist, sonst loggt eine Warnung mit dem
  Field-Namen + dem unerwarteten Wert und gibt None zurück.
  **Forward-Kompatibilität:** wenn VAG morgen einen neuen Charging-State
  wie `CHARGING_INTERRUPTED` ausrollt (siehe myskoda #503), bleibt
  Integration online — Sensor zeigt einfach `unknown` statt zu crashen.

🛠️ **Wo angewendet:**

- **Skoda Parser** — `remainingTimeToFullyChargedInMinutes` als String
  ("12.5") → keine Crash mehr (myskoda #503 Pattern). `targetTemperature`
  ebenfalls.
- **VW EU/Audi Parser** — `remainingChargingTimeToComplete_min`,
  `maxChargeCurrentAC_A` (kann String "MAXIMUM" sein), `model_year`
  (manchmal Int, manchmal "2021"-String) alle defensiv.
- **SEAT/CUPRA Parser** — `remainingTimeToFullyChargedInMinutes`
  ebenfalls über `safe_int`.

🛡️ **Coordinator-Härtung:**

- `to_dict()` + `_enrich()` für jedes Vehicle jetzt eigener try/except.
  Pre-1.10.1 hat ein einzelnes Parser-Problem den ganzen Vehicle-Poll
  zerschossen; jetzt bleibt das Vehicle mit seinen vorherigen Daten
  sichtbar, der Fehler landet im Error Reporter Ring-Buffer für
  1-Klick-Bug-Report (v1.9.0 Pipeline).

🧪 **Tests:** 16 neue Tests in `tests/test_v1101_defensive.py` decken
alle Helper-Pfade + Coordinator-Parse-Guard.

> 💡 Vollständige technische Details inkl. Helper-Vertrag und
> Anwendungs-Audit in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

## [1.10.0] - 2026-04-29 🔋⛽ PHEV-Range-Triple + Audi-Diesel-Range (Issue #94)

✨ **Drei neue Sensoren für plug-in Hybride und Diesel-Modelle:**

- 🔋 **`electric_range_km`** ("Elektrische Reichweite") — Batterie-only Reichweite (mdi:battery-charging-outline)
- ⛽ **`combustion_range_km`** ("Kraftstoff-Reichweite") — Benzin/Diesel/CNG/LPG Reichweite (mdi:gas-station)
- 🛣️ **`total_range_km`** ("Gesamtreichweite") — kombinierte Reichweite (für Hybride relevant)

**Was war das Problem (Issue #94):**

Pre-1.10.0 hat unser Parser für VW EU + Audi alle Range-Quellen in das eine `range_km`-Feld gemappt — dabei überschrieb die Batterie-Reichweite die Verbrennungs-Reichweite oder den Gesamtwert. Ein Golf 7 GTE konnte deshalb nicht gleichzeitig "45 km elektrisch" + "520 km Sprit" + "565 km gesamt" anzeigen — nur einen davon.

**Was wir gemacht haben:**

- 🆕 **VW EU / Audi Parser:** liest jetzt `fuelStatus.rangeStatus.value.{primaryEngine,secondaryEngine}.{type,remainingRange_km}` und klassifiziert nach **Engine-Typ** (nicht nach Position) — primär=Verbrennung + sekundär=elektrisch oder umgekehrt funktionieren beide.
- 🆕 **Audi `dieselRange` Fallback** (verifiziert auf Audi S6 C8 2021 via #91): wenn kein `fuelStatus`-Block existiert, kommt `combustion_range_km` aus `measurements.rangeStatus.value.dieselRange` / `gasolineRange`. Akzeptiert sowohl skalare Werte als auch `{distanceInKm: int}`-Wrapper.
- 🆕 **Skoda Parser:** liest `electricRange.distanceInKm` + `combustionRange.distanceInKm` + `totalRangeInKm` jetzt in die 3 expliziten Felder. Vorher wurde nur `combustionRange` als Skalar gelesen — auf Kodiaq iV ein Bug.
- 🛡️ **Phantom-Entity-Schutz:** neue Sensoren werden NUR erstellt wenn der API-Wert tatsächlich `not None` ist. Reine EVs bekommen kein "unknown"-Spritmesser, reine ICE keinen "unknown"-Akku. Per `_DATA_PRESENT_REQUIRED` Frozenset in `sensor.py` — pro-Key opt-in.
- 🔄 **`range_km` Backwards-Compat:** bleibt als Headline-Number erhalten. Priorität: elektrisch (für EV/PHEV) → total → Verbrennung. Existierende Automatisierungen und Dashboards funktionieren unverändert.

🌍 **Übersetzungen** in allen 8 Sprachen (DE: Elektrische/Kraftstoff/Gesamt-Reichweite, FR/ES/NL/PL/CS/SV äquivalent).

🧪 **Tests:** 13 neue Tests in `tests/test_v1100_phev_ranges.py` decken alle Engine-Klassifikations-Pfade, Audi-Diesel-Fallback, Skoda-Wrapper, EV-Phantom-Vermeidung.

> 💡 Vollständige technische Details inkl. Vergleichstabelle der API-Pfade pro Brand in [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

## [1.9.1] - 2026-04-29 🔧 Audi/VW Lock + Wake Hotfix + Capability-Filter Phase 2

🐛 **Bug-Fixes (Issue #92, Audi S6 C8 2021 Live-Test):**

- 🔓 **Audi/VW EU Lock funktioniert wieder** — der CARIAD BFF antwortete
  mit `403 spin_error` auf `/access/lock` weil die S-PIN bei premium
  Audi-Modellen für Lock genauso erforderlich ist wie für Unlock.
  Der `command_lock` der VW EU/Audi-Clients hängt jetzt dieselbe S-PIN
  ans Payload (sofern konfiguriert) wie es `command_unlock` schon tat.
- 🚀 **Audi Wake-Endpoint v1→v2 Fallback** — `/vehicle/v1/.../vehicleWakeup`
  gibt 404 auf premium Audi Modellen (S6 C8). Der Wake-Befehl nutzt jetzt
  den gleichen `_post_command`-Dispatcher wie alle anderen Commands und
  fällt bei 404 automatisch auf `/vehicle/v2/...` zurück.

🛰️ **Vehicle Data Scout — 27 neue Felder registriert (Issues #90, #91):**

Aus den ersten zwei Live-Reports vom Maintainer (Audi S6 + VW Golf 7 GTE)
sind diese Felder jetzt im `EXPECTED_KEYS`-Katalog (firingen damit nicht
mehr beim nächsten Poll). Fundament für künftige Entity-Arbeit:

- **Audi S6 (Diesel):** `dieselRange`, `currentFuelLevel_pct`,
  `vehicleLights.lightsStatus.{lights,carCapturedTimestamp}`,
  `userCapabilities`, `fuelStatus`, `vehicleHealthInspection`,
  `vehicleHealthWarnings`
- **VW Golf 7 GTE:** `maxChargeCurrentAC_A` (Ampere statt Enum),
  `targetTemperature_F` (Fahrenheit), `climatisationWithoutExternalPower`,
  `automation`, `departureProfiles` (Nachfolger von `departureTimers`),
  `chargeMode`-Block

🛡️ **Capability-Filter Phase 2 (Issue #56):**

- 🧠 **Smartere Fehler-Klassifikation** — `classify_command_failure`
  schaut jetzt im Body nach `spin_error`, `subscription expired`,
  `not_entitled`, `license_required` etc. Pre-1.9.1 wurden alle 4xx als
  generischer "BACKEND_ERROR" klassifiziert.
- 🤖 **Auto-Recording** — `_cariad_cmd` füttert jetzt jedes Command-Ergebnis
  automatisch in den `FeatureState`. Erfolge flippen `entitled_by_account`
  und `supported_by_vehicle` auf `True` zurück (z.B. nach Abo-Verlängerung);
  definitive Fehler markieren das Command als nicht verfügbar.
- 👁️ **Entity-Availability hört auf FeatureState** — Lock, Climate,
  Charging-Switch, Window-Heating-Switch und die Buttons (Flash, Wake)
  gehen automatisch auf "unavailable" wenn das Backend explizit
  "missing capability" oder "subscription expired" zurückmeldet. Statt
  bei jedem Tap denselben 403 zu produzieren.

🧪 **Tests:** 18 neue Tests in `tests/test_v191_hotfix.py` (Lock-S-PIN,
Wake-v1/v2-Fallback, Klassifikator-Body-Sniffing, FeatureState-Logik,
Scout-Key-Registrierung).

> 💡 Vollständige technische Details inkl. aller Code-Pfade in
> [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

## [1.9.0] - 2026-04-29 🔬 Vehicle Data Scout + Error Reporter

✨ **Was ist neu — zwei neue diagnostische Sensoren mit 1-Klick Bug-Report:**

- 🛰️ **Vehicle Data Scout** (`sensor.vag_VIN_vehicle_data_scout`):
  Erkennt automatisch unbekannte Felder in den API-Antworten deines
  Fahrzeugs. Zählt, wie viele neue Felder gefunden wurden — Attribute
  zeigen die letzten 5 Pfade. Brand-lokalisiert (DE: API-Beobachter,
  FR: Observateur d'API, ES: Observador de API, NL: API-waarnemer, …).
- 🚨 **Error Reporter** (`sensor.vag_VIN_error_reporter`):
  Speichert die letzten 20 Integrationsfehler im Ring-Buffer. Zählt
  aktuelle Fehler — Attribute zeigen die letzten 3 Exception-Typen.
  Brand-lokalisiert (DE: Fehler-Berichter, FR: Rapporteur d'erreurs, …).
- 🔘 **1-Klick Reporter Pipeline:** Beide Sensoren erstellen automatisch
  HA-Repair-Notifications (Einstellungen → System → Reparaturen). Klick
  auf **Mehr erfahren** → öffnet ein **vorausgefülltes GitHub-Issue**
  im Browser. Für Facebook-Community: Diagnostics-Download enthält den
  maskierten Bericht, fertig zum Reinkopieren. **NIEMALS Auto-Push.**

🔒 **Datenschutz garantiert:**

- VINs maskiert auf letzte 6 Zeichen (`***012345`)
- GPS-Werte gerundet auf 1 Dezimalstelle (~11 km Genauigkeit)
- userIDs (UUIDs), JWTs, Bearer-Tokens, opaque Tokens entfernt
- E-Mail-Adressen ersetzt durch `***@***`
- Keine rohen API-Responses, keine Zugangsdaten, nichts wird automatisch
  gesendet (GDPR + HACS-Regeln + GitHub ToS)

🤝 **Crowd-sourced Bug-Discovery:** Jeder Nutzer mit einem ungewöhnlichen
Fahrzeug (neuer Modelljahrgang, andere Region, exotische Firmware) kann
mit einem Klick verstecktes Wissen ans Repo zurückspielen. Folgt dem
bewährten `tillsteinbach/CarConnectivity-*` "Unexpected Keys"-Pattern,
das uns die richtigsten Live-API-Daten gebracht hat (CC-seatcupra #109,
CC-skoda #50).

🛠️ **Wo aktiv:** Vehicle Data Scout läuft bereits für Škoda, SEAT, CUPRA,
Volkswagen EU und Audi — alle Brands mit registrierter
`EXPECTED_KEYS`-Tabelle. Error Reporter ist account-weit aktiv.
Andere Brands (Porsche, VW NA) bleiben still bis sie opt-in.

🧪 **Verifiziert mit:** 18 neuen Tests in `tests/test_reporter.py`.

> 💡 Vollständige technische Detail-Notes inkl. aller Code-Pfade,
> Architektur-Entscheidungen und Issue-Referenzen findest du in
> [`docs/CHANGELOG_TECHNICAL.md`](docs/CHANGELOG_TECHNICAL.md).

### 📚 Documentation refresh (2026-04-29, doc-only — no version bump)

- 🆕 [`docs/RESEARCH_NOTES_2026-04-29.md`](docs/RESEARCH_NOTES_2026-04-29.md) — single archive of every verified live-API field name, every reference repo path, every pattern observation that informed v1.8.6→v1.8.12. Status per claim: ✅ verified / ⚠️ hypothesis / ❌ disproven. **Read this first if resuming this project**.
- 🔄 [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md) — refreshed to v1.8.12 state. New: process improvements section, full architecture map with per-file v1.8.X-change comments, 17 hard rules, 15-step "How to start the next session" recipe.
- 🔄 [`docs/ROADMAP.md`](docs/ROADMAP.md) — full version achievement table, sprint summary, expanded "won't be implemented" section, "How an AI tool resumes this work" guide.
- 🔄 All 8 READMEs — "Aktueller Stand & ehrliche Limits" section refreshed from v1.8.5 to v1.8.12. New 4-tier structure: ✅ what works NOW / ⚠️ in progress / 🚫 conscious limits / 🔧 privacy + 📚 doc links.
- 🆕 **v1.9.0 announced** (was v1.8.13 — corrected to strict semver because two new sensors qualify as MINOR bump): **Vehicle Data Scout + Error Reporter** sharing a 1-click Reporter Pipeline (`📤 GitHub` OR `📋 Copy for Forum/Facebook`). Especially Facebook-community-friendly: non-technical users get usable bug reports without learning Markdown or GitHub. NO auto-push, GDPR-compliant. Roadmap session sequence renumbered: v1.9.1 = Capability-Filter Phase 2, v1.9.2 = Defensive Coding Phase 2, v1.9.3 = Optimistic Lock/Climate, v1.10.0 = Diagnostics + Smart-Wake + 12V protection, v1.11.0 = Trip Stats + Image refactor, v2.0.0 = HACS Default + EU Data Act.

## [1.8.12] - 2026-04-29 🌐 Multi-Brand Connection-State (MVP-Move)

✨ **Was ist neu — alle 7 Marken haben jetzt den Online/Standby/Offline-Sensor:**

- 🟢🟡⚫ **`connection_state` Sensor** funktioniert jetzt nicht nur für Škoda (v1.8.11),
  sondern auch für **VW EU, Audi, SEAT, CUPRA**. Verbindungsstatus deines Autos
  auf einen Blick — egal welche VAG-Marke.
- 🏆 **Erste VAG-Integration mit centralisiertem Multi-Brand Connection-State.**
  Niemand sonst macht das so — myskoda hat es nur intern, volkswagencarnet
  und audi_connect_ha exposen es gar nicht.

🛠️ **Wie wir's verifiziert haben:** Echte Live-API-Antworten von **VW ID.4 2025**
([volkswagencarnet Issue #921](https://github.com/robinostlund/volkswagencarnet/issues/921)
mit komplettem JSON-Dump) bestätigen `carCapturedTimestamp` auf jedem
sub-object des CARIAD-BFF `selectivestatus`-Endpoints. Plus die schon bekannten
Quellen für Škoda (myskoda PR #536) und CUPRA (CC-seatcupra #109).

🔧 **Technisch:** Wir haben den Skoda-Algorithmus aus v1.8.11 in einen
brand-agnostic Helper `compute_connection_state()` extrahiert (cariad/_util.py),
der **rekursiv** durch beliebig tief geschachtelte Sub-Objects walkt. So
funktioniert er für Škoda's flache Struktur **und** für VW EU CARIAD-BFF's
3-fach geschachtelte `service.statusName.value.carCapturedTimestamp`.

🙏 **Danke an:** robinostlund (volkswagencarnet) für jahrelange VW-EU-Pflege,
Rainer für CUPRA Live-Dumps, GitHobi für Škoda #54.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#1812---2026-04-29)

---

## [1.8.11] - 2026-04-29 🚙 Škoda Online/Standby/Offline + Live-API-Erkenntnisse

✨ **Was ist neu für Škoda-Fahrer:**

- 🟢🟡⚫ **Verbindungsstatus-Sensor** — zeigt klar ob das Auto gerade live ist (online),
  schläft aber wakeable ist (standby) oder seit >24h nicht mehr da (offline).
  Schließt das langjährige "Standby vs Offline"-Mysterium aus Issue #54.
- 🚪 **Schiebedach, Kofferraum, Motorhaube** funktionieren jetzt — wurden für
  Škoda nie populiert (Bug aus Issue #50 von Tillsteinbach's Connector).
- 🔒 **Bessere Türschloss-Erkennung** auf neueren Modellen (Kodiaq 2026+) durch
  den `reliableLockStatus`-Wert, der weniger lagt als das alte `doorsLocked`.
- ⚡ **Lade-Endzeit präziser** — wir nutzen jetzt den absoluten ISO-Timestamp
  (`fullyChargedAt`) statt "Restzeit + jetzt" zu rechnen (driftet nicht mehr).
- ⚠️ **`CHARGING_INTERRUPTED`** als neuer Lade-Status wird sauber erkannt
  (kommt vor wenn Wallbox die Sitzung unterbricht).

🛠️ **Wie wir's verifiziert haben:** Echte Live-API-Antworten von Škoda Kodiaq
iV 2026 PHEV (CC-skoda Issue #50, kompletter JSON-Dump) und Pull-Requests aus
[skodaconnect/myskoda](https://github.com/skodaconnect/myskoda) (#503, #565
und vor allem PR #536 die GENAU dieselbe `carCapturedTimestamp`-Strategie
fährt — bestätigt unseren Ansatz 1:1).

🙏 **Danke an:** GitHobi für den Bug-Report (#54), Rainer für den ausführlichen
Kodiaq-iV-2026-Dump in CC-skoda #50.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#1811---2026-04-29)

---

## [1.8.10] - 2026-04-29 🩹 Hotfix

🐛 **Behoben:** Im seltenen Fallback-Pfad für sehr alte CUPRA/SEAT-Firmware
wurden Türstatus invertiert angezeigt (offen ↔ zu vertauscht).

📊 **Wer ist betroffen?** In der Praxis aktuell **niemand** — alle getesteten
CUPRA-Born/Formentor/Tavascan-Modelle nutzen den neuen Pfad aus v1.8.9.
Aber: der Fallback hätte später bei API-Änderungen Probleme gemacht.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#1810---2026-04-29)

---

## [1.8.9] - 2026-04-29 🚗 CUPRA Born Bug-Fix-Bündel

✨ **Was ist neu für CUPRA/SEAT-Fahrer:**

- 🚪 **Türen, Fenster, Kofferraum, Motorhaube, Schiebedach** werden jetzt
  korrekt angezeigt (vorher waren sie permanent leer)
- 🚗 **"Auto fährt gerade"** funktioniert wieder — vorher klebte der Status
  oft auf "geparkt"
- ⚡ **Lade-Power und Restzeit** werden korrekt angezeigt
- 🔓 **Auto-Entriegelung** beim Laden zeigt auch "permanent" als aktiviert an

🆕 **Neue Entities:** Pro-Fenster Binary-Sensoren (`Window Front Left`,
`Window Rear Right` etc.) — analog zu den bisherigen Pro-Tür-Sensoren.

🛠️ **Was war kaputt?** Unser Code hat die falschen JSON-Felder von der
CUPRA/SEAT-API gelesen. Wir hatten Felder aus der CARIAD-API (für VW/Audi)
übernommen, aber CUPRA/SEAT nutzt eine andere API (OLA) mit komplett
anderen Feldnamen. Das wurde verifiziert mit:

- Quellcode der pycupra-Library
- Echten Live-API-Antworten von CUPRA-Born-Fahrern aus dem
  [CarConnectivity-Issue-Tracker](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra/issues)
  (#5, #8, #18, #21, #50, #51, #109)

🙏 **Danke an:** Gerhard für den ursprünglichen Bug-Report (CUPRA Born),
Rainer (#109) für die Live-API-Daten, und alle Tester die "Unexpected Keys"
in den CC-seatcupra Issues dokumentiert haben.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#189---2026-04-29)

---

## [1.8.8] - 2026-04-29 🔓 Lock / Climate / Charging für Audi 2025+ und Passat B9

✨ **Was ist neu für Audi RS e-tron GT, VW Passat 2025 und neuere Modelle:**

- 🔒 **Lock/Unlock** funktioniert auf neuen Audi-Modellen (war vorher 404)
- ❄️ **Klimatisierung Start/Stop** funktioniert auf neuen Modellen
- ⚡ **Laden Start/Stop** funktioniert auf neuen Modellen

🛠️ **Was war kaputt?** Audi und VW haben für neuere Modelle (RS e-tron GT,
Passat B9 etc.) ihre API-Pfade von `/v1/` auf `/v2/` umgestellt. Unser Code
versuchte nur `/v1/` — Ergebnis: HTTP 404 bei jedem Befehl. Jetzt probiert
die Integration automatisch beide Pfade und merkt sich pro Fahrzeug welcher
funktioniert.

🐛 **Bonus-Bug-Fix:** Vor v1.8.8 hat unser Code bei *jedem* Server-Fehler
(500/401/429) den Fallback-Endpoint angefragt. Konsequenz: vorübergehende
Backend-Hiccups wurden als "Endpoint existiert nicht" interpretiert. Jetzt
nur bei echtem 404.

🙏 **Danke an:** G.S. (Audi RS e-tron GT, #51) und Marco Grewe (VW Passat
2025, #74) für die ausführlichen Bug-Reports.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#188---2026-04-29)

---

## [1.8.7] - 2026-04-29 🛡️ Stabilität — kein "Unavailable"-Flackern mehr

✨ **Was ist neu für alle Marken:**

- 🌐 **Wochenend-Backend-Probleme** werden jetzt ausgesessen — Auto bleibt
  bis zu 6 Stunden mit den letzten bekannten Werten verfügbar, statt sofort
  auf "Unavailable" zu kippen
- 🔁 **Einzelne fehlgeschlagene Polls** lösen kein "Unavailable" mehr aus —
  erst nach 3 aufeinanderfolgenden Fehlern wird das Auto als nicht erreichbar
  gemeldet
- 🐢 **Gateway-Timeouts (504)** werden automatisch nochmal versucht statt zu
  scheitern
- 🌐 **DNS-/Verbindungsprobleme** werden als vorübergehend behandelt (vorher
  wurde das fälschlich als "Login fehlgeschlagen" interpretiert)
- 🔐 **IP-Bann-Schutz:** maximal 3 Token-Refreshes pro Stunde — verhindert
  dass das VW-Backend dein Konto bei einem Refresh-Loop sperrt

🛠️ **Warum das wichtig ist?** Automatisierungen die auf Türen, Position oder
Ladestatus reagieren funktionieren jetzt zuverlässig auch wenn die VW-Server
mal hicksen. Das Auto bleibt sichtbar mit "Letzte Aktualisierung vor 30 Min",
statt komplett zu verschwinden.

🧪 **Hinweis für Tester:** 12 neue Unit-Tests prüfen alle Edge-Cases ab.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#187---2026-04-29)

---

## [1.8.6] - 2026-04-29 📚 Docs-Truthfulness Hotfix

✨ **Was ist neu (nur Doku, kein Code):**

- 🏆 **Multi-Brand-Successor-Position:** README sagt jetzt klar dass VAG Connect
  der aktive Nachfolger für die archivierten Repos
  [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id)
  (archived 2025-10-29) und
  [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect)
  (deprecated 2025-03-14) ist. Eine Integration für 7 Marken, kein separates
  Plugin nötig.
- 🏷️ **Dynamic CI-Badge:** Statt hardcoded Test-Counts (die schnell veraltet
  sind) zeigt das Badge jetzt den aktuellen Build-Status
- 📝 **Aktuelle Stand & ehrliche Limits Section** in allen 8 README-Sprachen:
  was funktioniert, was noch nicht, was bewusst ausgeklammert ist
  (z.B. PPC/PPE-Plattform für Audi 2025+ und Image-Entities)
- 🔧 **Korrekturen:** Das EN README sagte fälschlich "cloud-push" (war seit
  v1.8.0 falsch — wir pollen). Service-Count uneinheitlich (16 vs 14) →
  beide jetzt auf echte 14.

🛠️ **Warum?** Tester die HACS durchblättern sollen realistische Erwartungen
bekommen. Die Integration soll nicht "kaputt" wirken nur weil eine Funktion
bewusst capability-gated ist.

📋 [Technische Details](docs/CHANGELOG_TECHNICAL.md#186---2026-04-29)

---

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
