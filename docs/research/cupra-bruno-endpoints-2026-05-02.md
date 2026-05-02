# Cupra/SEAT WeConnect — Bruno Collection Endpoint Reference

**Source:** https://github.com/Timwun/Cupra-WeConnect-Bruno-Collection
**Author:** Timwun · **License:** see repo · **Files crawled:** 53 .bru + collection.bru
**Base host:** `https://ola.prod.code.seat.cloud.vwgroup.com` (unless noted)
**Auth (collection.bru):** OAuth2 authorization_code, IDP `identity.vwgroup.io/oidc/v1/{authorize,token}`,
client_id `3c756d46-...@apps_vw-dilab_com`, scope `openid profile nickname birthdate phone cars badge dealers`,
token placed as `Authorization: Bearer <access_token>`. Most endpoints use `auth: inherit` (= bearer from collection).

---

## Section 1 — Endpoints we ALREADY have

- `V5 Users vehicles mycar.bru` (seq 41) — GET `/v5/users/{userId}/vehicles/{vin}/mycar` — **matches**.
- `V1 ParkingPosition.bru` (seq 16) — GET `/v1/vehicles/{vin}/parkingposition` — **matches**, doc shows `{lat, lon, updatedAt}`.
- `V1 Ranges.bru` (seq 18) — GET `/v1/vehicles/{vin}/ranges` — **matches**.
- `V2 Status.bru` (seq 35) — GET `/v2/vehicles/{vin}/status` — **matches**.
- `V1 Charging Status.bru` (seq 5) — GET `/v1/vehicles/{vin}/charging/status` — **matches** (note: there is also a newer `/vehicles/{vin}/charging/status` without `/v1` prefix, see Section 2).
- `V1 Charging Info.bru` (seq 9) — GET `/v1/vehicles/{vin}/charging/info` — **matches**.
- `V2 Climatisation settings.bru` (seq 36) — GET `/v2/vehicles/{vin}/climatisation/settings` — **matches** GET; we currently POST start at `/v1/.../climatisation/requests/start` (Section 5 confirms that's the correct path).
- `V1 Maintenance.bru` (seq 14) — GET `/v1/vehicles/{vin}/maintenance` — **matches**.
- `V1 Remote Availability - Connection.bru` (seq 2) — GET `/v1/vehicles/{vin}/remote-availability` — **matches**, returns `{remote-availability: "online"}`.
- `V1 Capabilities.bru` (seq 4) — GET `/v1/user/{userId}/vehicle/{vin}/capabilities` — **diff**: spec uses singular `user`/`vehicle`, our impl currently calls `/v1/vehicles/{vin}/capabilities`. Worth verifying which still works in prod.
- `V2 Renders` — collection has `/v1/vehicles/{vin}/renders` (seq 20), we use `/v2/...`. Likely both exist; keep ours.
- `V1 Honk and Flash.bru` (seq 33) — POST `/v1/vehicles/{vin}/honk-and-flash` — **matches**, no body, just `Content-Type: application/json`.
- Charging actions: `V1 Charging Actions Update Settings.bru` (seq 26) → POST `/v1/vehicles/{vin}/charging/actions/update-settings` body `{"targetSocPercentage":80}`. Confirms our `/charging/actions` path; spec shows the precise sub-route + body for SoC change.

---

## Section 2 — NEW endpoints, HIGH PRIORITY (target v1.17.x)

### Auxiliary heating (Standheizung) — closes long-standing ICE/PHEV requests
- **`V1 Auxiliary Heating Start.bru` (seq 29)** — POST `/v1/vehicles/{vin}/auxiliary-heating/start`
  Headers: `Content-Type: application/json`, **`SecToken:`** (S-PIN-derived, required, empty in spec)
  Body: none
- **`V1 Auxiliary Heating Stop.bru` (seq 30)** — POST `/v1/vehicles/{vin}/auxiliary-heating/stop`
  Headers: `Content-Type: application/json` (no SecToken)
- **Note:** new feature for v1.17.x for PHEV/ICE owners. Need S-PIN flow first (see Sect. 5).

### Ventilation
- **`V1 Ventilation Start.bru` (seq 31)** — POST `/v1/vehicles/{vin}/ventilation/start` — no body.
- **`V1 Ventilation Stop.bru` (seq 32)** — POST `/v1/vehicles/{vin}/ventilation/stop` — no body.
- **Note:** Pair with aux-heating; same v1.17.x.

### Window heating (rear/front defrost)
- **`Windowheating Start.bru` (seq 50)** — POST `/vehicles/{vin}/windowheating/requests/start` (no `/v1` prefix)
- **`Windowheating Stop.bru` (seq 51)** — POST `/vehicles/{vin}/windowheating/requests/stop`
  Both: no body, `Content-Type: application/json`. Returns `{requestId}`.
- **Note:** new switch entity for v1.17.x; many users have asked for this on rainy mornings.

### Battery care / charging targets (granular control)
- **`V1 Charging Battery Care.bru` (seq 10)** — GET `/v1/vehicles/{vin}/charging/battery-care` → `{enabled: true}`
- **`V1 Charging Battery Care Target.bru` (seq 11)** — GET `/v1/vehicles/{vin}/charging/battery-care/target` → `{targetSocPercentage: 80}`
- **Note:** Lets us expose a dedicated `binary_sensor.battery_care` + `number.battery_care_soc`. Pair with the existing `actions/update-settings` POST. Suggested v1.17.x.

### Charging settings GET/POST (full payload)
- **`V1 Charging Settings GET.bru` (seq 6)** — GET `/v1/vehicles/{vin}/charging/settings` → `{maxChargeCurrentAc, autoUnlockPlugWhenCharged, targetSocPercentage, defaultMaxTargetSocPercentage}`
- **`V1 Charging Settings.bru` (seq 27)** — POST same URL, body:
  ```json
  {"maxChargeCurrentAc":"maximum","autoUnlockPlugWhenChargedAc":"off","targetSoc":80.0}
  ```
- **Note:** unlocks select-entities for max AC current ("maximum"/"reduced") and auto-unlock-plug. v1.17.x.

### Climatisation settings POST + timers
- **`V2 Climatisation Settings Post.bru` (seq 39)** — POST `/v2/vehicles/{vin}/climatisation/settings`
  ```json
  {"windowHeatingEnabled":false,"zoneFrontLeftEnabled":false,
   "zoneFrontRightEnabled":false,"targetTemperature":22.0,
   "targetTemperatureUnit":"celsius","climatisationAtUnlock":false}
  ```
- **`Climatisation Requests Timers.bru` (seq 49)** — POST `/vehicles/{vin}/climatisation/requests/timers` (no `/v1`), body has up to N timers with `{id, enabled, recurringTimer:{startTime (UTC), recurringOn:{mondays..sundays}}}`. Returns `{requestId}`.
- **`Climatisation Timers.bru` (seq 42)** — GET `/vehicles/{vin}/climatisation/timers` (despite spec docs showing charging-state response — likely doc copy-paste error in upstream).
- **Note:** Adds `number.target_temperature` write, zone-switches, and timer entities. v1.17.x for settings POST; timers in v1.18.0.

### Climatisation/charging start-stop without `/v1` (newer route)
- **`Climatisation Stop.bru` (seq 48)** — POST `/vehicles/{vin}/climatisation/requests/stop`
- **`Charging Start.bru` (seq 47)** / **`Charging Stop.bru` (seq 46)** — POST `/vehicles/{vin}/charging/requests/{start,stop}`
- **`Charging Status.bru` (seq 43)** — GET `/vehicles/{vin}/charging/status` returns richer payload (`battery.cruisingRangeElectric_km`, `charging.chargeMode`, `plug.externalPower`)
- **`Charging Settings.bru` (seq 44)** — GET `/vehicles/{vin}/charging/settings` returns `batteryCareModeEnabled`, `batteryCareTargetSocPercentage` directly
- **`Charging Profiles.bru` (seq 45)** — GET `/vehicles/{vin}/charging/profiles` includes `nextChargingTimer`
- **Note:** Suggests Cariad migrated some endpoints away from `/v1`. **Action:** A/B test in v1.17.x — keep `/v1` fallback, prefer new path. May fix users hitting 404s on newer firmware.

### Warning lights — new diagnostic surface
- **`V3 Vehicles Warninglights.bru` (seq 40)** — GET `/v3/vehicles/{vin}/warninglights`
  Returns `{statuses: [{text, category, priority, priorityGroup, icon (base64 PNG), iconColor, serviceLead}]}`.
- **Note:** Big win — users can have HA notify them on warning lights ("vehicle key not in vehicle", "ABS error", "tyre pressure", etc.). New `sensor` per warning + composite `binary_sensor.has_warnings`. v1.18.0.

---

## Section 3 — NEW endpoints, MEDIUM PRIORITY

- `V2 Users garage vehicles.bru` (seq 38) — GET `/v2/users/{userId}/garage/vehicles` — alternative garage list.
- `V1 Garage.bru` (seq 3) — GET `/v1/users/{userId}/garage` — full vehicle metadata (colors, wheels, model year, salesType). Useful for device_info enrichment.
- `V1 Mileage.bru` (seq 15) — GET `/v1/vehicles/{vin}/mileage` → `{mileageKm}`. Simple sensor.
- `V1 Driving data.bru` (seq 22) — GET `/v1/vehicles/{vin}/driving-data/{cyclic|longTerm|shortTerm}` — trip statistics.
- `V1 Driving data Last.bru` (seq 23) — GET `/v1/vehicles/{vin}/driving-data/longTerm/last` — last completed trip.
- `V1 Vehicle Measurements Engines.bru` (seq 13) — GET `/v1/vehicles/{vin}/measurements/engines` — engine telemetry.
- `V1 Vehicles Permissions.bru` (seq 17) — GET `/v1/vehicles/{vin}/permissions` — needed to gate features by user-role.
- `V1 Notifications.bru` (seq 19) — GET `/v1/vehicles/{vin}/notifications` — backend notifications stream.
- `V1 Climatisation Status.bru` (seq 12) — GET `/v1/vehicles/{vin}/climatisation/status` — alt path to current climatisation state.
- `V1 Charging Modes.bru` (seq 8) / `V2 Charging Modes.bru` (seq 37) — GET `/v{1,2}/vehicles/{vin}/charging/modes` → `{selected, available:[...]}`. Powers a `select` entity for mode (immediate/manual/timed).
- `V1 Charging Profiles.bru` (seq 7) — GET `/v1/vehicles/{vin}/charging/profiles` → list of charging profiles.
- `VW UserInfo.bru` (seq 1) — GET `https://identity-userinfo.vwgroup.io/oidc/userinfo` — IdP user info (email, name, picture). Useful for first-time setup confirmation in HA config flow.
- **Charging statistics (different host!)** — `Charging Statistics.bru` (seq 52) POST `https://prod.emea.mobile.charging.cariad.digital/charging_statistics` body `{startedAfter, startedBefore, selectedFilterOptions:[{id:VIN, filterType:"VEHICLE"}], fetchFilterOptions:false, capabilities:[]}`. Powers a "kWh charged this month" sensor.
- `Charging Statistics Power Curve.bru` (seq 53) — GET `https://prod.emea.mobile.charging.cariad.digital/charging_statistics/{sessionId}/power-curve` — charging-curve over time per session.

---

## Section 4 — SKIP / unclear value

- `V1 Destination.bru` (seq 34) — PUT `/v1/users/vehicles/{vin}/destination` — sends a navigation destination to the car. Useful but rarely automatable from HA, and incorrect URL pattern (`/users/vehicles/...` without userId looks suspicious — may have been wrong in upstream).
- `V1 Charging Points.bru` (seq 28) — POST `/v1/charging/points` body `{center:{lat,lon}, radius:5000}` — public charge-point lookup. Out of scope for HA integration.
- `V1 Shop articles.bru` (seq 24) — GET `/v1/shop/vehicles/{vin}/articles` — Cupra shop catalog. No HA value.
- `V1 Lead History.bru` (seq 21) — GET `/v1/users/{userId}/vehicles/{vin}/leads/history` — sales-leads, useless for HA.

---

## Section 5 — Authentication patterns observed

1. **Bearer token** for almost everything: `Authorization: Bearer <access_token>` injected automatically (`auth: inherit` from collection.bru OAuth2 block). The IdP is `identity.vwgroup.io/oidc/v1/{authorize,token}`. Already what we do.
2. **`SecToken` header** appears on **`V1 Auxiliary Heating Start`** (and is empty in the spec, indicating a per-call value the user must supply). This is the **S-PIN-derived** confirmation token used by the SEAT/Cupra app for security-sensitive remote actions. Notably, neither `lock`/`unlock` nor charging-start show SecToken in this collection — but in our impl we already pass it for lock/unlock. **Aux-heating-start needs SecToken; aux-heating-stop does NOT.** This is the only NEW SecToken-requiring endpoint we'd add in v1.17.x.
3. **Locale headers** on a few endpoints:
   - `V1 Shop articles`: `Accept-Language: de_DE`
   - `Charging Statistics` & `Power Curve`: `Accept-Language: de-DE`, `Accept-Encoding: gzip`
   We currently do not always send `Accept-Language`. Low risk, but worth setting from HA's configured locale for shop/statistics.
4. **Two host families:**
   - `ola.prod.code.seat.cloud.vwgroup.com` — main vehicle API (everything we use today)
   - `prod.emea.mobile.charging.cariad.digital` — charging statistics & power curve (new host, would need a second client)
5. **No special X-* headers** observed beyond those above. No CSRF, no signed-request, no nonce headers.

---

## Section 6 — Implementation roadmap

**v1.17.x (next minor):**
1. Window heating start/stop (`switch.window_heating`) — easiest win, no SecToken.
2. Ventilation start/stop (`switch.ventilation`).
3. Auxiliary heating start/stop (`switch.aux_heating`) — gate behind S-PIN config; reuse SecToken flow.
4. Battery care GET endpoints + expose as `binary_sensor` + `number`.
5. Charging settings GET/POST → `select.max_charge_current_ac`, `switch.auto_unlock_plug`.
6. Climatisation settings POST → make `number.target_temperature` and zone switches writeable.
7. A/B fallback: try `/vehicles/{vin}/charging/{status,settings,requests/start}` first, fall back to `/v1/...`.

**v1.18.0:**
8. Warninglights (`sensor.warning_*` + composite `binary_sensor.has_warnings` + persistent_notification on new lights).
9. Climatisation timers (CRUD service `cupra.set_climatisation_timer`).
10. Mileage sensor (trivial, but defer because `mycar` already exposes it).
11. `select.charging_mode` from `/v2/.../charging/modes`.

**v1.19.0+:**
12. Charging statistics — separate Cariad client, `sensor.kwh_this_month`.
13. Power-curve graph data (long-term storage attribute on charging_session sensor).
14. Driving data trips — `sensor.last_trip_distance`, `sensor.last_trip_avg_consumption`.
15. Notifications stream (poll-or-push? unclear).

---

## Section 7 — Open questions

1. **Climatisation Timers GET (seq 42) response shape** — the upstream `docs` block actually shows the **charging status** payload, which is clearly a copy-paste error. We need a real capture from a running car before we can model the timer entities. Suggest asking a beta tester to dump the response.
2. **Newer non-`/v1` paths** (`/vehicles/{vin}/charging/...`, `/vehicles/{vin}/climatisation/requests/...`, `/vehicles/{vin}/windowheating/...`) — does Cariad still serve the `/v1`-prefixed variants for older models, or are both paths universally available? Need a compat probe before we switch defaults.
3. **`SecToken` lifetime & generation** — the collection shows the header but not how it's derived. Our existing lock/unlock code already produces it; verify the same token works for `auxiliary-heating/start` (likely yes — same `cariad/api/seat_cupra.py:request_secure_token` flow).

---

*Generated 2026-05-02 from the 53 .bru files at upstream HEAD. Re-run extraction if the upstream repo updates (Bruno files are tiny — full re-crawl is ~2 minutes via `gh api`).*
