from __future__ import annotations

import json
from pathlib import Path

from services.analytics import multi_symbol_paper_campaign_generator as gen


def _manifest(path: Path, campaigns: list[dict]) -> Path:
    path.write_text(json.dumps({"schema_version": 1, "campaigns": campaigns}), encoding="utf-8")
    return path


def _campaign(*, name: str, state_dir: str, symbol: str = "BTC/USDT") -> dict:
    return {
        "name": name,
        "enabled": True,
        "state_dir": state_dir,
        "strategy": "ema_cross",
        "session_strategy_id": name,
        "symbol": symbol,
        "venue": "coinbase",
        "signal_source": "public_ohlcv_5m",
        "runtime_sec": 900,
        "strategy_drain_sec": 2,
        "poll_interval_sec": 300,
        "max_daily_attempts": 2,
        "desktop_notify": True,
    }


def _candidate(symbol: str, strategy: str, score: float = 72.0) -> dict:
    return {
        "symbol": symbol,
        "preferred_strategy": strategy,
        "composite_score": score,
        "trade_type": "quick_flip",
        "mapping_reason": "test_mapping",
    }


def test_multi_symbol_generator_proposes_isolated_paper_campaign_rows(monkeypatch, tmp_path: Path) -> None:
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="existing_btc", state_dir=".cbp_state")])
    hetzner = _manifest(
        tmp_path / "hetzner.json",
        [
            _campaign(
                name="existing_doge",
                state_dir=".cbp_state_challengers/existing_doge_daily",
                symbol="DOGE/USDT",
            )
        ],
    )
    before = laptop.read_text(encoding="utf-8")
    candidates = [_candidate("ETH/USDT", "momentum"), _candidate("SOL/USDT", "breakout_donchian")]

    monkeypatch.setattr(gen, "build_candidate_list", lambda **_kwargs: list(candidates))

    def _preflight(**kwargs):
        return {
            "ok": True,
            "status": "ok",
            "reason": "public_ohlcv_reachable",
            "symbol": kwargs["symbol"],
            "signal_source": kwargs["signal_source"],
            "row_count": 50,
        }

    report = gen.build_multi_symbol_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        symbols=["ETH/USDT", "SOL/USDT"],
        symbols_data=[{"symbol": "ETH/USDT", "ohlcv": []}, {"symbol": "SOL/USDT", "ohlcv": []}],
        proposal_host="laptop",
        preflight_fn=_preflight,
    )

    assert report["status"] == "ok"
    assert report["summary"]["proposal_count"] == 2
    assert report["preflight_summary"] == {"checked": 2, "passed": 2, "failed": 0}
    rows = [item["proposed_manifest_row"] for item in report["proposals"]]
    assert rows[0]["symbol"] == "ETH/USDT"
    assert rows[0]["state_dir"] == ".cbp_state_challengers/momentum_eth_usdt_default_daily"
    assert rows[1]["symbol"] == "SOL/USDT"
    assert rows[1]["state_dir"] == ".cbp_state_challengers/breakout_donchian_sol_usdt_default_daily"
    assert report["safety"]["manifest_files_written"] is False
    assert report["safety"]["campaigns_started"] is False
    assert report["safety"]["orders_routed"] is False
    assert laptop.read_text(encoding="utf-8") == before


def test_multi_symbol_generator_rejects_failed_ohlcv_preflight(monkeypatch, tmp_path: Path) -> None:
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="existing_btc", state_dir=".cbp_state")])
    hetzner = _manifest(
        tmp_path / "hetzner.json",
        [
            _campaign(
                name="existing_doge",
                state_dir=".cbp_state_challengers/existing_doge_daily",
                symbol="DOGE/USDT",
            )
        ],
    )
    monkeypatch.setattr(gen, "build_candidate_list", lambda **_kwargs: [_candidate("ETH/USDT", "momentum")])

    def _preflight(**_kwargs):
        return {
            "ok": False,
            "status": "ohlcv_source_unreachable",
            "reason": "public ohlcv fetch failed",
        }

    report = gen.build_multi_symbol_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        symbols=["ETH/USDT"],
        symbols_data=[{"symbol": "ETH/USDT", "ohlcv": []}],
        proposal_host="laptop",
        preflight_fn=_preflight,
    )

    assert report["status"] == "no_eligible_proposals"
    assert report["summary"]["proposal_count"] == 0
    assert report["preflight_summary"] == {"checked": 1, "passed": 0, "failed": 1}
    assert "ohlcv_preflight_failed:ohlcv_source_unreachable" in report["rejected_candidates"][0]["reasons"]


def test_multi_symbol_generator_keeps_market_diagnostics_when_no_candidates(monkeypatch, tmp_path: Path) -> None:
    laptop = _manifest(tmp_path / "laptop.json", [_campaign(name="existing_btc", state_dir=".cbp_state")])
    hetzner = _manifest(
        tmp_path / "hetzner.json",
        [
            _campaign(
                name="existing_doge",
                state_dir=".cbp_state_challengers/existing_doge_daily",
                symbol="DOGE/USDT",
            )
        ],
    )
    monkeypatch.setattr(gen, "build_candidate_list", lambda **_kwargs: [])
    monkeypatch.setattr(
        gen,
        "rank_market",
        lambda **_kwargs: [
            {
                "symbol": "ETH/USDT",
                "composite_score": 31.5,
                "symbol_return_pct": 0.4,
                "scores": {"momentum_score": 5.0, "illiquidity_risk_score": 0.0},
            }
        ],
    )

    report = gen.build_multi_symbol_paper_campaign_plan(
        repo_root=tmp_path,
        laptop_manifest=laptop,
        hetzner_manifest=hetzner,
        symbols=["ETH/USDT"],
        symbols_data=[{"symbol": "ETH/USDT", "ohlcv": []}],
        proposal_host="laptop",
    )

    assert report["status"] == "no_ranked_candidates"
    assert report["proposals"] == []
    assert report["market_diagnostics"][0]["symbol"] == "ETH/USDT"
    assert report["market_diagnostics"][0]["trade_type"] == "pass"


def test_fetch_candidate_market_data_returns_structured_factory_error(monkeypatch) -> None:
    def _raise_factory(*_args, **_kwargs):
        raise AttributeError("missing venue")

    monkeypatch.setattr(gen, "make_exchange", _raise_factory)

    out = gen.fetch_candidate_market_data(
        venue="missing_venue",
        symbols=["BTC/USDT"],
        timeframe="5m",
        limit=10,
    )

    assert out["ok"] is False
    assert out["source"] == "exchange_factory"
    assert out["requested"] == 1
    assert out["fetched"] == 0
    assert out["rows"] == []
    assert out["errors"][0]["type"] == "AttributeError"


def test_multi_symbol_generator_writes_only_plan_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = {
        "report_type": gen.REPORT_TYPE,
        "summary": {},
        "safety": {},
        "proposals": [],
        "rejected_candidates": [],
    }

    paths = gen.write_multi_symbol_paper_campaign_plan(report)

    latest = tmp_path / "data" / "multi_symbol_paper_campaign_plans" / "multi_symbol_paper_campaign_plan.latest.json"
    assert paths["latest_json"] == str(latest)
    assert json.loads(latest.read_text(encoding="utf-8"))["report_type"] == gen.REPORT_TYPE
    assert not (tmp_path / "configs" / "paper_evidence_campaigns.json").exists()
    assert not (tmp_path / ".cbp_state_challengers").exists()
