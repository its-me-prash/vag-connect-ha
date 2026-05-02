# Brand Captains / Brand-Patenschaft

> Initiated v1.13.0 (#64). Brand Captains sind Community-User die für ein
> spezifisches Brand + Modell Live-Tests laufen, Scout-Reports einreichen
> und bei Bug-Verifikation helfen. Im Gegenzug bekommen sie GitHub
> CODEOWNERS-Mention für ihren Brand-API-Client und werden in Release-
> Notes namentlich gedankt.

## Aktive Captains

> Initial leer — der Maintainer ist Captain für alle Brands. Diese
> Tabelle wächst sobald Community-Mitglieder Verantwortung übernehmen.

| Brand | Captain | Modell + Jahr | Beigetreten | Was sie testen |
|---|---|---|---|---|
| _alle_ | [@its-me-prash](https://github.com/its-me-prash) | — (Maintainer) | 2026-04 | alles |

## Bewährte Tester (von denen Live-Daten bereits ausgewertet wurden)

| Brand | Tester | Modell | Beiträge |
|---|---|---|---|
| CUPRA Born | [@Gerhard2808](https://github.com/Gerhard2808) | Born 2023 (DE, active subscription) | 6 Releases ausgelöst (v1.8.4/8/9/10/12 + v1.10.2). Anonymized Born Fixture mit Consent (v1.12.1, [`tests/fixtures/seat_cupra/cupra_born_2023_active_subscription_redacted.json`](tests/fixtures/seat_cupra/cupra_born_2023_active_subscription_redacted.json)) |
| Skoda | [@tritanium73](https://github.com/tritanium73) | (Diesel, mysmob v3 firmware) | Erster Community Vehicle Data Scout Report (#107 → v1.12.2) |
| Audi | [@DnnsJp74](https://github.com/DnnsJp74) | (Audi mit 23 unbekannten Fields) | Zweiter Community Scout Report (#111 → v1.12.3) |

## Wie werde ich Captain?

1. **Mindestens 1 Vehicle Data Scout Report** über die v1.9.0 Reporter
   Pipeline einreichen (Settings → System → Reparaturen → Klick auf
   "Mehr erfahren" beim Scout-Notification)
2. **Mindestens 2 Wochen aktiv** mit deinem Vehicle die Integration
   nutzen + bei Live-Tests mitmachen
3. Issue-Comment hier: "Ich melde mich als Captain für `<Brand>` mit
   `<Modell + Jahr>`"

Captains werden in `.github/CODEOWNERS` für die brand-spezifischen
Files (`cariad/api/<brand>.py`) als Co-Owner eingetragen — sie
bekommen automatisch Review-Requests bei PRs die ihren Brand
betreffen.

## Was Captains tun (kein Pflichtprogramm — bei Verfügbarkeit)

- ✅ **Live-Tests** für neue Releases mit ihrem Vehicle (1× pro Monat reicht)
- ✅ **Scout-Reports einreichen** wenn Notification erscheint (1-Klick)
- ✅ **Bug-Verify-Pings beantworten** (z.B. "ist v1.12.3 OK?" — kurz Ja/Nein reicht)
- ✅ **Anonymized Fixtures genehmigen** wenn der Maintainer für Regression-
  Tests fragt (siehe Workflow in [`CONTRIBUTING.md`](CONTRIBUTING.md)
  "Privacy & data handling" Sektion)
- ❌ **NICHT erforderlich:** Code-Reviews, Programmieren, Feature-Implementation

## Privacy für Captains

Captains' GitHub-Handles sind public (sie wurden ja sowieso public auf
Issues kommentiert), aber **kein** Vehicle-VIN, **kein** Standort, **keine**
persönlichen Daten landen jemals im Repo ohne explicit Consent. Siehe
[`CONTRIBUTING.md`](CONTRIBUTING.md) "Privacy & data handling" für die
verbindlichen Maintainer-Regeln.
