# Contributing to VAG Connect

## Bug Reports
→ [Issue Template](https://github.com/its-me-prash/vag-connect-ha/issues/new/choose)

Bitte immer: Version, Marke, HA-Version und Logs mitschicken.

## Pull Requests

```bash
git clone https://github.com/its-me-prash/vag-connect-ha
cd vag-connect-ha
pip install pytest pytest-asyncio ruff
python -m pytest tests/        # alle Tests grün
python -m ruff check custom_components/vag_connect/  # Lint sauber
```

**Regeln:**
- Alle neuen Features brauchen Tests
- Lint muss sauber sein (`ruff check`)
- CHANGELOG.md aktualisieren
- Neue Marken oder API-Endpoints brauchen eine Quelle (Link zu MIT/Apache-2.0 Referenzprojekt)

## Neue Marke hinzufügen

1. `cariad/api/{marke}.py` — API-Client (von `CariadBaseClient` ableiten oder eigene Klasse)
2. `cariad/models.py` — `BrandConfig` + `BRANDS` dict ergänzen
3. `cariad/api/factory.py` — Routing ergänzen
4. `const.py` — BRANDS dict
5. `config_flow.py` — `_BRAND_OPTIONS` ergänzen
6. Tests in `tests/test_cariad.py`
7. README Feature-Tabelle ergänzen

## Tester gesucht

Porsche und VW US/CA sind implementiert aber ohne echten Live-Test. Wenn du eines dieser Fahrzeuge hast:
→ [Tester-Issue öffnen](https://github.com/its-me-prash/vag-connect-ha/issues/new?template=new_brand.yml)
