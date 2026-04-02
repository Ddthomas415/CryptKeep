from __future__ import annotations

import asyncio

from services.admin.kill_switch import ensure_default as ensure_kill_default
from services.admin.kill_switch import get_state as kill_state
from services.security.permission_probes import DEFAULT_PROBES, run_probes
from services.security.private_connectivity import test_private_connectivity


def _normalize_list(values: list[str] | tuple[str, ...] | None, default: list[str]) -> list[str]:
    out: list[str] = []
    for value in values or default:
        item = str(value).strip()
        if item:
            out.append(item)
    return out or list(default)


def _safe_private_connectivity(exchange: str, *, sandbox: bool = False) -> dict:
    try:
        return test_private_connectivity(exchange, sandbox=bool(sandbox))
    except Exception as e:
        return {"ok": False, "exchange": str(exchange), "reason": type(e).__name__, "error": str(e)[:600]}


def _safe_probes(exchange: str, probe_keys: list[str], *, sandbox: bool = False) -> dict:
    try:
        return run_probes(exchange, probe_keys, sandbox=bool(sandbox))
    except Exception as e:
        return {
            "ok": False,
            "exchange": str(exchange),
            "results": [],
            "reason": type(e).__name__,
            "error": str(e)[:600],
        }


async def run_preflight(
    venues: list[str] | None = None,
    symbols: list[str] | None = None,
    *,
    time_tolerance_ms: int = 1500,
    do_private_check: bool = False,
    probe_keys: list[str] | None = None,
    sandbox: bool = False,
) -> dict:
    ensure_kill_default()
    venue_list = [v.lower() for v in _normalize_list(venues, ["coinbase", "gateio"])]
    symbol_list = _normalize_list(symbols, ["BTC/USD"])
    probes = _normalize_list(probe_keys, list(DEFAULT_PROBES))

    out = {
        "ok": True,
        "venues": venue_list,
        "symbols": symbol_list,
        "time_tolerance_ms": int(time_tolerance_ms),
        "private_checks_enabled": bool(do_private_check),
        "sandbox": bool(sandbox),
        "probe_keys": probes,
        "kill_switch": kill_state(),
        "private_connectivity": [],
        "permission_probes": [],
    }
    if not do_private_check:
        return out

    private_connectivity = []
    permission_probes = []
    all_ok = True
    for venue in venue_list:
        conn = _safe_private_connectivity(venue, sandbox=bool(sandbox))
        probe = _safe_probes(venue, probes, sandbox=bool(sandbox))
        private_connectivity.append(conn)
        permission_probes.append(probe)
        all_ok = all_ok and bool(conn.get("ok")) and bool(probe.get("ok"))

    out["ok"] = all_ok
    out["private_connectivity"] = private_connectivity
    out["permission_probes"] = permission_probes
    return out


if __name__ == "__main__":
    print(asyncio.run(run_preflight()))
