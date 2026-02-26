from __future__ import annotations

import sys
import time
from pathlib import Path

from services.os.app_paths import runtime_dir


def test_start_service_writes_pid(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    from services.desktop.simple_service_manager import ServiceSpec, start_service, stop_service, is_running

    spec = ServiceSpec(
        name="axp-test-service",
        cmd=[sys.executable, "-u", "-c", "import time; time.sleep(1.0)"],
        log_file=tmp_path / "logs" / "axp-test-service.log",
    )

    result = start_service(spec)
    assert result["ok"] and result.get("running")

    pid_path = runtime_dir() / "pids" / f"{spec.name}.pid"
    assert pid_path.exists()
    assert is_running(spec.name)

    stop_service(spec.name, hard=True)
    assert not pid_path.exists()
