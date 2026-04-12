# Dependency Audit — CarConnectivity vs Own Client

> Prash Balan (@its-me-prash) — 2026-04-12

---

## Current Dependencies (v0.11.0)

```
carconnectivity>=0.11.8
  └─ requests~=2.32.5          ← CONFLICT: HA 2026.x has requests==2.33.1
  └─ threading (sync I/O)      ← violates HA async-dependency rule

carconnectivity-connector-audi>=0.3.0
  └─ requests~=2.32.3          ← same conflict

carconnectivity-connector-volkswagen>=0.10.4
  └─ requests~=2.32.5          ← same conflict

carconnectivity-connector-skoda>=0.12.4
  └─ requests~=2.32.5          ← same conflict

carconnectivity-connector-seatcupra>=0.6.1
  └─ requests~=2.32.5          ← same conflict
```

**Result:** Integration cannot be installed on HA 2026.x at all.

---

## Target Dependencies (v0.12.0+)

```
aiohttp>=3.9.0    ← already in HA, injected via async_get_clientsession(hass)
pyjwt>=2.8.0      ← JWT token validation — already in HA core
```

**That's it.** No `requests`. No `carconnectivity`. No `threading`.

Optional for Škoda MQTT push:
```
aiomqtt>=2.2.0    ← already in HA core dependencies
```

---

## Risk Comparison

| Risk | CarConnectivity | Own Client |
|---|---|---|
| requests version conflict | 🔴 CRITICAL — blocks install | ✅ no requests at all |
| API change breaks integration | 🟡 upstream must fix | 🟡 we fix directly |
| Auth flow changes | 🟡 upstream must fix | 🟡 we fix in hours |
| New HA version incompatibility | 🔴 happened with HA 2026.x | ✅ no transitive deps |
| Maintenance abandoned | 🔴 one maintainer upstream | ✅ we own it |
| Feature requests | 🔴 depend on upstream | ✅ we implement |

---

## Upstream Issues Filed

- **#144** (our issue): `requests~=2.32.5 constraint incompatible with HA 2026.x`
  https://github.com/tillsteinbach/CarConnectivity/issues/144

- **#143** (marksieczkowski): `Loosen requests pin`
  https://github.com/tillsteinbach/CarConnectivity/issues/143

Status as of 2026-04-12: Both open, no response from @tillsteinbach.

---

## License of Reference Projects

All reference code used for our implementation:

| Reference | License | Usage |
|---|---|---|
| audiconnect | MIT | Auth flow reference, Audi endpoints |
| myskoda | MIT | Škoda endpoints (could use as dep) |
| pycupra | Apache-2.0 | SEAT/CUPRA endpoints |
| CC-connector-audi | MIT | Newer Audi client_id |
| WeConnect-python | MIT | VW EU auth reference |
| pyporscheconnectapi | MIT | Porsche (Phase 3) |

**volkswagencarnet (GPL-3.0):** Used only as reference to understand VW EU API paths. No code copied. Our implementation is clean-room.

---

*Prash Balan (@its-me-prash)*
