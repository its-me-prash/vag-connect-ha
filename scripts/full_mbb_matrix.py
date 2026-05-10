#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Full Python-only MBB test matrix — no Bruno trust required.

Tests EVERY known combination systematically and shows results in a clean
matrix. Eliminates Bruno from the loop entirely.

Test combinations:
  A. VW WeConnect-ID id_token → MBB exchange (VW-brand register)
  B. VW WeConnect-ID access_token → direct on data endpoints
  C. VW WeConnect-ID id_token → direct on data endpoints (as bearer)
  D. Audi id_token → MBB exchange (Audi-brand register) → MBB vwToken → data endpoints
  E. Audi id_token → MBB exchange (VW-brand register) → MBB vwToken → data endpoints

Asks for password ONCE, runs both logins (VW + Audi) sequentially, then
tries all combinations.
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
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

_ha_stub = types.ModuleType("homeassistant")
sys.modules.setdefault("homeassistant", _ha_stub)
for sub in ("config_entries", "core", "helpers", "const", "exceptions", "util"):
    sys.modules.setdefault(f"homeassistant.{sub}", types.ModuleType(f"homeassistant.{sub}"))


def _load(pkg_path: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(pkg_path, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg_path] = mod
    spec.loader.exec_module(mod)
    return mod


_CARIAD_DIR = _REPO / "custom_components" / "vag_connect" / "cariad"
sys.modules["cariad_auth_only"] = types.ModuleType("cariad_auth_only")
sys.modules["cariad_auth_only"].__path__ = [str(_CARIAD_DIR)]
sys.modules["cariad_auth_only.auth"] = types.ModuleType("cariad_auth_only.auth")
sys.modules["cariad_auth_only.auth"].__path__ = [str(_CARIAD_DIR / "auth")]
_load("cariad_auth_only.exceptions", _CARIAD_DIR / "exceptions.py")
_models = _load("cariad_auth_only.models", _CARIAD_DIR / "models.py")
_idk = _load("cariad_auth_only.auth.idk", _CARIAD_DIR / "auth" / "idk.py")


_BRAND_VW_VIA_AUDI = _models.BrandConfig(
    name="vw-via-audi",
    client_id="09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com",
    redirect_uri="myaudi:///",
    user_agent="Android/4.31.0 (Build 800341641.root project 'myaudi_android'.ext.buildTime) Android/13",
    api_base="https://msg.volkswagen.de",
    scope=(
        "address profile badge birthdate birthplace nationalIdentifier "
        "nationality profession email vin phone nickname name picture mbb "
        "gallery openid"
    ),
)


_MBB = "https://mbboauth-1d.prd.ece.vwg-connect.com"
_MBB_REG = f"{_MBB}/mbbcoauth/mobile/register/v1"
_MBB_TOKEN = f"{_MBB}/mbbcoauth/mobile/oauth2/v1/token"
_MAL = "https://mal-1a.prd.ece.vwg-connect.com"
_MSG = "https://msg.volkswagen.de"

_VW_UA = "Volkswagen/3.51.1-android/14"
_AUDI_UA = "Android/4.31.0 (Build 800341641.root project 'myaudi_android'.ext.buildTime) Android/13"

_REG_VW = {
    "client_name": "SM-A405FN", "platform": "google",
    "client_brand": "VW", "appName": "Volkswagen",
    "appVersion": "3.51.1", "appId": "de.volkswagen.car-net.eu.eremote",
}
_REG_AUDI = {
    "client_name": "SM-A405FN", "platform": "google",
    "client_brand": "Audi", "appName": "myAudi",
    "appVersion": "4.31.0", "appId": "de.myaudi.mobile.assistant",
}


def _read_vin() -> str:
    """Read VIN from mbb.local.bru."""
    local = _REPO / "tests" / "bruno" / "mbb_legacy" / "environments" / "mbb.local.bru"
    if not local.exists():
        return "WVWZZZAUZFW805377"  # fallback
    for line in local.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("vin:"):
            return line[4:].strip()
    return "WVWZZZAUZFW805377"


async def _mbb_register(session, brand: str) -> str | None:
    body = _REG_VW if brand == "VW" else _REG_AUDI
    ua = _VW_UA if brand == "VW" else _AUDI_UA
    try:
        async with session.post(
            _MBB_REG,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "User-Agent": ua,
            },
        ) as resp:
            text = await resp.text()
            if resp.status != 200:
                return None
            return json.loads(text).get("client_id")
    except Exception:
        return None


async def _mbb_exchange(session, id_token: str, x_client_id: str, ua: str):
    """Returns (status, body_excerpt, vwToken_dict_or_None)."""
    try:
        async with session.post(
            _MBB_TOKEN,
            data={
                "grant_type": "id_token",
                "token": id_token,
                "scope": "sc2:fal",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": ua,
                "X-Client-Id": x_client_id,
            },
        ) as resp:
            text = await resp.text()
            vw_token = None
            if resp.status == 200:
                try:
                    vw_token = json.loads(text)
                except Exception:
                    pass
            return resp.status, text[:200], vw_token
    except Exception as exc:
        return 0, f"EXCEPTION: {exc}", None


async def _try_data(session, vin: str, token: str, ua: str, x_client: str | None = None):
    """Try a few key data endpoints, return summary string."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": ua,
    }
    if x_client:
        headers["X-Client-Id"] = x_client

    endpoints = [
        ("homeRegion", f"{_MAL}/api/cs/vds/v1/vehicles/{vin}/homeRegion"),
        ("vehicle_status", f"{_MSG}/fs-car/bs/vsr/v1/VW/DE/vehicles/{vin}/status"),
        ("charger", f"{_MSG}/fs-car/bs/batterycharge/v1/VW/DE/vehicles/{vin}/charger"),
    ]

    results = []
    for name, url in endpoints:
        try:
            async with session.get(url, headers=headers) as resp:
                text = (await resp.text())[:80]
                marker = "✓" if 200 <= resp.status < 300 else "✗"
                results.append(f"{marker}{resp.status}")
        except Exception:
            results.append("EXC")
    return " ".join(results)


async def main() -> int:
    email = input("VW account email: ").strip()
    password = getpass.getpass("VW account password: ")
    if not email or not password:
        sys.exit("ERROR: email + password required")

    vin = _read_vin()
    print(f"\nVIN: ...{vin[-4:]}")
    print("=" * 90)

    async with aiohttp.ClientSession() as session:
        # === LOGIN A: VW WeConnect-ID ===
        print("\n[Login A] VW WeConnect-ID (a24fba63)...", end=" ", flush=True)
        try:
            auth_vw = _idk.IDKAuth(session, _models.BRAND_VW_EU)
            tokens_vw = await auth_vw.authenticate(email, password)
            print(f"✓ ({len(tokens_vw.id_token)} char id_token, {len(tokens_vw.access_token)} char access_token)")
        except Exception as exc:
            print(f"✗ FAILED: {exc}")
            tokens_vw = None

        # === LOGIN B: VW via Audi-IDK ===
        print("[Login B] Audi-IDK (09b6cbec)...        ", end=" ", flush=True)
        try:
            auth_audi = _idk.IDKAuth(session, _BRAND_VW_VIA_AUDI)
            tokens_audi = await auth_audi.authenticate(email, password)
            print(f"✓ ({len(tokens_audi.id_token)} char id_token)")
        except Exception as exc:
            print(f"✗ FAILED: {exc}")
            tokens_audi = None

        # === MBB register (both brands) ===
        print()
        x_vw = await _mbb_register(session, "VW")
        x_audi = await _mbb_register(session, "Audi")
        print(f"[MBB Reg] VW brand:   {('✓ ...' + x_vw[-12:]) if x_vw else '✗'}")
        print(f"[MBB Reg] Audi brand: {('✓ ...' + x_audi[-12:]) if x_audi else '✗'}")

        # === Test MATRIX ===
        print("\n" + "=" * 90)
        print("MBB EXCHANGE MATRIX")
        print("=" * 90)
        print(f"{'#':<3} {'id_token from':<22} {'X-Client-Id brand':<18} {'Status':<10} {'Body excerpt':<40}")
        print("-" * 90)

        matrix = []
        if tokens_vw and x_vw:
            matrix.append(("A1", "VW WeConnect-ID", "VW", tokens_vw, x_vw, _VW_UA))
        if tokens_vw and x_audi:
            matrix.append(("A2", "VW WeConnect-ID", "Audi", tokens_vw, x_audi, _AUDI_UA))
        if tokens_audi and x_vw:
            matrix.append(("B1", "Audi-IDK", "VW", tokens_audi, x_vw, _VW_UA))
        if tokens_audi and x_audi:
            matrix.append(("B2", "Audi-IDK", "Audi", tokens_audi, x_audi, _AUDI_UA))

        successful_combos = []
        for label, src, reg_brand, tokens, x_client, ua in matrix:
            status, body, vw_token = await _mbb_exchange(session, tokens.id_token, x_client, ua)
            marker = "✓" if status == 200 else "✗"
            print(f"{label:<3} {src:<22} {reg_brand:<18} {marker}{status:<9} {body[:60]}")
            if status == 200 and vw_token:
                successful_combos.append((label, src, reg_brand, vw_token, ua, x_client))

        # === Data endpoints test for successful combos ===
        if successful_combos:
            print("\n" + "=" * 90)
            print("DATA ENDPOINT MATRIX (für jede erfolgreiche MBB-Exchange)")
            print("=" * 90)
            print(f"{'#':<3} {'src':<18} {'reg':<6} {'homeRegion':<8} {'status':<8} {'charger':<8}")
            print("-" * 90)

            for label, src, reg, vw_token, ua, x_client in successful_combos:
                # Try with vwToken access_token
                results = await _try_data(session, vin, vw_token["access_token"], ua, x_client)
                cells = results.split()
                cells += [""] * (3 - len(cells))
                print(f"{label:<3} {src:<18} {reg:<6} {cells[0]:<8} {cells[1]:<8} {cells[2]:<8}")

        # === BONUS: Try direct IDK access_tokens against data endpoints ===
        print("\n" + "=" * 90)
        print("BONUS: IDK access_token DIREKT auf MBB Data Endpoints")
        print("=" * 90)
        print(f"{'#':<3} {'token from':<22} {'homeRegion':<8} {'status':<8} {'charger':<8}")
        print("-" * 90)

        if tokens_vw:
            results = await _try_data(session, vin, tokens_vw.access_token, _VW_UA)
            cells = results.split()
            cells += [""] * (3 - len(cells))
            print(f"C1  VW WeConnect-ID    {cells[0]:<8} {cells[1]:<8} {cells[2]:<8}")
        if tokens_audi:
            results = await _try_data(session, vin, tokens_audi.access_token, _AUDI_UA)
            cells = results.split()
            cells += [""] * (3 - len(cells))
            print(f"C2  Audi-IDK           {cells[0]:<8} {cells[1]:<8} {cells[2]:<8}")

        print("\n" + "=" * 90)
        print("LEGEND:  ✓2xx = grün  |  ✗400 = invalid_request  |  ✗401 = unauthorized")
        print("         ✗403 = forbidden (CLS check)  |  ✗404 = endpoint missing  |  ✗5xx = server error")
        print("=" * 90)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
