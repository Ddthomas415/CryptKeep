from __future__ import annotations

from pathlib import Path

import scripts.bootstrap as bootstrap


def test_write_launchers_creates_expected_files(tmp_path):
    created = bootstrap.write_launchers(tmp_path)
    names = {p.name for p in created}
    assert names == {
        "CryptoBotPro.command",
        "CryptoBotPro_Supervisor.command",
        "CryptoBotPro.bat",
        "CryptoBotPro_Supervisor.bat",
    }
    for p in created:
        assert p.exists()
        assert p.read_text(encoding="utf-8")


def test_write_launchers_command_targets(tmp_path):
    bootstrap.write_launchers(tmp_path)
    desktop = (tmp_path / "launchers" / "CryptoBotPro.command").read_text(encoding="utf-8")
    supervisor = (tmp_path / "launchers" / "CryptoBotPro_Supervisor.command").read_text(encoding="utf-8")
    assert "scripts/run_desktop.py" in desktop
    assert "scripts/supervisor_ctl.py start" in supervisor


def test_bootstrap_main_skip_install(tmp_path):
    rc = bootstrap.main(["--skip-install", "--repo-root", str(tmp_path)])
    assert rc == 0
    launchers = tmp_path / "launchers"
    assert (launchers / "CryptoBotPro.command").exists()
    assert (launchers / "CryptoBotPro_Supervisor.command").exists()
