import pytest
import scripts.run_pipeline_loop as run_pipeline_loop
import scripts.run_pipeline_once as run_pipeline_once


def _write_cfg(root, body: str):
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "trading.yaml").write_text(body, encoding="utf-8")


def test_run_pipeline_loop_requires_symbols(tmp_path, monkeypatch):
    _write_cfg(
        tmp_path,
        """
pipeline:
  exchange_id: coinbase
execution:
  executor_mode: paper
symbols: []
""",
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:symbols\[0\]"):
        run_pipeline_loop.main()


def test_run_pipeline_once_requires_pipeline_exchange_id(tmp_path, monkeypatch):
    _write_cfg(
        tmp_path,
        """
pipeline: {}
execution:
  executor_mode: paper
symbols:
  - BTC/USD
""",
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id"):
        run_pipeline_once.main()


def test_run_pipeline_once_requires_execution_executor_mode(tmp_path, monkeypatch):
    _write_cfg(
        tmp_path,
        """
pipeline:
  exchange_id: coinbase
execution: {}
symbols:
  - BTC/USD
""",
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:execution.executor_mode"):
        run_pipeline_once.main()
