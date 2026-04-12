# Mitmachen bei VAG Connect

Danke dass du zum Projekt beitragen möchtest!

## Schnellstart

```bash
git clone https://github.com/its-me-prash/vag-connect-ha
cd vag-connect-ha
pip install homeassistant ruff mypy pytest pytest-cov
pip install -r requirements_dev.txt 2>/dev/null || true
```

## Tests ausführen

```bash
python3 -m pytest tests/           # 342 Tests müssen grün sein
python3 -m ruff check custom_components/vag_connect/
python3 -m mypy custom_components/vag_connect/ --ignore-missing-imports
python3 -m pytest tests/ --cov=custom_components/vag_connect  # 95%+
```

## Was besonders gesucht wird

| Aufgabe | Schwierigkeit |
|---|---|
| Neue Übersetzung hinzufügen (`translations/xx.json`) | ⭐ Einfach |
| Neue Sensoren aus VehicleData mappen | ⭐⭐ Mittel |
| Porsche-Support (Auth0 + api.ppa.porsche.com) | ⭐⭐⭐ Schwer |
| VW North America (US/CA) testen | ⭐⭐⭐ Schwer |
| Live-Test auf echten Fahrzeugen | ⭐⭐ Mittel |

## Neue Übersetzung hinzufügen

1. `custom_components/vag_connect/translations/de.json` kopieren
2. Dateiname = [ISO 639-1 Sprachcode](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (z.B. `ja.json`, `ko.json`)
3. Alle Strings übersetzen
4. PR öffnen — wird schnell gemerged

## Neue Marke / API hinzufügen

Die Architektur ist klar:

```
caridad/auth/      ← Auth-Module (idk.py für 5 Marken, porsche.py geplant)
cariad/api/        ← API-Clients (einer pro Marke/Backend)
cariad/models.py   ← VehicleData dataclass (70 Felder, einfach erweiterbar)
cariad/api/factory.py ← CariadClientFactory.create(brand, session, ...)
```

Neue Marke = neue Datei in `cariad/api/`, Factory-Eintrag, Tests.

## Porsche mitentwickeln? (v0.15.0)

Auth-System: `identity.porsche.com` (Auth0, PKCE)
API: `https://api.ppa.porsche.com/app`
Client-ID: `XhygisuebbrqQ80byOuU5VncxLIm8E6H`
Referenz: [pyporscheconnectapi](https://github.com/CJNE/pyporscheconnectapi) (MIT)

Wenn du ein Porsche-Fahrzeug hast und testen möchtest → Issue öffnen.

## Code-Standards

- Python 3.12+
- `ruff check` ohne Fehler
- `mypy --disallow-untyped-defs` ohne Fehler
- Alle neuen Funktionen mit Tests (Ziel: Coverage bleibt bei 95%+)
- Keine Credentials, VINs oder persönliche Daten in Tests oder Logs

## PR-Checkliste

- [ ] Tests laufen durch (`pytest tests/`)
- [ ] Lint clean (`ruff check`)
- [ ] Typen sauber (`mypy`)
- [ ] CHANGELOG.md Eintrag hinzugefügt
- [ ] Keine Credentials/VINs im Code

---

*Copyright 2026 Prash Balan (@its-me-prash) · Apache License 2.0*
