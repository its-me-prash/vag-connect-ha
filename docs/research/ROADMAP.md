# VAG Connect — Roadmap

> Maintained by Prash Balan (@its-me-prash)

---

## Current State (v0.11.0)

```
Engine:         CarConnectivity (tillsteinbach) — TEMPORARY
Quality Scale:  Gold ✅ + strict-typing ✅
Blocker:        requests~=2.32.5 vs HA 2026.x requests==2.33.1
Tests:          192/192 passing | 72% coverage
```

---

## v0.12.0 — CARIAD Client Phase 1: Auth + VW EU + Audi

**Goal:** Remove CarConnectivity entirely for VW EU and Audi.  
**Status:** 🔵 In Development

### Deliverables
- `cariad/auth/idk.py` — async PKCE/OIDC, aiohttp, all IDK brands
- `cariad/api/vw_eu.py` — full VW EU selectivestatus + commands
- `cariad/api/audi.py` — VW EU + AZS/MBB auth chain
- `cariad/models.py` — unified VehicleData → coordinator
- `cariad/exceptions.py` — typed errors
- Tests: 95%+ coverage via mockable aiohttp session
- **No `requests` dependency**

### Platinum rules unlocked
- `async-dependency` ✅
- `inject-websession` ✅
- `test-coverage` ✅ (target)

---

## v0.13.0 — CARIAD Client Phase 2: Škoda + SEAT/CUPRA

**Goal:** All IDK brands on own client. CarConnectivity completely removed.

### Deliverables
- `cariad/api/skoda.py` — mysmob.api.connect.skoda-auto.cz
- `cariad/api/seat_cupra.py` — ola.prod.code.seat.cloud.vwgroup.com
- Optional: `aiomqtt` for Škoda real-time push

---

## v0.14.0 — Feature Expansion (post-CC)

New sensors/features now possible without CC limitations:

| Feature | Source | Brand |
|---|---|---|
| Trip statistics (last/refuel/longterm) | CARIAD + Škoda API | VW, Audi, Škoda |
| AdBlue level | CARIAD measurements | Diesel |
| Hood open/closed | CARIAD access | All |
| Trunk locked/closed | CARIAD access | All |
| Sunroof status | CARIAD access | All |
| Battery temperature min/max | CARIAD measurements | EV/PHEV |
| Connector LED colour | CARIAD charging | EV |
| Charging history | Škoda API | Škoda |
| Driving score | Škoda API | Škoda |
| Auxiliary heating | CARIAD/Škoda | PHEV/Verbrenner |
| Parking time | CARIAD readiness | All |
| Battery care mode | CARIAD charging | EV |
| VIN selection in config flow | UX | All |

---

## v0.15.0 — Porsche (optional)

- `cariad/auth/porsche.py` — Auth0
- `cariad/api/porsche.py` — api.ppa.porsche.com
- OR: integration with existing `ha-porscheconnect` (MIT, collaboration)

---

## v1.0.0 — HACS Official

**Requirements before submission:**
- [ ] CarConnectivity dependency removed
- [ ] Live-tested on: Audi S6, VW Golf GTE
- [ ] Community-tested on: at least 1 Škoda, 1 SEAT/CUPRA
- [ ] 95%+ test coverage
- [ ] Full Platinum quality scale
- [ ] 10+ GitHub stars / real-world users
- [ ] Stable for 2+ minor releases

---

## What Will Never Be Supported

| Brand | Reason |
|---|---|
| VW China (2026+) | CEA/XPeng platform — undocumented, HA user base near zero |
| Lamborghini | No API exists |
| Bentley | No API exists |
| Bugatti | Too small, no API |
| Ducati | Motorcycles, different use case |
| MAN / Scania | Commercial fleet, different use case |

---

*Updated: 2026-04-12 | Prash Balan (@its-me-prash)*
