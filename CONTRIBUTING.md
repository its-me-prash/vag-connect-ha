# Mitmachen bei VAG Connect

Danke dass du zum Projekt beitragen möchtest! Hier sind die wichtigsten Regeln.

## Schnellstart

```bash
git clone https://github.com/its-me-prash/vag-connect-ha
cd vag-connect-ha
pip install carconnectivity carconnectivity-connector-audi \
            carconnectivity-connector-volkswagen \
            carconnectivity-connector-skoda \
            carconnectivity-connector-seatcupra \
            ruff homeassistant
```

## Was besonders gesucht wird

| Aufgabe | Schwierigkeit |
|---|---|
| Neue Übersetzung hinzufügen (`translations/xx.json`) | ⭐ Einfach |
| Neuen Sensor aus CarConnectivity-Daten mappen | ⭐⭐ Mittel |
| Porsche-Connector testen + integrieren | ⭐⭐⭐ Schwer |
| CN-Region (China) testen | ⭐⭐⭐ Schwer |
| MQTT Push statt Polling | ⭐⭐⭐ Schwer |

## Neue Übersetzung hinzufügen

1. `custom_components/vag_connect/translations/de.json` kopieren
2. Dateiname = [ISO 639-1 Sprachcode](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (z.B. `fr.json`, `nl.json`)
3. Alle Strings übersetzen
4. PR öffnen — wird sofort gemerged!

## Code-Standards

- Python 3.12+
- `ruff check` muss ohne Fehler durchlaufen
- Keine Credentials oder VINs in Tests oder Logs

## PR-Checkliste

- [ ] `ruff check custom_components/` läuft sauber
- [ ] Alle JSON-Dateien sind valide
- [ ] Beschreibung erklärt was sich ändert und warum
- [ ] Getestet mit echtem Fahrzeug (falls möglich — Marke + Modell angeben)

## API-Ressourcen

Wenn du neue Endpoints findest, schau hier nach:
- [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) — Haupt-Engine
- [ioBroker VW-Connect Forum](https://forum.iobroker.net/topic/26438) — Aktivste Community
- [myskoda MQTT Docs](https://myskoda.readthedocs.io/en/stable/mqtt/) — Push-Events
- [audi_connect_ha_q4](https://github.com/moritzwiechers/audi_connect_ha_q4) — CARIAD endpoint

## Kommunikation

Öffne einfach ein GitHub Issue — Deutsch und Englisch sind beide willkommen.
