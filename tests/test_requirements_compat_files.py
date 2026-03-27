from __future__ import annotations

from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_requirements_compat_files_exist() -> None:
    root = _root()
    expected = [
        root / "requirements-dev.txt",
        root / "requirements-packaging.txt",
        root / "requirements" / "desktop.txt",
        root / "requirements" / "dev.txt",
        root / "requirements" / "requirements.packaging.txt",
    ]
    missing = [str(p.relative_to(root)) for p in expected if not p.exists()]
    assert not missing, f"missing requirements compat files: {missing}"


def test_requirements_compat_files_chain_to_main_requirements() -> None:
    root = _root()
    files = [
        root / "requirements-dev.txt",
        root / "requirements-packaging.txt",
        root / "requirements" / "desktop.txt",
        root / "requirements" / "dev.txt",
        root / "requirements" / "requirements.packaging.txt",
    ]
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        assert "-r" in text


def test_packaging_requirements_chain_to_desktop_profile() -> None:
    root = _root()
    root_packaging = (root / "requirements-packaging.txt").read_text(encoding="utf-8", errors="replace")
    compat_packaging = (root / "requirements" / "requirements.packaging.txt").read_text(
        encoding="utf-8", errors="replace"
    )

    assert "-r requirements/desktop.txt" in root_packaging
    assert "-r desktop.txt" in compat_packaging
