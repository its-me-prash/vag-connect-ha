# Migration research: `mitch-dc/volkswagen_we_connect_id` → `vag-connect-ha`

**Date:** 2026-05-03 · **Author:** research session · **Status:** draft for README/SEO + migration guide intake

---

## A) Repo status

- **Archived:** YES — archived at **2025-10-29 13:01:50 UTC**. Source: `gh repo view mitch-dc/volkswagen_we_connect_id --json isArchived,archivedAt`.
- **Last push:** **2025-10-29 13:01:38 UTC** (same moment as archival).
- **Stars/forks at archive:** 254 stars · 69 forks.
- **Deprecation notice (verbatim, README):** *"Because I no longer have access to a Volkswagen ID vehicle, development on this integration has been discontinued."* — https://github.com/mitch-dc/volkswagen_we_connect_id/blob/main/README.md
- **Maintainer's recommended alternative:** None named in the README. The only forward-pointer in tracker conversation is issue [#295](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/295) ("Switch from WeConnect library to CarConnectivity") + draft [PR #300](https://github.com/mitch-dc/volkswagen_we_connect_id/pull/300) by `@anothertobi` to migrate to `tillsteinbach/CarConnectivity` — both abandoned (PR closed unmerged 2026-01-11).

## B) Top 10 open issues (problem class)

| # | Created | Title | Class |
|---|---------|-------|-------|
| [306](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/306) | 2025-10-12 | Unknown attribute | new-API-field (Vehicle Data Scout territory) |
| [305](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/305) | 2025-09-30 | Fix/change odometer state_class to total_increasing | bug — wrong state_class (LTS-breaking) |
| [302](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/302) | 2025-08-07 | Missing option in warning lights (`COMFORT` category) | new-API-field |
| [301](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/301) | 2025-07-17 | Show status messages | feature-request |
| [299](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/299) | 2025-04-15 | id connect not working since a few days | auth/backend break |
| [296](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/296) | 2025-03-13 | Integration stopped (cookies-region workaround failed) | auth/backend break |
| [295](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/295) | 2025-03-04 | Switch from WeConnect library to CarConnectivity | dependency EOL |
| [294](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/294) | 2025-03-02 | Login failure 0.2.6 | auth |
| [293](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/293) | 2025-02-23 | Username & password not accepted | auth |
| [292](https://github.com/mitch-dc/volkswagen_we_connect_id/issues/292) | 2025-02-19 | Integration not work | setup-fail |

**Pattern:** 6/10 are auth/login/backend-break issues, 2 new-API-field surfacing problems, 1 LTS-breaking state_class, 1 EOL dependency request. Migration drivers are clear.

## C) Last 5 closed PRs

| # | Merged? | Title | Notes |
|---|---------|-------|-------|
| [300](https://github.com/mitch-dc/volkswagen_we_connect_id/pull/300) | NO (closed 2026-01-11) | Migrate WeConnect to CarConnectivity (`@anothertobi`) | Draft — only target temp + read worked. Library-swap effort that died with the repo. |
| [290](https://github.com/mitch-dc/volkswagen_we_connect_id/pull/290) | YES 2025-02-20 | Allow changing username/password/update interval via UI (`@jonasbkarlsson`) | Already standard in vag-connect-ha. |
| [288](https://github.com/mitch-dc/volkswagen_we_connect_id/pull/288) | YES 2024-12-18 | Fix manifest.json missing separator | Cosmetic. |
| [282](https://github.com/mitch-dc/volkswagen_we_connect_id/pull/282) | YES 2024-12-09 | Add Issue link | Cosmetic. |
| [278](https://github.com/mitch-dc/volkswagen_we_connect_id/pull/278) | YES 2024-12-09 | Fix `last_trip_average_electric_consumption` state_class | Same LTS-breaking class as open #305. |

**In-flight at deprecation:** Library swap to CarConnectivity (#300). Nothing valuable to borrow — they relied on the `weconnect` package (`weconnect==0.60.8` in `manifest.json`); we own our endpoint layer in `cariad/api/vw_eu.py`.

## D) Endpoint catalog comparison

`mitch-dc/volkswagen_we_connect_id` does **not** call CARIAD-BFF endpoints directly. It delegates everything to the third-party `weconnect` PyPI package (`weconnect==0.60.8` in [manifest.json](https://github.com/mitch-dc/volkswagen_we_connect_id/blob/main/custom_components/volkswagen_we_connect_id/manifest.json), confirmed by inspection of `__init__.py` which only calls `weconnect.WeConnect()` / `_we_connect.login` / `_we_connect.api.update`). All endpoint discipline is opaque, locked to that library version.

| Capability (from their entity surface) | Their key (sensor.py / button.py / number.py) | Our endpoint (`vag-connect-ha`) | File:line |
|---|---|---|---|
| Vehicle list | `weconnect.update()` | `GET /vehicle/v1/vehicles` | `cariad/api/vw_eu.py:55` |
| Capabilities | (not exposed) | `GET /vehicle/v1/vehicles/{vin}/capabilities` | `cariad/api/vw_eu.py:125` |
| Trip statistics | (not exposed) | `GET /vehicle/v1/vehicles/{vin}/tripstatistics` | `cariad/api/vw_eu.py:161` |
| Selective status | via library | `GET /vehicle/v1/vehicles/{vin}/selectivestatus?jobs=…` (15 jobs incl. `lvBattery`, `vehicleLights`, `departureProfiles`) | `cariad/api/vw_eu.py:19-40,167` |
| Parking position | via library | `GET /vehicle/v1/vehicles/{vin}/parkingposition` | `cariad/api/vw_eu.py:173` |
| Lock / Unlock | (no entity) | `POST …/access/lock-unlock` + fallback `…/access/lock` `…/access/unlock`, S-PIN injected | `cariad/api/vw_eu.py:206-256` |
| Start/Stop charging | `start_charging` / `stop_charging` buttons | `POST …/charging/start-stop` + fallback `…/charging/start` `…/charging/stop` | `cariad/api/vw_eu.py:312-330` |
| Start/Stop climate | `start_climate` / `stop_climate` buttons (default 21°C, climatisationWithoutExternalPower=True) | `POST …/climatisation/start-stop` + fallback + PPE/PPC body shape | `cariad/api/vw_eu.py:258-310` |
| Set target SoC | `target_state_of_charge` number (10-100/10) | `POST …/charging/settings {targetSOC_pct}` | `cariad/api/vw_eu.py:450` |
| Set target temp | `target_climate_temperature` number (10-30/0.5) | `POST …/climatisation/settings {targetTemperature_C}` | `cariad/api/vw_eu.py:456` |
| Toggle AC charge speed | `toggle_ac_charge_speed` button (maximum/reduced enum) | `POST …/charging/settings {maxChargeCurrentAC_A}` (writeable 6-32A slider) | `cariad/api/vw_eu.py:477-500` |
| Set charge mode | service `set_ac_charge_speed` | `POST …/charging/settings {chargeMode}` | `cariad/api/vw_eu.py:462` |
| Set min SoC (PHEV) | (none) | `POST …/charging/settings {minChargeLimit_pct}` | `cariad/api/vw_eu.py:471` |
| Honk & Flash | (none) | `POST …/vehicleLights/flash` | `cariad/api/vw_eu.py:339` |
| Wake | (none) | `POST …/vehicleWakeup` (v1→v2 fallback) | `cariad/api/vw_eu.py:354` |
| Window heating | (binary sensor only) | `POST …/climatisation/windowheating/start-stop` | `cariad/api/vw_eu.py:502-514` |
| Departure timers | (none, sensor exposes 3 timers via library) | `POST …/climatisation/timers` (id 1-3) | `cariad/api/vw_eu.py:516-537` |
| 12V battery monitoring | (none) | `lvBattery` job in selectivestatus → `voltage_12v` + `warning_12v_low` | `cariad/api/vw_eu.py:799-802` |
| v1/v2 path auto-fallback | (none — fixed paths via library) | Per-VIN learning cache in `_post_command` | `cariad/api/vw_eu.py:381-407` |
| Multi-brand (Audi/Škoda/SEAT/CUPRA/Porsche/VW NA) | (none — VW EU only) | 7 brand clients via `cariad/api/factory.py` | `cariad/api/factory.py` |

**Endpoints they had that we don't:** none — their library-mediated surface is a strict subset.
**Our advantages:** capabilities API, trip statistics, lock/unlock with S-PIN, PPE/PPC body conditional, v1↔v2 path fallback, `lvBattery`, departure-profile jobs, 6 additional brands.

## E) Migration guide draft

### Pre-migration checklist
1. Open Settings → Devices & Services → Volkswagen We Connect ID → click any device → note your **VIN** and the entity-ID prefix (typically your **car nickname**, e.g. `myid_*`).
2. Export automations + scripts that reference `sensor.myid_*`, `button.myid_*`, `number.myid_*` (Settings → Automations → ⋮ → Download).
3. Note current entity friendly names if you renamed anything — vag-connect-ha uses different IDs.
4. Long-term statistics: identify which sensors you want preserved (typically odometer, electric consumption, charge power). Decide whether to **rename new entity → old entity ID** (preserves LTS) or accept fresh history.
5. Backup HA before removing the old integration.

### Install vag-connect-ha
1. HACS → ⋮ → Custom repositories → add `https://github.com/its-me-prash/vag-connect-ha` → category Integration → Add.
2. HACS → Integrations → search "VAG Connect" → Download → Restart HA.
3. Settings → Devices & Services → Add Integration → "VAG Connect".
4. Pick brand: **Volkswagen EU (WeConnect ID)** for ID.3/4/5/7/Buzz, Tiguan, Passat, Golf etc. (other 6 brands available — Audi, Škoda, SEAT, CUPRA, Porsche, VW US/CA).
5. Enter your We Connect ID app credentials. S-PIN is optional (only needed for lock/unlock on premium models).
6. Default poll interval is 10 min (raised from 5 min in v1.17.0 for API quota — see `const.py:49`).

### Remove the old integration
After verifying vag-connect-ha works: Settings → Devices & Services → Volkswagen We Connect ID → ⋮ → Delete.

### Entity ID mapping (best-effort, EV/PHEV common cases)
Old IDs use `{nickname}_{camelCaseKey}`; new IDs use `{nickname}_{snake_case_key}`. Drop the old domain prefix `volkswagen_we_connect_id_` if HA generated one.

| Old (mitch-dc) | New (vag-connect-ha) |
|---|---|
| `sensor.{nick}_state_of_charge` (`currentSOC_pct`) | `sensor.{nick}_battery_soc` |
| `sensor.{nick}_target_state_of_charge` (`targetSOC_pct`) | `sensor.{nick}_target_soc` |
| `sensor.{nick}_range` (`cruisingRangeElectric`) | `sensor.{nick}_electric_range_km` (+ new `combustion_range_km`, `total_range_km`) |
| `sensor.{nick}_odometer` | `sensor.{nick}_odometer_km` |
| `sensor.{nick}_charging_state` | `sensor.{nick}_charging_state` |
| `sensor.{nick}_charge_power` (`chargePower_kW`) | `sensor.{nick}_charging_power_kw` |
| `sensor.{nick}_charge_rate` (`chargeRate_kmph`) | `sensor.{nick}_charging_rate_kmh` |
| `sensor.{nick}_remaining_charging_time` | `sensor.{nick}_charge_complete_eta` (datetime, not minutes) |
| `sensor.{nick}_charge_type` | `sensor.{nick}_charging_type` |
| `sensor.{nick}_climatisation_state` | `sensor.{nick}_climatisation_state` |
| `sensor.{nick}_target_temperature` | `sensor.{nick}_target_temperature` |
| `sensor.{nick}_plug_connection_state` | `sensor.{nick}_plug_state` |
| `sensor.{nick}_door_lock_status` | `binary_sensor.{nick}_doors_locked` |
| `binary_sensor.{nick}_car_is_online` (`isOnline`) | `sensor.{nick}_connection_state` (online/standby/offline tri-state) |
| `sensor.{nick}_health_inspection` (`inspectionDue` days) | `sensor.{nick}_service_due_in_days` (+ `service_due_at` date) |
| `sensor.{nick}_health_inspection_km` | `sensor.{nick}_service_km` |
| `sensor.{nick}_oil_inspection_days` | `sensor.{nick}_oil_service_due_in_days` |
| `sensor.{nick}_oil_inspection_km` | `sensor.{nick}_oil_service_km` |
| `sensor.{nick}_fuel_level` | `sensor.{nick}_fuel_level` |
| `sensor.{nick}_gasoline_range` | `sensor.{nick}_combustion_range_km` |
| `button.{nick}_start_climate` | `button.{nick}_start_climate` (+ optional climate entity) |
| `button.{nick}_stop_climate` | `button.{nick}_stop_climate` |
| `button.{nick}_start_charging` | `button.{nick}_start_charging` (+ switch) |
| `button.{nick}_stop_charging` | `button.{nick}_stop_charging` |
| `button.{nick}_toggle_ac_charge_speed` | `number.{nick}_max_charge_current` (writeable 6-32A) |
| `number.{nick}_target_state_of_charge` | `number.{nick}_target_soc` |
| `number.{nick}_target_climate_temperature` | `number.{nick}_target_temperature` |
| `device_tracker.{nick}_tracker` | `device_tracker.{nick}` |
| (none) | new: `sensor.{nick}_voltage_12v`, `binary_sensor.{nick}_warning_12v_low`, `sensor.{nick}_wake_count_today`, per-light binary sensors, `sensor.{nick}_parking_address`/`_city` |

### Long-term-statistics preservation
Two options after install:
1. **Rename new entity → old entity ID** — Settings → Devices & Services → click new entity → settings cog → Entity ID. This stitches LTS continuity for renamed sensors. Recommended for `odometer_km`, `charging_power_kw`, electric consumption.
2. **Use the Statistics → Adjust Sum tool** to back-fill if the unit changed (some old sensors had wrong `state_class`, see closed #305 — ours are correct from day one).

## F) SEO recommendations

**Add to README.md (top of file, near the existing "Multi-Brand-Nachfolger" line) and to HACS description:**

Phrases:
- `WeConnect ID` · `We Connect ID` · `wecoid` · `volkswagen_we_connect_id` · `mitch-dc` (deprecated alternative names)
- `MyAudi` · `myAudi` · `audi connect` · `audiconnect` · `audiconnectpy` · `audi_connect_ha` (deprecated single-brand integrations)
- `Skoda Connect` · `skodaconnect` · `mySkoda` · `MyCupra` · `MySEAT` · `pycupra` · `myskoda` · `mysmob`
- `My Porsche` · `Porsche Connect`
- `CARIAD` · `CARIAD BFF` · `emea.bff.cariad.digital` · `IDK` (Identity Kit auth)

Models (helps users searching for vehicle-specific instructions):
- `ID.3`, `ID.4`, `ID.4 GTX`, `ID.5`, `ID.7`, `ID.7 Tourer`, `ID.7 Limousine`, `ID. Buzz`, `ID Buzz`
- `Tiguan`, `Tiguan eHybrid`, `Passat`, `Passat GTE`, `Passat B7/B8/B9`, `Golf 7 GTE`, `Golf 8 eHybrid`, `Multivan eHybrid`, `Touareg PHEV`
- `Audi e-tron GT`, `RS e-tron GT`, `Q4 e-tron`, `Q5 e-tron`, `Q6 e-tron`, `A6 e-tron`, `A3 e-tron`, `A6 PHEV`, `A8 PHEV`, `S6 C8`
- `Skoda Enyaq`, `Enyaq Coupé`, `Octavia iV`, `Superb iV`, `Kodiaq iV`, `Elroq`
- `SEAT Mii electric`, `SEAT Leon e-Hybrid`, `SEAT Tarraco PHEV`
- `CUPRA Born`, `CUPRA Tavascan`, `CUPRA Leon e-Hybrid`, `CUPRA Formentor PHEV`
- `Porsche Taycan`, `Macan EV`, `Cayenne PHEV`, `Panamera PHEV`
- `VW ID.4 US`, `VW ID.4 Canada`, `Atlas`, `Tiguan US`

HA-forum / problem-class search terms ex-users type:
- "WeConnect login broken", "We Connect ID Home Assistant integration", "MyAudi Home Assistant"
- "Skoda Connect deprecated alternative", "mitch-dc archived"
- "CARIAD 403 spin_error", "CARIAD 404 vehicleWakeup", "weconnect EOL"
- "ID.4 charging sensor unavailable", "ID Buzz Home Assistant"

Suggested README badge / one-liner:
> *Drop-in upgrade from `volkswagen_we_connect_id` (mitch-dc, archived 2025-10-29), `homeassistant-skodaconnect`, `audi_connect_ha`, `myskoda`, `pycupra` — one HACS integration for all 7 VAG brands.*

## G) Open questions

1. **Exact pre-deprecation user complaints in PR comments** — only ~12 open issues sampled; there may be additional patterns in older closed issues (>30) we didn't drill into.
2. **CarConnectivity migration draft (#300) code** — abandoned, not inspected line-by-line. Possibly some endpoint shape hints in `tillsteinbach/CarConnectivity-connector-volkswagen` worth a separate research pass.
3. **HACS Default discoverability** — vag-connect-ha is currently HACS Custom (per `hacs.json`). Default-listing (planned v2.0.0 per README:108) would make SEO of these keywords matter ~10× more.
4. **Entity-ID mapping verification** — table above is reconstructed from sensor.py readings; live A/B comparison on a real ID.3/4/5 install would catch nickname-prefix variations and any sensor whose name differs from key.
5. **`weconnect==0.60.8` library is itself EOL end-of-2025** (per #295) — useful note for the README to underline urgency for stragglers still on mitch-dc.
