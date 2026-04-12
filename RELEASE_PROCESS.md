# Release-Prozess

## Täglich: Änderungen dokumentieren

Jeder Commit der `custom_components/` anfasst braucht einen Eintrag im `[Unreleased]`-Block:

```markdown
## [Unreleased]

### Added / Changed / Fixed / Removed
- Kurze Beschreibung was geändert wurde
```

Commit-Prefix (Pflicht per `changelog_check.yml`):
```
feat:     Neues Feature          → Added
fix:      Bugfix                 → Fixed
refactor: Code-Umstrukturierung  → Changed
docs:     Nur Dokumentation
test:     Tests
chore:    Build, Abhängigkeiten
ci:       GitHub Actions
```

---

## Semver-Regeln

| Was | Version | Beispiel |
|---|---|---|
| Bugfix, kleine Enhancement | PATCH `0.x.y` | 0.11.0 → 0.11.1 |
| Neue Feature, neue Marke, neue Entity-Klasse | MINOR `0.x.0` | 0.11.1 → 0.12.0 |
| Breaking Change (Entity umbenannt, Config-Schema geändert) | MINOR `0.x.0` | 0.11.0 → 0.12.0 |
| Ab v1.0.0: Breaking Change | MAJOR `x.0.0` | 1.0.0 → 2.0.0 |

**Faustregel pre-1.0.0:**  
Bugfix → PATCH. Alles andere → MINOR.  
MAJOR erst ab v1.0.0 bei echter Inkompatibilität.

---

## Release erstellen (step by step)

### 1. Version bestimmen und manifest.json bumpen

```bash
# Datei: custom_components/vag_connect/manifest.json
# Beispiel: 0.11.0 → 0.11.1 (Bugfix) oder 0.12.0 (Feature)
"version": "0.12.0"
```

### 2. CHANGELOG.md finalisieren

```markdown
## [0.12.0] - 2026-MM-DD      ← [Unreleased] ersetzen + Datum

### Added
- Porsche-Unterstützung (Auth0 + api.ppa.porsche.com)

## [Unreleased]               ← Neuer leerer Block oben
```

### 3. Committen und pushen

```bash
git add custom_components/vag_connect/manifest.json CHANGELOG.md
git commit -m "chore: release 0.12.0"
git push origin main
```

### 4. Tag erstellen

```bash
git tag -a v0.12.0 -m "Release 0.12.0 — Porsche Support"
git push origin v0.12.0
```

→ `release.yml` erstellt automatisch:
  - ZIP der Integration (`vag_connect.zip`)
  - GitHub Release mit Changelog-Inhalt

### 5. HACS-Nutzer bekommen Update-Hinweis

~6 Stunden nach GitHub Release.

---

## Checkpoints vor jedem Release

```bash
python3 -m pytest tests/                           # 342+ Tests grün
python3 -m ruff check custom_components/            # 0 Fehler
python3 -m mypy custom_components/vag_connect/ \
  --ignore-missing-imports \
  --disallow-untyped-defs --warn-return-any          # 0 Fehler
python3 -m pytest tests/ --cov=custom_components/vag_connect \
  --cov-fail-under=90                                # ≥90% Coverage
```

---

## Aktuelle Versionshistorie

Vollständige History: [CHANGELOG.md](CHANGELOG.md)

| Version | Datum | Typ | Inhalt |
|---|---|---|---|
| **0.11.0** | 2026-04-12 | MINOR | Platinum, 95% Coverage, 342 Tests |
| 0.10.1 | 2026-04-12 | PATCH | CC aus manifest entfernt |
| 0.10.0 | 2026-04-12 | MINOR | Eigener CARIAD-Client |
| 0.9.0 | 2026-04-12 | MINOR | Apache 2.0, strict-typing |
| 0.8.2 | 2026-04-12 | PATCH | requests-Konflikt Erkennung |
| 0.8.1 | 2026-04-11 | PATCH | Python 3.11 fix |
| 0.8.0 | 2026-04-11 | MINOR | Diagnostics, Gold Quality Scale |
