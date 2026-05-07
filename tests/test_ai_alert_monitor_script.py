from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path


def _load(path: Path):
    mod_name = f"{path.stem}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_ai_alert_monitor_import_has_no_state_side_effects(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    root = Path(__file__).resolve().parents[1]

    mod = _load(root / "scripts" / "run_ai_alert_monitor.py")

    assert callable(getattr(mod, "main", None))
    assert not any(tmp_path.iterdir())
