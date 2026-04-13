# VAG Group GraphQL & Vehicle Image API — Research Notes

> Reverse-engineered April 2026 by Prash Balan (@its-me-prash)  
> Network-crawling auf www.audi.de/de/myaudi/ — bestätigt live getestet  
> Apache 2.0 / CC-BY-SA 4.0

---

## Zusammenfassung

Das VW-Group-Portal (myAudi, myVW, MyŠkoda etc.) nutzt einen gemeinsamen
GraphQL-Layer (`vgql`) für Fahrzeugdaten inklusive Render-Bilder.
Die Bilder selbst (`mediaservice.audi.com`) sind **öffentlich zugänglich** —
kein Auth-Header nötig für den PNG-Abruf nach dem initialen GraphQL-Call.

---

## 1. Authentifizierung — identity.vwgroup.io

### 1.1 Login Step 1: Identifier (E-Mail)

```
POST https://identity.vwgroup.io/signin-service/v1/{clientId}/login/identifier
Content-Type: application/x-www-form-urlencoded

Felder:
  email       — Benutzer-E-Mail
  _csrf       — CSRF-Token (aus HTML hidden input)
  relayState  — Relay-State Token (hidden input)
  hmac        — HMAC-Signatur (hidden input)

Response: HTTP 302 → Passwort-Seite
```

### 1.2 Login Step 2: Authenticate (Passwort)

```
POST https://identity.vwgroup.io/signin-service/v1/{clientId}/login/authenticate
Content-Type: application/x-www-form-urlencoded

Felder:
  password    — Benutzer-Passwort
  _csrf       — Neues CSRF-Token (aus Passwort-Seite)
  relayState  — Relay-State Token
  email       — E-Mail (hidden input, aus Step 1)
  hmac        — HMAC-Signatur

Response: Redirect-Kette → Session-Cookies gesetzt
```

### 1.3 Auth-Details

- Login-Seite = klassisches Server-Side-Rendered Formular (kein SPA)
- `_csrf`, `relayState`, `hmac` aus HTML `<input type="hidden">` parsen
- `clientId` bestimmt Ziel-Portal (Audi, VW, Škoda etc.)
- Nach Auth: OAuth2/OIDC Token-Flow mit Redirect-Kette
- Session-basierte Auth (Cookies), NICHT Bearer für Portal-APIs

**Client ID Audi:** `ea73e952-ecd9-4b44-aa39-8acc33f3ff9b@apps_vw-dilab_com`

**Session-Cookies (www.audi.de):**
- `csrf_token` — CSRF-Token für API-Calls
- `authproxy_session_timeout` — Session-Ablaufzeit
- `bm_mi` / `bm_sv` — Akamai Bot-Management

---

## 2. Audi ID Account APIs — audiid.vwgroup.io

Nach Login auf audiid.vwgroup.io:

### Profil-Daten

| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/profile/get/personalData` | Vorname, Nachname, Adresse, Telefon |
| GET | `/profile/get/identityData` | Account-ID, E-Mail, Erstellungsdatum |
| GET | `/picture/profile-picture` | Profilbild des Users |
| GET | `/choices` | User-Präferenzen |

### Fahrzeug- & Consent-Daten

| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/consent/vehicles` | Liste aller verknüpften Fahrzeuge mit VIN und Rolle |
| GET | `/consent/users/self` | Consent-Status des Users |
| GET | `/consent/marketing/campaigns` | Marketing-Consent-Status |

```json
// Beispiel-Response /consent/vehicles
{
  "vin": "WAUZZZF29MN024037",
  "role": "PRIMARY_USER",
  "roleDisplayName": "Hauptnutzer"
}
```

**Auth-Cookies (audiid.vwgroup.io):**
- `identity-kit-access-token-expiration`
- `identity-kit-user-email`
- `XSRF-TOKEN`
- `display-language`

---

## 3. myAudi Portal APIs — www.audi.de

Alle API-Calls laufen über `/userinfo-emea/v2/myaudi/`.

### 3.1 Session & User

| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/userinfo-emea/v2/myaudi/authenticated` | Session-Check |
| GET | `/userinfo-emea/v2/myaudi/user` | User-Daten |

### 3.2 Fahrzeug-Daten (REST)

| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/userinfo-emea/v2/myaudi/proxy/v1` | Garage (alle Fahrzeuge) |
| GET | `/userinfo-emea/v2/myaudi/proxy/vehicles/{VIN}/usercapabilities` | Fähigkeiten |
| GET | `/userinfo-emea/v2/myaudi/proxy/patp/v1/sprmyaudi/v1/smda/v1/v2/state?vin={VIN}` | Status |

### 3.3 GraphQL — Fahrzeugdaten & Render-Bilder

```
POST https://www.audi.de/userinfo-emea/v2/myaudi/proxy/vgql/v1/graphql
Content-Type: application/json
Authorization: Bearer {IDK_access_token}
```

### 3.4 Weitere myAudi-Endpoints

| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/userinfo-emea/v2/myaudi/proxy/boac/v1/4.4.1/profile-picture` | Profilbild (Proxy) |
| GET | `/userinfo-emea/v2/myaudi/proxy/favorite-partner` | Bevorzugter Händler |
| POST | `dealer-graphql.apps.emea.vwapps.io/` | Händler-GraphQL (503 beobachtet) |

---

## 4. VW Group GraphQL (vgql) — GET_USER_VEHICLES

### Exakte Query

```graphql
query GET_USER_VEHICLES {
  userVehicles {
    csid
    vin
    nickname
    favorite
    devicePlatform
    mbbConnect
    userRole { role }
    vehicle {
      brand { name }
      classification { driveTrain }
      core { vin modelYear modelCoding }
      media { exteriorColor interiorColor shortName longName }
      renderPictures(
        mediaTypes: [
          "MYAAN8NB"
          "MYAPN8NB"
          "MYAAN3NB"
          "MYAPN3NB"
          "MS_MYP3"
          "MS_MYP4"
          "MS_MYP5"
        ]
      ) {
        mediaType
        url
      }
      pdw { pdwVehicle }
    }
  }
}
```

### Alternative mit Sortierung

```graphql
query GET_USER_VEHICLES_ORDERED_BY($orderBy: String) {
  userVehicles(orderBy: $orderBy) {
    # ...gleiches Schema...
  }
}
```

### Beispiel-Response (Audi S6 Avant, bestätigt April 2026)

```json
{
  "data": {
    "userVehicles": [
      {
        "csid": "523c81d575294ac48d8da1267d497b9b",
        "vin": "WAUZZZF29MN024037",
        "nickname": null,
        "favorite": true,
        "devicePlatform": "MBB_ODP",
        "mbbConnect": true,
        "userRole": { "role": "PRIMARY_USER" },
        "vehicle": {
          "brand": { "name": "Audi" },
          "classification": { "driveTrain": "MHEV" },
          "core": {
            "vin": "WAUZZZF29MN024037",
            "modelYear": 2021,
            "modelCoding": "4A5SVA"
          },
          "media": {
            "exteriorColor": "...",
            "interiorColor": "...",
            "shortName": "Audi S6 Avant",
            "longName": "Audi S6 Avant TDI quattro tiptronic"
          },
          "renderPictures": [
            { "mediaType": "MS_MYP3",   "url": "https://mediaservice.audi.com/media/fast/v3_..." },
            { "mediaType": "MS_MYP4",   "url": "https://mediaservice.audi.com/media/fast/v3_..." },
            { "mediaType": "MS_MYP5",   "url": "https://mediaservice.audi.com/media/fast/v3_..." },
            { "mediaType": "MYAPN3NB",  "url": "https://mediaservice.audi.com/media/fast/v3_..." },
            { "mediaType": "MYAPN8NB",  "url": "https://mediaservice.audi.com/media/fast/v3_..." },
            { "mediaType": "MYAAN3NB",  "url": "https://mediaservice.audi.com/media/fast/v3_..." },
            { "mediaType": "MYAAN8NB",  "url": "https://mediaservice.audi.com/media/fast/v3_..." }
          ]
        }
      }
    ]
  }
}
```

---

## 5. Fahrzeugbilder — mediaservice.audi.com

### URL-Struktur

```
https://mediaservice.audi.com/media/fast/v3_{base64url_encoded_protobuf}
```

- Payload = base64url-kodiertes Protobuf-Binary mit Fahrzeugkonfiguration
- Enthält: Modell, Farbe, Ausstattung, Perspektive
- **Kann NICHT manuell aus der VIN konstruiert werden — URL muss aus GraphQL kommen**
- Bilder = PNG mit transparentem Hintergrund
- **Öffentlich zugänglich** — kein Auth-Header nötig für GET nach dem GraphQL-Call
- URLs stabil, ändern sich nur bei Fahrzeug-Konfigurationsänderung

### Alle 7 MediaTypes

| MediaType | Entity-Suffix | Ansicht | Größe | Tag | Empfehlung |
|---|---|---|---|---|---|
| MS_MYP3 | `render_icon` | 3/4-Ansicht klein | ~76 KB | `icon` | Mini-Icons, Badges |
| MS_MYP4 | `render_small` | 3/4-Ansicht | ~117 KB | `small` | Kleine Karten |
| MS_MYP5 | `render_medium` | 3/4-Ansicht | ~196 KB | `medium` | Standard-Karten |
| MYAPN3NB | `render_side_sm` | Seitenprofil klein | ~158 KB | `side_small` | Kompakte Seite |
| MYAPN8NB | `render_side_lg` | Seitenprofil groß | ~309 KB | `side_large` | ⭐ Lovelace-Standard |
| MYAAN3NB | `render_angle_hd` | 3/4-Ansicht HD | ~1.7 MB | `angle_hd` | Hero/Wallpaper |
| MYAAN8NB | `render_angle_lg` | 3/4-Ansicht groß | ~879 KB | `angle_large` | Dashboard-Karten |

---

## 6. Cross-Brand GraphQL Endpoints

Alle EU-Marken teilen den `vgql`-Layer — gleiche Query, unterschiedliche Proxy-Pfade:

| Marke | GraphQL Endpoint | Status |
|---|---|---|
| **Audi** | `https://www.audi.de/userinfo-emea/v2/myaudi/proxy/vgql/v1/graphql` | ✅ Bestätigt |
| **VW EU** | `https://www.volkswagen.de/app/proxy/vgql/v1/graphql` | ❓ Tester gesucht |
| **Škoda** | `https://www.skoda-auto.com/myskoda/proxy/vgql/v1/graphql` | ❓ Tester gesucht |
| **SEAT** | `https://www.seat.com/myway/proxy/vgql/v1/graphql` | ❓ Tester gesucht |
| **CUPRA** | `https://www.cupraofficial.com/mycupra/proxy/vgql/v1/graphql` | ❓ Tester gesucht |
| VW US/CA | Separate NA API | ❌ Nicht implementiert |
| Porsche | Auth0, andere Architektur | ❌ Nicht implementiert |

**Live-Test-Tracking:** Issue #13 — bitte dort Ergebnisse kommentieren.

---

## 7. Frontend-Architektur (für zukünftiges Reverse-Engineering)

- **Framework:** React (React Fiber)
- **GraphQL-Client:** Apollo Client (nur für Händler-Daten)
- **Fahrzeugdaten:** Kommen über vgql-Proxy direkt (nicht Apollo)
- **Bundle:** `oneaudi-falcon-integrator.prod.renderer.one.audi/csr/15.2.0/audi-feature-hub-integrator-csr.js` (~1 MB)
- Fahrzeugdatenobjekt im React Fiber Tree verfügbar (für Browser-Extensions)

---

## 8. Vollständige API-Kette (Login → Bild)

```
1. POST identity.vwgroup.io/signin-service/v1/{clientId}/login/identifier
   Body: email, _csrf, relayState, hmac
   → Redirect zur Passwort-Seite

2. POST identity.vwgroup.io/signin-service/v1/{clientId}/login/authenticate
   Body: password, _csrf, relayState, email, hmac
   → Redirect-Kette → Session-Cookies gesetzt

3. GET www.audi.de/userinfo-emea/v2/myaudi/authenticated
   → {"authenticated": true}

4. POST www.audi.de/userinfo-emea/v2/myaudi/proxy/vgql/v1/graphql
   Body: {"query": "query GET_USER_VEHICLES { ... }"}
   Headers: Authorization: Bearer {IDK_token}
   → JSON mit userVehicles[] inkl. renderPictures[].url

5. GET mediaservice.audi.com/media/fast/v3_{protobuf_payload}
   → PNG-Bild (KEIN Auth-Header nötig — öffentliche URL)
```

---

## 9. Implementierungsstand in VAG Connect

| Feature | Version | Status |
|---|---|---|
| GraphQL-Client (`VehicleImageFetcher`) | v1.3.0 | ✅ |
| 7 Image-Entities pro Fahrzeug | v1.3.1 | ✅ |
| Lokales Caching `/config/www/vehicles/` | v1.3.1 | ✅ |
| `VehicleImageData` Dataclass | v1.3.1 | ✅ |
| `fetch_images()` in `CariadBaseClient` | v1.3.2 | ✅ |
| Škoda, SEAT, CUPRA Images | v1.3.2 | ✅ |
| VW NA Images | — | ❌ andere API |
| Porsche Images | — | ❌ andere Architektur |

---

*Letzte Aktualisierung: April 2026*  
*Quelle: Network-Crawling www.audi.de/de/myaudi/, React Fiber Inspektion*
