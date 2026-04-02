from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from services.security.permission_probes import DEFAULT_PROBES, run_probes
from services.security.private_connectivity import test_private_connectivity


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_exchange_connectivity(
    exchange: str,
    *,
    probe_keys: Iterable[str] | None = None,
    sandbox: bool = False,
) -> Dict[str, Any]:
    ex = str(exchange).lower().strip()
    private = test_private_connectivity(ex, sandbox=bool(sandbox))
    probes = run_probes(ex, list(probe_keys or DEFAULT_PROBES), sandbox=bool(sandbox))
    ok = bool(private.get("ok")) and bool(probes.get("ok"))
    return {
        "ok": ok,
        "exchange": ex,
        "sandbox": bool(sandbox),
        "ts": _now(),
        "private_connectivity": private,
        "permission_probes": probes,
    }


def check_many_connectivity(
    exchanges: Iterable[str],
    *,
    probe_keys: Iterable[str] | None = None,
    sandbox: bool = False,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for ex in exchanges or []:
        rows.append(check_exchange_connectivity(str(ex), probe_keys=probe_keys, sandbox=bool(sandbox)))
    return {
        "ok": all(bool(r.get("ok")) for r in rows) if rows else True,
        "count": len(rows),
        "sandbox": bool(sandbox),
        "rows": rows,
        "ts": _now(),
    }
