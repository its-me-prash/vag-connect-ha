# Research Notes — VAG / Cupra / Seat → Home Assistant integration landscape

> **Source:** Compiled from public WulfgarW/homeassistant-pycupra GitHub repo +
> anonymized topic-level observations of the V.A.G. Connected Cars
> #homeassistant Discord channel. No verbatim user messages, no usernames
> beyond the repo maintainer (already a public author).
> **Imported:** 2026-05-02
> **Original author:** community researcher

## 1. Upstream projects (lineage)

The relevant open-source stack for VAG (Volkswagen Auto Group) car
integrations into Home Assistant is a chain of forks:

- `lendy007/homeassistant-skodaconnect` — original Skoda Connect HA integration
- `Farfar/homeassistant-seatconnect` — fork of the above, adapted for Seat
- `WulfgarW/homeassistant-pycupra` — current actively-maintained fork,
  rewritten to use the new Cupra/Seat API. Pairs with the Python library
  `WulfgarW/pycupra`

For a new repo (`its-me-prash/vag-connect-ha`) targeting the broader VAG
family, this lineage is the cleanest reference architecture: a thin HA
`custom_components/<name>` layer on top of a separate, pure-Python API
client library. Keeping the API client as its own package (like pycupra)
makes it testable outside of HA and reusable by non-HA scripts.

## 2. Architecture worth copying

Key design ideas pulled from the upstream README and release notes:

- **Pull, not push from car.** The integration never talks to the car
  directly. The car pushes telemetry to the manufacturer's cloud
  (MyCupra / MySeat / MyVW / MySkoda) on specific events. The
  integration polls the cloud. *Useful design implication:* don't
  promise real-time data; promise "freshest cloud-known state."

- **Three update buckets to stay under daily API quota.** The
  MyCupra/MySeat portal limits API calls (~1,500/day across the app +
  integrations). Bucket strategy:
  - **Bucket 1** — fast-changing state (doors, windows, range,
    charge/climate status) — polled at user-configured INTERVAL
    (recommended ≥ 600 s, or 900 s with push enabled)
  - **Bucket 2** — slower data (mileage, parking position, full
    charge/climate info, departure timers/profiles, climate timers)
    — refreshed roughly every 20 min (≥ 1100 s since last bucket-2
    refresh)
  - **Bucket 3** — model images — refreshed every ~2 h
  - A "Request full update" switch forces a refresh of buckets 1 and 2

- **Optional push notifications.** When enabled, the cloud pushes
  status changes to the integration so polling can be relaxed.
  Registered via the manufacturer's notification channel
  (Firebase-based; see `pycupra.firebase`).

- **Optional nightly throttle.** A "Nightly update reduction" mode
  lowers polling between 22:00 and 05:00 local to preserve the
  daily quota.

- **One config entry per vehicle.** Multi-vehicle support is achieved
  by adding the integration multiple times. Each entry can define
  a log prefix to disambiguate logs from `pycupra.connection`,
  `pycupra.vehicle`, `pycupra.dashboard`, `pycupra.firebase`.

- **Discovery driven by capabilities.** Entities are added based on
  the vehicle's enabled API capabilities (e.g., the wakeup button only
  appears if `vehicleWakeUp` capability is active — added in v0.2.8).
  This avoids dead/unsupported entities cluttering dashboards.

- **Local file storage convention.**
  - Model images stored under HA's `www/pycupra/` so they can be
    referenced as `/local/pycupra/image_<VIN>_front.png` etc.
  - Driving history stored under `pycupra_data/` as
    `_drivingData_dailySums.csv` and `_drivingData_monthlySums.csv`
    (with `.old` backups). Worth replicating for any "trip history"
    feature.

## 3. Entity surface (feature inventory)

Useful as a checklist for what `vag-connect-ha` should aim to expose:

- **Charging:** cable connected, cable locked, charging state, power,
  rate, time left, mode, preferred mode, profile defined, battery
  level, electric range, start/stop, change current (max/reduced, A),
  change target SOC.
- **Combustion / hybrid:** odometer, service info, engine status,
  fuel level, combustion range, combined range, AdBlue range.
- **Body state:** locks, windows, trunk, hood, sunroof, doors;
  lock/unlock action.
- **Trip data:** last trip (last day used) and last cycle (last month
  used) summaries.
- **Online status:** vehicle online binary sensor.
- **Climatisation & auxiliary heating:** status, settings, start/stop
  electric climate, window heater, start/stop aux heating, departure
  timers, departure profiles, climate timers.
- **Position:** device tracker Position (zone-aware, GPS in
  attributes); Last known position tracker that holds last fix while
  moving.
- **Actions:** request wakeup (capability-gated), request full update.
- **Media:** model images (front, rear, side, top, rbcFront, rbcCable).
- **Navigation:** send a destination to the vehicle.

## 4. Configuration options to expose

From the upstream config flow, worth implementing:

- Poll frequency (with a hard floor of 300 s and recommended 600/900 s)
- Use push notifications (toggle)
- Nightly update reduction (toggle)
- S-PIN (optional; required for aux heater, lock, etc.)
- "Mutable" toggle (master kill switch — when off, only "Request full
  update" and "Request wakeup" do anything; everything else only emits
  a notification). **Excellent safety pattern to copy.**
- Full API debug logging (toggle)
- Per-resource monitoring selection

## 5. Common error patterns and recurring topics

Distilled (anonymized, paraphrased) from the public release notes and
the recurring themes seen in the Discord support channel. These are
the hot spots for an integration in this domain — your repo can
preempt them with documentation, defensive code, and clearer UX.

### 5.1 Login / credential failures
**By far the most frequent issue.**

- **Symptom:** integration setup or background refresh fails after a
  manufacturer password change, after the user accepts new T&Cs, or
  when the account is temporarily locked.
- **Log signature:** `[pycupra.connection] Login failed for <user>.
  If the problem persists, verify ...` and `Could not refresh tokens.`
- **Upstream guidance:** open `cupraid.vwgroup.io` /
  `seatid.vwgroup.io` in a browser, finish any pending consent
  dialogs, log out, log back in, then retry.
- v0.2.10 changed behavior so that incorrect credentials / locked
  accounts no longer auto-retry; the user is invited to re-enter
  credentials. **Worth replicating** — auto-retry on bad creds risks
  getting the account locked harder.
- **Reconfiguration UX gap reported on Discord:** there is no obvious
  in-UI flow to update credentials without removing and re-adding the
  device. A dedicated "Reauthenticate" config-flow step (HA's
  `async_step_reauth`) would help. Note: removing and re-adding the
  integration preserves dashboard entity IDs but loses long-term
  statistics history — a known trade-off worth documenting.

### 5.2 Privacy-setting limitations
If the in-car privacy setting is stricter than "Share my position",
the device tracker, "requests remaining" and parking-time sensors
degrade or stop working entirely. **Surface this prominently** in
setup and in a sensor's `extra_state_attributes` so users
self-diagnose.

### 5.3 Vehicle not in online mode
- **Log signature:** `[custom_components.pycupra] Could not query
  update from Cupra/Seat API. Continuing with old vehicle data.`
  (warning, single occurrence).
- Often resolves itself, or indicates the car is parked in poor
  connectivity, or that online services are disabled in the in-app
  privacy settings. Document as informational, not a fault.

### 5.4 Daily API quota exhaustion
Cloud resets around 02:00. After exhaustion, no fresh data until
reset. **UX win:** expose a "requests remaining today" sensor (the
upstream API exposes one) and consider a HA repair issue when
remaining hits 0.

### 5.5 Push-notification edge cases
Several releases (v0.2.10, v0.2.12, v0.2.13) added handling for
previously-unknown push notification types:
- `charging-settings-failed-timeout`
- `charging-error`
- `user-capabilities-change`
- `vehicle-connection-state-online`
- `charging-stop-error`
- `vehicle-wake-up-failed`

**Lesson:** design the push-notification dispatcher with an explicit
"unknown type" path that logs and no-ops rather than crashes. The
upstream had to ship multiple patch releases as new types were
observed in the wild.

### 5.6 Action requests that fail silently
Pre-v0.2.10, failed action requests (lock, unlock, change timer, etc.)
didn't surface to the user. Fix pattern adopted: when a request fails
or returns `PyCupraInvalidRequestException` /
`PyCupraRequestInProgressException`, raise a HA persistent
notification. **Good UX baseline — copy it.**

### 5.7 Estimated-end-time year shows as previous year
Upstream issue #33 (climatisation/charging estimated-end timestamps
showing the prior year). Root cause class: timezone/DST or year-rollover
handling in datetime arithmetic against API strings. **Worth a unit
test** in the new repo around year boundaries.

### 5.8 Disappearing entities after upgrade / regression in trip aggregates
Versions 0.2.3+ changed the meaning of last-trip / last-cycle
aggregate entities (e.g. start flashing, area alarm, average
fuel/speed, duration, length). The fix re-introduced them with revised
semantics. **Lesson:** when changing the meaning of an existing
entity, prefer adding a new entity ID and deprecating the old one
rather than mutating in place — Home Assistant statistics and Lovelace
cards bind to entity IDs.

### 5.9 Battery level reading 0
Some vehicles report 0 from the `mycar` endpoint while the charging
status endpoint has the real value. v0.2.7 added a fallback: if
`mycar` says 0, use the value from charging status; only show 0 if
both are 0. **Generally useful pattern:** cross-validate scalars
across endpoints when one endpoint is known to be flaky.

### 5.10 Target-SoC slider minimum
v0.2.10 set a minimum of 50 for Born / Raval / Tavascan. Other models
may differ. **Build the min/max from the API capability where possible**
and only hard-code per-model as a last resort.

### 5.11 Config-flow blockage when adding a new device
Issues 65 and 66, fixed in v0.2.11. Class of bug worth watching:
the very first config-flow step deadlocking on an awaitable / on a
network call without timeout. **Add explicit timeouts and a unit test
around the first step.**

### 5.12 Init-time vehicle missing / deactivated
v0.2.14 added: if a previously-configured vehicle is not found or is
deactivated at startup, log a warning and (in the deactivated case)
raise a HA notification. **Good pattern — don't silently drop
entities.**

### 5.13 hassfest validation failure from URLs in translations
v0.2.7 had to remove URLs from `strings.json` / translation files
because hassfest CI rejected them. **If `vag-connect-ha` aims for the
official HACS default repo or core inclusion, run hassfest and
hacs/action in CI from day one.**

### 5.14 find_path() crashes on unexpected payload shapes
v0.2.9 added try/except in `utilities.find_path()` (issue 58).
**Generic lesson:** defensive parsing on a vendor JSON whose shape
mutates without notice.

### 5.15 Long delay in charge-status updates
Fixed in v0.2.15 (issue 68). Likely a stale-cache / bucket-coalescing
bug. **Worth mirroring in tests:** changes pushed via push-notification
should invalidate the relevant bucket cache immediately rather than
waiting for the next poll.

## 6. Suggested layout for `its-me-prash/vag-connect-ha`

(Already largely matches our current layout — see ARCHITECTURE_DECISION.md
for our actual structure.)

## 7. Concrete suggestions back to `WulfgarW/homeassistant-pycupra`

Highest-leverage upstream improvements based on the research above:

1. Add a reauth config-flow step so users can update credentials after a
   password change without deleting and re-adding the device (addresses
   the most common Discord question; preserves long-term statistics).
2. Add a "Reload" service / button that re-runs discovery without
   removing the entry.
3. Surface "API requests remaining today" as a sensor and raise a HA
   repair issue when it hits 0.
4. Default the push-notification handler to a log + ignore path for
   unknown types and add a regression test fixture per known type so
   adding a new one is one-line.
5. Add CI running hassfest and hacs/action to prevent the strings.json
   URL-style regression from coming back.
6. Add timezone-safe parsing of estimated-end timestamps with an
   explicit unit test for year-end / DST boundaries (issue #33 class).
7. Draft a `FAQ.md` section on the privacy-setting matrix
   (Share / Use / stricter) and exactly which entities degrade for each.
8. Document the entity-ID-stability policy so users know that removing
   and re-adding preserves dashboards but loses long-term statistics,
   and that schema-changing fixes will use new entity IDs rather than
   mutate old ones.
