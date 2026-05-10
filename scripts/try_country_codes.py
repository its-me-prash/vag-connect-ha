#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Test different country codes in fs-car URL — CH/DE/AT/EU.

Pre-Cariad MBB URLs include /fs-car/bs/{service}/v1/{brand}/{country}/...
If the VIN is registered to a different country than what we send, the
permission check on the gateway returns 403. Try common EU country codes.
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
_MSG = "https://msg.volkswagen.de"

# Common EU country codes — your GTE could be registered to any of these
_COUNTRIES = ["DE", "CH", "AT", "FR", "IT", "ES", "GB", "NL", "BE", "LU", "EU"]


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


async def _try(session, vin, token, x_client, country, endpoint_name, path):
    url = f"{_MSG}/fs-car/bs/{path}/v1/VW/{country}/vehicles/{vin}/{endpoint_name}"
    try:
        async with session.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": _USER_AGENT,
                "X-Client-Id": x_client,
                "X-App-Name": "Volkswagen",
                "X-App-Version": "3.51.1",
            },
        ) as resp:
            text = (await resp.text())[:60]
            return resp.status, text
    except Exception as exc:
        return 0, str(exc)[:60]


async def main():
    env = _read_env()
    if not env.get("vw_access_token"):
        sys.exit("ERROR: no vw_access_token in mbb.local.bru — run get_mbb_token.py first")

    print(f"\nTesting fs-car URLs across country codes (charger endpoint, PHEV-relevant)")
    print(f"VIN: ...{env['vin'][-4:]}")
    print("=" * 90)
    print(f"{'Country':<10} {'charger':<35} {'status':<35}")
    print("-" * 90)

    async with aiohttp.ClientSession() as session:
        for country in _COUNTRIES:
            charger_status, charger_body = await _try(
                session, env["vin"], env["vw_access_token"], env["x_client_id"],
                country, "charger", "batterycharge",
            )
            status_status, status_body = await _try(
                session, env["vin"], env["vw_access_token"], env["x_client_id"],
                country, "status", "vsr",
            )
            charger_marker = "✓" if 200 <= charger_status < 300 else "✗"
            status_marker = "✓" if 200 <= status_status < 300 else "✗"
            print(f"{country:<10} {charger_marker}{charger_status} {charger_body[:30]:<32} {status_marker}{status_status} {status_body[:30]:<32}")

    print("=" * 90)
    print("\nLEGEND: ✓2xx = country grants access | ✗403 = no permission for this country")
    print("        ✗404 = country code not recognized at all")


if __name__ == "__main__":
    asyncio.run(main())
