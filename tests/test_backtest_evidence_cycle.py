from __future__ import annotations

import json
import sqlite3

from services.backtest import evidence_cycle


def test_default_evidence_windows_expose_multiple_benchmarks() -> None:
    windows = evidence_cycle.default_evidence_windows()
    window_ids = {str(item["window_id"]) for item in windows}

    assert len(windows) >= 8
    assert windows[0]["window_id"] == "synthetic_default"
    assert "false_breakout_whipsaw" in window_ids
    assert "event_trend_grind" in window_ids
    assert "low_vol_fee_bleed" in window_ids
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
    monkeypatch.setattr(
        evidence_cycle,
        "load_paper_history_evidence",
        lambda journal_path="", symbol="": {
            "ok": False,
            "status": "missing",
            "journal_path": "/tmp/trade_journal.sqlite",
            "symbol_filter": symbol or None,
            "source": "trade_journal_sqlite",
            "as_of": None,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": [],
            "caveat": "No persisted trade journal exists yet.",
        },
    )
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


def test_load_paper_history_evidence_filters_by_symbol(tmp_path) -> None:
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
                ("f1", "2026-03-19T12:00:00Z", "breakout_donchian", "o1", "2026-03-19T12:00:00Z", "paper", "BTC/USD", "buy", 1.0, 100.0, 0.1, "USD"),
                ("f2", "2026-03-19T12:10:00Z", "breakout_donchian", "o2", "2026-03-19T12:10:00Z", "paper", "BTC/USD", "sell", 1.0, 110.0, 0.1, "USD"),
                ("f3", "2026-03-19T12:20:00Z", "breakout_donchian", "o3", "2026-03-19T12:20:00Z", "paper", "APR/USD", "buy", 1.0, 50.0, 0.1, "USD"),
                ("f4", "2026-03-19T12:30:00Z", "breakout_donchian", "o4", "2026-03-19T12:30:00Z", "paper", "APR/USD", "sell", 1.0, 40.0, 0.1, "USD"),
            ],
        )
        con.commit()
    finally:
        con.close()

    out = evidence_cycle.load_paper_history_evidence(journal_path=str(db), symbol="BTC/USD")

    assert out["status"] == "available"
    assert out["symbol_filter"] == "BTC/USD"
    assert out["fills_count"] == 2
    assert out["strategy_count"] == 1
    assert out["rows"][0]["strategy"] == "breakout_donchian"
    assert out["rows"][0]["closed_trades"] == 1
    assert out["rows"][0]["net_realized_pnl"] > 0.0
    assert "BTC/USD" in out["caveat"]


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
        lambda journal_path="", symbol="": {
            "ok": True,
            "status": "available",
            "journal_path": "/tmp/trade_journal.sqlite",
            "symbol_filter": symbol or None,
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


def test_run_strategy_evidence_cycle_rank1_downgrade_keeps_rank_aware_reason(monkeypatch) -> None:
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
                    "max_drawdown_pct": 8.5,
                    "regime_robustness": 1.0,
                    "regime_return_dispersion_pct": 1.2,
                    "slippage_sensitivity_pct": 0.3,
                    "closed_trades": 3,
                    "trade_count": 4,
                    "exposure_fraction": 0.25,
                }
            ],
        },
    )
    monkeypatch.setattr(
        evidence_cycle,
        "load_paper_history_evidence",
        lambda journal_path="", symbol="": {
            "ok": True,
            "status": "available",
            "journal_path": "/tmp/trade_journal.sqlite",
            "symbol_filter": symbol or None,
            "source": "trade_journal_sqlite",
            "as_of": "2026-03-19T12:00:00Z",
            "fills_count": 6,
            "strategy_count": 1,
            "rows": [
                {
                    "strategy": "breakout_donchian",
                    "fills": 6,
                    "closed_trades": 3,
                    "win_rate": 0.0,
                    "net_realized_pnl": -5.0,
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
    assert row["rank"] == 1
    assert row["decision"] == "freeze"
    assert "weaker than the top aggregate candidate" not in row["decision_reason"]
    assert "strongest aggregate candidate" in row["decision_reason"]
    assert "negative after 3 closed trade(s)" in row["decision_reason"]


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
        lambda journal_path="", symbol="": {
            "ok": True,
            "status": "available",
            "journal_path": "/tmp/trade_journal.sqlite",
            "symbol_filter": symbol or None,
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


def test_run_strategy_evidence_cycle_ignores_other_symbol_paper_history(tmp_path) -> None:
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
                ("f1", "2026-03-19T12:00:00Z", "breakout_donchian", "o1", "2026-03-19T12:00:00Z", "paper", "APR/USD", "buy", 1.0, 50.0, 0.1, "USD"),
                ("f2", "2026-03-19T12:10:00Z", "breakout_donchian", "o2", "2026-03-19T12:10:00Z", "paper", "APR/USD", "sell", 1.0, 40.0, 0.1, "USD"),
            ],
        )
        con.commit()
    finally:
        con.close()

    out = evidence_cycle.run_strategy_evidence_cycle(
        base_cfg={},
        symbol="BTC/USD",
        windows=[
            {
                "window_id": "w1",
                "label": "One",
                "warmup_bars": 5,
                "candles": evidence_cycle._candles_from_closes([100.0, 101.0, 102.0, 103.0, 104.0, 105.0], start_ts_ms=1_700_000_000_000),
            },
            {
                "window_id": "w2",
                "label": "Two",
                "warmup_bars": 5,
                "candles": evidence_cycle._candles_from_closes([100.0, 99.0, 98.0, 97.0, 96.0, 95.0], start_ts_ms=1_700_010_000_000),
            },
        ],
        paper_history_path=str(db),
    )

    breakout_row = next(row for row in out["aggregate_leaderboard"]["rows"] if row["strategy"] == "breakout_donchian")
    assert out["paper_history"]["symbol_filter"] == "BTC/USD"
    assert breakout_row["paper_history_note"] == "No strategy-attributed persisted paper-history fills are available yet."
    assert "negative after" not in breakout_row["decision_reason"]


def test_persist_strategy_evidence_writes_latest_and_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(evidence_cycle, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(evidence_cycle, "ensure_dirs", lambda: None)
    report = {"ok": True, "as_of": "2026-03-19T12:00:00Z"}

    out = evidence_cycle.persist_strategy_evidence(report)

    latest_path = tmp_path / "strategy_evidence" / "strategy_evidence.latest.json"
    assert out["ok"] is True
    assert latest_path.exists()
    assert json.loads(latest_path.read_text(encoding="utf-8"))["as_of"] == "2026-03-19T12:00:00Z"


def test_persist_strategy_evidence_attaches_comparison_to_previous_latest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(evidence_cycle, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(evidence_cycle, "ensure_dirs", lambda: None)
    latest_dir = tmp_path / "strategy_evidence"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_path = latest_dir / "strategy_evidence.latest.json"
    (latest_dir / "strategy_evidence.20260317T120000Z.json").write_text(
        json.dumps(
            {
                "ok": True,
                "as_of": "2026-03-17T12:00:00Z",
                "aggregate_leaderboard": {"rows": [{"strategy": "breakout_donchian", "rank": 1, "decision": "keep"}]},
            }
        ),
        encoding="utf-8",
    )
    (latest_dir / "strategy_evidence.20260318T120000Z.json").write_text(
        json.dumps(
            {
                "ok": True,
                "as_of": "2026-03-18T12:00:00Z",
                "aggregate_leaderboard": {"rows": [{"strategy": "ema_cross", "rank": 1, "decision": "keep"}]},
            }
        ),
        encoding="utf-8",
    )
    latest_path.write_text(
        json.dumps(
            {
                "ok": True,
                "as_of": "2026-03-18T12:00:00Z",
                "aggregate_leaderboard": {
                    "rows": [
                        {
                            "strategy": "ema_cross",
                            "rank": 1,
                            "decision": "keep",
                            "leaderboard_score": 0.40,
                            "avg_return_pct": 2.0,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    report = {
        "ok": True,
        "as_of": "2026-03-19T12:00:00Z",
        "aggregate_leaderboard": {
            "rows": [
                {
                    "strategy": "breakout_donchian",
                    "rank": 1,
                    "decision": "keep",
                    "leaderboard_score": 0.55,
                    "avg_return_pct": 8.0,
                },
                {
                    "strategy": "ema_cross",
                    "rank": 2,
                    "decision": "improve",
                    "leaderboard_score": 0.35,
                    "avg_return_pct": 1.5,
                },
            ]
        },
    }

    evidence_cycle.persist_strategy_evidence(report)

    persisted = json.loads(latest_path.read_text(encoding="utf-8"))
    comparison = dict(persisted.get("comparison") or {})
    assert comparison["has_previous"] is True
    assert comparison["top_strategy_previous"] == "ema_cross"
    assert comparison["top_strategy_current"] == "breakout_donchian"
    assert comparison["top_strategy_changed"] is True
    assert report["comparison"]["top_strategy_changed"] is True
    assert comparison["recent_trend"]["run_count"] == 3
    assert comparison["recent_trend"]["transition_count"] == 2
    assert comparison["recent_trend"]["current_top_streak"] == 1
    assert comparison["recent_trend"]["top_strategy_sequence"] == [
        "breakout_donchian",
        "ema_cross",
        "breakout_donchian",
    ]
    changes = {item["strategy"]: item for item in comparison["changes"]}
    assert changes["ema_cross"]["movement"] == "degraded"
    assert changes["breakout_donchian"]["movement"] == "new"


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
        "comparison": {
            "has_previous": True,
            "previous_as_of": "2026-03-18T12:00:00Z",
            "current_as_of": "2026-03-19T12:00:00Z",
            "top_strategy_previous": "ema_cross",
            "top_strategy_current": "breakout_donchian",
            "top_strategy_changed": True,
            "improved_count": 1,
            "degraded_count": 1,
            "unchanged_count": 0,
            "new_count": 0,
            "summary_text": "Top strategy changed from ema_cross to breakout_donchian versus the prior persisted evidence run.",
            "recent_trend": {
                "run_count": 3,
                "distinct_top_strategy_count": 2,
                "current_top_streak": 1,
                "summary_text": "Top strategy changed 2 time(s) across the last 3 persisted evidence runs; current top is breakout_donchian.",
            },
            "changes": [
                {
                    "strategy": "breakout_donchian",
                    "movement": "improved",
                    "previous_rank": 2,
                    "current_rank": 1,
                    "previous_decision": "improve",
                    "current_decision": "keep",
                }
            ],
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
    assert "## Run-to-Run Comparison" in text
    assert "top strategy changed: `yes`" in text
    assert "Top strategy changed from ema_cross to breakout_donchian" in text
    assert "- recent persisted runs considered: `3`" in text
    assert "- distinct recent top strategies: `2`" in text
    assert "- current top streak: `1`" in text
    assert "Recent trend: Top strategy changed 2 time(s) across the last 3 persisted evidence runs; current top is breakout_donchian." in text
    assert "Decision: `keep`" in text
    assert "- evidence status: `unknown`" in text
    assert "- confidence: `unknown`" in text
    assert "- paper-history: 1 closed trade, positive net realized pnl." in text
    assert "- `breakout_donchian`" in text
    assert "- extend persisted evidence comparison beyond the immediately previous artifact" in text
    assert "- improve deterministic windows where strategies still show no realized closed-trade participation" in text
    assert "feed the persisted evidence artifact into the Home Digest" not in text
