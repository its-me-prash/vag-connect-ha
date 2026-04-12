# VAG Connect — Roadmap

> Maintained by Prash Balan (@its-me-prash)

---

## Current State (v0.14.0) — PLATINUM 🏆

```
Engine:         Own CARIAD API Client (aiohttp, zero external deps)
Quality Scale:  47/47 done — PLATINUM
Tests:          342/342 passing | 95% coverage
mypy:           0 errors (--disallow-untyped-defs)
ruff:           0 errors
Dependencies:   requirements: []
```

---

## v0.15.0 — Porsche Support

**Goal:** Add Porsche as a 6th supported brand.

**Why separate:** Porsche uses a completely different auth system from the other 5 brands:
- **Auth:** `identity.porsche.com` (Auth0) — NOT `identity.vwgroup.io` (IDK)
- **API:** `api.ppa.porsche.com` — NOT CARIAD BFF
- **Client-ID:** `XhygisuebbrqQ80byOuU5VncxLIm8E6H` (Auth0 public client)
- **X-Client-ID:** `41843fb4-691d-4970-85c7-2673e8ecef40`

**Deliverables:**
- `cariad/auth/porsche.py` — Auth0 PKCE flow
- `cariad/api/porsche.py` — api.ppa.porsche.com endpoints
- Factory support: `CariadClientFactory.create("porsche", ...)`
- Config flow: Porsche option in brand selector

**Reference:** [pyporscheconnectapi](https://github.com/CJNE/pyporscheconnectapi) (MIT)

**Alternative for users now:** [ha-porscheconnect](https://github.com/CJNE/ha-porscheconnect) (MIT, 55 stars)

---

## v0.16.0 — VW North America (US/CA)

**Goal:** VW US and Canada users.

**Auth system:** `b-h-s.spr.{country}00.p.con-veh.net` — completely separate from EU IDK

**Client IDs:**
- US: `59992128-69a9-42c3-8621-7942041ba824_MYVW_ANDROID`
- CA: `69eb3c39-d2be-4006-8197-37cc4971e8fe_MYVW_ANDROID`

**Reference:** [CarConnectivity-connector-volkswagen-na](https://github.com/zackcornelius/CarConnectivity-connector-volkswagen-na) (MIT)

---

## v0.17.0 — Feature Expansion (post-core)

New sensors/features now possible with own client:

| Feature | Source | Brand |
|---|---|---|
| Trip statistics | CARIAD + Škoda API | VW, Audi, Škoda |
| Charging history | Škoda API | Škoda |
| Driving score | Škoda API | Škoda |
| Auxiliary heating | CARIAD/Škoda | PHEV |
| Battery care mode | CARIAD charging | EV |
| Parking time | CARIAD readiness | All |
| VIN selection in config flow | UX | All |

---

## v1.0.0 — HACS Official

**Requirements before submission:**
- [x] CarConnectivity dependency removed ✅
- [x] 95%+ test coverage ✅
- [x] Full Platinum quality scale ✅
- [ ] Live-tested: Audi S6 + VW Golf GTE (Prash's vehicles)
- [ ] Community-tested: at least 1 Škoda, 1 SEAT/CUPRA
- [ ] Stable for 2+ minor releases
- [ ] 10+ GitHub stars / real-world users

---

## What Will Never Be Supported

| Brand | Reason |
|---|---|
| VW China (2026+) | CEA/XPeng platform — undocumented, HA user base near zero |
| Lamborghini | No API exists |
| Bentley | No API found |
| Bugatti | Too small, no API |
| Ducati | Motorcycles, different use case |
| MAN / Scania | Commercial fleet, different use case |

---

*Updated: 2026-04-12 | Prash Balan (@its-me-prash)*
