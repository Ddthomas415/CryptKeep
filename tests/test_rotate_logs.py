from __future__ import annotations

import importlib.util
from pathlib import Path

from services.desktop.logging_control import rotate_logs
from services.os.app_paths import runtime_dir


def test_rotate_logs_rotates_oversized_file(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    logs = runtime_dir() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log_file = logs / "test.log"
    log_file.write_text("x" * 256, encoding="utf-8")

    out = rotate_logs(max_bytes=32, max_keep=3)
    assert out.get("ok") is True
    assert any("test.log." in p for p in out.get("rotated", []))
    assert log_file.exists()
    assert log_file.stat().st_size == 0


def test_rotate_logs_script_imports():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "rotate_logs.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(getattr(mod, "main", None))
