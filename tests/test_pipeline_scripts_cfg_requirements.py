import pytest
import scripts.run_pipeline_loop as run_pipeline_loop
import scripts.run_pipeline_once as run_pipeline_once


def test_run_pipeline_loop_requires_symbols(monkeypatch):
    monkeypatch.setattr(
        run_pipeline_loop,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {"exchange_id": "coinbase"},
            "execution": {"executor_mode": "paper"},
            "symbols": [],
        },
    )
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:symbols\[0\]"):
        run_pipeline_loop.main()


def test_run_pipeline_once_requires_pipeline_exchange_id(monkeypatch):
    monkeypatch.setattr(
        run_pipeline_once,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {},
            "execution": {"executor_mode": "paper"},
            "symbols": ["BTC/USD"],
        },
    )
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id"):
        run_pipeline_once.main()


def test_run_pipeline_once_requires_execution_executor_mode(monkeypatch):
    monkeypatch.setattr(
        run_pipeline_once,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {"exchange_id": "coinbase"},
            "execution": {},
            "symbols": ["BTC/USD"],
        },
    )
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:execution.executor_mode"):
        run_pipeline_once.main()


def test_run_pipeline_once_uses_runtime_config(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        run_pipeline_once,
        "load_runtime_trading_config",
        lambda: {
            "pipeline": {"exchange_id": "coinbase", "strategy": "ema"},
            "execution": {"executor_mode": "paper", "db_path": "/tmp/execution.sqlite"},
            "symbols": ["BTC/USD"],
        },
    )

    class _FakePipeline:
        def run_once(self):
            return {"ok": True}

    def _build(cfg):
        captured["cfg"] = cfg
        return _FakePipeline()

    monkeypatch.setattr(run_pipeline_once, "build_pipeline", _build)

    assert run_pipeline_once.main() == 0
    assert captured["cfg"].exchange_id == "coinbase"
    assert captured["cfg"].symbol == "BTC/USD"
    assert captured["cfg"].mode == "paper"
