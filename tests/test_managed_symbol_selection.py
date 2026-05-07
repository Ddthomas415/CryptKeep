from __future__ import annotations

import importlib
import json


def _reload_module(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.runtime.managed_symbol_selection as mss

    return importlib.reload(mss)


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
    monkeypatch.setattr(mss, "_busy_paper_symbols", lambda: ["BTC/USD"])

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
    monkeypatch.setattr(mss, "_busy_paper_symbols", lambda: ["BTC/USD"])

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
