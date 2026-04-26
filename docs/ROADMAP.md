# VAG Connect — Roadmap

> Single canonical source of truth. The README ships an identical table in 8
> languages. This file mirrors it for archive/historical purposes and links
> the active GitHub issues for each session.

Last updated: 2026-04-26 (v1.8.0 PR #65)

---

## Where to follow progress

- **Issues:** https://github.com/its-me-prash/vag-connect-ha/issues
- **PRs:** https://github.com/its-me-prash/vag-connect-ha/pulls
- **Releases:** https://github.com/its-me-prash/vag-connect-ha/releases

---

## Achieved

| Version | Content |
|---|---|
| v1.0–v1.5 | 9 platforms, 7 brands, bug fixes, entity audit |
| v1.6.0 | SEAT/CUPRA 9 endpoints, Škoda fix, Audi PPC, Lock platform, nightly polling reduction |
| v1.7.0 | Complete Škoda rewrite, car-friendly translations all 8 languages, reliability (rate limit backoff, token refresh lock, stale-data tracking) |

---

## Session plan (P0 → P1 → P2)

Strict order. Sessions 1–4 are non-negotiable before any new features land.

| Session | Version | Scope | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 (PR #65) | iot_class, per-VIN availability, S-PIN fail-fast, fake writables removed, geocoding opt-in, platforms in sync, quality_scale cleaned | **#60** + #53 (Cupra flash) |
| **2 — Capabilities** | v1.8.1 | Capability-gated entities, subscription detection | #56 |
| **3 — Command Profile** | v1.8.2 | Brand/region/platform routing, Audi RS e-tron GT fix | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.3 | Anonymized diagnostics, regression tests | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Read-only mode, command locking, cloud vs wake distinction | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | MQTT broker integration | #57 |
| **9 — Feature batch** | v1.10.0 | Trip stats, charging history, departure timer UI, alarm, charge profiles | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live tests all brands, compatibility matrix, EU Data Act ready | #13, #59 |

---

## What will not be implemented

| Brand / feature | Reason |
|---|---|
| VW China (2026+) | CEA/XPeng platform — undocumented, near-zero HA user base |
| Lamborghini commands | No verified public API. Research only — see `research/LUXURY_BRANDS.md` |
| Bentley commands | No verified public API. Research only |
| Bugatti | Fleet too small, no API surfaced |
| Ducati | Motorcycles — out of scope |
| MAN / Scania | Commercial fleet APIs — different use case |

---

## Process notes

- Every session = atomic PR + tagged release.
- No new features land before #60 P0 fixes are merged and stable.
- Every command-sending entity must be capability-gated (#56) before reaching v1.9.0.
- Translation strings: English in `strings.json`, mirrored across `translations/{de,en,cs,es,fr,nl,pl,sv}.json`.
