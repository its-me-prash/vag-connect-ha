# VAG Connect HA — Roadmap

> Stand: April 2026

---

## ✅ Abgeschlossen

| Version | Features |
|---|---|
| v1.0.0 | 5 EU-Marken, 8 Plattformen, 60+ Entities |
| v1.1.0 | `_enrich()`, Reverse Geocoding, Import-Cleanup |
| v1.1.1 | Fix #917 (charging_rate=0), Fix #927 (Options ohne Reload) |
| v1.2.0 | Lademodus Select, Min SoC Number |
| v1.3.x | Image-Platform (7 Entities/Auto), AZS Token, GDC-Filter, CI-Fixes |
| v1.4.0 | CI vollständig grün, 17 Enhancement Issues aus Cross-Integration Audit |

---

## 🔜 Geplant

### v1.5.0 — Bugs & Stabilität (Mai 2026)
- [ ] #32 `is_charging` stuck nach Ladeende — defensiver Reset
- [ ] #34 Warnleuchten als binary_sensor (Check Engine, Reifendruck)
- [ ] AZS Token live verifizieren (Render Images Audi)

### v1.6.0 — Erweiterte EV Features (Juni 2026)
- [ ] #30 Fensterheizung Switch für alle Marken
- [ ] #31 Ladeprofile pro Standort
- [ ] #33 Fahrzeug-Alarm binary_sensor
- [ ] #24 Verbrauchsdaten
- [ ] #25 Standort-spezifischer SoC
- [ ] #26 Klimatisierungs-Timer UI
- [ ] #35 Ladehistorie in HA Long-Term Statistics

### v1.7.0 — Navigation & Vehicle Health (Juli 2026)
- [ ] #36 Navigation — Ziel ans Fahrzeug senden
- [ ] #28 Remote Start (2024+ Modelle)
- [ ] #29 PPC-Plattform 2025 Support
- [ ] #27 GPS Push-Updates während Fahrt

### v2.0.0 — HACS Official (September 2026)
- [ ] #13 Live-Tests alle 7 Marken (Porsche, VW NA Beta verifizieren)
- [ ] HACS Pull Request erstellen
- [ ] 3+ Tester pro Marke

---

## Issue-Tracker

https://github.com/its-me-prash/vag-connect-ha/issues

| Label | Anzahl |
|---|---|
| `bug` | 1 |
| `enhancement` | 21 |
| `testing` | 1 |
