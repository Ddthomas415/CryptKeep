from __future__ import annotations

from typing import Any


def load_crypto_edge_report() -> dict[str, Any]:
    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
        }


def load_crypto_edge_workspace(*, history_limit: int = 5) -> dict[str, Any]:
    report = load_crypto_edge_report()
    if not bool(report.get("ok")):
        report["history_rows"] = []
        return report

    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
    except Exception as exc:
        report["history_rows"] = []
        report["history_reason"] = f"store_import_failed:{type(exc).__name__}"
        return report

    try:
        report["history_rows"] = CryptoEdgeStoreSQLite().recent_snapshot_history(limit_per_kind=int(history_limit))
        return report
    except Exception as exc:
        report["history_rows"] = []
        report["history_reason"] = f"history_read_failed:{type(exc).__name__}"
        return report

    try:
        store = CryptoEdgeStoreSQLite()
        report = store.latest_report()
        report["ok"] = True
        report["research_only"] = True
        report["execution_enabled"] = False
        return report
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
        }
