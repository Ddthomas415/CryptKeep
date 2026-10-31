from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from shared.config import get_settings
from shared.logging import configure_logging
from shared.retry import retry_async
from shared.probe import probe_active, probe_headers, require_probe_origin

settings = get_settings()
logger = configure_logging("copilot-tools", settings.log_level)
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def build_opportunity_snapshot(*args, **kwargs):
    """Load optional dashboard intelligence only when the ordinary route uses it."""
    try:
        from dashboard.services.intelligence import build_opportunity_snapshot as build
    except Exception:
        return {
            "status": "unavailable",
            "reason": "dashboard_import_failed",
            "opportunities": [],
        }
    return build(*args, **kwargs)

_MARKET_DATA_URL = "http://market-data:8003"
_NEWS_INGESTION_URL = "http://news-ingestion:8004"
_ARCHIVE_LOOKUP_URL = "http://archive-lookup:8005"


OPENAI_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_market_snapshot",
        "description": "Get the latest known market snapshot for an asset symbol.",
        "parameters": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Ticker symbol like BTC, ETH, or SOL."},
            },
            "required": ["asset"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_risk_summary",
        "description": "Get the current system risk posture and whether trading is enabled.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_operations_summary",
        "description": "Get a simple operational health summary for core research copilot services.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_signal_summary",
        "description": "Get recent market, news, historical, and future-catalyst context for an asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "User question for keyword retrieval; not semantic search."},
                "asset": {"type": "string", "description": "Ticker symbol like BTC, ETH, or SOL."},
            },
            "required": ["asset"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_crypto_edge_report",
        "description": "Get the latest stored research-only crypto structural edge report covering funding, basis, and cross-venue dislocations.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_latest_live_crypto_edge_snapshot",
        "description": "Get the latest stored live-public crypto structural edge snapshot, isolated from sample or manual research data.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_crypto_edge_change_summary",
        "description": "Get a research-only summary of what changed across funding, basis, and cross-venue dislocations between the latest stored snapshots.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_crypto_edge_staleness_summary",
        "description": "Get a research-only summary of whether live-public structural-edge data is stale or whether the collector runtime needs attention.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_crypto_edge_staleness_digest",
        "description": "Get a compact research-only while-away digest for structural-edge freshness, collector health, and recent stored changes.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


def _asset_symbol(asset: str) -> str:
    value = str(asset or "").strip().upper()
    return value.split("/", 1)[0] if "/" in value else value


def _default_market_snapshot(asset: str) -> dict[str, Any]:
    asset_symbol = _asset_symbol(asset)
    return {"asset": asset_symbol, "symbol": f"{asset_symbol}/USDT", "source": "unavailable",
            "ok": False, "as_of": None, "price": None, "bid": None, "ask": None, "volume": None,
            "reason": "market_service_unavailable"}


def _default_signal_summary(asset: str) -> dict[str, Any]:
    return {"asset": _asset_symbol(asset), "market": {"ok": False, "latest_price": None,
            "change_pct": None, "window_samples": 0}, "recent_news": [], "past_context": [],
            "future_context": [], "vector_matches": [],
            "counts": {"recent_news": 0, "past_context": 0, "future_context": 0, "vector_matches": 0},
            "intelligence": {"status": "unavailable", "opportunities": []}, "source": "unavailable"}


async def _request_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    async def _call() -> dict[str, Any]:
        require_probe_origin(url)
        allowed = [_MARKET_DATA_URL, _NEWS_INGESTION_URL, _ARCHIVE_LOOKUP_URL,
                   settings.memory_service_url, settings.parser_service_url,
                   settings.risk_service_url, settings.audit_service_url]
        target = urlsplit(url)
        if target.scheme not in {"http", "https"} or target.username is not None or target.password is not None or (target.scheme, target.netloc) not in {(urlsplit(base).scheme, urlsplit(base).netloc) for base in allowed}:
            raise RuntimeError("unconfigured_service_origin")
        token = str(settings.service_token or "")
        if not token:
            raise RuntimeError("service_auth_not_configured")
        client_options: dict[str, Any] = {}
        if probe_active():
            client_options["transport"] = httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=False,
                                     trust_env=False, **client_options) as client:
            response = await client.request(method, url, params=params, json=payload,
                                            headers={"Authorization": f"Bearer {token}", **probe_headers()})
            response.raise_for_status()
            return response.json()

    try:
        return await retry_async(_call, retries=0 if probe_active() else 1, base_delay=0.2)
    except Exception as exc:
        if probe_active():
            raise
        logger.warning(
            "tool_request_failed",
            extra={"context": {"method": method, "url": url, "error_type": type(exc).__name__}},
        )
        return None


async def get_probe_tool_results(asset: str, question: str, lookback_minutes: int) -> dict[str, Any]:
    """Use persisted retrieval and the real risk response, never tool fallbacks."""
    if not probe_active():
        raise RuntimeError("probe_profile_required")
    signal = await _request_json(
        "POST", f"{settings.memory_service_url.rstrip('/')}/v1/memory/retrieve",
        payload={"asset": _asset_symbol(asset), "question": question,
                 "lookback_minutes": lookback_minutes, "limit": 3},
    )
    if not isinstance(signal, dict) or signal.get("ok") is not True:
        raise RuntimeError("probe_retrieval_unavailable")
    risk = await _request_json("GET", f"{settings.risk_service_url.rstrip('/')}/v1/risk/status")
    if (not isinstance(risk, dict) or risk.get("gate") != "NO_TRADING"
            or risk.get("allow_trading") is not False or risk.get("execution_mode") != "DISABLED"):
        raise RuntimeError("probe_risk_unavailable")
    return {"get_signal_summary": signal, "get_risk_summary": risk}


async def get_market_snapshot(asset: str) -> dict[str, Any]:
    asset_symbol = _asset_symbol(asset)
    symbol = f"{asset_symbol}/USDT"
    payload = await _request_json("GET", f"{_MARKET_DATA_URL}/v1/market/latest", params={"symbol": symbol})
    tick = payload.get("tick") if isinstance(payload, dict) else None
    if isinstance(tick, dict):
        return {
            "ok": True,
            "asset": asset_symbol,
            "symbol": str(tick.get("symbol") or symbol),
            "price": float(tick.get("price") or 0.0),
            "bid": float(tick.get("bid") or 0.0),
            "ask": float(tick.get("ask") or 0.0),
            "volume": float(tick.get("volume") or 0.0),
            "exchange": str(tick.get("exchange") or settings.exchange_id),
            "as_of": tick.get("event_ts"),
            "source": str(tick.get("source") or "market-data"),
        }
    return _default_market_snapshot(asset_symbol)


async def get_risk_summary() -> dict[str, Any]:
    payload = await _request_json("GET", f"{settings.risk_service_url.rstrip('/')}/v1/risk/status")
    if isinstance(payload, dict) and payload:
        return payload
    return {
        "execution_mode": "DISABLED",
        "gate": "NO_TRADING",
        "allow_trading": False,
        "reason": "Research-only mode fallback",
    }


async def get_operations_summary() -> dict[str, Any]:
    services = {
        "audit-log": f"{settings.audit_service_url.rstrip('/')}/healthz",
        "memory-retrieval": f"{settings.memory_service_url.rstrip('/')}/healthz",
        "parser-normalizer": f"{settings.parser_service_url.rstrip('/')}/healthz",
        "risk-stub": f"{settings.risk_service_url.rstrip('/')}/healthz",
        "market-data": f"{_MARKET_DATA_URL}/healthz",
        "news-ingestion": f"{_NEWS_INGESTION_URL}/healthz",
        "archive-lookup": f"{_ARCHIVE_LOOKUP_URL}/healthz",
    }
    results: list[dict[str, Any]] = []
    healthy = 0
    for name, url in services.items():
        payload = await _request_json("GET", url)
        ok = bool((payload or {}).get("ok"))
        if ok:
            healthy += 1
        results.append({"service": name, "ok": ok, "status": "healthy" if ok else "unavailable"})

    return {
        "healthy_services": healthy,
        "total_services": len(results),
        "services": results,
        "source": "healthz",
    }


async def get_signal_summary(asset: str, question: str = "") -> dict[str, Any]:
    asset_symbol = _asset_symbol(asset)
    payload = await _request_json(
        "POST",
        f"{settings.memory_service_url.rstrip('/')}/v1/memory/retrieve",
        payload={
            "asset": asset_symbol,
            "question": question or f"Why is {asset_symbol} moving?",
            "lookback_minutes": 60,
            "limit": 3,
        },
    )
    if isinstance(payload, dict) and payload:
        recent_news = payload.get("recent_news") if isinstance(payload.get("recent_news"), list) else []
        past_context = payload.get("past_context") if isinstance(payload.get("past_context"), list) else []
        future_context = payload.get("future_context") if isinstance(payload.get("future_context"), list) else []
        vector_matches = payload.get("vector_matches") if isinstance(payload.get("vector_matches"), list) else []
        market = payload.get("market") if isinstance(payload.get("market"), dict) else {}
        snapshot = await get_market_snapshot(asset_symbol)
        intelligence = build_opportunity_snapshot(
            signal_row={
                "asset": asset_symbol,
                "signal": "research",
                "confidence": min(
                    0.95,
                    0.4
                    + (0.12 if recent_news else 0.0)
                    + (0.1 if past_context else 0.0)
                    + (0.08 if future_context else 0.0),
                ),
            },
            market_row={
                "price": market.get("latest_price") or snapshot.get("price"),
                "change_24h_pct": market.get("change_pct"),
                "spread": (
                    float(snapshot.get("ask") or 0.0) - float(snapshot.get("bid") or 0.0)
                    if snapshot
                    else 0.0
                ),
                "volume_24h": snapshot.get("volume") if isinstance(snapshot, dict) else 0.0,
            },
            summary={"current_regime": "trend_up"},
        )
        return {
            "asset": asset_symbol,
            "market": market,
            "recent_news": recent_news,
            "past_context": past_context,
            "future_context": future_context,
            "vector_matches": vector_matches,
            "lexical_matches": payload.get("lexical_matches", []),
            "retrieval_method": payload.get("retrieval_method"),
            "keyword_query": payload.get("keyword_query"),
            "vector_method": payload.get("vector_method"),
            "archive_view": payload.get("archive_view"),
            "counts": {
                "recent_news": len(recent_news),
                "past_context": len(past_context),
                "future_context": len(future_context),
                "vector_matches": len(vector_matches),
            },
            "intelligence": intelligence,
            "source": "memory-retrieval",
        }
    return _default_signal_summary(asset_symbol)


async def get_crypto_edge_report() -> dict[str, Any]:
    try:
        from dashboard.services.crypto_edge_research import load_crypto_edge_workspace
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
        }

    try:
        return load_crypto_edge_workspace(history_limit=5)
    except Exception as exc:
        logger.warning(
            "crypto_edge_report_failed",
            extra={"context": {"error_type": type(exc).__name__}},
        )
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
        }


async def get_latest_live_crypto_edge_snapshot() -> dict[str, Any]:
    try:
        from dashboard.services.crypto_edge_research import load_latest_live_crypto_edge_snapshot
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
            "has_live_data": False,
        }

    try:
        return load_latest_live_crypto_edge_snapshot()
    except Exception as exc:
        logger.warning(
            "latest_live_crypto_edge_snapshot_failed",
            extra={"context": {"error_type": type(exc).__name__}},
        )
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
            "has_live_data": False,
        }


async def get_crypto_edge_change_summary() -> dict[str, Any]:
    try:
        from dashboard.services.crypto_edge_research import load_crypto_edge_change_summary
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
            "has_change_data": False,
        }

    try:
        return load_crypto_edge_change_summary(history_limit=5)
    except Exception as exc:
        logger.warning(
            "crypto_edge_change_summary_failed",
            extra={"context": {"error_type": type(exc).__name__}},
        )
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": False,
            "has_change_data": False,
        }


async def get_crypto_edge_staleness_summary() -> dict[str, Any]:
    try:
        from dashboard.services.crypto_edge_research import load_crypto_edge_staleness_summary
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
        }

    try:
        return load_crypto_edge_staleness_summary()
    except Exception as exc:
        logger.warning(
            "crypto_edge_staleness_summary_failed",
            extra={"context": {"error_type": type(exc).__name__}},
        )
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
        }


async def get_crypto_edge_staleness_digest() -> dict[str, Any]:
    try:
        from dashboard.services.crypto_edge_research import load_crypto_edge_staleness_digest
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"store_import_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
        }

    try:
        return load_crypto_edge_staleness_digest()
    except Exception as exc:
        logger.warning(
            "crypto_edge_staleness_digest_failed",
            extra={"context": {"error_type": type(exc).__name__}},
        )
        return {
            "ok": False,
            "reason": f"store_read_failed:{type(exc).__name__}",
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
        }


async def execute_tool_call(name: str, raw_arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(raw_arguments, str):
        try:
            arguments = json.loads(raw_arguments) if raw_arguments.strip() else {}
        except json.JSONDecodeError:
            arguments = {}
    elif isinstance(raw_arguments, dict):
        arguments = raw_arguments
    else:
        arguments = {}

    if name == "get_market_snapshot":
        return await get_market_snapshot(str(arguments.get("asset") or ""))
    if name == "get_risk_summary":
        return await get_risk_summary()
    if name == "get_operations_summary":
        return await get_operations_summary()
    if name == "get_signal_summary":
        return await get_signal_summary(str(arguments.get("asset") or ""), question=str(arguments.get("question") or ""))
    if name == "get_crypto_edge_report":
        return await get_crypto_edge_report()
    if name == "get_latest_live_crypto_edge_snapshot":
        return await get_latest_live_crypto_edge_snapshot()
    if name == "get_crypto_edge_change_summary":
        return await get_crypto_edge_change_summary()
    if name == "get_crypto_edge_staleness_summary":
        return await get_crypto_edge_staleness_summary()
    if name == "get_crypto_edge_staleness_digest":
        return await get_crypto_edge_staleness_digest()
    return {"ok": False, "error": f"unsupported_tool:{name}"}
