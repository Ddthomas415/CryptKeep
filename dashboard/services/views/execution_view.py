from __future__ import annotations

# execution_view.py — auto-split from view_data.py
from dashboard.services.views._shared import *  # noqa: F401,F403

def get_recent_activity() -> list[str]:
    local_rows = _load_local_recent_activity(limit=6)
    if local_rows:
        return local_rows

    envelope = _fetch_envelope("/api/v1/audit/events")
    if isinstance(envelope, dict) and envelope.get("status") == "success":
        data = envelope.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            out = []
            for item in data["items"][:6]:
                if not isinstance(item, dict):
                    continue
                details = str(item.get("details") or "").strip()
                action = str(item.get("action") or "").strip()
                line = details or action
                if line:
                    out.append(line)
            if out:
                return out
    return _default_activity()



def get_portfolio_view() -> dict[str, Any]:
    summary = get_dashboard_summary()
    portfolio = summary.get("portfolio") if isinstance(summary.get("portfolio"), dict) else {}
    watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []

    watch_prices = {
        str(item.get("asset") or ""): float(item.get("price") or 0.0)
        for item in watchlist
        if isinstance(item, dict) and str(item.get("asset") or "").strip()
    }

    local_snapshot = _load_local_portfolio_snapshot(watch_prices)
    if isinstance(local_snapshot, dict):
        local_portfolio = local_snapshot.get("portfolio") if isinstance(local_snapshot.get("portfolio"), dict) else {}
        local_positions = (
            local_snapshot.get("positions") if isinstance(local_snapshot.get("positions"), list) else []
        )
        if local_portfolio and local_positions:
            merged_portfolio = {**portfolio, **local_portfolio}
            return {
                "currency": "USD",
                "portfolio": merged_portfolio,
                "positions": local_positions,
            }

    positions = _default_positions()
    enriched_positions: list[dict[str, Any]] = []
    for row in positions:
        asset = str(row.get("asset") or "")
        size = float(row.get("size") or 0.0)
        entry = float(row.get("entry") or 0.0)
        mark = float(watch_prices.get(asset) or row.get("mark") or 0.0)
        pnl = round((mark - entry) * size, 2) if size and entry and mark else float(row.get("pnl") or 0.0)
        enriched_positions.append(
            {
                "asset": asset,
                "side": str(row.get("side") or "long"),
                "size": size,
                "entry": entry,
                "mark": mark,
                "pnl": pnl,
            }
        )

    return {
        "currency": "USD",
        "portfolio": portfolio,
        "positions": enriched_positions,
    }



def get_trades_view() -> dict[str, Any]:
    summary = get_dashboard_summary()
    pending_approvals = _load_local_pending_approvals(limit=20)
    if not pending_approvals:
        recommendations = get_recommendations()
        pending_approvals = [
            {
                "id": str(item.get("id") or f"rec_{index + 1}"),
                "asset": str(item.get("asset") or ""),
                "side": str(item.get("signal") or "hold"),
                "risk_size_pct": float(item.get("risk_size_pct") or 0.0),
                "status": str(item.get("status") or "pending_review"),
            }
            for index, item in enumerate(recommendations)
            if str(item.get("status") or "").strip() in {"pending_review", "pending", "watch"}
        ]
    if not pending_approvals:
        pending_approvals = [
            {"id": "rec_1", "asset": "SOL", "side": "buy", "risk_size_pct": 1.5, "status": "pending_review"}
        ]

    recent_fills = _load_local_recent_fills(limit=20)
    if not recent_fills:
        recent_fills = _default_recent_fills()

    open_orders = _load_local_open_orders(limit=20)
    failed_orders = _load_local_failed_orders(limit=20)

    return {
        "approval_required": bool(summary.get("approval_required", True)),
        "pending_approvals": pending_approvals,
        "open_orders": open_orders,
        "failed_orders": failed_orders,
        "recent_fills": recent_fills,
    }


