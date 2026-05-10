from __future__ import annotations

import importlib
import json
import sys
import types
from datetime import datetime, timedelta, timezone


def _reload_module(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.runtime.managed_symbol_selection as mss

    return importlib.reload(mss)


def _iso_at(base: datetime, offset_sec: float) -> str:
    return (base + timedelta(seconds=offset_sec)).isoformat()


def test_scanner_selection_preserves_busy_paper_symbols(monkeypatch, tmp_path):
    mss = _reload_module(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mss,
        "_scan_symbol_candidates",
        lambda *, venue, managed: {
            "ok": True,
            "selected": ["SOL/USD"],
            "source": "coinbase_movers",
            "ts": "2026-05-07T12:00:00Z",
            "errors": [],
            "cached": False,
        },
    )
    monkeypatch.setattr(
        mss,
        "_busy_paper_symbol_details",
        lambda *, venue, managed: [{"symbol": "BTC/USD", "source": "intent_queue", "status": "queued", "age_sec": 12.0}],
    )

    out = mss.resolve_managed_symbol_selection(
        {
            "symbols": ["ETH/USD"],
            "managed_symbols": {"source": "scanner", "preserve_active": True},
        },
        venue="coinbase",
        mode="paper",
        live_enabled=False,
    )

    assert out["symbols"] == ["SOL/USD", "BTC/USD"]
    assert out["selected_symbols"] == ["SOL/USD"]
    assert out["protected_symbols"] == ["BTC/USD"]
    assert out["protected_symbol_details"] == [
        {"symbol": "BTC/USD", "reasons": [{"source": "intent_queue", "status": "queued", "age_sec": 12.0}]}
    ]
    assert out["reason"] == "scanner_selected"
    assert out["scan_ok"] is True
    assert out["scan_cached"] is False


def test_scanner_selection_falls_back_to_base_and_busy_symbols(monkeypatch, tmp_path):
    mss = _reload_module(monkeypatch, tmp_path)
    monkeypatch.setattr(
        mss,
        "_scan_symbol_candidates",
        lambda *, venue, managed: {
            "ok": False,
            "selected": [],
            "source": "coinbase_movers",
            "ts": "2026-05-07T12:00:00Z",
            "errors": ["network"],
            "cached": True,
        },
    )
    monkeypatch.setattr(
        mss,
        "_busy_paper_symbol_details",
        lambda *, venue, managed: [{"symbol": "BTC/USD", "source": "paper_position", "qty": 1.0, "age_sec": 60.0}],
    )

    out = mss.resolve_managed_symbol_selection(
        {
            "symbols": ["ETH/USD"],
            "managed_symbols": {"source": "scanner", "preserve_active": True},
        },
        venue="coinbase",
        mode="paper",
        live_enabled=False,
    )

    assert out["symbols"] == ["ETH/USD", "BTC/USD"]
    assert out["reason"] == "scanner_fallback_to_base_cached"
    assert out["scan_ok"] is False
    assert out["scan_cached"] is True
    assert out["protected_symbol_details"] == [
        {"symbol": "BTC/USD", "reasons": [{"source": "paper_position", "qty": 1.0, "age_sec": 60.0}]}
    ]


def test_scanner_selection_uses_refresh_cache(monkeypatch, tmp_path):
    mss = _reload_module(monkeypatch, tmp_path)
    calls: list[tuple[str, dict[str, float | int]]] = []

    def _select_symbols(*, venue, top_n, min_hot_score, min_change_pct, min_volume_24h):
        calls.append(
            (
                str(venue),
                {
                    "top_n": top_n,
                    "min_hot_score": min_hot_score,
                    "min_change_pct": min_change_pct,
                    "min_volume_24h": min_volume_24h,
                },
            )
        )
        return {
            "ok": True,
            "selected": ["SOL/USD", "ADA/USD"],
            "source": "coinbase_movers",
            "ts": "2026-05-07T12:00:00Z",
            "errors": [],
        }

    monkeypatch.setattr(mss, "select_symbols", _select_symbols)

    managed = {
        "source": "scanner",
        "refresh_sec": 300.0,
        "top_n": 2,
        "min_hot_score": 25.0,
        "min_change_pct": 2.5,
        "min_volume_24h": 100000.0,
    }

    first = mss._scan_symbol_candidates(venue="coinbase", managed=managed)
    second = mss._scan_symbol_candidates(venue="coinbase", managed=managed)

    assert first["selected"] == ["SOL/USD", "ADA/USD"]
    assert first["cached"] is False
    assert second["selected"] == ["SOL/USD", "ADA/USD"]
    assert second["cached"] is True
    assert calls == [
        (
            "coinbase",
            {
                "top_n": 2,
                "min_hot_score": 25.0,
                "min_change_pct": 2.5,
                "min_volume_24h": 100000.0,
            },
        )
    ]

    cache = json.loads(mss._scan_cache_path().read_text(encoding="utf-8"))
    assert cache["selected"] == ["SOL/USD", "ADA/USD"]
    assert cache["venue"] == "coinbase"


def test_scanner_source_fails_closed_to_static_in_live_mode(monkeypatch, tmp_path):
    mss = _reload_module(monkeypatch, tmp_path)

    out = mss.resolve_managed_symbol_selection(
        {
            "symbols": ["ETH/USD"],
            "managed_symbols": {"source": "scanner"},
        },
        venue="coinbase",
        mode="live",
        live_enabled=True,
    )

    assert out["symbols"] == ["ETH/USD"]
    assert out["source"] == "static"
    assert out["reason"] == "scanner_source_live_unsupported"


def test_busy_paper_symbol_details_filters_stale_and_non_actionable_rows(monkeypatch, tmp_path):
    mss = _reload_module(monkeypatch, tmp_path)
    base = datetime(2026, 5, 7, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(mss.time, "time", lambda: base.timestamp())

    paper_mod = types.ModuleType("storage.paper_trading_sqlite")
    intent_mod = types.ModuleType("storage.intent_queue_sqlite")

    class _PaperTradingSQLite:
        def list_positions(self, limit=500):
            return [
                {"symbol": "ETH/USD", "qty": 1.0, "updated_ts": _iso_at(base, -120)},
                {"symbol": "SOL/USD", "qty": 1.0, "updated_ts": _iso_at(base, -(8 * 24 * 60 * 60))},
                {"symbol": "ADA/USD", "qty": 0.0, "updated_ts": _iso_at(base, -60)},
            ]

    class _IntentQueueSQLite:
        def list_intents(self, limit=1000):
            return [
                {"intent_id": "q1", "symbol": "BTC/USD", "venue": "coinbase", "status": "queued", "updated_ts": _iso_at(base, -30), "created_ts": _iso_at(base, -45)},
                {"intent_id": "h1", "symbol": "XRP/USD", "venue": "coinbase", "status": "held", "updated_ts": _iso_at(base, -30), "created_ts": _iso_at(base, -45)},
                {"intent_id": "s1", "symbol": "DOGE/USD", "venue": "coinbase", "status": "submitted", "updated_ts": _iso_at(base, -(2 * 24 * 60 * 60)), "created_ts": _iso_at(base, -(2 * 24 * 60 * 60))},
                {"intent_id": "b1", "symbol": "BNB/USD", "venue": "binance", "status": "queued", "updated_ts": _iso_at(base, -20), "created_ts": _iso_at(base, -25)},
            ]

    paper_mod.PaperTradingSQLite = _PaperTradingSQLite
    intent_mod.IntentQueueSQLite = _IntentQueueSQLite
    monkeypatch.setitem(sys.modules, "storage.paper_trading_sqlite", paper_mod)
    monkeypatch.setitem(sys.modules, "storage.intent_queue_sqlite", intent_mod)

    details = mss._busy_paper_symbol_details(
        venue="coinbase",
        managed={
            "preserve_position_max_age_sec": 3600.0,
            "preserve_intent_max_age_sec": 3600.0,
            "preserve_intent_statuses": ["queued", "submitting", "submitted"],
        },
    )

    assert details == [
        {
            "symbol": "ETH/USD",
            "source": "paper_position",
            "qty": 1.0,
            "updated_ts": _iso_at(base, -120),
            "age_sec": 120.0,
        },
        {
            "symbol": "BTC/USD",
            "source": "intent_queue",
            "status": "queued",
            "intent_id": "q1",
            "updated_ts": _iso_at(base, -30),
            "created_ts": _iso_at(base, -45),
            "age_sec": 30.0,
        },
    ]


def test_protected_symbol_details_merge_multiple_reasons(monkeypatch, tmp_path):
    mss = _reload_module(monkeypatch, tmp_path)

    merged = mss._protected_symbol_details(
        [
            {"symbol": "BTC/USD", "source": "paper_position", "qty": 1.0, "age_sec": 12.0},
            {"symbol": "BTC/USD", "source": "intent_queue", "status": "submitted", "age_sec": 6.0},
            {"symbol": "ETH/USD", "source": "paper_position", "qty": 2.0, "age_sec": 30.0},
        ]
    )

    assert merged == [
        {
            "symbol": "BTC/USD",
            "reasons": [
                {"source": "paper_position", "qty": 1.0, "age_sec": 12.0},
                {"source": "intent_queue", "status": "submitted", "age_sec": 6.0},
            ],
        },
        {
            "symbol": "ETH/USD",
            "reasons": [{"source": "paper_position", "qty": 2.0, "age_sec": 30.0}],
        },
    ]
