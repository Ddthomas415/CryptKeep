from __future__ import annotations

from services.os import app_paths


def test_state_root_honors_cbp_state_dir_override_in_dev(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    assert app_paths.state_root() == tmp_path.resolve()
    assert app_paths.runtime_dir() == tmp_path.resolve() / "runtime"
    assert app_paths.data_dir() == tmp_path.resolve() / "data"
