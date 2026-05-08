# External-Blocked Roadmap & Tester-Recruiting

> **Status:** v1.24.2 shipped 2026-05-08. This document tracks all ROADMAP
> items that are technically *ready to ship* but require external input —
> live-tests, community testers, brand-owner reproduction reports — before
> code can land or be activated.
>
> **Audience:** Community contributors, brand-track testers, Prash's own
> maintainer-fleet (Audi A4 B9, Audi Q5 2021, VW Golf 7 2015 — all with
> active Connect+ subscriptions).
>
> **Why this exists:** the 2026-05-08 Audit found that 6 internal
> ROADMAP items had no GitHub issue → no public visibility → no way for
> community testers to self-select. This doc + the GitHub issues spawned
> from it close that visibility gap.

---

## How to volunteer as a tester

If you own one of the brands/vehicles listed below and have an active
Connect+ subscription:

1. **Open the corresponding GitHub issue** (linked per item below) and
   comment "I can test on `<brand> <model> <year>`".
2. **Provide the diagnostics export** when asked — Settings → Devices &
   Services → VAG Connect → ⋮ → "Diagnostik herunterladen". The export
   is auto-redacted (VINs masked, GPS rounded, tokens stripped — see
   `PRIVACY.md` for full list).
3. **Be ready for 1-2 short test cycles** — usually a "try this PR
   build, tell me what HA log says" loop. Most testers wrap up in
   30 minutes total.

---

## Track 1: MBB Legacy Phase 2 — Lock / Climate / Charger Fallbacks

**Status:** `cariad/_mbb.py` exists since v1.21.0 with Phase 1 (`command_wake`
auto-fallback Cariad → MBB on wrapper-404). Phase 2 ports the same fallback
pattern to write-side commands so the full set of remote actions works on
older MIB3 vehicles.

**Affected models** (verified via 8 user reports 2026-05-07):
- Audi A4 B9 (2018-2022) — IDK + MBB
- Audi Q5 2021 — IDK + MBB
- Audi A6 C8 (2018+) — likely (untested)
- VW Golf 7 (2015+) — IDK + MBB legacy
- VW Passat B8 (2015+) — likely (untested)

**Phase 1 (shipped v1.21.0):** `command_wake` proven to fall back from
Cariad-BFF wrapper-404 to MBB legacy `mal-1a.prd.ece.vwg-connect.com`.

**Phase 2 (next): Port to:**
- `command_lock` / `command_unlock` (with S-PIN flow on MBB)
- `command_start_climate` / `command_stop_climate`
- `command_start_charging` / `command_stop_charging`
- `command_set_target_soc`

**Blocker:** Need maintainer-fleet live confirmation that the v1.21.0
wake fallback works on Prash's 3 vehicles. Until then we can't be
confident that MBB endpoints respond correctly to setter commands —
write-side has different auth requirements (S-PIN), error shapes
(MBB-specific 400 codes), and timing (poll-back after async accept).

**What we need:**
- Prash himself (or a 2nd Audi A4 B9 / Q5 2021 / Golf 7 2015 owner)
  runs HA with v1.21.0+, triggers a wake from the integration, watches
  the HA log for `Cariad → MBB fallback engaged for VIN ***xxxxxx`.
  If the fallback fires AND the car responds within 10s → green light
  for Phase 2.
- A diagnostic export from a single failed write-side command (lock or
  climate-start) on one of those models, so we can see the exact
  Cariad-BFF response shape and confirm MBB has a matching setter URL.

**ETA after blocker clears:** 1 day coding (mechanical port of the
v1.21.0 pattern) + 1-2 days iteration with the tester.

**GitHub issue:** TODO — to be opened during cleanup-pass.

---

## Track 2: Push Phase 2 Wire-In (3 brand tracks)

**Status:** Phase 1 Foundation komplett shipped:
- v1.18.0 — Skoda MQTT (`cariad/push/skoda_mqtt.py`)
- v1.19.0 — CUPRA/SEAT FCM (`cariad/push/cupra_seat_fcm.py`)
- v1.23.0 — Audi/VW Cariad FCM (`cariad/push/audi_vw_fcm.py`)

All three have: `PushManager` base class, brand-validation, identical
lifecycle + reconnect-backoff (5s→600s ±10% jitter), lazy-import for
`firebase-messaging` (and `aiomqtt` for Skoda). Activation toggles in
ConfigFlow exist but default OFF.

**Phase 2:** Replace foundation stubs with real network code. Per-brand
verifications needed.

### 2A. Skoda MQTT Push (Skoda Connect+ tester needed)

**What we need from the tester:**
- Skoda account with active Connect+ subscription
- Willingness to:
  1. Install firebase-messaging + aiomqtt (`pip install firebase-messaging aiomqtt` inside HA's venv, or HACS dep override)
  2. Enable the `enable_push_mqtt` toggle in integration options
  3. Provide the HA log (`/config/home-assistant.log`) for the first 5 minutes after enable
  4. Confirm: car action via mobile app → HA shows the change within 5 seconds (vs the standard 10-min poll)

**What that gives us:** Real FCM project ID (currently stubbed), TOTP
token scheme verification, MQTT broker auth handshake confirmation.
After 1-2 iterations, we can ship `v1.18.x` with live activation
behind a non-experimental toggle.

**ETA after tester signs up:** 2-3 days iteration.

**GitHub issue:** #57 (existing) — Phase 1 done, Phase 2 awaiting tester.

### 2B. CUPRA/SEAT FCM Push (MyCupra or MySeat tester needed)

**What we need:** identical to Skoda track but via OLA backend instead
of mysmob.
- MyCupra or MySeat account with active subscription (CUPRA Born,
  Formentor, SEAT Mii, Mii Electric, Tarraco, etc.)
- Provide the OLA `/v2/subscriptions/register` schema confirmation
  (OLA endpoint exists per pycupra reverse-engineering, but we don't
  have a verified live request/response sample)

**ETA after tester signs up:** 2-3 days iteration.

**GitHub issue:** #57 Phase 2 (sub-track CUPRA/SEAT).

### 2C. Audi/VW FCM Push (Audi or VW Connect+ tester needed)

**What we need:** Audi or VW with active Connect+ subscription, but
specifically a vehicle where the **mobile app shows push notifications**
(myAudi, We Connect ID — check Settings → Notifications → push enabled).
- Provide the Cariad-BFF `notification-subscription` endpoint URL
  (we believe it's `https://emea.bff.cariad.digital/...` but the exact
  path is unverified — user-suggested 2026-05-07 based on observed
  app behavior)
- Confirm: trigger a remote action via myAudi/We Connect mobile app,
  and HA picks up the new state within 5 seconds

**Note:** Prash's own Audi A4 B9 + VW Golf 7 are MBB-legacy vehicles —
they likely DON'T have Cariad-FCM push (push is a modern Cariad-BFF
feature). So Prash himself can't test this; we need a 2024+ Audi e-tron
GT, ID.4, ID.7, or similar Cariad-only vehicle owner.

**ETA after tester signs up:** 2-3 days iteration.

**GitHub issue:** #57 Phase 2 (sub-track Audi/VW).

---

## Track 3: HomeRegion Full Wire-In

**Status:** v1.21.0 wired the HomeRegion-Helper into `command_wake` (the
single most-failing call for non-EU-Standard-Region MBB vehicles). The
helper itself is complete (`cariad/_home_region.py`) — discovery
endpoint, 7-day per-VIN cache, all defensive.

**Phase 2:** Wire HomeRegion into the remaining 12 call-sites in
`vw_eu.py` (and via inheritance: `audi.py`). These are read-side calls
(`get_status`, `get_capabilities`, `get_charging_profiles`, etc.) where
a non-EU vehicle currently 403s on the default EU-Standard-Region URL.

**Blocker:** Need at least one user reproducing the issue. We have
**#75 Christian** as one report (Skoda Kodiaq 2 Mk2 — MQB Evo, possibly
non-EU region) but no other reproductions.

**What we need:**
- Christian (#75) responds with: country/region (DE/AT/CH/anders?), App
  activation date, subscription status. If region != EU-Standard →
  HomeRegion full wire-in clearly the right fix.
- OR: a 2nd report from a non-EU-region user (UK, Norway, Switzerland?)
  with the same 403 pattern on read endpoints.

**ETA after blocker clears:** 1 day (mechanical: replace 12 `f"{_BASE}/..."`
expressions with `f"{await self._base_for_vin(vin)}/..."`).

**GitHub issue:** #75 (existing) — closes when wire-in ships.

---

## Track 4: Charging-Profile Write-Side Live-Test

**Status:** Slated for v1.25.0 PR-D (see `SPRINT_C_v1.25.0_PLAN.md`).
Code will ship with EXPERIMENTAL marker because we have read-side
verified but write-side is API-discovery-confidence-only.

**What we need post-v1.25.0:**
- Per-brand: 1 user runs the new `vag_connect.set_charging_profile`
  service, confirms target_soc actually changes when next polled.
- For Skoda: any MyŠkoda app user with charging profiles configured.
- For VW EU: ID.x or Passat GTE user.
- For SEAT/CUPRA: MyCupra/MySeat user (could be the same as Track 2B).
- For VW NA: ID.4 NA user.

**ETA after testers confirm:** Drop EXPERIMENTAL marker in v1.25.x patch.

**GitHub issue:** #25 + #31 (existing).

---

## Track 5: Theft / Alarm Binary Sensor

**Status:** Long-standing #33 in P2 backlog. Needs API-Endpoint research
— we believe `alarmStatus` is published as a job inside CARIAD
selectivestatus but haven't verified.

**What we need:**
- A user with a Cariad-BFF vehicle (Audi e-tron, VW ID.x, etc.) who
  experiences an alarm trigger (parking sensor false-alert, car alarm
  going off) and exports diagnostics within 5 minutes of the event.
- We can then see if `alarmStatus` appears in the export, and at what
  selectivestatus path.

**ETA after capture:** 0.5 day (parser + sensor + Bruno fixture).

**GitHub issue:** #33 (existing).

---

## Track 6: Departure-Timer UI Bundle (writable)

**Status:** Read-side already shipped (v1.16.0 introduced the HA `time`
platform). Write-side will land as part of v1.25.0 PR-D. After that,
this track folds into Track 4 (live-test pattern).

**GitHub issue:** none — folds into v1.25.0 release notes.

---

## Track 7: Klima-Modus / heaterSource exposure

**Status:** `heaterSource` field silenced v1.17.5 (we know it exists for
ID.x electric heat pumps). Question: read-only sensor, or writable
select?

**What we need:**
- ID.4 / ID.7 / e-tron user with electric heat-pump configuration
- Confirms via app that they can SWITCH between "electric" and "fuel"
  heater modes (some PHEVs allow this)
- If yes → writable `select.<vin>_heater_source`
- If no → read-only `sensor.<vin>_heater_source`

**ETA after tester confirms:** 0.5 day.

**GitHub issue:** TODO — to be opened.

---

## Summary table — all external-blocked tracks

| # | Track | Blocker | ETA after blocker | Effort post-clear |
|---|---|---|---|---|
| 1 | MBB Phase 2 (lock/climate/charger) | Maintainer-fleet wake live-test (Prash's A4 B9 / Q5 / Golf 7) | days | 1d code + 1-2d iteration |
| 2A | Skoda MQTT Push live | Skoda Connect+ tester | weeks (none signed up) | 2-3d |
| 2B | CUPRA/SEAT FCM Push live | MyCupra/MySeat tester | weeks | 2-3d |
| 2C | Audi/VW Cariad FCM Push live | Audi/VW Connect+ tester (Cariad-modern vehicle) | weeks | 2-3d |
| 3 | HomeRegion full wire-in | #75 Christian region info OR 2nd non-EU report | weeks | 1d |
| 4 | Charging-Profile write live-test | Per-brand single user post-v1.25.0 | weeks | 0.5d/brand |
| 5 | Theft/Alarm binary sensor | User captures alarm event diagnostics | weeks | 0.5d |
| 7 | heaterSource select/sensor | ID.x heat-pump user confirms write capability | weeks | 0.5d |

---

## How Prash should proceed

**Top priority** (unblocks the most other tracks): **Test his own
maintainer-fleet on v1.21.0 wake fallback.** A single evening with the
3 cars settles MBB Phase 2 (Track 1) and validates the entire
HomeRegion machinery used by Track 3.

**Second priority**: Open GitHub issues for tracks 1, 2A, 2B, 2C, 3, 5,
7 so community testers can self-select. Currently 6 of these have no
public tracker → no recruitment funnel.

**Third priority** (parallel, no dependency): Ship v1.25.0 (Sprint C
plan). After v1.25.0 ships, Track 4 becomes actionable.

---

*Last updated: 2026-05-08 — post v1.24.2 ship.*
