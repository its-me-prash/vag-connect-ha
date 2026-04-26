# Architecture Decision Record — Own CARIAD API Client

> Status: **APPROVED & IMPLEMENTED** (shipped in v0.12.0, in use through v1.8.0)
> Date: 2026-04-12 | Author: Prash Balan (@its-me-prash)

> **Historical record.** This ADR is preserved unchanged from when the
> decision was made. The implementation went live with v0.12.0 and is
> still the architecture as of v1.8.0. CarConnectivity is no longer a
> dependency. Refer to [`docs/SESSION_HANDOFF.md`](../SESSION_HANDOFF.md)
> for the current architecture map.

---

## Decision

**We build our own async CARIAD API client directly inside the integration.**  
We remove the dependency on CarConnectivity (`tillsteinbach`) entirely.

---

## Context

CarConnectivity is the current engine behind VAG Connect. It wraps the same CARIAD/VAG APIs we would talk to directly — but adds a sync `requests` dependency that:
- Blocks installation on HA 2026.x (`requests==2.33.1` vs `requests~=2.32.5`)
- Violates HA Platinum rule `async-dependency`
- Prevents `inject-websession` (Platinum)
- Adds an uncontrolled upstream failure point

All the APIs CarConnectivity uses are publicly documented by the open-source community. We have already mapped every endpoint, every client ID, every auth flow. Building our own client is **less work** than waiting for upstream fixes that may never come.

---

## Target Architecture

```
custom_components/vag_connect/
  cariad/
    __init__.py
    auth/
      __init__.py
      idk.py          # VAG IDK auth (VW EU, Audi, Škoda, SEAT, CUPRA)
      porsche.py      # Auth0 auth (Porsche)
      vw_na.py        # VW NA auth (US/CA)
    api/
      __init__.py
      vw_eu.py        # emea.bff.cariad.digital
      audi.py         # CARIAD BFF + AZS/MBB
      skoda.py        # mysmob.api.connect.skoda-auto.cz
      seat_cupra.py   # ola.prod.code.seat.cloud.vwgroup.com
      porsche.py      # api.ppa.porsche.com (optional Phase 3)
      vw_na.py        # b-h-s.spr.{country}00... (optional Phase 3)
    models.py         # unified data model → coordinator.vehicles dict
    exceptions.py     # AuthError, APIError, RateLimitError, SpinError
  coordinator.py      # uses cariad.api.* via injected aiohttp session
```

### Data Flow (target)

```
HA startup
  └─ async_setup_entry
       └─ session = async_get_clientsession(hass)        ← inject-websession ✅
       └─ client = CariadClient(session, brand, creds)
       └─ coordinator = VagConnectCoordinator(hass, entry, client)
            └─ coordinator.async_setup()
                 └─ client.authenticate()
                 └─ vehicles = await client.get_vehicles()
                 └─ data = await client.get_status(vin)
                 └─ coordinator.async_set_updated_data(data)
```

### Why `cloud_push` becomes even more reactive

Škoda exposes an MQTT broker (`mqtt.messagehub.de:8883`). Once we own the client, we can use `aiomqtt` (already in HA dependencies) for true push — no polling at all for Škoda.

For VW/Audi: we keep the CC-style observer approach but with our own polling loop (async, configurable interval), bridging to HA via `async_set_updated_data`.

---

## Implementation Plan

### Phase 1 — VW EU + Audi (Prash's own vehicles)
**Scope:** S6 (Audi) + Golf GTE (VW/PHEV)  
**Estimate:** 2–3 weeks  
**Deliverable:** Working integration for both vehicles, no CC dependency

```
cariad/auth/idk.py       # PKCE/OIDC, aiohttp, clean-room (no GPL copying)
cariad/api/vw_eu.py      # selectivestatus, commands, parking, trips
cariad/api/audi.py       # VW EU + AZS/MBB extra steps
cariad/models.py         # VehicleData dataclass → coordinator dict
```

### Phase 2 — Škoda + SEAT/CUPRA
**Scope:** Community-tested  
**Estimate:** 1–2 weeks (APIs fully documented, needs live testing)

```
cariad/api/skoda.py      # mysmob.api.connect.skoda-auto.cz
cariad/api/seat_cupra.py # ola.prod.code.seat.cloud.vwgroup.com
```

Optional: `aiomqtt` for Škoda push events.

### Phase 3 — Porsche + VW NA (optional)
**Scope:** Community contribution welcome  
**Estimate:** 1 week each  
**Note:** Porsche has existing `ha-porscheconnect` (MIT) — collaboration over duplication.

---

## What We Are NOT Doing

- **Porsche:** Recommend existing `ha-porscheconnect` integration for now. Will integrate if there's user demand.
- **VW China (2026+):** CEA/XPeng platform — undocumented, no API found, very small HA user base.
- **Lamborghini/Bentley/Bugatti:** No API, no demand.
- **MAN/Scania:** Commercial fleet, different use case.

---

## License Strategy

All code in `cariad/` is our own implementation:
- **Auth flow:** clean-room implementation of standard PKCE/OAuth2 (IETF RFC 7636) — no code copied from any GPL project
- **Client IDs:** Discovered from public MIT/Apache open-source projects — listed in VAG_GROUP_ECOSYSTEM.md
- **API paths:** Documented in VAG_GROUP_ECOSYSTEM.md — functional facts, not copyrightable
- **License:** Apache 2.0 (same as rest of integration)

---

## Quality Scale Impact

Building own client unblocks **3 Platinum rules simultaneously:**

| Rule | Current | After |
|---|---|---|
| `async-dependency` | ❌ blocked (CC uses requests) | ✅ pure aiohttp |
| `inject-websession` | ❌ blocked | ✅ `async_get_clientsession(hass)` |
| `test-coverage` | ⏳ 72% (CC code untestable) | ✅ fully mockable session |
| `strict-typing` | ✅ done | ✅ stays done |

**Result: Full Platinum** 🏆

---

*Prash Balan (@its-me-prash) — 2026-04-12*
