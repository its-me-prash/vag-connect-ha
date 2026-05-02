# VAG ↔ Home Assistant integration — research notes (v2)

> **Source:** Compiled from public GitHub artifacts (READMEs, release notes,
> PR/issue titles) and from anonymized topic-level observations in the
> V.A.G. Connected Cars community. No personal data, no verbatim user content.
> **Imported:** 2026-05-02
> **Supersedes:** `upstream-pycupra-notes.md` (v1) — keep both for citation
> traceability; this v2 covers Skoda + MQTT + HACS topics in addition.

## 1. Project landscape

There are three actively-relevant projects in the VAG → Home Assistant
space, each backed by a Python client library:

| Brand(s) | HA integration | Python library | Status |
|---|---|---|---|
| Cupra / Seat | `WulfgarW/homeassistant-pycupra` | `WulfgarW/pycupra` | Active |
| Skoda (current MySkoda API) | `skodaconnect/homeassistant-myskoda` | `skodaconnect/myskoda` | Active |
| Skoda (legacy SkodaConnect API) | `lendy007/homeassistant-skodaconnect` | — | Archived; API closed by Skoda |
| Seat (legacy) | `Farfar/homeassistant-seatconnect` | — | Superseded by pycupra |

**Architectural takeaway for `vag-connect-ha`:** stay with the proven
pattern of (a) a thin HA `custom_components/<name>` layer, (b) a
separate, pure-Python API client published as its own package. It's
testable outside HA, reusable in non-HA scripts, and survives HA
refactors.

## 2. Architecture worth copying (validated by both upstreams)

- **Pull from the cloud, not from the car.** Cars push telemetry to
  the manufacturer's cloud on events (lock/unlock, charge state,
  climate, parking). The integration polls the cloud. *Don't promise
  real-time data; promise "freshest cloud-known state."*
- **Bucketed polling under a daily quota.** The MyCupra/MySeat portal
  has a per-day API limit (~1,500 calls including the official app +
  integrations). Pycupra's three-bucket strategy is the cleanest design:
  - **Bucket 1** — fast-changing state (doors, windows, range,
    charge/climate status) — at user-configured INTERVAL (recommended
    ≥ 600 s, or 900 s with push enabled)
  - **Bucket 2** — slower data (mileage, parking position, full
    charge/climate info, departure timers/profiles, climate timers)
    — refreshed about every 20 min
  - **Bucket 3** — model images — every ~2 h
  - A "Request full update" switch forces buckets 1 + 2
- **Push notifications via the manufacturer's notification channel.**
  Both stacks now use a Firebase-backed channel: pycupra has had this
  since v0.2.x; the Skoda stack landed it in PR #1083 ("fix(mqtt):
  integrate Firebase-backed MQTTv5 auth"). Push lets you relax polling
  significantly. **Build the dispatcher with an explicit "unknown
  notification type" path** that logs and no-ops — the upstream had to
  ship multiple patch releases (`charging-settings-failed-timeout`,
  `charging-error`, `user-capabilities-change`,
  `vehicle-connection-state-online`, `charging-stop-error`,
  `vehicle-wake-up-failed`) as new types appeared.
- **Nightly throttle.** A "nightly update reduction" mode (e.g.
  22:00–05:00 local) lowers polling to ~once / 20 min to preserve quota.
- **One config entry per vehicle.** Multi-vehicle support comes from
  adding the integration multiple times. Each entry should support a
  log prefix so logs from `vehicle`, `connection`, `dashboard`,
  `firebase` etc. are disambiguated.
- **Capability-driven entity discovery.** Only add entities the
  vehicle actually supports. Pycupra v0.2.8 added the rule that
  "Request wakeup vehicle" only appears if the vehicle has the
  `vehicleWakeUp` capability — copy this pattern for everything.
- **Local file storage convention.** Mirror pycupra's:
  - Model images under `www/<integration>/`, referenceable as
    `/local/<integration>/image_<VIN>_*.png`
  - Driving history aggregates under
    `<config>/<integration>_data/` as
    `_drivingData_dailySums.csv` and `_drivingData_monthlySums.csv`
    (with `.old` backups)
  - Note: per-trip distance is rounded down by the API, so a year's
    "monthly sums" can be ~2.5% smaller than (end_mileage −
    start_mileage). **Document this; do not "correct" it silently.**
- **MQTT-vs-API event freshness.** A recurring real bug: MQTT events
  arrive late or out of order and overwrite fresher API data. The
  Skoda stack fixed this in v1.31.1 by stamping each MQTT event with
  the API's last-update timestamp and rejecting older events.
  **Bake this into your event handler from day one.**

## 3. Configuration options to expose

From both upstreams' config flows, the proven set:

- Poll frequency (hard floor 300 s, recommend 600 s; recommend 900 s
  when push is enabled)
- Use push notifications (toggle)
- Nightly update reduction (toggle)
- S-PIN (optional; required for aux heater, lock)
- **"Mutable" master kill switch** — when off, only "Request full
  update" / "Request wakeup" act; everything else only emits a HA
  notification. Excellent safety pattern; copy it.
- Full API debug logging (toggle)
- Per-resource monitoring selection
- **(Suggested addition) `mqtt_enabled` toggle** — community report:
  when MQTT auth is broken upstream, a clean way to disable just the
  MQTT path keeps the integration functional via polling. Confirmed by
  upstream guidance to pass `mqtt_enabled=False` to the library while
  MQTT issues are being investigated.

## 4. Entity surface (feature checklist)

(See `upstream-pycupra-notes.md` §3 for the per-domain inventory.
Additional v2 detail:)

- **Charging:** rate (W/kWh; some models also report rate in km/h —
  gate by capability), time left
  (`remainingTimeToFullyChargedInMinutes`), change current (max/reduced
  AND amperes for some EVs)
- **Diagnostic (suggested additions):** "API requests remaining
  today", "last API error code/url", "MQTT connection state"

## 5. Error & topic taxonomy (anonymized)

Every entry below was observed both in community discussion and
corroborated against public release notes / issue titles.

### 5.1 Authentication

- **Login fails after manufacturer password change / new T&Cs.** Most
  common single issue. Resolution: the user must finish any pending
  consent at `cupraid.vwgroup.io` / `seatid.vwgroup.io` / equivalent,
  log out, log back in. Pycupra v0.2.10 stopped auto-retrying on bad
  credentials to avoid lockouts.
- **Tokens lost after a few days.** Reported against the Skoda Python
  library; symptom is the integration was authenticated then silently
  de-authenticates. Maintainers' recommendation: re-authenticate from
  the library when tokens go stale.
- **MQTT CONNACK code 5 — "Not authorized" / "Connection lost
  ([code:135] Not authorized)".** Caused by token/MQTT auth
  interaction. Workaround until fixed: pass `mqtt_enabled=False`.
  Permanent fix landed via the Firebase-backed MQTTv5 auth PR
  (`skodaconnect/homeassistant-myskoda#1083`).
- **No in-UI re-authentication.** Users currently must remove and
  re-add the integration after a credential change, which preserves
  entity IDs but loses long-term statistics. Mitigation: implement
  HA's `async_step_reauth`.

### 5.2 Cloud-side / API

- **HTTP 500 from `/api/v2/garage/vehicles` and similar endpoints.**
  Bursts of `aiohttp.client_exceptions.ClientResponseError: 500,
  message='Internal Server Error'`. Upstream stance: this is the
  vendor's cloud being unhealthy; the integration should log it once,
  not each retry, and continue with cached data.
- **Daily request limit exhaustion.** Cloud resets ~02:00. After
  exhaustion, no new data until reset. Mitigation: surface a
  `requests_remaining_today` sensor; raise a HA repair issue when it
  hits 0.
- **Endpoint-level inconsistency / desync.** Two endpoints can return
  logically inconsistent data at the same instant (e.g. `mycar` says
  battery 0% while electric range is non-zero). *Pattern:*
  cross-validate scalars across endpoints; prefer the higher-trust
  endpoint per field.
- **"Inconsistent sensor source data."** Tracked as
  `skodaconnect/homeassistant-myskoda#1006`. Manifests as
  SoC / charging values jumping up and down vs. the official app.
  Often correlates with MQTT out-of-order delivery.

### 5.3 Vehicle-side

- **Vehicle "not in online mode."** Log signature: `Could not query
  update from Cupra/Seat API. Continuing with old vehicle data.`
  Causes: parked in poor connectivity, online services disabled in
  in-car privacy. Mitigation: surface as informational, not error;
  expose a binary sensor.
- **Privacy setting too strict.** Anything stricter than "Share my
  position" degrades device tracker, requests-remaining, and
  parking-time sensors. Mitigation: detect at setup and surface as a
  HA repair / UI hint with the exact setting to flip.
- **Cold-weather / 12 V battery degradation.** Recurring pattern (≤
  −15 °C, low 12 V): scheduled departures missed, intermittent
  failures. Not an integration bug, but document it so users don't
  open issues.
- **"What actually wakes the car?"** Definitive answer per upstream:
  **nothing wakes the car for normal polling — polling just reads
  what's already in the cloud.** Any state-change request (start
  heating, change charge settings, "Wake Up Car" button) is what
  causes a wake-up. Document this so users don't accidentally drain
  the 12 V by polling more aggressively expecting fresher data.

### 5.4 Integration UX

- **Action requests fail silently.** Pre-pycupra-v0.2.10, failed
  action requests didn't surface. Now they raise a HA notification.
- **First-step config flow deadlock.** Class of bug fixed in pycupra
  v0.2.11 (issues #65/#66). Mitigation: timeouts on every awaitable
  in step 1, plus a unit test.
- **Estimated-end-time shows previous year.** Pycupra issue #33.
  Class: timezone / year-rollover datetime arithmetic. Mitigation:
  explicit unit tests across DST and year-end boundaries.
- **Entity meaning changing across versions.** Pycupra 0.2.3 changed
  `last_trip` / `last_cycle` aggregate semantics; users perceived
  "entities disappeared." Mitigation policy: when changing the
  meaning of an existing entity, **add a new entity ID and deprecate
  the old one — don't mutate in place.**
- **Charging-status delay.** Pycupra v0.2.15 fixed a long delay in
  charging-status updates (issue #68). Pattern: push-driven changes
  must invalidate the relevant bucket cache immediately.
- **"Notify me to retry" UX.** Community ask: when login becomes
  invalid mid-session, the warning notification should include a
  one-click "Retry/Reload" button that re-runs the auth flow rather
  than telling the user to navigate to integrations.

### 5.5 Sensor history quality

- **SoC graph jump-back during charging.** Caused by MQTT out-of-order
  delivery. Fixed upstream (Skoda) in v1.31.1 by validating MQTT event
  timestamps against the latest API timestamp.
- **Trip aggregate vs. odometer asynchrony.** When odometer and
  last-trip endpoints return out-of-sync values, downstream
  calculations get distorted. Mitigation: do downstream calculations
  off the daily/monthly CSV trip sums, not by differencing odometer
  between polls.

### 5.6 CI / packaging hygiene

- **hassfest rejects URLs in `strings.json` / translations.** Pycupra
  v0.2.7 had to strip them. Mitigation: run hassfest and hacs/action
  in CI from the first commit.
- **Quietly-too-many-API-requests after release.** Reported around
  myskoda v1.31.1 — interval changes can multiply requests.
  Mitigation: log a one-line summary every N minutes ("X requests
  this period, Y remaining today") so regressions are visible.

## 6. HACS-safe integration checklist

(Move to `docs/HACS-CHECKLIST.md` once we audit our compliance.)

### Repo structure
- [ ] `custom_components/<domain>/manifest.json` with domain, name,
  version, documentation, issue_tracker, codeowners, requirements,
  iot_class, config_flow: true, dependencies
- [ ] `hacs.json` at repo root with name, content_in_root: false,
  country if relevant
- [ ] `README.md` describing supported brands, install via HACS,
  install manually, configuration, and the privacy + quota notes
- [ ] `LICENSE` (Apache 2.0 or MIT recommended)
- [ ] `info.md` (optional, displayed in HACS)

### Code quality
- [ ] Async only (aiohttp, no blocking I/O on the event loop)
- [ ] All API calls behind a single Coordinator per bucket
- [ ] Strict typing (mypy --strict in CI)
- [ ] Defensive parsing — wrap any `dict[...]` / nested-path access in
  helpers that return None on malformed payloads
- [ ] No URLs in `strings.json` / translations

### Config flow
- [ ] Initial step with timeouts on every network call
- [ ] `async_step_reauth` for credential refresh without removing the
  device
- [ ] `async_step_reconfigure` for changing poll interval, push
  toggle, S-PIN
- [ ] Discovery uses vehicle capabilities — no entity is created for
  an unsupported feature

### Operational safety
- [ ] "Mutable" master kill switch
- [ ] Polling interval floor (300 s minimum, 600 s default, 900 s
  when push is on)
- [ ] Nightly throttle window (configurable)
- [ ] Per-vehicle log prefix
- [ ] On any failed user action: HA persistent notification with the
  failure reason
- [ ] On unknown push-notification type: log + no-op (never raise)
- [ ] On out-of-order push event: drop if older than the last API
  timestamp for that field
- [ ] On HTTP 500 from upstream: log once at WARNING with the URL,
  continue with cached data
- [ ] On vehicle "offline": surface as a binary sensor; do not error
- [ ] On daily quota near-zero: HA repair issue with explanation +
  reset time

### CI / release
- [ ] hassfest action
- [ ] hacs/action validate
- [ ] pytest with fixtures for: each known push notification type,
  year-end / DST boundary, MQTT out-of-order event, malformed API
  payload, daily-quota exhaustion, vehicle offline, capability-gated
  entity creation
- [ ] mypy and ruff
- [ ] Release notes follow upstream pattern: "New entities", "Bug
  fixes", "Others"
- [ ] Semver, with HACS-recognizable tag names (vX.Y.Z)

### User-facing docs
- [ ] `FAQ.md` (privacy-setting matrix, quota explanation, "what
  wakes the car", credential-rotation flow, removing-and-readding
  caveat re: long-term statistics)
- [ ] `PRIVACY.md` describing exactly what data is read and stored
  locally
- [ ] `CONTRIBUTING.md` pointing community contributions to issues /
  discussions, not Discord scrape

## 7. High-leverage upstream contributions to `WulfgarW/homeassistant-pycupra`

These are framed as friendly contributions you could open as issues
or PRs — they directly address community pain in a way that benefits
both your repo and his.

1. Add `async_step_reauth` so users can update credentials after a
   manufacturer password change without removing the device.
2. Add an "API requests remaining today" sensor + repair issue when
   the quota hits zero.
3. One-click "Retry login" action on the warning notification when
   auth fails mid-session.
4. Push-notification dispatcher hardening: dictionary-driven handlers
   + explicit unknown-type log/no-op + regression test fixtures for
   every known type.
5. hassfest and hacs/action GitHub Actions workflows to prevent the
   `strings.json` URL regression from coming back.
6. Year-end / DST unit tests around estimated-end-time computation
   (issue #33 class).
7. Adopt the Skoda stack's pattern for MQTT freshness validation —
   drop MQTT events older than the most recent API timestamp for
   that field.
8. `FAQ.md` privacy-setting matrix mapping each in-car privacy level
   to which entities degrade / stop.
