#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Test engineType + getFuelStatus + oilLevelStatus dedicated endpoints.

Capabilities revealed three NEW operations we haven't directly tested:
  - getEngineType  — might return the TRUE engine info (not the misclassified one)
  - getFuelStatus  — dedicated fuel endpoint (not via selectivestatus)
  - getStates (oilLevelStatus) — oil level (might also have fuel hint)

The capabilities use endpoint:"vs" for some, suggesting URL pattern
/vehicle/v1/vehicles/{vin}/{capability}/...
"""

from __future__ import annotations

import asyncio
import getpass
import importlib.util
import json
import sys
import types
from pathlib import Path

import aiohttp

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

_ha = types.ModuleType("homeassistant")
sys.modules.setdefault("homeassistant", _ha)
for sub in ("config_entries", "core", "helpers", "const", "exceptions", "util"):
    sys.modules.setdefault(f"homeassistant.{sub}", types.ModuleType(f"homeassistant.{sub}"))


def _load(pkg, file_path):
    spec = importlib.util.spec_from_file_location(pkg, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    spec.loader.exec_module(mod)
    return mod


_C = _REPO / "custom_components" / "vag_connect" / "cariad"
sys.modules["c"] = types.ModuleType("c"); sys.modules["c"].__path__ = [str(_C)]
sys.modules["c.auth"] = types.ModuleType("c.auth"); sys.modules["c.auth"].__path__ = [str(_C / "auth")]
_load("c.exceptions", _C / "exceptions.py")
_models = _load("c.models", _C / "models.py")
_idk = _load("c.auth.idk", _C / "auth" / "idk.py")


_LOCAL = _REPO / "tests" / "bruno" / "mbb_legacy" / "environments" / "mbb.local.bru"
_BASE = "https://emea.bff.cariad.digital"


def _read_vin() -> str:
    if _LOCAL.exists():
        for line in _LOCAL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("vin:"):
                return line[4:].strip()
    return "WVWZZZAUZFW805377"


async def _try(session, name, url, headers):
    try:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
            marker = "✓" if 200 <= resp.status < 300 else "✗"
            print(f"\n  {marker} {resp.status:<4} {name}")
            print(f"        URL: {url}")
            if text and text != "{}":
                try:
                    parsed = json.loads(text)
                    pretty = json.dumps(parsed, indent=2, ensure_ascii=False)[:1500]
                    for line in pretty.split("\n"):
                        print(f"        {line}")
                except Exception:
                    print(f"        {text[:400]}")
            return resp.status, text
    except Exception as exc:
        print(f"  EXC      {name}: {exc}")
        return 0, ""


async def main():
    email = input("VW account email: ").strip()
    password = getpass.getpass("VW account password: ")
    if not email or not password:
        sys.exit("ERROR: email + password required")

    vin = _read_vin()
    print(f"\nDedicated endpoint test for VIN ...{vin[-4:]}")
    print("=" * 100)

    async with aiohttp.ClientSession() as session:
        print("\n[Login] Cariad WeConnect-ID...", end=" ", flush=True)
        try:
            auth = _idk.IDKAuth(session, _models.BRAND_VW_EU)
            tokens = await auth.authenticate(email, password)
            print(f"✓")
        except Exception as exc:
            print(f"✗ {exc}")
            return 1

        headers = {
            "Authorization": f"Bearer {tokens.access_token}",
            "Accept": "application/json",
            "User-Agent": "Volkswagen/3.51.1-android/14",
            "Accept-Language": "de-de",
        }

        # Endpoints inferred from operations names + capabilities patterns
        # Common pattern: /vehicle/v1/vehicles/{vin}/{capability}/{noun}
        endpoints = [
            # engineType — direct
            ("engineType direct", f"{_BASE}/vehicle/v1/vehicles/{vin}/engineType"),
            ("engineType v2", f"{_BASE}/vehicle/v2/vehicles/{vin}/engineType"),
            ("engine info", f"{_BASE}/vehicle/v1/vehicles/{vin}/engineInfo"),
            # fuelStatus — dedicated
            ("fuelStatus direct", f"{_BASE}/vehicle/v1/vehicles/{vin}/fuelStatus"),
            ("fuelStatus v2", f"{_BASE}/vehicle/v2/vehicles/{vin}/fuelStatus"),
            # oilLevelStatus
            ("oilLevelStatus", f"{_BASE}/vehicle/v1/vehicles/{vin}/oilLevelStatus"),
            ("oilLevel states", f"{_BASE}/vehicle/v1/vehicles/{vin}/oilLevel/states"),
            ("oilLevel direct", f"{_BASE}/vehicle/v1/vehicles/{vin}/oilLevel"),
            # measurements direct
            ("measurements direct", f"{_BASE}/vehicle/v1/vehicles/{vin}/measurements"),
            # selectivestatus with engineType (we saw it as a job)
            ("selectivestatus jobs=engineType", f"{_BASE}/vehicle/v1/vehicles/{vin}/selectivestatus?jobs=engineType"),
            ("selectivestatus jobs=oilLevelStatus", f"{_BASE}/vehicle/v1/vehicles/{vin}/selectivestatus?jobs=oilLevelStatus"),
            # garage / vehicle metadata
            ("garage", f"{_BASE}/vehicle/v1/garage"),
            ("vehicle metadata", f"{_BASE}/vehicle/v1/vehicles/{vin}"),
        ]

        for name, url in endpoints:
            await _try(session, name, url, headers)

        print("\n" + "=" * 100)
        print("Look for 'gasoline' or 'fuel' in any of these responses!")


if __name__ == "__main__":
    asyncio.run(main())
