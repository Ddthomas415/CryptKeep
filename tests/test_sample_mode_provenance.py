"""
Active backlog #21 proofs: sample-mode provenance agrees with the actual
data source.

The runner derives `market_data_source`/`ohlcv_sample_mode` from the source
that actually produced the OHLCV rows, records the env claim alongside, and
holds the signal fail-closed when claim and source disagree. Env-only
stampers (evidence logger, collector, es_daily_trend default extra) mark
their labels `ohlcv_sample_mode_origin="env"` so claimed and derived labels
are distinguishable downstream. Gate provenance bucketing is unchanged.
"""
from __future__ import annotations

import importlib
import json


def _reload_strategy_runner(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_STARTUP_CONFIRM_FLAT", "true")

    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.intent_queue_sqlite as intent_queue_sqlite
    import storage.paper_trading_sqlite as paper_trading_sqlite
    import storage.strategy_state_sqlite as strategy_state_sqlite
    import services.execution.strategy_runner as runner

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(intent_queue_sqlite)
    importlib.reload(paper_trading_sqlite)
    importlib.reload(strategy_state_sqlite)
    importlib.reload(runner)
    return runner


def _info(source, *, env, path=None, fallback=False):
    return {
        "source": source,
        "sample_path": path,
        "sample_fallback": fallback,
        "row_count": 5,
        "env_sample_mode": env,
    }


# ---------------------------------------------------------------------------
# evidence extra derivation and mismatch tripwire
# ---------------------------------------------------------------------------


def test_extra_mismatch_when_env_claims_sample_but_source_is_public(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    out = runner._public_ohlcv_evidence_extra(
        {"venue": "coinbase", "symbol": "BTC/USDT"}, "1d",
        _info("public_ohlcv", env=True),
    )
    assert out["market_data_source"] == "public_ohlcv"
    assert out["ohlcv_sample_mode"] is False
    assert out["ohlcv_sample_mode_env"] is True
    assert out["ohlcv_source_mismatch"] is True


def test_extra_mismatch_when_env_claims_public_but_source_is_sample(monkeypatch, tmp_path):
    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    out = runner._public_ohlcv_evidence_extra(
        {"venue": "coinbase", "symbol": "BTC/USDT"}, "1d",
        _info("sample_ohlcv", env=False, path="/tmp/s.json"),
    )
    assert out["market_data_source"] == "sample_ohlcv"
    assert out["ohlcv_sample_mode"] is True
    assert out["ohlcv_sample_mode_env"] is False
    assert out["ohlcv_source_mismatch"] is True
    assert out["ohlcv_sample_path"] == "/tmp/s.json"


def test_extra_marks_unknown_source_as_mismatch(monkeypatch, tmp_path):
    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    out = runner._public_ohlcv_evidence_extra(
        {"venue": "coinbase", "symbol": "BTC/USDT"}, "1d",
        _info("none", env=False),
    )
    assert out["market_data_source"] == "unknown_ohlcv"
    assert out["ohlcv_source_mismatch"] is True


def test_extra_records_sample_fallback_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    out = runner._public_ohlcv_evidence_extra(
        {"venue": "coinbase", "symbol": "BTC/USDT"}, "1d",
        _info("sample_ohlcv", env=True, path="/tmp/s.json", fallback=True),
    )
    assert out["ohlcv_source_mismatch"] is False
    assert out["ohlcv_sample_fallback"] is True


def test_extra_without_source_info_is_env_derived_and_marked(monkeypatch, tmp_path):
    """Legacy callers without fetch-site truth keep env labels, marked env-origin."""
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    sample = runner._public_ohlcv_evidence_extra({"venue": "v", "symbol": "s"}, "1d")
    assert sample["market_data_source"] == "sample_ohlcv"
    assert sample["ohlcv_sample_mode_origin"] == "env"
    assert "ohlcv_source_mismatch" not in sample
    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    public = runner._public_ohlcv_evidence_extra({"venue": "v", "symbol": "s"}, "1d")
    assert public["market_data_source"] == "public_ohlcv"
    assert public["ohlcv_sample_mode_origin"] == "env"


def test_fetch_env_sample_mode_with_missing_file_reports_none(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    rows, source_info = runner._fetch_public_ohlcv(
        {
            "signal_source": "public_ohlcv_1d",
            "venue": "coinbase",
            "symbol": "NOSUCH/PAIR",
            "min_bars": 2,
            "max_bars": 2,
        }
    )
    assert rows == []
    assert source_info["source"] == "none"
    assert source_info["env_sample_mode"] is True


def test_fetch_and_extra_use_same_truthy_sample_env_values(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "on")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)

    rows, source_info = runner._fetch_public_ohlcv(
        {
            "signal_source": "public_ohlcv_1d",
            "venue": "coinbase",
            "symbol": "BTC/USDT",
            "min_bars": 2,
            "max_bars": 2,
        }
    )
    out = runner._public_ohlcv_evidence_extra(
        {"venue": "coinbase", "symbol": "BTC/USDT"}, "1d", source_info
    )

    assert rows
    assert source_info["source"] == "sample_ohlcv"
    assert source_info["env_sample_mode"] is True
    assert out["ohlcv_sample_mode_env"] is True
    assert out["ohlcv_source_mismatch"] is False


# ---------------------------------------------------------------------------
# runner loop holds the signal fail-closed on mismatch
# ---------------------------------------------------------------------------


def test_run_forever_holds_signal_on_provenance_mismatch(monkeypatch, tmp_path):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    qdb = runner.IntentQueueSQLite()

    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)  # env claims public
    monkeypatch.setenv("CBP_STRATEGY_SIGNAL_SOURCE", "public_ohlcv_1m")
    monkeypatch.setenv("CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE", "1")
    monkeypatch.setattr(
        runner,
        "load_user_yaml",
        lambda **kwargs: {
            "strategy_runner": {
                "strategy": {
                    "name": "breakout_donchian",
                    "trade_enabled": True,
                    "donchian_len": 3,
                    "filter_window": 3,
                    "min_volatility_pct": 0.0,
                    "min_volume_ratio": 0.0,
                    "min_trend_efficiency": 0.0,
                    "min_channel_width_pct": 0.0,
                    "breakout_buffer_pct": 0.0,
                    "require_directional_confirmation": False,
                },
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "min_bars": 5,
                "max_bars": 20,
                "loop_interval_sec": 0.0,
                "qty": 0.5,
                "allow_first_signal_trade": True,
            }
        },
    )
    # ...but the rows actually came from sample data.
    monkeypatch.setattr(
        runner,
        "_fetch_public_ohlcv",
        lambda cfg: (
            [
                [1, 100.0, 100.0, 100.0, 100.0, 1.0],
                [2, 100.0, 100.0, 100.0, 100.0, 1.0],
                [3, 100.0, 100.0, 100.0, 100.0, 1.0],
                [4, 100.0, 100.0, 100.0, 100.0, 1.0],
                [5, 100.0, 101.0, 100.0, 101.0, 1.0],
            ],
            _info("sample_ohlcv", env=False, path="/tmp/s.json"),
        ),
    )

    seen_notes: list[str] = []

    def fake_sleep(_seconds: float) -> None:
        if runner.STATUS_FILE.exists():
            status = json.loads(runner.STATUS_FILE.read_text(encoding="utf-8"))
            note = str(status.get("note") or "")
            seen_notes.append(note)
            if note == "sample_mode_provenance_mismatch":
                runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
                runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(runner.time, "sleep", fake_sleep)

    runner.run_forever()

    assert "sample_mode_provenance_mismatch" in seen_notes
    assert qdb.list_intents(limit=10) == []


# ---------------------------------------------------------------------------
# env-only stampers carry explicit origin markers
# ---------------------------------------------------------------------------


def test_evidence_logger_env_stamp_marks_origin(monkeypatch):
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    from services.strategies import evidence_logger

    stamp = evidence_logger._sample_provenance_stamp()
    assert stamp["market_data_source"] == "sample_ohlcv"
    assert stamp["ohlcv_sample_mode"] is True
    assert stamp["ohlcv_sample_mode_origin"] == "env"

    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    assert evidence_logger._sample_provenance_stamp() == {}


def test_evidence_logger_stamp_never_overwrites_source_derived_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    import services.os.app_paths as app_paths
    from services.strategies import evidence_logger as el

    importlib.reload(app_paths)
    importlib.reload(el)

    logger = el.EvidenceLogger("prov_test", log_dir=tmp_path / "evidence")
    logger._append(
        "signal",
        {
            "market_data_source": "public_ohlcv",
            "ohlcv_sample_mode": False,
            "ohlcv_sample_mode_origin": "source",
        },
    )
    files = list((tmp_path / "evidence").glob("signal_*.jsonl"))
    assert len(files) == 1
    record = json.loads(files[0].read_text().strip().splitlines()[-1])
    # setdefault semantics: env stamp must not override source-derived truth
    assert record["market_data_source"] == "public_ohlcv"
    assert record["ohlcv_sample_mode"] is False
    assert record["ohlcv_sample_mode_origin"] == "source"


def test_collector_campaign_extra_marks_env_origin(monkeypatch):
    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    import scripts.run_paper_strategy_evidence_collector as collector

    class _Cfg:
        signal_source = "public_ohlcv_1d"
        venue = "coinbase"
        symbol = "BTC/USD"

    out = collector._campaign_provenance_extra(_Cfg())
    assert out["market_data_source"] == "public_ohlcv"
    assert out["ohlcv_sample_mode_origin"] == "env"


def test_es_daily_trend_default_extra_marks_env_origin(monkeypatch):
    monkeypatch.delenv("CBP_USE_SAMPLE_OHLCV", raising=False)
    from services.strategies import es_daily_trend

    out = es_daily_trend._default_evidence_extra({})
    assert out["market_data_source"] == "unknown_ohlcv"
    assert out["ohlcv_sample_mode_origin"] == "env"

    provided = es_daily_trend._default_evidence_extra(
        {"market_data_source": "public_ohlcv", "ohlcv_sample_mode": False, "ohlcv_sample_mode_origin": "source"}
    )
    assert provided["market_data_source"] == "public_ohlcv"
    assert provided["ohlcv_sample_mode_origin"] == "source"


# ---------------------------------------------------------------------------
# promotion gate provenance bucketing is unchanged by the new fields
# ---------------------------------------------------------------------------


def test_gate_provenance_counting_unchanged_with_new_fields():
    from scripts.check_promotion_gates import _evidence_provenance_summary

    public_row = {
        "market_data_source": "public_ohlcv",
        "ohlcv_sample_mode": False,
        "ohlcv_sample_mode_env": False,
        "ohlcv_sample_mode_origin": "source",
        "ohlcv_source_mismatch": False,
    }
    sample_row = {
        "market_data_source": "sample_ohlcv",
        "ohlcv_sample_mode": True,
        "ohlcv_sample_mode_env": True,
        "ohlcv_sample_mode_origin": "source",
        "ohlcv_source_mismatch": False,
        "ohlcv_sample_path": "/tmp/s.json",
    }
    legacy_public_row = {"market_data_source": "public_ohlcv", "ohlcv_sample_mode": False}

    summary = _evidence_provenance_summary(
        {"signal": [public_row, sample_row, legacy_public_row], "order": [], "fill": [], "session": []}
    )
    counts = summary["by_type"]["signal"] if "by_type" in summary else summary.get("signal")
    if counts is None:
        counts = summary.get("types", {}).get("signal")
    assert counts["public"] == 2
    assert counts["sample"] == 1
    assert counts["unknown"] == 0
    assert counts["missing"] == 0
