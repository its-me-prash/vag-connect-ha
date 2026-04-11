```
 _   _  ___  _____   _____                             _
| | | |/ _ \|  __ \ /  __ \                           | |
| | | / /_\ \ |  \/ | /  \/ ___  _ __  _ __   ___  ___| |_
| | | |  _  | | __  | |    / _ \| '_ \| '_ \ / _ \/ __| __|
\ \_/ / | | | |_\ \ | \__/\ (_) | | | | | | |  __/ (__| |_
 \___/\_| |_/\____/  \____/\___/|_| |_|_| |_|\___|\___|\__|

  Home Assistant Integration  |  Audi · VW · Skoda · SEAT · CUPRA
```

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/github/v/release/Prash1407/vag-connect-ha)](https://github.com/Prash1407/vag-connect-ha/releases)
[![Lizenz](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](LICENSE)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)
[![Tests](https://img.shields.io/badge/Tests-57%2F57-brightgreen)](tests/)

**[English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Ich wollte meinen Audi in Home Assistant steuern, ohne drei verschiedene Integrationen parallel zu pflegen oder einen extra MQTT-Broker zu betreiben. Also hab ich das hier gebaut.

**VAG Connect** verbindet Home Assistant direkt mit den offiziellen Apps von Audi, VW, Skoda, SEAT und CUPRA. Keine Zwischenschicht, kein Docker, kein separater Dienst. Integration installieren, Zugangsdaten eingeben, fertig.

Die technische Arbeit dahinter hat vor allem Till Steinbach mit seinem [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)-Framework erledigt. Diese Integration ist ein sauberer Home Assistant-Wrapper darum.

---

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

### Verbrenner und Hybrid

| Feature | Verfügbarkeit |
|---|---|
| Tankstand | Alle Verbrenner + PHEV |
| Nächste Inspektion (km) | Audi, VW, Škoda |
| Inspektionsdatum | Audi, VW, Škoda |
| Nächster Ölwechsel (km) | Audi, VW |
| Ölwechseldatum | Audi, VW |

---

## Installation

### Via HACS (empfohlen)

1. HACS öffnen → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL eingeben: `https://github.com/Prash1407/vag-connect-ha`
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

**Ein Konto, mehrere Fahrzeuge:** Alle Fahrzeuge des Kontos werden automatisch erkannt und als separate Geräte angelegt.

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

---

## Danksagungen

Diese Integration wäre ohne folgende Open-Source-Projekte nicht möglich:

- **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** von @tillsteinbach — das Herzstück
- **[CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi)** von @acfischer42
- **[CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen)** von @tillsteinbach
- **[CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda)** von @tillsteinbach
- **[CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra)** von @tillsteinbach
- **[CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na)** von @matpoulin
- **[ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect)** von @TA2k — API-Recherche

---

## Lizenz

MIT — Details in [LICENSE](LICENSE).

Diese Integration nutzt inoffizielle APIs — dieselben, die die offiziellen Apps verwenden. Es gibt keine Garantie, dass sie dauerhaft funktioniert. Audi, Volkswagen, Škoda, SEAT und CUPRA sind eingetragene Marken der jeweiligen Hersteller.
