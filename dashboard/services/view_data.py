from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = os.environ.get("CK_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_TIMEOUT_SECONDS = float(os.environ.get("CK_API_TIMEOUT_SECONDS", "0.6"))


def _default_dashboard_summary() -> dict[str, Any]:
    return {
        "mode": "research_only",
        "execution_enabled": False,
        "approval_required": True,
        "risk_status": "safe",
        "kill_switch": False,
        "portfolio": {
            "total_value": 124850.0,
            "cash": 48120.0,
            "unrealized_pnl": 2145.0,
            "realized_pnl_24h": 812.0,
            "exposure_used_pct": 18.4,
            "leverage": 1.0,
        },
        "watchlist": [
            {"asset": "BTC", "price": 84250.12, "change_24h_pct": 2.4, "signal": "watch"},
            {"asset": "ETH", "price": 4421.34, "change_24h_pct": 1.3, "signal": "monitor"},
            {"asset": "SOL", "price": 187.42, "change_24h_pct": 6.9, "signal": "research"},
        ],
    }


def _default_recommendations() -> list[dict[str, Any]]:
    return [
        {
            "asset": "SOL",
            "signal": "buy",
            "confidence": 0.78,
            "summary": "Momentum + catalyst alignment",
            "evidence": "spot volume, ecosystem releases",
            "status": "pending_review",
        },
        {
            "asset": "BTC",
            "signal": "hold",
            "confidence": 0.66,
            "summary": "Range breakout not confirmed",
            "evidence": "weak continuation volume",
            "status": "watch",
        },
    ]


def _default_activity() -> list[str]:
    return [
        "Generated explanation for SOL",
        "Health check passed",
        "Listing logs refreshed",
        "Paper trade blocked by risk policy",
    ]


def _read_mock_envelope(filename: str) -> dict[str, Any] | None:
    path = REPO_ROOT / "crypto-trading-ai" / "shared" / "mock-data" / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch_envelope(path: str) -> dict[str, Any] | None:
    url = f"{API_BASE_URL}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "CryptKeepDashboard/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (TimeoutError, OSError, ValueError, urllib.error.URLError):
        return None


def get_dashboard_summary() -> dict[str, Any]:
    envelope = _fetch_envelope("/api/v1/dashboard/summary")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return dict(envelope["data"])

    mock = _read_mock_envelope("dashboard.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return dict(mock["data"])
    return _default_dashboard_summary()


def get_recommendations() -> list[dict[str, Any]]:
    envelope = _fetch_envelope("/api/v1/trading/recommendations")
    if isinstance(envelope, dict) and envelope.get("status") == "success":
        data = envelope.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            mapped: list[dict[str, Any]] = []
            for item in data["items"]:
                if not isinstance(item, dict):
                    continue
                mapped.append(
                    {
                        "asset": str(item.get("asset") or ""),
                        "signal": str(item.get("side") or "hold"),
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": str(item.get("strategy") or ""),
                        "evidence": str(item.get("target_logic") or ""),
                        "status": str(item.get("status") or "pending"),
                    }
                )
            if mapped:
                return mapped
    return _default_recommendations()


def get_recent_activity() -> list[str]:
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
