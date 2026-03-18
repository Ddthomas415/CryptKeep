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
