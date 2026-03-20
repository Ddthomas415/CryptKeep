from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None
from fastapi import APIRouter, HTTPException

from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.logging import get_logger

settings = get_settings("gateway")
logger = get_logger("gateway.alerts", settings.log_level)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _extract_detail(exc: Exception) -> tuple[int, str]:
    if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
        status = int(exc.response.status_code)
        detail = "execution_sim request failed"
        try:
            body = exc.response.json()
            detail = str(body.get("detail") or detail)
        except Exception:
            detail = exc.response.text or detail
        return status, detail
    return 503, "execution_sim unavailable"


async def _call_execution_sim(
    *,
    path: str,
    params: dict[str, Any] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    url = f"{settings.execution_sim_url}{path}"
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                res = await client.get(url, params=params)
                res.raise_for_status()
                return res.json()
        except Exception as exc:
            last_err = exc
            if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
                raise
            await asyncio.sleep(0.2)
    raise RuntimeError(str(last_err) if last_err else "execution_sim_unavailable")


def _paper_concentration_pct(summary: dict[str, Any]) -> float:
    gross = abs(_as_float(summary.get("gross_exposure_usd"), 0.0))
    if gross <= 0:
        return 0.0
    positions = list(summary.get("positions") or [])
    if not positions:
        return 0.0
    largest_notional = max(abs(_as_float(p.get("notional_usd"), 0.0)) for p in positions)
    return (largest_notional / gross) * 100.0


def _risk_severity(*, value: float, threshold: float) -> str:
    if threshold <= 0:
        return "info"
    ratio = value / threshold
    if ratio >= 1.5:
        return "high"
    if ratio >= 1.2:
        return "medium"
    return "low"


def _build_paper_risk_alerts(
    *,
    summary: dict[str, Any],
    performance: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    drawdown_pct = _as_float(performance.get("max_drawdown_pct"), 0.0)
    concentration_pct = _paper_concentration_pct(summary)
    drawdown_threshold = float(settings.paper_alert_drawdown_pct_threshold)
    concentration_threshold = float(settings.paper_alert_concentration_pct_threshold)

    alerts: list[dict[str, Any]] = []
    if drawdown_threshold > 0 and drawdown_pct >= drawdown_threshold:
        alerts.append(
            {
                "type": "paper_drawdown_breach",
                "severity": _risk_severity(value=drawdown_pct, threshold=drawdown_threshold),
                "message": f"Paper max drawdown {drawdown_pct:.2f}% breached threshold {drawdown_threshold:.2f}%",
                "metric": "max_drawdown_pct",
                "value": round(drawdown_pct, 4),
                "threshold": round(drawdown_threshold, 4),
                "as_of": now,
            }
        )
    if concentration_threshold > 0 and concentration_pct >= concentration_threshold:
        alerts.append(
            {
                "type": "paper_concentration_breach",
                "severity": _risk_severity(value=concentration_pct, threshold=concentration_threshold),
                "message": (
                    f"Paper concentration {concentration_pct:.2f}% breached threshold "
                    f"{concentration_threshold:.2f}%"
                ),
                "metric": "concentration_pct",
                "value": round(concentration_pct, 4),
                "threshold": round(concentration_threshold, 4),
                "as_of": now,
            }
        )

    metrics = {
        "equity": _as_float(summary.get("equity"), 0.0),
        "gross_exposure_usd": _as_float(summary.get("gross_exposure_usd"), 0.0),
        "max_drawdown_pct": drawdown_pct,
        "concentration_pct": concentration_pct,
    }
    return alerts, metrics


@router.get("")
def list_alerts() -> dict:
    return {"status": "ok", "alerts": []}


@router.get("/paper/risk")
async def paper_risk_alerts() -> dict[str, Any]:
    try:
        summary = await _call_execution_sim(path="/paper/summary")
        performance = await _call_execution_sim(path="/paper/performance", params={"limit": 1000})
        triggered, metrics = _build_paper_risk_alerts(summary=summary, performance=performance)
        thresholds = {
            "drawdown_pct": float(settings.paper_alert_drawdown_pct_threshold),
            "concentration_pct": float(settings.paper_alert_concentration_pct_threshold),
        }
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_risk_alerts_evaluated",
            message="Paper risk alerts evaluated",
            payload={"triggered_count": len(triggered), "thresholds": thresholds, "metrics": metrics},
        )
        return {
            "status": "ok",
            "triggered": triggered,
            "metrics": metrics,
            "thresholds": thresholds,
        }
    except Exception as exc:
        status, detail = _extract_detail(exc)
        logger.error("paper_risk_alerts_failed", extra={"context": {"status": status, "error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_risk_alerts_failed",
            message="Paper risk alerts evaluation failed",
            payload={"error": str(exc)},
            level="ERROR",
        )
        raise HTTPException(status_code=status, detail=detail) from exc
