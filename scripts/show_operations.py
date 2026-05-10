#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Show the FULL operationList response — tells us what we're allowed to do."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parent.parent
_LOCAL = _REPO / "tests" / "bruno" / "mbb_legacy" / "environments" / "mbb.local.bru"


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


async def main():
    env = _read_env()
    url = f"https://mal-1a.prd.ece.vwg-connect.com/api/rolesrights/operationlist/v3/vehicles/{env['vin']}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers={
                "Authorization": f"Bearer {env['vw_access_token']}",
                "Accept": "application/json",
                "User-Agent": "Volkswagen/3.51.1-android/14",
            },
        ) as resp:
            print(f"HTTP {resp.status}\n")
            body = await resp.text()
            try:
                data = json.loads(body)
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception:
                print(body)


if __name__ == "__main__":
    asyncio.run(main())
