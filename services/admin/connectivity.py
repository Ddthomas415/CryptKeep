from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from services.security.permission_probes import DEFAULT_PROBES, run_probes
from services.security.private_connectivity import test_private_connectivity


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_exchange_connectivity(exchange: str, *, probe_keys: Iterable[str] | None = None) -> Dict[str, Any]:
    ex = str(exchange).lower().strip()
    private = test_private_connectivity(ex)
    probes = run_probes(ex, list(probe_keys or DEFAULT_PROBES))
    ok = bool(private.get("ok")) and bool(probes.get("ok"))
    return {
        "ok": ok,
        "exchange": ex,
        "ts": _now(),
        "private_connectivity": private,
        "permission_probes": probes,
    }


def check_many_connectivity(exchanges: Iterable[str], *, probe_keys: Iterable[str] | None = None) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for ex in exchanges or []:
        rows.append(check_exchange_connectivity(str(ex), probe_keys=probe_keys))
    return {"ok": all(bool(r.get("ok")) for r in rows) if rows else True, "count": len(rows), "rows": rows, "ts": _now()}
