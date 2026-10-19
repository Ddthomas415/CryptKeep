"""Report-only fill cost verification counts (operator decision 2026-10-09): counting must not change."""
from tests.test_paper_gate_qualification_report import _create_journal, _write_jsonl

PROV = {"market_data_source": "public_ohlcv", "ohlcv_sample_mode": False, "ohlcv_timeframe": "1d",
        "ohlcv_venue": "coinbase", "ohlcv_symbol": "BTC/USDT"}


def _journal_row(oid, ts, side, price):
    return (f"fill-{oid}", ts, "sma_200_trend", oid, ts, "coinbase", "BTC/USDT", side, 1.0, price, 0.0, "USD")


def _build(tmp_path, monkeypatch, buy_extra, sell_extra):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    from services.control.paper_gate_qualification_report import build_paper_gate_qualification_report
    from services.control.promotion_thresholds import ES_DAILY_TREND_STRATEGY_ID
    from services.os.app_paths import data_dir
    ev_dir = data_dir() / "evidence" / ES_DAILY_TREND_STRATEGY_ID
    _write_jsonl(ev_dir / "fill_progress.jsonl", [
        {"timestamp": "2026-06-17T00:00:00+00:00", "side": "buy", "size": 1.0, "order_id": "old-buy"},
        {"timestamp": "2026-06-17T01:00:00+00:00", "side": "sell", "size": 1.0, "order_id": "old-sell"},
        {"timestamp": "2026-06-19T00:00:00+00:00", "side": "buy", "size": 1.0, "order_id": "q-buy", **PROV, **buy_extra},
        {"timestamp": "2026-06-19T01:00:00+00:00", "side": "sell", "size": 1.0, "order_id": "q-sell", **PROV, **sell_extra},
    ])
    _create_journal(data_dir() / "trade_journal.sqlite", [
        _journal_row("old-buy", "2026-06-17T00:00:00+00:00", "buy", 100.0),
        _journal_row("old-sell", "2026-06-17T01:00:00+00:00", "sell", 101.0),
        _journal_row("q-buy", "2026-06-19T00:00:00+00:00", "buy", 103.0),
        _journal_row("q-sell", "2026-06-19T01:00:00+00:00", "sell", 104.0),
    ])
    return build_paper_gate_qualification_report()


def test_counts_split_by_verification_without_changing_gate(tmp_path, monkeypatch):
    base = _build(tmp_path / "a", monkeypatch, {}, {})
    tagged = _build(tmp_path / "b", monkeypatch, {"execution_identity_fill_status": "cost_policy_verified"},
                    {"execution_identity_fill_status": "invalid"})
    assert tagged["summary"] == base["summary"]  # report-only: gate counting unchanged
    report = tagged["fill_cost_verification_report_only"]
    assert report["affects_gate"] is False
    assert report["counted_evidence_fills"] == {"cost_policy_verified": 1, "invalid": 1}
    assert report["all_evidence_fills"] == {"no_identity_evidence": 2, "cost_policy_verified": 1, "invalid": 1}
    assert base["fill_cost_verification_report_only"]["counted_evidence_fills"] == {"no_identity_evidence": 2}
