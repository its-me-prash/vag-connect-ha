# Contributing to VAG Connect

> Thanks for taking the time to look at the code. This integration is
> community-maintained and grows from the contributions of users who file
> good bug reports, share anonymised diagnostics and write small focused
> patches.

---

## Bug reports

Use the issue templates:
<https://github.com/its-me-prash/vag-connect-ha/issues/new/choose>

A good bug report contains:

- VAG Connect version (`manifest.json`)
- Home Assistant version
- Brand and rough vehicle model
- Country / region (some endpoints differ)
- Whether the same action works in the manufacturer's official app
- Whether the manufacturer's online services subscription is active
- Whether an S-PIN is configured
- Sanitised logs (filter `vag_connect` in HA logs)
- Anonymised diagnostics (download via Settings → Devices & Services →
  VAG Connect → ⋮ → Diagnose herunterladen)

**Please remove tokens, full VINs, GPS coordinates, email addresses and
S-PIN values before pasting anything in a public issue.** Diagnostics
already redact these by default — if you paste a raw HA log, double-check.

---

## Pull requests

```bash
git clone https://github.com/its-me-prash/vag-connect-ha
cd vag-connect-ha
pip install pytest pytest-asyncio pytest-cov ruff mypy aiohttp voluptuous homeassistant
python -m pytest tests/        # all green
python -m ruff check custom_components/
python -m mypy custom_components/vag_connect/ --ignore-missing-imports \
  --disallow-untyped-defs --disallow-incomplete-defs --warn-return-any
```

### Rules

- **One PR = one concern.** Atomic, reviewable. The session-based roadmap
  in [`docs/ROADMAP.md`](docs/ROADMAP.md) gives the broader plan.
- **Tests for new features.** A new sensor needs a parser test plus an
  entity test. A new command needs a coordinator dispatch test.
- **Lint clean** — `ruff check` returns 0.
- **CHANGELOG.md updated** — CI fails the PR otherwise.
- **No external runtime dependencies.** `manifest.json` requirements stay
  empty. We bundle our own CARIAD client.
- **No broken behaviour.** If you change a contract, update the matching
  test instead of disabling it.
- **No fake writable entities.** A switch must call a real API command
  or it must not exist.
- **Privacy first.** Anything that could send user data to a third party
  is opt-in and documented in [`PRIVACY.md`](PRIVACY.md).
- **Reference projects must be MIT or Apache-2.0.** GPL code may not be
  copied. See [`NOTICE.md`](NOTICE.md) for the current reference list.

### Commit messages

```
feat:     new feature              → Added in CHANGELOG
fix:      bug fix                  → Fixed
refactor: code restructuring        → Changed
docs:     documentation only
test:     tests
chore:    build / deps
ci:       GitHub Actions
i18n:     translations
```

The `changelog_check.yml` workflow rejects PRs that touch
`custom_components/` without a CHANGELOG entry.

### Translations

`strings.json` is the **English source of truth**. Mirror every change
into all 8 language files (`translations/{de,en,cs,es,fr,nl,pl,sv}.json`).
Use everyday driver vocabulary, not API jargon: e.g. *Lichthupe*, not
*Lichtsignal*.

---

## Adding a new brand

1. `cariad/api/{brand}.py` — API client, derive from `CariadBaseClient`
   or write a brand-specific class
2. `cariad/models.py` — add `BrandConfig` + `BRANDS` entry
3. `cariad/api/factory.py` — routing
4. `const.py` — `BRANDS` dict
5. `config_flow.py` — `_BRAND_OPTIONS`
6. `tests/test_cariad.py` — at minimum: factory routing, status parser
7. README feature table (mirror in all 8 languages)
8. `docs/research/VAG_GROUP_ECOSYSTEM.md` — add the brand to the map

**Capability-first:** the new client must implement a capability check
so commands the vehicle does not support are not exposed as entities.
See issue #56.

---

## Live testers wanted

Some brands are implemented but lack real-world verification:

| Brand | Status |
|---|---|
| Audi | Live tested (S6, multiple models) |
| VW EU | Live tested (ID series, Golf, Tiguan) |
| Škoda | Live tested (Octavia 2025) — see #54 |
| SEAT | Awaiting first real account |
| CUPRA | Live tested (Born — limited by subscription, see #53 #42) |
| Porsche | Implemented, **no live test** — `new_brand.yml` template |
| VW US/CA | Implemented, **no live test** — `new_brand.yml` template |

If you have a vehicle and want to help, open the
[`new_brand.yml`](https://github.com/its-me-prash/vag-connect-ha/issues/new?template=new_brand.yml)
template.

---

## Code of conduct

Be civil. Be specific. Don't paste secrets. The maintainer is one person
on their own time — patches and patience travel further than demands.
