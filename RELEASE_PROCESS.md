# Release-Prozess

## Täglich: Änderungen dokumentieren

Jeder Commit der `custom_components/` anfasst braucht einen Eintrag im `[Unreleased]`-Block:

```markdown
## [Unreleased]

### Behoben
- Kurze Beschreibung was behoben wurde
  **Autor:** @github-name
  **Quelle:** Link zur Referenz wenn relevant
```

Commit-Prefix (Pflicht):
```
feat:     Neues Feature
fix:      Bugfix
docs:     Nur Dokumentation
refactor: Kein Feature, kein Bug — Code-Umstrukturierung
test:     Tests
chore:    Abhängigkeiten, Build
ci:       GitHub Actions
```

---

## Release erstellen (step by step)

### 1. manifest.json Version bumpen
```bash
# Bestimme neue Version nach SemVer:
# PATCH (0.1.x): nur Bugfixes
# MINOR (0.x.0): neue Features (neue Marke, neue Entities)
# MAJOR (x.0.0): Breaking Changes (Entities umbenannt etc.)
```

Datei: `custom_components/vag_connect/manifest.json`
```json
"version": "0.1.2"
```

### 2. CHANGELOG.md aktualisieren
```markdown
## [0.1.2] - 2026-MM-DD    ← Unreleased ersetzen + Datum

## [Unreleased]             ← Neuer leerer Unreleased-Block oben
```

### 3. Committen
```bash
git add custom_components/vag_connect/manifest.json CHANGELOG.md
git commit -m "chore: release 0.1.2"
git push origin main
```

### 4. Tag erstellen und pushen
```bash
git tag -a v0.1.2 -m "Release 0.1.2

Kurze Beschreibung was in dieser Version neu ist."

git push origin v0.1.2
```

→ GitHub Actions `release.yml` erstellt automatisch:
  - ZIP der Integration
  - GitHub Release mit Changelog-Inhalt

### 5. HACS aktualisiert sich automatisch
Nutzer die HACS verwenden bekommen den Update-Hinweis innerhalb von ~6 Stunden.

---

## Versioning-Regeln (SemVer)

| Situation | Bump | Beispiel |
|---|---|---|
| Bugfix, Übersetzung, Dependency-Update | PATCH | 0.1.0 → 0.1.1 |
| Neue Marke (z.B. Porsche) | MINOR | 0.1.1 → 0.2.0 |
| Neue Entity-Klasse hinzugefügt | MINOR | 0.1.1 → 0.2.0 |
| Entities umbenannt (breaking) | MAJOR | 0.x.x → 1.0.0 |
| API-Inkompatibilität | MAJOR | 0.x.x → 1.0.0 |

Bis Version `1.0.0`: Mindestens Audi + VW + Skoda stabil getestet.
