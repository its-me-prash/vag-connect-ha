#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Explore the owner_v1 enrollment endpoints — operationList showed:
  G_VUSERENROLLMENTSTATUS, G_VENROLLMENTSTATUS, G_ENROLLMENTCODE, P_MILAGEENROLLMENT

Hypothesis: vehicle/user enrollment is the missing step that grants
XID_APP_VW system permission to a freshly registered xclientId. We try
common URL patterns for these operations to see if any return data.

ONLY READ-only G_* operations — no destructive D_* calls.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import aiohttp

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parent.parent
_LOCAL = _REPO / "tests" / "bruno" / "mbb_legacy" / "environments" / "mbb.local.bru"

_USER_AGENT = "Volkswagen/3.51.1-android/14"
_MAL = "https://mal-1a.prd.ece.vwg-connect.com"
_MSG = "https://msg.volkswagen.de"


def _read_env() -> dict[str, str]:
    out = {}
    for line in _LOCAL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        for f in ("vw_access_token", "x_client_id", "vin"):
            if line.startswith(f + ":"):
                v = line[len(f) + 1:].strip()
                if v and not v.startswith(("PASTE_", "WILL_BE_")):
                    out[f] = v
    return out


async def _get(session, url, headers, name):
    try:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
            marker = "✓" if 200 <= resp.status < 300 else "✗"
            excerpt = text[:120].replace("\n", " ")
            print(f"  {marker} {resp.status:<4} {name:<40} {excerpt}")
            return resp.status, text
    except Exception as exc:
        print(f"  EXC      {name:<40} {exc}")
        return 0, ""


async def main():
    env = _read_env()
    if not env.get("vw_access_token"):
        sys.exit("ERROR: no vw_access_token in mbb.local.bru — run get_mbb_token.py first")

    vin = env["vin"]
    headers = {
        "Authorization": f"Bearer {env['vw_access_token']}",
        "Accept": "application/json",
        "User-Agent": _USER_AGENT,
        "X-Client-Id": env["x_client_id"],
        "X-App-Name": "Volkswagen",
        "X-App-Version": "3.51.1",
    }

    print(f"\nVIN: ...{vin[-4:]}")
    print("=" * 100)
    print("Trying owner_v1 / enrollment endpoint URL variations\n")

    # Common URL patterns for owner_v1 service in MBB
    candidates = [
        # MAL-based (rolesrights gateway)
        ("MAL owner v1 status", f"{_MAL}/api/owner/v1/vehicles/{vin}/userEnrollmentStatus"),
        ("MAL owner v1 enrollment", f"{_MAL}/api/owner/v1/vehicles/{vin}/enrollment"),
        ("MAL owner v1 enrollmentCode", f"{_MAL}/api/owner/v1/vehicles/{vin}/enrollmentCode"),
        ("MAL cs owner v1", f"{_MAL}/api/cs/owner/v1/vehicles/{vin}/enrollmentStatus"),
        ("MAL bs owner v1", f"{_MAL}/api/bs/owner/v1/vehicles/{vin}/enrollmentStatus"),
        ("MAL rolesrights owner", f"{_MAL}/api/rolesrights/operationlist/v1/vehicles/{vin}/services/owner_v1"),

        # FS-CAR based (msg.volkswagen.de)
        ("FS-CAR bs owner v1", f"{_MSG}/fs-car/bs/owner/v1/VW/DE/vehicles/{vin}/enrollmentStatus"),
        ("FS-CAR vehicleMgmt", f"{_MSG}/fs-car/vehicleMgmt/vehicledata/v2/VW/DE/vehicles/{vin}/"),
        ("FS-CAR vehiclepairing", f"{_MSG}/fs-car/vehiclepairing/v1/VW/DE/vehicles/{vin}/pairing"),
        ("FS-CAR enrollment", f"{_MSG}/fs-car/enrollment/v1/VW/DE/vehicles/{vin}/status"),

        # alternative API paths
        ("API users me", f"{_MAL}/api/usermanagement/users/v1/me"),
        ("API my vehicles", f"{_MAL}/api/usermanagement/users/v1/vehicles"),
        ("API user vehicle", f"{_MAL}/api/usermanagement/users/v1/vehicles/{vin}"),
        ("API user info", f"{_MAL}/api/usermanagement/users/v2/me"),
    ]

    for name, url in candidates:
        await _get(session, url, headers, name) if False else None

    async with aiohttp.ClientSession() as session:
        for name, url in candidates:
            await _get(session, url, headers, name)

    print("\n" + "=" * 100)
    print("LEGEND: ✓2xx = endpoint exists + accessible | ✗403 = exists but no permission")
    print("        ✗404 = endpoint doesn't exist at this URL | ✗401 = auth issue")
    print("\nIf ANY 2xx response found → that endpoint may help us with enrollment.")
    print("If all 404 → these operations are not exposed at the URLs we tried.")


if __name__ == "__main__":
    asyncio.run(main())
