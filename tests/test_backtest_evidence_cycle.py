from __future__ import annotations

import json
import sqlite3

from services.backtest import evidence_cycle


def test_default_evidence_windows_expose_multiple_benchmarks() -> None:
    windows = evidence_cycle.default_evidence_windows()

    assert len(windows) >= 5
    assert windows[0]["window_id"] == "synthetic_default"
    assert all(int(item["bars"] if "bars" in item else len(item["candles"])) >= 100 for item in windows)


def test_run_strategy_evidence_cycle_aggregates_stubbed_window_rows(monkeypatch) -> None:
    calls: list[str] = []

    def _run_strategy_leaderboard(**kwargs):
        window_key = str(kwargs["candles"][0][0])
        calls.append(window_key)
        if window_key == "1":
            return {
                "ok": True,
                "rows": [
                    {
                        "candidate": "breakout_default",
                        "strategy": "breakout_donchian",
                        "symbol": "BTC/USDT",
                        "rank": 1,
                        "leaderboard_score": 0.8,
                        "net_return_after_costs_pct": 12.0,
                        "max_drawdown_pct": 4.0,
                        "regime_robustness": 1.0,
                        "regime_return_dispersion_pct": 1.2,
                        "slippage_sensitivity_pct": 0.3,
                        "closed_trades": 2,
                        "trade_count": 4,
                        "exposure_fraction": 0.25,
                    },
                    {
                        "candidate": "mean_reversion_default",
                        "strategy": "mean_reversion_rsi",
                        "symbol": "BTC/USDT",
                        "rank": 2,
                        "leaderboard_score": 0.2,
                        "net_return_after_costs_pct": 0.0,
                        "max_drawdown_pct": 0.0,
                        "regime_robustness": 0.0,
                        "regime_return_dispersion_pct": 0.0,
                        "slippage_sensitivity_pct": 0.0,
                        "closed_trades": 0,
                        "trade_count": 0,
                        "exposure_fraction": 0.0,
                    },
                ],
            }
        return {
            "ok": True,
            "rows": [
                {
                    "candidate": "breakout_default",
                    "strategy": "breakout_donchian",
                    "symbol": "BTC/USDT",
                    "rank": 1,
                    "leaderboard_score": 0.7,
                    "net_return_after_costs_pct": 8.0,
                    "max_drawdown_pct": 5.0,
                    "regime_robustness": 1.0,
                    "regime_return_dispersion_pct": 1.5,
                    "slippage_sensitivity_pct": 0.5,
                    "closed_trades": 2,
                    "trade_count": 3,
                    "exposure_fraction": 0.30,
                },
                {
                    "candidate": "mean_reversion_default",
                    "strategy": "mean_reversion_rsi",
                    "symbol": "BTC/USDT",
                    "rank": 2,
                    "leaderboard_score": 0.2,
                    "net_return_after_costs_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "regime_robustness": 0.0,
                    "regime_return_dispersion_pct": 0.0,
                    "slippage_sensitivity_pct": 0.0,
                    "closed_trades": 0,
                    "trade_count": 0,
                    "exposure_fraction": 0.0,
                },
            ],
        }

    monkeypatch.setattr(evidence_cycle, "run_strategy_leaderboard", _run_strategy_leaderboard)
    windows = [
        {"window_id": "w1", "label": "One", "warmup_bars": 5, "candles": [["1", 0, 0, 0, 0, 0]]},
        {"window_id": "w2", "label": "Two", "warmup_bars": 5, "candles": [["2", 0, 0, 0, 0, 0]]},
    ]

    out = evidence_cycle.run_strategy_evidence_cycle(base_cfg={}, symbol="BTC/USDT", windows=windows)

    assert out["ok"] is True
    assert calls == ["1", "2"]
    assert out["window_count"] == 2
    rows = out["aggregate_leaderboard"]["rows"]
    assert rows[0]["candidate"] == "breakout_default"
    assert rows[0]["closed_trades"] == 4
    assert rows[0]["decision"] == "keep"
    assert rows[0]["evidence_status"] == "synthetic_only"
    assert rows[0]["confidence_label"] == "low"
    assert rows[1]["decision"] == "freeze"
    assert rows[1]["evidence_status"] == "insufficient"
    assert out["paper_history"]["status"] == "missing"


def test_load_paper_history_evidence_summarizes_trade_journal(tmp_path) -> None:
    db = tmp_path / "trade_journal.sqlite"
    con = sqlite3.connect(str(db))
    try:
        con.execute(
            """
            CREATE TABLE journal_fills (
              fill_id TEXT PRIMARY KEY,
              journal_ts TEXT NOT NULL,
              intent_id TEXT,
              source TEXT,
              strategy_id TEXT,
              client_order_id TEXT,
              order_id TEXT NOT NULL,
              fill_ts TEXT NOT NULL,
              venue TEXT NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              qty REAL NOT NULL,
              price REAL NOT NULL,
              fee REAL NOT NULL,
              fee_currency TEXT NOT NULL,
              cash_quote REAL,
              pos_qty REAL,
              pos_avg_price REAL,
              realized_pnl_total REAL
            )
            """
        )
        con.executemany(
            "INSERT INTO journal_fills(fill_id, journal_ts, strategy_id, order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                ("f1", "2026-03-19T12:00:00Z", "ema_crossover_v1", "o1", "2026-03-19T12:00:00Z", "paper", "BTC/USD", "buy", 1.0, 100.0, 0.1, "USD"),
                ("f2", "2026-03-19T12:10:00Z", "ema_crossover_v1", "o2", "2026-03-19T12:10:00Z", "paper", "BTC/USD", "sell", 1.0, 110.0, 0.1, "USD"),
            ],
        )
        con.commit()
    finally:
        con.close()

    out = evidence_cycle.load_paper_history_evidence(journal_path=str(db))

    assert out["status"] == "available"
    assert out["fills_count"] == 2
    assert out["strategy_count"] == 1
    assert out["rows"][0]["strategy"] == "ema_cross"
    assert out["rows"][0]["closed_trades"] == 1
    assert out["rows"][0]["net_realized_pnl"] > 0.0


def test_run_strategy_evidence_cycle_downgrades_on_negative_paper_history(monkeypatch) -> None:
    monkeypatch.setattr(
        evidence_cycle,
        "run_strategy_leaderboard",
        lambda **kwargs: {
            "ok": True,
            "rows": [
                {
                    "candidate": "breakout_default",
                    "strategy": "breakout_donchian",
                    "symbol": "BTC/USDT",
                    "rank": 1,
                    "leaderboard_score": 0.8,
                    "net_return_after_costs_pct": 12.0,
                    "max_drawdown_pct": 4.0,
                    "regime_robustness": 1.0,
                    "regime_return_dispersion_pct": 1.2,
                    "slippage_sensitivity_pct": 0.3,
                    "closed_trades": 2,
                    "trade_count": 4,
                    "exposure_fraction": 0.25,
                }
            ],
        },
    )
    monkeypatch.setattr(
        evidence_cycle,
        "load_paper_history_evidence",
        lambda journal_path="": {
            "ok": True,
            "status": "available",
            "journal_path": "/tmp/trade_journal.sqlite",
            "source": "trade_journal_sqlite",
            "as_of": "2026-03-19T12:00:00Z",
            "fills_count": 4,
            "strategy_count": 1,
            "rows": [
                {
                    "strategy": "breakout_donchian",
                    "fills": 4,
                    "closed_trades": 2,
                    "win_rate": 0.0,
                    "net_realized_pnl": -12.5,
                }
            ],
            "caveat": "Supplemental paper history.",
        },
    )

    out = evidence_cycle.run_strategy_evidence_cycle(
        base_cfg={},
        symbol="BTC/USDT",
        windows=[
            {"window_id": "w1", "label": "One", "warmup_bars": 5, "candles": [[1, 0, 0, 0, 0, 0]]},
            {"window_id": "w2", "label": "Two", "warmup_bars": 5, "candles": [[2, 0, 0, 0, 0, 0]]},
        ],
    )

    row = out["aggregate_leaderboard"]["rows"][0]
    assert row["decision"] == "improve"
    assert "negative after 2 closed trade(s)" in row["decision_reason"]
    assert row["evidence_status"] == "paper_thin"
    assert row["confidence_label"] == "low"


def test_run_strategy_evidence_cycle_marks_paper_supported_when_history_is_present(monkeypatch) -> None:
    monkeypatch.setattr(
        evidence_cycle,
        "run_strategy_leaderboard",
        lambda **kwargs: {
            "ok": True,
            "rows": [
                {
                    "candidate": "breakout_default",
                    "strategy": "breakout_donchian",
                    "symbol": "BTC/USDT",
                    "rank": 1,
                    "leaderboard_score": 0.8,
                    "net_return_after_costs_pct": 12.0,
                    "max_drawdown_pct": 4.0,
                    "regime_robustness": 1.0,
                    "regime_return_dispersion_pct": 1.2,
                    "slippage_sensitivity_pct": 0.3,
                    "closed_trades": 2,
                    "trade_count": 4,
                    "exposure_fraction": 0.25,
                }
            ],
        },
    )
    monkeypatch.setattr(
        evidence_cycle,
        "load_paper_history_evidence",
        lambda journal_path="": {
            "ok": True,
            "status": "available",
            "journal_path": "/tmp/trade_journal.sqlite",
            "source": "trade_journal_sqlite",
            "as_of": "2026-03-19T12:00:00Z",
            "fills_count": 6,
            "strategy_count": 1,
            "rows": [
                {
                    "strategy": "breakout_donchian",
                    "fills": 6,
                    "closed_trades": 3,
                    "win_rate": 0.5,
                    "net_realized_pnl": 5.0,
                }
            ],
            "caveat": "Supplemental paper history.",
        },
    )

    out = evidence_cycle.run_strategy_evidence_cycle(
        base_cfg={},
        symbol="BTC/USDT",
        windows=[
            {"window_id": "w1", "label": "One", "warmup_bars": 5, "candles": [[1, 0, 0, 0, 0, 0]]},
            {"window_id": "w2", "label": "Two", "warmup_bars": 5, "candles": [[2, 0, 0, 0, 0, 0]]},
        ],
    )

    row = out["aggregate_leaderboard"]["rows"][0]
    assert row["evidence_status"] == "paper_supported"
    assert row["confidence_label"] == "medium"
    assert "research-grade" in row["evidence_note"]


def test_persist_strategy_evidence_writes_latest_and_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(evidence_cycle, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(evidence_cycle, "ensure_dirs", lambda: None)
    report = {"ok": True, "as_of": "2026-03-19T12:00:00Z"}

    out = evidence_cycle.persist_strategy_evidence(report)

    latest_path = tmp_path / "strategy_evidence" / "strategy_evidence.latest.json"
    assert out["ok"] is True
    assert latest_path.exists()
    assert json.loads(latest_path.read_text(encoding="utf-8"))["as_of"] == "2026-03-19T12:00:00Z"


def test_render_decision_record_includes_decision_summary() -> None:
    report = {
        "as_of": "2026-03-19T12:00:00Z",
        "symbol": "BTC/USDT",
        "window_count": 2,
        "initial_cash": 10000.0,
        "fee_bps": 10.0,
        "slippage_bps": 5.0,
        "windows": [{"window_id": "w1", "label": "One", "bars": 120}, {"window_id": "w2", "label": "Two", "bars": 140}],
        "paper_history": {
            "status": "available",
            "source": "trade_journal_sqlite",
            "journal_path": "/tmp/trade_journal.sqlite",
            "fills_count": 4,
        },
        "aggregate_leaderboard": {
            "rows": [
                {
                    "candidate": "breakout_default",
                    "strategy": "breakout_donchian",
                    "rank": 1,
                    "leaderboard_score": 0.8123,
                    "avg_return_pct": 6.5,
                    "worst_window_return_pct": -1.2,
                    "max_drawdown_pct": 4.0,
                    "closed_trades": 4,
                    "active_window_count": 2,
                    "window_count": 2,
                    "positive_window_count": 1,
                    "best_window_id": "w1",
                    "worst_window_id": "w2",
                    "paper_history_note": "1 closed trade, positive net realized pnl.",
                    "decision": "keep",
                    "decision_reason": "Strong enough.",
                    "biggest_weakness": "False breakouts.",
                    "next_improvement": "Test exits.",
                }
            ]
        },
        "decisions": [{"strategy": "breakout_donchian", "decision": "keep"}],
    }

    text = evidence_cycle.render_decision_record(report, artifact_path="/tmp/report.json")

    assert "Strategy Decision Record — 2026-03-19" in text
    assert "evidence artifact: `/tmp/report.json`" in text
    assert "paper-history source: `trade_journal_sqlite`" in text
    assert "Decision: `keep`" in text
    assert "- evidence status: `unknown`" in text
    assert "- confidence: `unknown`" in text
    assert "- paper-history: 1 closed trade, positive net realized pnl." in text
    assert "- `breakout_donchian`" in text
