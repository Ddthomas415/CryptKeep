from __future__ import annotations

from typing import Any


def _trend_value(latest: dict[str, Any] | None, previous: dict[str, Any] | None, field: str) -> float | None:
    if not latest or not previous:
        return None
    try:
        return float(latest.get(field) or 0.0) - float(previous.get(field) or 0.0)
    except Exception:
        return None


def _build_trend_rows(
    *,
    funding_history: list[dict[str, Any]],
    basis_history: list[dict[str, Any]],
    dislocation_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    latest_funding = funding_history[0] if funding_history else None
    previous_funding = funding_history[1] if len(funding_history) > 1 else None
    carry_delta = _trend_value(latest_funding, previous_funding, "annualized_carry_pct")
    if latest_funding:
        rows.append(
            {
                "theme": "funding",
                "current_state": str(latest_funding.get("dominant_bias") or "flat").replace("_", " ").title(),
                "latest": f"{float(latest_funding.get('annualized_carry_pct') or 0.0):.2f}%",
                "vs_prior": f"{carry_delta:+.2f} pts" if carry_delta is not None else "No prior snapshot",
                "capture_ts": str(latest_funding.get("capture_ts") or "-"),
            }
        )

    latest_basis = basis_history[0] if basis_history else None
    previous_basis = basis_history[1] if len(basis_history) > 1 else None
    basis_delta = _trend_value(latest_basis, previous_basis, "avg_basis_bps")
    if latest_basis:
        rows.append(
            {
                "theme": "basis",
                "current_state": "Premium" if float(latest_basis.get("avg_basis_bps") or 0.0) > 0.0 else "Discount" if float(latest_basis.get("avg_basis_bps") or 0.0) < 0.0 else "Flat",
                "latest": f"{float(latest_basis.get('avg_basis_bps') or 0.0):.2f} bps",
                "vs_prior": f"{basis_delta:+.2f} bps" if basis_delta is not None else "No prior snapshot",
                "capture_ts": str(latest_basis.get("capture_ts") or "-"),
            }
        )

    latest_dislocation = dislocation_history[0] if dislocation_history else None
    previous_dislocation = dislocation_history[1] if len(dislocation_history) > 1 else None
    count_delta = _trend_value(latest_dislocation, previous_dislocation, "positive_count")
    if latest_dislocation:
        rows.append(
            {
                "theme": "dislocations",
                "current_state": str(latest_dislocation.get("top_symbol") or "-"),
                "latest": str(int(latest_dislocation.get("positive_count") or 0)),
                "vs_prior": f"{count_delta:+.0f} venues" if count_delta is not None else "No prior snapshot",
                "capture_ts": str(latest_dislocation.get("capture_ts") or "-"),
            }
        )

    return rows


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


def load_crypto_edge_workspace(*, history_limit: int = 5) -> dict[str, Any]:
    report = load_crypto_edge_report()
    if not bool(report.get("ok")):
        report["history_rows"] = []
        report["funding_history"] = []
        report["basis_history"] = []
        report["dislocation_history"] = []
        report["trend_rows"] = []
        return report

    try:
        from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite
    except Exception as exc:
        report["history_rows"] = []
        report["funding_history"] = []
        report["basis_history"] = []
        report["dislocation_history"] = []
        report["trend_rows"] = []
        report["history_reason"] = f"store_import_failed:{type(exc).__name__}"
        return report

    try:
        store = CryptoEdgeStoreSQLite()
        report["history_rows"] = store.recent_snapshot_history(limit_per_kind=int(history_limit))
        report["funding_history"] = store.recent_funding_history(limit=int(history_limit))
        report["basis_history"] = store.recent_basis_history(limit=int(history_limit))
        report["dislocation_history"] = store.recent_dislocation_history(limit=int(history_limit))
        report["trend_rows"] = _build_trend_rows(
            funding_history=list(report.get("funding_history") or []),
            basis_history=list(report.get("basis_history") or []),
            dislocation_history=list(report.get("dislocation_history") or []),
        )
        return report
    except Exception as exc:
        report["history_rows"] = []
        report["funding_history"] = []
        report["basis_history"] = []
        report["dislocation_history"] = []
        report["trend_rows"] = []
        report["history_reason"] = f"history_read_failed:{type(exc).__name__}"
        return report
