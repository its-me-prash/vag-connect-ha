#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Wake the car + wait + re-read selectivestatus.

Hypothesis: PHEV gasoline ECU reports only when the car is "awake" or after
explicit refresh-request. Cariad shows the car as electric-only because the
gasoline data hasn't been updated recently (climate settings stamp is from
2026-04-12, almost a month old).

Workflow:
  1. POST /vehicleWakeup → triggers backend to query the car
  2. Wait 30 seconds
  3. Re-read selectivestatus → see if gasoline data appears now
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
_WAIT_SECONDS = 30


def _read_vin() -> str:
    if _LOCAL.exists():
        for line in _LOCAL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("vin:"):
                return line[4:].strip()
    return "WVWZZZAUZFW805377"


async def main():
    email = input("VW account email: ").strip()
    password = getpass.getpass("VW account password: ")
    if not email or not password:
        sys.exit("ERROR: email + password required")

    vin = _read_vin()
    print(f"\nWake + Refresh test for VIN ...{vin[-4:]}")
    print("=" * 100)

    async with aiohttp.ClientSession() as session:
        # === Step 1: Login ===
        print("\n[1/4] Login...", end=" ", flush=True)
        try:
            auth = _idk.IDKAuth(session, _models.BRAND_VW_EU)
            tokens = await auth.authenticate(email, password)
            print(f"✓ ({len(tokens.access_token)} char token)")
        except Exception as exc:
            print(f"✗ {exc}")
            return 1

        headers = {
            "Authorization": f"Bearer {tokens.access_token}",
            "Accept": "application/json",
            "User-Agent": "Volkswagen/3.51.1-android/14",
            "Accept-Language": "de-de",
        }

        # === Step 2: Read fuelStatus BEFORE wake ===
        print("\n[2/4] Read fuelStatus BEFORE wake...")
        async with session.get(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/selectivestatus?jobs=fuelStatus,measurements",
            headers=headers,
        ) as resp:
            text = await resp.text()
            print(f"      HTTP {resp.status}")
            if 200 <= resp.status < 300:
                data = json.loads(text)
                fs = data.get("fuelStatus", {}).get("rangeStatus", {}).get("value", {})
                ms = data.get("measurements", {}).get("fuelLevelStatus", {}).get("value", {})
                print(f"      fuelStatus.carType: {fs.get('carType')!r}")
                print(f"      fuelStatus.primaryEngine: {fs.get('primaryEngine')}")
                print(f"      fuelStatus.secondaryEngine: {fs.get('secondaryEngine')}")
                print(f"      measurements.carType: {ms.get('carType')!r}")
                print(f"      measurements.primaryEngineType: {ms.get('primaryEngineType')!r}")
                print(f"      measurements.secondaryEngineType: {ms.get('secondaryEngineType')!r}")

        # === Step 3: Trigger wake ===
        print("\n[3/4] Trigger vehicleWakeup...")
        # Try v2 first (Audi-style), fall back to v1 (VW-style)
        for version in ["v2", "v1"]:
            url = f"{_BASE}/vehicle/{version}/vehicles/{vin}/vehicleWakeup"
            async with session.post(url, headers=headers, json={}) as resp:
                text = await resp.text()
                marker = "✓" if 200 <= resp.status < 300 else "✗"
                print(f"      {marker} {version}: HTTP {resp.status}  {text[:150]}")
                if 200 <= resp.status < 300:
                    print(f"      Wake successful via {version}!")
                    break

        # === Step 4: Wait + re-read ===
        print(f"\n[4/4] Waiting {_WAIT_SECONDS}s for car to wake + report...")
        for i in range(_WAIT_SECONDS, 0, -5):
            print(f"      ... {i}s remaining", end="\r", flush=True)
            await asyncio.sleep(5)
        print(" " * 40, end="\r")

        print(f"\n      Re-reading fuelStatus AFTER wake...")
        async with session.get(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/selectivestatus?jobs=fuelStatus,measurements",
            headers=headers,
        ) as resp:
            text = await resp.text()
            print(f"      HTTP {resp.status}")
            if 200 <= resp.status < 300:
                data = json.loads(text)
                fs = data.get("fuelStatus", {}).get("rangeStatus", {}).get("value", {})
                ms = data.get("measurements", {}).get("fuelLevelStatus", {}).get("value", {})
                print(f"      fuelStatus.carType: {fs.get('carType')!r}")
                print(f"      fuelStatus.primaryEngine: {fs.get('primaryEngine')}")
                print(f"      fuelStatus.secondaryEngine: {fs.get('secondaryEngine')}")
                print(f"      measurements.carType: {ms.get('carType')!r}")
                print(f"      measurements.primaryEngineType: {ms.get('primaryEngineType')!r}")
                print(f"      measurements.secondaryEngineType: {ms.get('secondaryEngineType')!r}")

                # Compare timestamps
                fs_ts = fs.get("carCapturedTimestamp", "")
                ms_ts = ms.get("carCapturedTimestamp", "")
                print(f"\n      Timestamps:")
                print(f"      fuelStatus carCapturedTimestamp: {fs_ts}")
                print(f"      measurements.fuelLevelStatus carCapturedTimestamp: {ms_ts}")

        print("\n" + "=" * 100)
        print("If carType is still 'electric' or secondaryEngine is still missing → no gasoline data possible")
        print("If new timestamp + secondaryEngine appears → wake refreshed the gasoline ECU!")


if __name__ == "__main__":
    asyncio.run(main())
