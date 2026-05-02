#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Bruno-vs-Python URL drift check.

Walks ``custom_components/vag_connect/cariad/api/*.py`` for HTTP URLs
constructed via f-string against ``{_BASE}`` constants, then walks
``tests/bruno/<brand>/*.bru`` for documented endpoint URLs, then
reports:

- URLs in Python that have NO matching .bru file (under-documented)
- URLs in .bru that have NO matching Python call (drift / removed
  features / Bruno spec ahead of code)

Pure stdlib, no Bruno-CLI required. Designed for CI pre-flight check
that runs in <1 second.

Usage:
    python scripts/check_bruno_url_drift.py
    python scripts/check_bruno_url_drift.py --brand seat_cupra
    python scripts/check_bruno_url_drift.py --strict  # fail on any drift

Exit codes:
    0 — no drift (or non-strict mode just warned)
    1 — drift detected in strict mode
    2 — config / file-not-found error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows default cp1252 console can't print emoji. Force UTF-8 if
# stdout supports reconfigure (Python 3.7+).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

# Project root = parent of scripts/ directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Python-side: f-string URL extraction.
# Matches f"{_BASE}/some/path/{vin}/etc" or f"{base_url}/..."
# Captures everything between the leading {var} and the closing quote
# so we can normalise placeholders.
_PY_URL_RE = re.compile(
    r'f["\']\{(?:_BASE|base_url|baseurl)\}([^"\']+)["\']'
)

# Bruno-side: extract URL from `get/post/put/patch/delete { url: ... }` block.
_BRU_URL_RE = re.compile(
    r"^\s*url:\s*\{\{base_url\}\}([^\s]+)",
    re.MULTILINE,
)

# Map of brand → (python file pattern, bruno dir)
_BRAND_DIRS = {
    "seat_cupra": (
        "custom_components/vag_connect/cariad/api/seat_cupra.py",
        "tests/bruno/seat_cupra",
    ),
    "skoda": (
        "custom_components/vag_connect/cariad/api/skoda.py",
        "tests/bruno/skoda",
    ),
    "vw_eu": (
        "custom_components/vag_connect/cariad/api/vw_eu.py",
        "tests/bruno/cariad_bff",
    ),
    "audi": (
        "custom_components/vag_connect/cariad/api/audi.py",
        "tests/bruno/cariad_bff",
    ),
}


def _normalise(url: str) -> str:
    """Strip query strings + normalise common placeholder names.

    Matches Python ``{vin}`` against Bruno ``{{vin}}``, normalises
    user-id placeholder variations, strips trailing slashes.
    """
    base = url.split("?", 1)[0]
    # Bruno → Python placeholder collapse: {{vin}} → {vin}
    base = base.replace("{{", "{").replace("}}", "}")
    # Python-side variations of vin placeholder
    base = base.replace("{vin.upper()}", "{vin}")
    base = base.replace("{vin_u}", "{vin}")
    base = base.replace("{VIN}", "{vin}")
    # Python-side variations of user_id placeholder
    base = base.replace("{self._user_id}", "{user_id}")
    base = base.replace("{userId}", "{user_id}")
    return base.rstrip("/")


# Python URLs that contain a runtime `{action}` placeholder which expands
# to one of multiple known values at call time. Expand each into the
# concrete URLs so Bruno's literal-action specs match.
_ACTION_EXPANSIONS = {
    "{action}": ["start", "stop"],
}


def _expand_action_placeholders(urls: set[str]) -> set[str]:
    """For each URL containing a known runtime placeholder, also include
    every concrete expansion. Originals stay (so Bruno can match either)."""
    out = set(urls)
    for placeholder, values in _ACTION_EXPANSIONS.items():
        for url in list(urls):
            if placeholder in url:
                for value in values:
                    out.add(url.replace(placeholder, value))
    return out


def _extract_python_urls(py_path: Path) -> set[str]:
    """Return a set of normalised path-after-host URLs from a Python file."""
    if not py_path.exists():
        return set()
    text = py_path.read_text(encoding="utf-8")
    raw = {_normalise(m.group(1)) for m in _PY_URL_RE.finditer(text)}
    return _expand_action_placeholders(raw)


def _extract_bruno_urls(bruno_dir: Path) -> set[str]:
    """Return a set of normalised URLs from every .bru file in the dir."""
    if not bruno_dir.exists():
        return set()
    urls: set[str] = set()
    for bru in bruno_dir.glob("*.bru"):
        text = bru.read_text(encoding="utf-8")
        urls.update(_normalise(m.group(1)) for m in _BRU_URL_RE.finditer(text))
    return urls


def check_brand(brand: str, *, strict: bool = False) -> int:
    """Check one brand. Return 0 (clean) / 1 (drift) / 2 (config error)."""
    if brand not in _BRAND_DIRS:
        print(f"ERROR: unknown brand {brand!r}", file=sys.stderr)
        return 2
    py_path, bruno_dir = _BRAND_DIRS[brand]
    py_urls = _extract_python_urls(_REPO_ROOT / py_path)
    bru_urls = _extract_bruno_urls(_REPO_ROOT / bruno_dir)

    py_only = py_urls - bru_urls
    bru_only = bru_urls - py_urls
    common = py_urls & bru_urls

    print(f"\n=== Bruno drift check — {brand} ===")
    print(
        f"  Python URLs: {len(py_urls)}   "
        f"Bruno URLs: {len(bru_urls)}   "
        f"Both: {len(common)}"
    )

    if py_only:
        print(f"\n  ⚠️ Python URLs WITHOUT a matching .bru ({len(py_only)}):")
        for url in sorted(py_only):
            print(f"    + {url}")

    if bru_only:
        print(f"\n  ⚠️ Bruno URLs WITHOUT a matching Python call ({len(bru_only)}):")
        for url in sorted(bru_only):
            print(f"    - {url}")

    drift = bool(py_only or bru_only)
    if drift and strict:
        print(f"\n  ❌ Drift detected for {brand} — strict mode → exit 1")
        return 1
    if drift:
        print(
            f"\n  ⚠️ Drift detected for {brand} but strict=False → exit 0\n"
            f"    (Run with --strict to fail CI on drift.)"
        )
    else:
        print(f"\n  ✅ No drift for {brand}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bruno-vs-Python URL drift check for vag-connect-ha"
    )
    parser.add_argument(
        "--brand",
        choices=list(_BRAND_DIRS.keys()) + ["all"],
        default="all",
        help="Which brand client to check (default: all)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any drift (for CI gating)",
    )
    args = parser.parse_args()

    brands = list(_BRAND_DIRS.keys()) if args.brand == "all" else [args.brand]
    rc = 0
    for brand in brands:
        result = check_brand(brand, strict=args.strict)
        rc = max(rc, result)
    print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
