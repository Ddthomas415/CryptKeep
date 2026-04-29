from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

import pytest


def _load(path: Path):
    mod_name = f"{path.stem}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "rel_path",
    [
        "scripts/run_intent_executor_safe.py",
        "scripts/run_intent_reconciler_safe.py",
        "scripts/run_intent_consumer_safe.py",
        "scripts/run_live_reconciler_safe.py",
        "scripts/run_tick_publisher.py",
        "scripts/run_ws_ticker_feed_safe.py",
    ],
)
def test_safe_wrapper_import_has_no_state_side_effects(monkeypatch, tmp_path, rel_path: str):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    root = Path(__file__).resolve().parents[1]
    mod = _load(root / rel_path)
    assert callable(getattr(mod, "main", None))
    assert not any(tmp_path.iterdir())
