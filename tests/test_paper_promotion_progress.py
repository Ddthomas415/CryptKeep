from __future__ import annotations

import json
import sqlite3


def test_load_paper_promotion_progress_reports_remaining_thresholds(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from services.control.paper_promotion_progress import load_paper_promotion_progress
    from services.control.promotion_thresholds import ES_DAILY_TREND_STRATEGY_ID
    from services.os.app_paths import data_dir

    ev_dir = data_dir() / "evidence" / ES_DAILY_TREND_STRATEGY_ID
    ev_dir.mkdir(parents=True, exist_ok=True)
    session_path = ev_dir / "session_progress.jsonl"
    session_path.write_text(
        "\n".join(
            json.dumps({"timestamp": f"2026-05-{day:02d}T00:00:00+00:00"})
            for day in range(1, 23)
        )
        + "\n",
        encoding="utf-8",
    )

    journal = data_dir() / "trade_journal.sqlite"
    con = sqlite3.connect(str(journal))
    try:
        con.execute(
            """
            CREATE TABLE journal_fills (
              fill_id TEXT PRIMARY KEY,
              journal_ts TEXT NOT NULL,
              strategy_id TEXT,
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
        for idx in range(7):
            day = idx + 1
            rows.append((
                f"buy-{idx}",
                f"2026-05-{day:02d}T00:00:00+00:00",
                "sma_200_trend",
                f"2026-05-{day:02d}T00:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "buy",
                1.0,
                100.0,
                0.0,
                "USD",
            ))
            rows.append((
                f"sell-{idx}",
                f"2026-05-{day:02d}T01:00:00+00:00",
                "sma_200_trend",
                f"2026-05-{day:02d}T01:00:00+00:00",
                "coinbase",
                "BTC/USDT",
                "sell",
                1.0,
                105.0,
                0.0,
                "USD",
            ))
        con.executemany("INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()

    out = load_paper_promotion_progress()

    assert out["ok"] is True
    assert out["days_recorded"] == 22
    assert out["days_remaining"] == 8
    assert out["round_trips_recorded"] == 7
    assert out["round_trips_remaining"] == 43
    assert out["thresholds_ready"] is False
    assert len(out["blocking_thresholds"]) == 2
    assert "22/30 days recorded (8 remaining)" in out["summary_text"]
    assert "7/50 round trips recorded (43 remaining)" in out["summary_text"]
