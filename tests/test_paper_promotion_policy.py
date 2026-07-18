from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone


def _policy_config(policy: dict | None = None) -> dict:
    out = {
        "signal_source": "public_ohlcv_1d",
        "strategy": {
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "signal": {"timeframe": "1d"},
        },
    }
    if policy is not None:
        out["promotion"] = {"paper": {"policy": dict(policy)}}
    return out


def _journal(path, order_ids: list[str]) -> None:
    con = sqlite3.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE journal_fills (
              fill_id TEXT PRIMARY KEY,
              journal_ts TEXT NOT NULL,
              order_id TEXT NOT NULL,
              fill_ts TEXT NOT NULL,
              venue TEXT NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              qty REAL NOT NULL,
              price REAL NOT NULL,
              fee REAL NOT NULL,
              fee_currency TEXT NOT NULL
            )
            """
        )
        rows = []
        for idx, order_id in enumerate(order_ids):
            side = "buy" if "buy" in order_id else "sell"
            rows.append(
                (
                    f"fill-{order_id}",
                    f"2026-06-{idx + 1:02d}T00:00:00+00:00",
                    order_id,
                    f"2026-06-{idx + 1:02d}T00:00:00+00:00",
                    "coinbase",
                    "BTC/USDT",
                    side,
                    1.0,
                    100.0 + idx,
                    0.0,
                    "USD",
                )
            )
        con.executemany("INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()


def test_legacy_policy_is_default_and_preserves_existing_thresholds() -> None:
    from services.control.paper_promotion_policy import resolve_paper_promotion_policy
    from services.control.promotion_thresholds import PAPER_MIN_DAYS, PAPER_MIN_ROUND_TRIPS

    policy = resolve_paper_promotion_policy({})

    assert policy.policy_id == "legacy_round_trip_v1"
    assert policy.valid is True
    assert policy.min_calendar_days == PAPER_MIN_DAYS
    assert policy.min_qualified_round_trips == PAPER_MIN_ROUND_TRIPS
    assert policy.min_qualified_bars == 0


def test_strategy_class_policy_cannot_lower_floor_thresholds() -> None:
    from services.control.paper_promotion_policy import resolve_paper_promotion_policy

    policy = resolve_paper_promotion_policy(
        _policy_config(
            {
                "id": "slow_daily_single_symbol_v1",
                "min_calendar_days": 1,
                "min_qualified_round_trips": 1,
                "min_qualified_bars": 1,
            }
        )
    )

    assert policy.valid is False
    assert policy.min_calendar_days == 45
    assert policy.min_qualified_round_trips == 5
    assert policy.min_qualified_bars == 60
    assert "min_calendar_days_below_floor" in policy.invalid_reasons
    assert "min_qualified_round_trips_below_floor" in policy.invalid_reasons
    assert "min_qualified_bars_below_floor" in policy.invalid_reasons


def test_slow_daily_bar_count_uses_unique_source_days_not_loop_iterations() -> None:
    from services.control.paper_promotion_policy import count_qualified_signal_bars

    config = _policy_config(
        {
            "id": "slow_daily_single_symbol_v1",
            "cohort_start": "2026-06-01T00:00:00Z",
        }
    )
    provenance = {
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_timeframe": "1d",
        "ohlcv_venue": "coinbase",
        "ohlcv_symbol": "BTC/USDT",
    }
    signals = [
        {"timestamp": "2026-05-31T00:00:00+00:00", **provenance},
        {"timestamp": "2026-06-01T01:00:00+00:00", **provenance},
        {"timestamp": "2026-06-01T02:00:00+00:00", **provenance},
        {"timestamp": "2026-06-02T01:00:00+00:00", **provenance},
        {"timestamp": "2026-06-03T01:00:00+00:00", **provenance, "ohlcv_sample_mode": True},
    ]

    out = count_qualified_signal_bars(signals, config=config)

    assert out["enabled"] is True
    assert out["qualified_bars_recorded"] == 2
    assert out["qualified_bars_required"] == 60
    assert out["qualified_bars_remaining"] == 58
    assert out["bar_count_source"] == "legacy_signal_date"
    assert out["excluded_before_cohort_signals"] == 1
    assert out["rejection_reason_counts"] == {"sample_mode_not_explicit_false": 1}


def test_intraday_policy_requires_explicit_source_bar_timestamp() -> None:
    from services.control.paper_promotion_policy import count_qualified_signal_bars

    config = {
        "signal_source": "public_ohlcv_5m",
        "strategy": {
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "signal": {"timeframe": "5m"},
        },
        "promotion": {
            "paper": {
                "policy": {"id": "intraday_single_symbol_v1", "min_qualified_bars": 2}
            }
        },
    }
    signal = {
        "timestamp": "2026-06-01T01:00:00+00:00",
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_timeframe": "5m",
        "ohlcv_venue": "coinbase",
        "ohlcv_symbol": "BTC/USDT",
    }

    out = count_qualified_signal_bars([signal], config=config)

    assert out["enabled"] is True
    assert out["qualified_bars_recorded"] == 0
    assert out["rejection_reason_counts"] == {"missing_ohlcv_bar_ts": 1}


def test_qualification_cohort_excludes_old_fills_without_counting_them_unqualified(tmp_path) -> None:
    from services.control.paper_evidence_qualification import qualify_paper_history

    config = _policy_config(
        {
            "id": "slow_daily_single_symbol_v1",
            "cohort_start": "2026-06-16T00:00:00Z",
        }
    )
    provenance = {
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_timeframe": "1d",
        "ohlcv_venue": "coinbase",
        "ohlcv_symbol": "BTC/USDT",
    }
    fills = [
        {
            "timestamp": "2026-06-01T00:00:00+00:00",
            "order_id": "old-buy",
            "side": "buy",
            "size": 1.0,
            **provenance,
        },
        {
            "timestamp": "2026-06-02T00:00:00+00:00",
            "order_id": "old-sell",
            "side": "sell",
            "size": 1.0,
            **provenance,
        },
        {
            "timestamp": "2026-06-16T00:00:00+00:00",
            "order_id": "new-buy",
            "side": "buy",
            "size": 1.0,
            **provenance,
        },
        {
            "timestamp": "2026-06-17T00:00:00+00:00",
            "order_id": "new-sell",
            "side": "sell",
            "size": 1.0,
            **provenance,
        },
    ]
    journal_path = tmp_path / "trade_journal.sqlite"
    _journal(journal_path, ["old-buy", "old-sell", "new-buy", "new-sell"])

    out = qualify_paper_history(
        evidence_fills=fills,
        config=config,
        journal_path=str(journal_path),
    )
    qualification = dict(out["qualification"])

    assert out["closed_trades"] == 1
    assert qualification["evidence_fills"] == 4
    assert qualification["cohort_evidence_fills"] == 2
    assert qualification["excluded_before_cohort_evidence_fills"] == 2
    assert qualification["unqualified_evidence_fills"] == 0
    assert qualification["qualified_order_ids"] == ["new-buy", "new-sell"]


def test_paper_gate_uses_explicit_strategy_class_thresholds() -> None:
    from scripts.check_promotion_gates import evaluate_paper_gates

    config = _policy_config({"id": "slow_daily_single_symbol_v1"})
    provenance = {
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_timeframe": "1d",
        "ohlcv_venue": "coinbase",
        "ohlcv_symbol": "BTC/USDT",
    }
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    sessions = [
        {"timestamp": (start + timedelta(days=idx)).isoformat()}
        for idx in range(45)
    ]
    signals = [
        {
            "timestamp": (start + timedelta(days=idx)).isoformat(),
            "ohlcv_bar_ts": (start + timedelta(days=idx)).isoformat(),
            **provenance,
        }
        for idx in range(60)
    ]
    evidence = {
        "signal": signals,
        "order": [],
        "fill": [],
        "session": sessions,
        "drawdown": [],
    }
    paper_history = {
        "source": "jsonl_provenance+trade_journal_sqlite",
        "qualification": {"evidence_fills": 10},
        "closed_trades": 5,
        "fills": 10,
        "all_history_closed_trades": 5,
        "expectancy_per_closed_trade": 1.0,
    }

    gates = evaluate_paper_gates(
        evidence,
        sessions,
        signals,
        [],
        paper_history,
        config,
    )

    labels = {gate["label"]: gate for gate in gates}
    assert labels["45 calendar days of operation"]["passed"] is True
    assert labels["5+ completed round trips"]["passed"] is True
    assert labels["60+ qualified source bars"]["passed"] is True
