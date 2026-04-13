# VAG Connect HA — Session Handoff Dokument

> Erstellt: 13. April 2026  
> Für: Nahtloser Start im nächsten Chat

---

## Repository

- **GitHub:** https://github.com/its-me-prash/vag-connect-ha
- **Token:** **GITHUB_TOKEN_REDACTED**
- **Branch:** `main`
- **Aktuelle Version:** v1.4.0
- **CI Status:** ✅ alle Jobs grün (Lint, mypy, Tests, Hassfest, HACS)

---

## Aktueller Codestand

### Architektur

```
custom_components/vag_connect/
  __init__.py          # Setup, Services, Options-Listener (live update ohne Reload)
  coordinator.py       # Poll-Loop, _enrich(), Reverse Geocoding, VehicleImageData
  entity_base.py       # VagConnectEntity Base + entity_picture (Render-Bild)
  sensor.py            # 40 Sensoren, suggested_display_precision=0 bei km
  binary_sensor.py     # 16 Binary Sensors
  switch.py            # Schalter (Fensterheizung, Klimatisierung etc.)
  number.py            # min_soc, max_charge_current, Ladeziel, Klimatemp
  select.py            # Lademodus (MANUAL/TIMER/PREFERRED_CHARGING_TIMES)
  button.py            # Aufwecken, Daten aktualisieren, Lichtsignal
  climate.py           # Vorklimatisierung
  device_tracker.py    # GPS
  image.py             # 7 Image-Entities pro Fahrzeug + lokales Caching
  cariad/
    models.py          # VehicleData (alle Felder), BRANDS (7), TokenSet
    exceptions.py      # Alle Exception-Typen
    auth/
      idk.py           # IDK PKCE Auth (VW Group, legacy signin-service)
      porsche.py       # Auth0 PKCE (Porsche)
    api/
      base.py          # CariadBaseClient + fetch_images() (geerbt von allen)
      vw_eu.py         # VW EU + unsupported platform filter
      audi.py          # AudiClient + AZS Token Exchange für vgql
      skoda.py         # SkodaClient
      seat_cupra.py    # SeatCupraClient
      porsche.py       # PorscheClient (Auth0)
      vw_na.py         # VWNAClient (UUID-basiert, US/CA)
      factory.py       # CariadClientFactory (7 Marken)
      graphql.py       # VehicleImageFetcher, RENDER_IMAGE_TYPES (7), VehicleImageData
```

### Plattformen (9)

`sensor | binary_sensor | device_tracker | switch | button | climate | number | select | image`

### Tests: 360/360 ✅

---

## Wichtige Erkenntnisse aus dieser Session

### Image-Fetching Auth (komplex, endlich gelöst)

- **Audi vgql**: Braucht AZS-Token, NICHT IDK-Bearer
  - `POST https://emea.bff.cariad.digital/login/v1/audi/token`
  - Body: `{"token": idk_access_token, "grant_type": "id_token", "stage": "live", "config": "myaudi"}`
  - Endpoint: `https://app-api.live-my.audi.com/vgql/v1/graphql`
  - Quelle: arjenvrh/audi_connect_ha (MIT)

- **VW EU vgql**: `https://myvw.volkswagen.de/userinfo-emea/v2/myvw/proxy/vgql/v1/graphql`
  - Status: Endpoint gefunden, aber Connection Reset (Server blockt Non-Browser?)
  
- **Škoda/SEAT/CUPRA vgql**: Endpoints konfiguriert, noch ungetestet

### AZS Token Status (v1.4.0)

Nach Update erscheint im HA-Log:
```
INFO [vag_connect] Audi AZS token acquired for image fetching
INFO [vag_connect] Audi images: render URLs for 1 vehicle(s)
```
→ dann erscheinen automatisch 7 `image.*_render_*` Entities pro Fahrzeug

### Bekannte Live-VINs aus Logs

- `WAUZZZF29MN024037` = Audi S6 Avant — **aktiv, Haupttestfahrzeug**
- `WAUZZZF29MN0XXXXX` (Golf GTE) — aktiv, VW EU
- `WAUZZZ8T99A012765` — GDC_MISSING/UNKNOWN platform → wird ab v1.3.7 übersprungen
- `WAUZZZ8FXCN011893` — GDC_MISSING/UNKNOWN platform → wird übersprungen
- `WAUZZZ8T9A0XXXXX` (vermutlich Golf V/Passat) — alte Generation, kein CARIAD

---

## Offene GitHub Issues (priorisiert)

### Bug (1)

| # | Titel | Milestone | Priorität |
|---|---|---|---|
| **#32** | `is_charging` bleibt 'on' nach Ladeende | v1.5.0 | 🔴 Hoch |

### Enhancements nach Milestone

**v1.5.0 — Bugs & Stabilität** (Mai 2026)
- #34 Warnleuchten als binary_sensor

**v1.6.0 — Erweiterte EV Features** (Juni 2026)
- #24 Verbrauchsdaten
- #25 Standort-spezifischer SoC
- #26 Klimatisierungs-Timer UI
- #30 Fensterheizung Switch für alle Marken
- #31 Ladeprofile pro Standort
- #33 Fahrzeug-Alarm binary_sensor
- #35 Ladehistorie in HA Statistics

**v1.7.0 — Navigation & Vehicle Health** (Juli 2026)
- #27 Zuverlässigere GPS-Updates
- #28 Remote Start
- #29 PPC-Plattform 2025 Support
- #36 Navigation — Ziel ans Fahrzeug

**v2.0.0 — HACS Official** (September 2026)
- #13 Live-Tests alle 7 Marken → offizielle HACS-Aufnahme

**Weitere Enhancement-Issues:** #9, #10, #12, #18–#23

---

## Nächste Schritte (empfohlene Reihenfolge)

### 1. v1.5.0 starten — Bug #32 fixen (is_charging stuck)

```python
# In coordinator._enrich() oder sensor.py:
# Wenn plug_connected=False und is_charging=True länger als N Zyklen:
# → is_charging forcieren auf False

# Defensiver Reset in VehicleData:
if not d.plug_connected and d.charging_state in (None, "READY_FOR_CHARGING", "OFF"):
    d.is_charging = False
```

### 2. AZS Token in Live-HA prüfen

Nach Update auf v1.4.0 im HA-Log prüfen ob Render-Images funktionieren.
Falls VW GraphQL immer noch Connection Reset → Issue #8 in docs/research analysieren.

### 3. Fensterheizung Switch (#30) — einfach

`switch.py` hat command_start/stop_window_heating bereits in base.py,
braucht nur Switch-Entity-Definition analog anderen Switches.

### 4. Warnleuchten (#34) — medium

`vehicleHealthWarnings` Endpoint im CARIAD BFF fetchen,
binary_sensor pro Warntyp erstellen.

---

## CI/CD Status

```yaml
# .github/workflows/ci.yml
jobs:
  - Lint & Validate  # ruff + mypy + manifest + CHANGELOG check
  - Unit Tests       # pytest --cov-fail-under=70
  - HA Hassfest      # home-assistant/actions/hassfest@master
  - HACS Validation  # hacs/action@main
```

Alle 4 Jobs auf `main` grün seit v1.4.0.

---

## Wichtige Konstanten

```python
# Auth
IDK_BASE      = "https://identity.vwgroup.io"
CARIAD_BFF    = "https://emea.bff.cariad.digital"
AZS_TOKEN_URL = "https://emea.bff.cariad.digital/login/v1/audi/token"

# Audi Client IDs
CARIAD_CLIENT = "09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com"  # CARIAD BFF
AZS_APP_API   = "app-api.live-my.audi.com"                                  # vgql (AZS token)

# GraphQL
AUDI_GRAPHQL  = "https://app-api.live-my.audi.com/vgql/v1/graphql"
VW_GRAPHQL    = "https://myvw.volkswagen.de/userinfo-emea/v2/myvw/proxy/vgql/v1/graphql"

# Image CDN (public, no auth needed)
MEDIASERVICE  = "https://mediaservice.audi.com/media/fast/v3_..."
```

---

## Referenz-Projekte (clean-room, MIT/Apache-2.0)

| Projekt | Verwendung |
|---|---|
| arjenvrh/audi_connect_ha (MIT) | AZS Token Exchange Pattern |
| robinostlund/homeassistant-volkswagencarnet (MIT) | VW EU Endpoints |
| skodaconnect/myskoda (MIT) | Škoda API Endpoints |
| WulfgarW/pycupra (Apache-2.0) | SEAT/CUPRA OLA Endpoints |
| CJNE/pyporscheconnectapi (Apache-2.0) | Porsche Auth0 Flow |
| matpoulin/CarConnectivity-connector-volkswagen-na (Apache-2.0) | VW NA Endpoints |
