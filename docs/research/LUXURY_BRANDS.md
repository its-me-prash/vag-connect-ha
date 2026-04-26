# VAG Group — Luxury & Extended Brands Research

> Research-only document. **No commands or features implemented.** This file
> exists so that future contributors don't have to redo the discovery work.

Last updated: 2026-04-26

---

## TL;DR

| Brand | Public connected-car API? | Implementation status |
|---|---|---|
| **Bentley** (My Bentley) | None found | Not planned |
| **Lamborghini** (UNICA) | None found | Not planned |
| **Bugatti** | None — fleet too small | Not planned |
| **Ducati** | Motorcycle-only mobile app | Not planned |
| **MAN Trucks** | Fleet management API only | Not planned |
| **Scania** | Fleet management API only | Not planned |
| **VW Commercial** | Likely IDK / WeConnect Pro (unverified) | Could land later if a tester is found |

---

## Bentley — My Bentley

**App:** My Bentley (iOS / Android)

**Likely backend:** Bentley uses VW Group infrastructure under the hood,
but the My Bentley app appears to talk to a separate `myb` API tenant.
**No reverse-engineered library exists at the time of writing.**

**Likely supported features (per app description, not code-verified):**
- vehicle status (lock state, light state, fuel/range)
- mileage, service intervals, warnings
- find my car (location)
- hybrid charging / departure timers (where applicable)

**What we would need:**
1. Test account for an actual Bentley owner
2. Anonymised network traces from the My Bentley app
3. Confirmation that endpoints are not behind certificate pinning

**Status:** Not pursued. Volume of Bentley owners using Home Assistant is
low enough that the maintenance cost outweighs the gain.

---

## Lamborghini — UNICA

**App:** Lamborghini UNICA (replaces older Connect app)

**Likely backend:** Custom infrastructure under `api.lamborghini.com` —
**no public API documentation, no community library found.**

**Likely supported features (per app store listing):**
- vehicle status
- lock / unlock
- horn / lights
- fuel / range / mileage
- geofence alerts
- speed alerts, valet mode
- location tracking
- remote climate (where the model supports it)
- hybrid charging (Revuelto, etc.)
- theft / security features

**What we would need:**
- Same as Bentley: real owner, traces, no cert pinning

**Status:** Not pursued. Sub-1% of HA users.

---

## Bugatti

No connected car app shipped at scale. **Not planned.**

---

## Ducati

Ducati Connect is motorcycle-focused. Not in scope for a car integration.

---

## MAN Trucks

MAN's connected-vehicle solution is `MAN ServiceCare` and `RIO`, both
fleet-management products with B2B API contracts. **Not in scope for a
consumer Home Assistant integration.**

---

## Scania

Same as MAN — Scania Fleet Management Portal is B2B. **Not in scope.**

---

## VW Commercial Vehicles

**App:** WeConnect Pro

**Likely backend:** Same VAG IDK auth as VW EU. WeConnect Pro is positioned
as the commercial-vehicle counterpart to WeConnect. The assumption is that
the API surface is similar to VW EU CARIAD BFF, but this has **not been
verified against real network traffic**.

**Possible models:**
- Transporter T6.1 / T7
- Crafter
- Multivan
- ID. Buzz Cargo

**What we would need:**
1. A tester with a WeConnect Pro account
2. Confirmation that brand discriminator returned by IDK matches one of
   the existing brand entries (or whether a new `volkswagen_commercial`
   brand is required)

**Status:** Could land as a small follow-up if a tester volunteers.
Filed under "no urgency" because VW EU coverage already serves most
private Transporter / ID. Buzz owners.

---

## Porsche (separate file — already implemented)

Porsche is **not luxury research** — it is a fully implemented brand since
v1.0.0 (Auth0 + PPA API). Live-test verification before HACS Default is
tracked under #13 / Session 10.

---

## Decision criteria for future luxury brands

A new VAG brand would be added only when **all** of the following hold:

1. A community tester with a real vehicle and the manufacturer app installed.
2. Anonymised payload samples (status fetch + at least one command).
3. The brand discriminator returned by IDK or its proprietary auth flow
   is compatible with the Command Profile Layer (#61).
4. Capability detection (#56) covers the brand to avoid 404 spam.

Without all four, the brand stays here as documentation only.
