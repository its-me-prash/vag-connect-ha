<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Intégration Home Assistant pour Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge"></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge"></a>
  <a href="../tests/"><img src="https://img.shields.io/badge/Tests-337%2F337-brightgreen?style=for-the-badge"></a>
  <a href="../custom_components/vag_connect/quality_scale.yaml"><img src="https://img.shields.io/badge/Quality%20Scale-Platinum%20%F0%9F%8F%86-gold?style=for-the-badge"></a>
</p>

<p align="center">
  <a href="../README.md">Deutsch</a> ·
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Je voulais contrôler mon Audi dans Home Assistant — complètement. Alors j'ai construit ça.

**VAG Connect** est une intégration Home Assistant autonome pour toutes les marques VAG. Aucune dépendance externe, aucun Docker, aucun service externe. Installez l'intégration, entrez vos identifiants, c'est prêt.

Depuis v0.14.1, l'intégration parle **directement** à l'API CARIAD — client async propre, entièrement autonome.

---

## Marques Supportées

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA :** Les deux marques sont disponibles en Beta depuis v1.0.0. Testeurs recherchés — signalez vos retours via un [Issue](https://github.com/its-me-prash/vag-connect-ha/issues) !

---

## Fonctionnalités

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Fuel / Battery level | ✓ | ✓ | ✓ | ✓ |
| Range | ✓ | ✓ | ✓ | ✓ |
| Odometer | ✓ | ✓ | ✓ | ✓ |
| GPS position | ✓ | ✓ | ✓ | ✓ |
| Doors (total + per door) | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ |
| Climate start/stop | ✓ | ✓ | ✓ | ✓ |
| Target temperature | ✓ | ✓ | ✓ | ✓ |
| Lock / Unlock | ✓ | ✓ | ✓ | ✓ |
| Flash lights | ✓ | ✓ | ✓ | ✓ |
| Wake vehicle | ✓ | ✓ | ✓ | ✓ |
| Service due km/days | ✓ | ✓ | ✓ | ✓ |
| Online status | ✓ | ✓ | ✓ | ✓ |
| Battery SoC % | ✓ | ✓ | ✓ | ✓ |
| Charge state | ✓ | ✓ | ✓ | ✓ |
| Charge power kW | ✓ | ✓ | ✓ | ✓ |
| Charge ETA | ✓ | ✓ | ✓ | ✓ |
| Charge target % | ✓ | ✓ | ✓ | ✓ |
| Window heating | ✓ | ✓ | ✓ | ✓ |
| Departure timers 1–3 | ✓ | ✓ | — | — |
| Battery temperature | ✓ | ✓ | — | — |
| AdBlue range | ✓ | ✓ | — | — |

---

## Installation

### HACS

1. HACS → Intégrations → ⋮ → Dépôts personnalisés
2. URL : `https://github.com/its-me-prash/vag-connect-ha` — Catégorie : Intégration
3. Installer **VAG Connect** → Redémarrer Home Assistant
4. Paramètres → Intégrations → **+ Intégration** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Redémarrez Home Assistant.

---

## Configuration

| Field | Required | Description |
|---|---|---|
| Marque | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| E-mail | ✓ | E-mail de connexion de l'application constructeur |
| Mot de passe | ✓ | Mot de passe de l'application |
| S-PIN | — | Requis pour le verrouillage (dans Sécurité dans l'app) |
| Intervalle | — | Minutes entre les mises à jour (défaut : 5) |

**Quelle app ?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Limitations Connues

- **S-PIN** requis pour le verrouillage — à configurer dans l'app
- **Intervalle** minimum 5 minutes — trop court entraîne un blocage temporaire
- **2FA** — confirmer une fois manuellement dans l'app
- **Porsche / VW NA** — fonctionnel en Beta, testeurs recherchés

---

## Feuille de Route

| Version | Content |
|---|---|
| ✅ v0.14.1 | Platinum, own CARIAD client |
| ✅ Beta | Porsche (Auth0 + PPA API) |
| ✅ Beta | VW North America |
| ✅ v1.0.0 | Porsche + VW NA (Beta), 7 brands |
| ✅ v1.5.7 | English labels, CUPRA/SEAT scope fix |
| 🔜 v2.0.0 | HACS Default, trip statistics, charging history |

---

## Licence

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** est une marque non déposée (™, pas ®). Veuillez ne pas utiliser ce nom dans les forks afin d'éviter toute confusion.

Cette intégration est un projet communautaire indépendant sans affiliation avec Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG ou toute filiale VAG.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
