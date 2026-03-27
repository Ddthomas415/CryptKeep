from __future__ import annotations

import json
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_packaging_core_files_exist() -> None:
    root = _root()
    required = [
        root / "packaging" / "config" / "app.json",
        root / "packaging" / "pyinstaller" / "build.py",
        root / "scripts" / "build_app.sh",
        root / "scripts" / "build_app.ps1",
        root / "scripts" / "build_macos.sh",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    assert not missing, f"missing packaging scaffold files: {missing}"


def test_packaging_app_config_entry_exists() -> None:
    root = _root()
    cfg = json.loads((root / "packaging" / "config" / "app.json").read_text(encoding="utf-8"))
    entry = cfg.get("entry")
    assert isinstance(entry, str) and entry
    assert (root / entry).exists(), f"packaging entry does not exist: {entry}"


def test_macos_build_script_targets_windowed_app() -> None:
    root = _root()
    text = (root / "scripts" / "build_macos.sh").read_text(encoding="utf-8", errors="replace")
    assert "CBP_WINDOWED=1" in text
    assert "dist/CryptoBotPro.app" in text


def test_windows_installer_uses_existing_build_wrapper() -> None:
    root = _root()
    text = (root / "scripts" / "build_windows_installer.ps1").read_text(encoding="utf-8", errors="replace")
    assert "scripts\\build_app.ps1" in text


def test_desktop_build_wrappers_use_desktop_requirements_profile() -> None:
    root = _root()
    targets = [
        root / "packaging" / "build_macos.sh",
        root / "packaging" / "build_windows.ps1",
        root / "scripts" / "build_desktop_mac.sh",
        root / "scripts" / "build_desktop_windows.ps1",
        root / "scripts" / "build_app.sh",
        root / "scripts" / "build_app.ps1",
    ]

    for path in targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "requirements/desktop.txt" in text or "requirements\\desktop.txt" in text


def test_pyinstaller_build_guidance_uses_desktop_requirements_profile() -> None:
    root = _root()
    text = (root / "packaging" / "pyinstaller" / "build.py").read_text(encoding="utf-8", errors="replace")
    assert "pip install -r requirements/desktop.txt" in text


def test_pyinstaller_macos_build_supports_explicit_target_arch() -> None:
    root = _root()
    shell = (root / "packaging" / "pyinstaller" / "build.sh").read_text(encoding="utf-8", errors="replace")
    driver = (root / "packaging" / "pyinstaller" / "build.py").read_text(encoding="utf-8", errors="replace")

    assert "CBP_TARGET_ARCH" in shell
    assert ".venv_x86_backup_" in shell
    assert "platform.machine().lower()" in shell
    assert "--target-arch" in driver
    assert "CBP_TARGET_ARCH" in driver
