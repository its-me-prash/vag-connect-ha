# Cariad Mobile-Charging Host — Deep Research

**Host under investigation:** `https://prod.emea.mobile.charging.cariad.digital`
**Discovered via:** `Timwun/Cupra-WeConnect-Bruno-Collection` files seq 52 + 53
**Purpose:** Charging-statistics & per-session power-curve backend for v1.18.0
`sensor.kwh_charged_this_month` work.
**Status:** Public-internet documentation = effectively zero. Bruno collection
is the ONLY source we found. Treat every response field as `unknown — needs
live capture` unless this doc says otherwise.

---

## A) Endpoint catalog

Verified from Bruno files (raw .bru on `Timwun/Cupra-WeConnect-Bruno-Collection`
@ `main`):

### A.1 — `POST /charging_statistics`
Source: `Charging Statistics.bru` (seq 52).
- Headers: `Content-Type: application/json`, `Accept-Encoding: gzip`,
  `Accept-Language: de-DE`, plus inherited `Authorization: Bearer <ola_access_token>`.
- Body: see §C.1.

### A.2 — `GET /charging_statistics/{sessionId}/power-curve`
Source: `Charging Statistics Power Curve.bru` (seq 53). URL placeholder is
literally `…/charging_statistics/XXX/power-curve` in the Bruno file —
`XXX` = a session-id presumably returned by §A.1.
- Same headers as §A.1, no body.

### A.3 — Sibling URLs
`unknown — needs live capture`. Bruno collection contains only the two above.
GitHub code-search across `WulfgarW/pycupra`, `skodaconnect/myskoda`,
`tillsteinbach/CarConnectivity-connector-volkswagen`,
`robinostlund/volkswagencarnet`, `arjenvrh/audi_connect_ha` returned **zero**
hits for the host (`prod.emea.mobile.charging.cariad.digital`) and for the
distinctive payload terms (`selectedFilterOptions`, `fetchFilterOptions`,
`filterType: VEHICLE`). Public web search for those payload keys returns 0
results — this API is not yet documented anywhere outside the Bruno repo.

The only related public URL is the staging/multi-tenant landing page
`https://mobile-stage-vw.emea.home.charging.cariad.digital/` (visible via
plain web search) — confirms the naming pattern
`mobile-{stage}-{brand}.{region}.{home|mobile}.charging.cariad.digital` and
that VW is on the same platform.

Plausible siblings to probe live (NOT confirmed):
`/sessions`, `/contracts`, `/plug-and-charge`, `/billing`, `/tariffs`,
`/charge-points`, `/filter-options`, `/users/{userId}/charging_statistics`.

---

## B) Auth flow

**Same OLA OAuth2 bearer token. No separate IdP.** `collection.bru` ships a
single `auth: oauth2` block at the collection level (authorize/token URLs =
`identity.vwgroup.io/oidc/v1/{authorize,token}`, client_id
`3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com`, scope
`openid profile nickname birthdate phone cars badge dealers`). Both seq 52
and seq 53 use Bruno's default `auth: inherit`, so the same access-token
that hits `ola.prod.code.seat.cloud.vwgroup.com` is sent verbatim to
`prod.emea.mobile.charging.cariad.digital`.

Required headers (verified):
- `Authorization: Bearer <access_token>` (inherited, not in .bru file)
- `Content-Type: application/json`
- `Accept-Encoding: gzip`
- `Accept-Language: de-DE` — likely **optional** but unverified. Strongly
  recommend mirroring HA's configured locale (`hass.config.language`) to
  match what the official MyCupra/MySEAT app sends; if the backend localises
  pricing/labels we want the right strings out of the gate.

Test curl (replace `$TOK` and `$VIN`):
```bash
curl -sS -X POST 'https://prod.emea.mobile.charging.cariad.digital/charging_statistics' \
  -H "Authorization: Bearer $TOK" \
  -H 'Content-Type: application/json' \
  -H 'Accept-Encoding: gzip' \
  -H 'Accept-Language: de-DE' \
  --data "{\"startedAfter\":\"2026-04-01\",\"startedBefore\":\"2026-05-02\",\"selectedFilterOptions\":[{\"id\":\"$VIN\",\"filterType\":\"VEHICLE\"}],\"fetchFilterOptions\":false,\"capabilities\":[]}"
```

No additional scope is needed — the existing `cars` scope appears sufficient
(no 403 is expected because the Bruno collection ships ONLY the OLA scope set
and the same token is used). `unknown — needs live capture` whether a stricter
scope is required for `power-curve`.

---

## C) Request body schemas

### C.1 — `POST /charging_statistics`

Verbatim from `Charging Statistics.bru`:
```json
{
  "startedAfter": "2026-03-11",
  "startedBefore": "2026-04-20",
  "selectedFilterOptions": [
    {"id": "{{VIN}}", "filterType": "VEHICLE"}
  ],
  "fetchFilterOptions": false,
  "capabilities": []
}
```

Field types & notes:
| Field | Type | Notes |
|---|---|---|
| `startedAfter` | string `YYYY-MM-DD` | Date only (no time/TZ) per Bruno example. ISO-8601 with TZ = `unknown — needs live capture`. |
| `startedBefore` | string `YYYY-MM-DD` | Same. |
| `selectedFilterOptions[].id` | string | VIN when `filterType=VEHICLE`. |
| `selectedFilterOptions[].filterType` | enum | Bruno only shows `VEHICLE`. `USER`, `LOCATION`, `TARIFF` are plausible — `unknown — needs live capture`. |
| `fetchFilterOptions` | bool | When `true` the response presumably also returns the catalog of available filter options (so the app can populate dropdowns). Confirm in live call. |
| `capabilities` | string[] | Empty in Bruno. Probably an opt-in for richer fields (e.g. `["powerCurve","cost","plugAndCharge"]`). `unknown — needs live capture`. |

### C.2 — `GET /charging_statistics/{sessionId}/power-curve`

No request body. `sessionId` shape `unknown — needs live capture`; almost
certainly the `id`/`sessionId` field from a `POST /charging_statistics` row.

---

## D) Response schemas

**Bruno collection ships NO `docs:` block / response sample for either
endpoint.** Both response shapes are `unknown — needs live capture`.

Best inference based on payload semantics + sibling Cariad responses
(emea.bff, OLA) we already model:

### D.1 — `POST /charging_statistics` (inferred)
Likely shape:
```json
{
  "sessions": [
    {
      "id": "<session-uuid>",
      "vin": "...",
      "startedAt": "<ISO-8601 UTC>",
      "endedAt": "<ISO-8601 UTC>",
      "durationInMinutes": 45,
      "energyChargedInKWh": 12.5,
      "currentType": "AC|DC",
      "location": {"lat": ..., "lon": ..., "name": "...", "operator": "..."},
      "cost": {"amount": 4.50, "currency": "EUR"},
      "plugAndCharge": false,
      "startSoc": 30, "endSoc": 80
    }
  ],
  "aggregates": {
    "totalEnergyKWh": ..., "totalCost": {...}, "totalDurationMin": ...,
    "totalSessions": ...
  },
  "filterOptions": [/* present iff fetchFilterOptions=true */]
}
```

This matches the `myskoda` `ChargingHistory` shape we already use for Skoda
in `cariad/api/skoda.py:get_charging_history()` (verified — `periods[].sessions[].chargedInKWh`,
`durationInMinutes`, `currentType`). High likelihood the Cariad team reused
the same JSON contract; we should code defensively but `_parse_charging_history()`
in `coordinator.py:201` is the right starting template.

### D.2 — `GET .../power-curve` (inferred)
Likely shape:
```json
{
  "sessionId": "...",
  "samples": [
    {"timestamp": "<ISO-8601>", "powerKW": 11.0, "soc": 32},
    ...
  ]
}
```
DC fast-charge sessions probably have higher sample density and a `voltageV`
/ `currentA` field. `unknown — needs live capture`.

---

## E) Cross-brand status

| Repo | Touches `*.charging.cariad.digital`? | Notes |
|---|---|---|
| `WulfgarW/pycupra` (`pycupra/connection.py` + `const.py`) | **NO** | Hostnames used: `ola.prod.code.seat.cloud.vwgroup.com`, `identity.vwgroup.io`, `cupraid.vwgroup.io`, `customer-profile.vwgroup.io`, `prod-ola-public-bucket.s3.eu-central-1.amazonaws.com`, `eu-data-act.drivesomethinggreater.com`, `mbboauth-1d.prd.ece.vwg-connect.com`, `profileintegrityservice.apps.emea.vwapps.io`. |
| `skodaconnect/myskoda` (`myskoda.py` + `rest_api.py` + `const.py`) | **NO** | Charging history is on `mysmob.api.connect.skoda-auto.cz/v1/charging/{vin}/history` — own brand backend. |
| `robinostlund/volkswagencarnet` | **NO** | Uses legacy `mal-3a.prd.eu.dp.vwg-connect.com` family. |
| `tillsteinbach/CarConnectivity-connector-volkswagen` | partial — uses sibling `emea.bff.cariad.digital/vehicle/v1/...` for status, **NOT** the mobile.charging host. |
| `arjenvrh/audi_connect_ha` (`audi_services.py`) | partial — uses `{region}.bff.cariad.digital` for vehicle BFF, **NOT** the mobile.charging host. |
| Our `vag-connect-ha` | **NO** — `cariad/api/vw_eu.py` and `cariad/api/audi.py` use `emea.bff.cariad.digital` (sibling); no client touches `mobile.charging.cariad.digital`. |

**Conclusion:** The Cupra Bruno collection is currently the ONLY public
source for this host. We'd be the first OSS HA integration to ship a client.
The host name (`emea` + `mobile` — i.e. mobile-app channel — + generic
`charging`) plus the staging-page evidence
(`mobile-stage-vw.emea.home.charging.cariad.digital`) strongly suggests it's
the unified Cariad mobile-charging backend across VW/Audi/Skoda/SEAT/Cupra,
not SEAT/Cupra-only. Live test with a VW Bearer token from
`emea.bff.cariad.digital` would confirm cross-brand.

---

## F) Implementation recommendation for vag-connect-ha

**1. New file `cariad/api/charging_stats.py`** — separate from `seat_cupra.py`
because (a) different host, (b) likely cross-brand later, (c) keeps
`seat_cupra.py` lean. Class `CariadChargingStatsClient` with constructor
that accepts an existing `CariadBaseClient` (composition over inheritance —
we just need its `_session`, `_tokens`, `_get`/`_post` helpers and the
shared refresh-storm protection in `base.py:55-80`). Sketch:

```python
# cariad/api/charging_stats.py
_BASE = "https://prod.emea.mobile.charging.cariad.digital"

class CariadChargingStatsClient:
    def __init__(self, parent: CariadBaseClient) -> None:
        self._parent = parent  # token reuse via parent._tokens

    async def get_statistics(self, vin: str, after: date, before: date) -> dict:
        body = {
            "startedAfter": after.isoformat(),
            "startedBefore": before.isoformat(),
            "selectedFilterOptions": [{"id": vin, "filterType": "VEHICLE"}],
            "fetchFilterOptions": False,
            "capabilities": [],
        }
        return await self._parent._post(
            f"{_BASE}/charging_statistics",
            json=body,
            extra_headers={"Accept-Language": self._parent._locale,
                           "Accept-Encoding": "gzip"},
        )

    async def get_power_curve(self, session_id: str) -> dict:
        return await self._parent._get(
            f"{_BASE}/charging_statistics/{session_id}/power-curve",
            extra_headers={"Accept-Language": self._parent._locale,
                           "Accept-Encoding": "gzip"},
        )
```

If `_post` doesn't exist on `base.py`, add it (it likely does — check
before duplicating). `extra_headers` plumbing also already exists for the
SecToken flow.

**2. Token reuse** — by composition the parent client owns the token; the
stats client never authenticates separately. Same OAuth2 token, same
identity.vwgroup.io IdP, no code-flow change. If we later add VW/Audi
support, instantiate a second stats client wrapping the VW/Audi parent.

**3. Coordinator hook** — mirror Skoda's `refresh_charging_history()` pattern
(`coordinator.py:1249`, 1h cache via `_charging_history_fetched_at[vin]`).
New method `refresh_cupra_charging_stats(vin)`:
- Cache key `_cupra_stats_fetched_at[vin]`, 1h TTL.
- Date window: `today.replace(day=1)` → `today` (covers "this month"
  cleanly; computes "today" subtotal client-side from session.startedAt).
- Call site: piggyback on the same triggers as `refresh_charging_history`
  (after a charging-stop event + once per coordinator cycle if cache stale).
- Capability gate: introduce `command_charging_stats` in `_capabilities.py`
  — disable for non-EV vehicles. Default `True` for SEAT/CUPRA, `None`
  (probe-and-cache) for other brands until live test.

**4. Sensor entity design**
- `sensor.{vin}_kwh_charged_this_month` — TOTAL_INCREASING, unit `kWh`,
  device_class `energy`. State = sum of `energyChargedInKWh` over current
  calendar month. Resets cleanly on month boundary (HA Energy Dashboard
  handles this natively for TOTAL_INCREASING + monotonic).
- `sensor.{vin}_kwh_charged_today` — SAME class; subset filtered by
  `startedAt.date() == today`. Beware off-by-one on TZ — use
  `hass.config.time_zone`.
- `sensor.{vin}_last_charging_session` — STATE = ISO `startedAt`, device_class
  `timestamp`. `extra_state_attributes` = full session dict (location,
  duration, kWh, AC/DC, cost, plug-and-charge marker, **+ power-curve
  array** lazily fetched once when session_id changes — store as
  `[(unix_ts, kw), ...]` no more than 200 points to keep state DB sane).
  Power curve as a state-attribute (not separate entity) avoids polluting
  the entity registry with one-shot history; users who want it in
  ApexCharts can pull from attributes.

**5. Refresh cadence** — 1h is right. Cariad backends are sluggish and
this is "kWh-charged-since-month-start" data, not real-time. Force-refresh
on `command_charging_stop` events (already a coordinator hook for Skoda
charging-history — extend the same callback).

**6. Brand wiring** — only register the entities when the active client is
`SeatCupraClient` for v1.18.0. Add VW/Audi behind a probe in v1.19.0.

---

## G) Open questions (need live capture)

1. **Date format** — does `startedAfter` accept `YYYY-MM-DD` only, or also
   `YYYY-MM-DDTHH:MM:SSZ` / Unix epoch?
2. **Response shape** — full schema for both endpoints. No public sample
   exists.
3. **`filterType` enum** — values beyond `VEHICLE` (USER? LOCATION? TARIFF?).
4. **`capabilities` array** — what strings does the backend accept and
   what fields do they unlock?
5. **`fetchFilterOptions: true`** — what catalog does it return?
6. **`sessionId` shape** — UUID v4? Cariad-internal ID format? Pulled from
   which field of the stats response?
7. **Power-curve response** — array structure, sample density, AC vs DC
   shape difference, presence of voltage/current fields.
8. **Cross-brand** — does a VW/Audi/Skoda OAuth token authenticate against
   this host? If yes, is the response schema identical?
9. **Pagination / limit** — `Charging Statistics` body has no `limit` or
   `cursor` field. Does the backend cap window size? What happens for a
   year-long range?
10. **Rate-limit behaviour** — Cariad backends typically 429 after ~30
    req/min per token; needs confirmation here.
11. **Response when account has no charging sessions** — empty array vs
    404 vs different envelope.
12. **`Accept-Language`** — required, optional, or affects content?

Capture plan: one beta tester with a live SEAT/Cupra EV runs the curl
in §B against month-to-date and a single sessionId, plus
`fetchFilterOptions: true` once. ~30 lines of JSON unblocks the
implementation entirely.

---

*Generated 2026-05-02. Sources: 2 .bru files + collection.bru on
`Timwun/Cupra-WeConnect-Bruno-Collection` @ main, plus null-result
GitHub crawls of the 5 upstream repos listed in §E.*
