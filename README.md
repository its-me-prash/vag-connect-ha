<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration für Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Lizenz-MIT-yellow.svg?style=for-the-badge" alt="Lizenz"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue?style=for-the-badge" alt="Home Assistant"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-192%2F192-brightgreen?style=for-the-badge" alt="Tests"></a>
  <a href="https://analytics.home-assistant.io/custom_integrations.json"><img src="https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Installs&suffix=%20aktiv&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.vag_connect.total&style=for-the-badge" alt="Installs"></a>
</p>

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Ich wollte meinen Audi in Home Assistant steuern — vollständig, nicht halbgar. Also hab ich das hier gebaut.

**VAG Connect** ist eine eigenständige Home Assistant Integration für alle VAG-Marken. Keine Zwischenschicht, kein Docker, kein separater Dienst. Integration installieren, Zugangsdaten eingeben, fertig.

Das Projekt nutzt [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) von @tillsteinbach als Kommunikations-Engine — und erweitert es mit eigenen Features, die im CC-Kern nicht existieren: Abfahrtstimer, Akkutemperatur, Ladeende-ETA, Ladesäuleninformationen, Standortadressen und mehr. Was CarConnectivity nicht kann, bauen wir selbst.


## Unterstützte Plattformen

```
sensor  |  binary_sensor  |  device_tracker  |  switch  |  button  |  climate  |  number
```

---

## Features

### Alle Fahrzeuge

| Feature | Audi | VW EU | VW US/CA | Škoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|:---:|
| Tankstand / Akkustand | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reichweite | ✓ | ✓ | ✓ | ✓ | ✓ |
| Kilometerstand | ✓ | ✓ | ✓ | ✓ | ✓ |
| GPS-Position | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Standort als Adresse** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Fahrtrichtung** | ✓ | ✓ | ✓ | ✓ | ✓ |
| Türen (gesamt + einzeln) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fenster | ✓ | ✓ | ✓ | ✓ | ✓ |
| Außentemperatur | ✓ | ✓ | ✓ | ✓ | ✓ |
| Klimatisierung | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Fahrzeugzustand** (fährt/geparkt/offline) | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Erreichbarkeit** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Kennzeichen** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Firmware-Version** | ✓ | ✓ | ✓ | ✓ | ✓ |
| Türen ver-/entriegeln | ✓ | ✓ | ✓ | ✓ | ✓ |
| Klimatisierung starten/stoppen | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lichtsignal | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fahrzeug aufwecken | ✓ | ✓ | ✓ | ✓ | ✓ |

### Elektro- und Hybridfahrzeuge

| Feature | Audi e-tron | VW ID | Škoda Enyaq | CUPRA Born |
|---|:---:|:---:|:---:|:---:|
| Akkustand (%) | ✓ | ✓ | ✓ | ✓ |
| Laden starten/stoppen | ✓ | ✓ | ✓ | ✓ |
| Ladeziel setzen (%) | ✓ | ✓ | ✓ | ✓ |
| Ladevorgang | ✓ | ✓ | ✓ | ✓ |
| Ladeleistung (kW) | ✓ | ✓ | ✓ | ✓ |
| Ladegeschwindigkeit (km/h) | ✓ | ✓ | ✓ | ✓ |
| **Ladeende (Uhrzeit)** | ✓ | ✓ | ✓ | ✓ |
| **Ladetyp (AC/DC)** | ✓ | ✓ | ✓ | ✓ |
| **Aktuelle Ladesäule** | ✓ | ✓ | ✓ | ✓ |
| **Akkutemperatur** | ✓ | ✓ | ✓ | ✓ |
| **Akkukapazität (kWh)** | ✓ | ✓ | ✓ | ✓ |
| Scheibenheizung | ✓ | ✓ | ✓ | ✓ |
| Sitzheizung | ✓ | ✓ | ✓ | ✓ |
| **Max. Ladestrom begrenzen** | ✓ | ✓ | ✓ | ✓ |
| **Stecker nach Laden entsperren** | ✓ | ✓ | ✓ | ✓ |
| **Abfahrtstimer (1–3)** | ✓ | ✓ | ✓ | ✓ |

### Verbrenner und Hybrid

| Feature | Verfügbarkeit |
|---|---|
| Tankstand | Alle Verbrenner + PHEV |
| Nächste Inspektion (km) | Audi, VW, Škoda |
| Inspektionsdatum | Audi, VW, Škoda |
| Nächster Ölwechsel (km) | Audi, VW |
| Ölwechseldatum | Audi, VW |

---

## API-Nutzung & Rate Limiting

VAG-APIs (Audi, VW, Škoda, SEAT/CUPRA) haben ein serverseitiges Rate Limit. VAG Connect ist darauf ausgelegt, es einzuhalten:

- **Reaktive Architektur** (`cloud_push`): Das Fahrzeug meldet sich selbst — kein permanentes Polling
- **Mindestintervall 3 Minuten** für manuelle Refreshes
- **Token-Persistenz**: Keine erneute Anmeldung bei HA-Neustarts

Falls der Account trotzdem kurz gesperrt wird (passiert selten): Die Sperre hebt sich automatisch nach 2–4 Stunden. Unter **Einstellungen → System → Reparaturen** erscheint dann ein Hinweis mit nächsten Schritten.

## Bekannte Einschränkungen

- **Kein Live-Test mit echtem Fahrzeug** — alle Features wurden gegen CC-Mocks entwickelt. Rückmeldungen aus echten Installationen sind sehr willkommen.
- **Platinum Quality Scale nicht erreichbar** — CarConnectivity nutzt `requests` (synchron) und `threading`. Platinum erfordert eine vollständig asynchrone Abhängigkeit. Das ist ein Upstream-Problem bei [@tillsteinbach](https://github.com/tillsteinbach/CarConnectivity).
- **SEAT/CUPRA 404 capabilities** — Bekanntes Upstream-Problem im `carconnectivity-connector-seatcupra`. Basis-Features funktionieren, manche Capabilities fehlen.
- **Porsche** — Kein offizieller Connector auf PyPI. Technisch identische CARIAD-API wie Audi — wartet auf Community-Tester.
- **Departure Timer** — Schreibzugriff auf CC-Objekt implementiert, aber ob die VAG-API den Wert tatsächlich ans Fahrzeug sendet ist ungetestet (kein echtes Fahrzeug verfügbar).

## Installation

### Via HACS (empfohlen)

1. HACS öffnen → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL eingeben: `https://github.com/its-me-prash/vag-connect-ha`
3. Kategorie: **Integration**
4. Hinzufügen → In HACS suchen: **VAG Connect** → Installieren
5. Home Assistant neu starten
6. Einstellungen → Geräte & Dienste → Integration hinzufügen → **VAG Connect**

### Manuell

1. Dieses Repository herunterladen
2. Ordner `custom_components/vag_connect/` in deinen HA-Config-Ordner kopieren
3. Home Assistant neu starten
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → **VAG Connect**

---

## Konfiguration

| Feld | Beschreibung |
|---|---|
| **Fahrzeugmarke** | Audi, VW EU, VW US/CA, Škoda oder SEAT/CUPRA |
| **E-Mail** | Die E-Mail-Adresse aus der jeweiligen App |
| **Passwort** | Das Passwort aus der App |
| **S-PIN** | Nur nötig für Türverriegelung. Steht in der App unter Sicherheit. |
| **Intervall** | Wie oft Daten abgerufen werden. Standard: 5 Minuten. |
| **Türen erzwingen** | Für ältere Modelle, bei denen Türzustand fehlt. |

---

## Mehrere Fahrzeuge

**Ein Konto, mehrere Fahrzeuge:** Alle Fahrzeuge des Kontos werden automatisch erkannt und als separate Fahrzeuge angelegt.

**Verschiedene Marken** (z.B. Audi + Škoda): Integration einfach ein zweites Mal hinzufügen — einmal für Audi, einmal für Škoda.

**Zwei gleiche Modelle:** Entity-IDs bekommen automatisch einen Zähler:
```
sensor.audi_q4_e_tron_akkustand       ← erstes Fahrzeug
sensor.audi_q4_e_tron_2_akkustand     ← zweites Fahrzeug
```

---

## Abfrageintervall

Standard: 15 Minuten. Nicht unter 5 Minuten gehen. Die Hersteller-APIs sind nicht für sehr häufige Abfragen ausgelegt — bei zu vielen Anfragen kann der Account vorübergehend gesperrt werden.

Reaktive Updates kommen trotzdem sofort: Wenn das Auto etwas meldet (Tür öffnet, Ladevorgang startet), wird Home Assistant sofort aktualisiert — ohne auf das nächste Intervall zu warten.

---

## Login-Probleme

### Zwei-Faktor-Authentifizierung (2FA)

Falls der Account 2FA aktiviert hat: Einmal manuell in der App anmelden und den E-Mail-Code bestätigen. Danach speichert VAG Connect das Login-Token lokal — bei HA-Neustarts ist keine erneute Anmeldung nötig.

### Nutzungsbedingungen / Datenschutz

Nach einer Änderung der Nutzungsbedingungen erscheint unter **Einstellungen → System → Reparaturen** eine Meldung mit genauen Schritten.

---

## Services

| Service | Beschreibung |
|---|---|
| `vag_connect.lock` | Fahrzeug verriegeln |
| `vag_connect.unlock` | Fahrzeug entriegeln |
| `vag_connect.start_climatisation` | Klimatisierung starten |
| `vag_connect.stop_climatisation` | Klimatisierung stoppen |
| `vag_connect.start_charging` | Laden starten |
| `vag_connect.stop_charging` | Laden stoppen |
| `vag_connect.start_window_heating` | Scheibenheizung starten |
| `vag_connect.stop_window_heating` | Scheibenheizung stoppen |
| `vag_connect.wake_vehicle` | Fahrzeug aufwecken |
| `vag_connect.flash_lights` | Lichtsignal |
| `vag_connect.refresh_vehicle` | Daten sofort aktualisieren |
| `vag_connect.set_target_soc` | Ladezielprozent setzen |
| `vag_connect.set_climatisation_temperature` | Klimatemperatur setzen |
| `vag_connect.set_departure_timer` | Abfahrtstimer setzen (neu in v0.5.0) |
## Beispiel-Automationen

```yaml
# Benachrichtigung wenn Akku unter 20% und nicht geladen
automation:
  trigger:
    platform: numeric_state
    entity_id: sensor.audi_q4_e_tron_akkustand
    below: 20
  condition:
    condition: state
    entity_id: binary_sensor.audi_q4_e_tron_ladt
    state: "off"
  action:
    service: notify.mobile_app
    data:
      message: "Audi Akku unter 20% — bitte laden!"

# Klimatisierung automatisch 15 Min vor Abfahrt starten
automation:
  trigger:
    platform: time
    at: "07:45:00"
  condition:
    condition: state
    entity_id: binary_sensor.audi_q4_e_tron_ladekabel_verbunden
    state: "on"
  action:
    service: vag_connect.start_climatisation
    data:
      vin: "WAUZZZ4G7EN123456"
```

Weiteres Beispiel-Dashboard: [`docs/lovelace-example.yaml`](docs/lovelace-example.yaml)

## Beispiel-Dashboard

Eine fertige Lovelace-Konfiguration (mushroom-cards + mini-graph-card) liegt in [`docs/lovelace-example.yaml`](docs/lovelace-example.yaml).

Benötigt aus HACS → Frontend:
- [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card)

---

## Integration entfernen

1. **Einstellungen → Geräte & Dienste → VAG Connect → ⋮ → Löschen**
2. HA neu starten
3. Optional: Token-Datei manuell löschen:
   ```
   config/.storage/vag_connect_tokens_{entry_id}.json
   ```
   (Entry-ID steht in der URL wenn du die Integration öffnest)

## Letzte Änderungen

**[v0.8.0](CHANGELOG.md)** — Gold Quality Scale vollständig
- `icons.json` — 64 Icon-Definitionen für alle Platforms
- Stale Devices: Fahrzeuge die aus dem Account entfernt wurden, werden automatisch aus HA gelöscht
- 192 Tests, 72% Coverage, 0 mypy-Fehler

**[v0.7.0](CHANGELOG.md)** — HA Quality Scale Gold
- `entry.runtime_data`, `async_step_reauth`, `async_step_reconfigure`
- `ServiceValidationError`, `log_when_unavailable`, `parallel_updates=0`
- 15 DIAGNOSTIC-Sensoren standardmäßig deaktiviert

**[v0.6.0](CHANGELOG.md)** — EntityCategory & neue Sensoren
- `EntityCategory.DIAGNOSTIC` / `CONFIG` für saubere Entity-Struktur
- 4 neue Sensoren: Reichweite bei 100%, WLTP, Akkuenergie verfügbar, Zuletzt aktualisiert
- Typo `Ladziel` → `Ladeziel` behoben

➜ [Vollständiger Changelog →](CHANGELOG.md)

## Danksagungen

Diese Integration wäre ohne folgende Open-Source-Projekte nicht möglich:

- **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** von @tillsteinbach — Kommunikations-Engine für alle VAG-APIs
- **[CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi)** von @acfischer42
- **[CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen)** von @tillsteinbach
- **[CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda)** von @tillsteinbach
- **[CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra)** von @tillsteinbach
- **[CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na)** von @matpoulin
- **[ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect)** von @TA2k — API-Recherche

