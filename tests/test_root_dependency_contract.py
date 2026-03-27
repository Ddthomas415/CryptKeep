from __future__ import annotations

from pathlib import Path

import install as install_mod
import tomllib


def _normalized_req_name(line: str) -> str:
    raw = line.strip()
    for marker in ("<", ">", "=", "!", "~", ";"):
        if marker in raw:
            raw = raw.split(marker, 1)[0]
    return raw.strip().lower()


def test_root_install_docs_name_requirements_txt_as_baseline_source_of_truth() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    install = Path("docs/INSTALL.md").read_text(encoding="utf-8")

    assert "root dependency source of truth for that baseline is `requirements.txt`" in readme
    assert "`requirements.txt` is the dependency source of truth and is required by the installer" in install


def test_requirements_txt_has_no_duplicate_root_baseline_entries() -> None:
    lines = [
        line.strip()
        for line in Path("requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    names = [_normalized_req_name(line) for line in lines]

    assert names.count("httpx") == 1
    assert names.count("fastapi") == 1
    assert names.count("uvicorn[standard]") == 1
    assert names.count("pydantic") == 1
    assert names.count("pydantic-settings") == 0
    assert names.count("pytest") == 0
    assert names.count("pywebview") == 0
    assert names.count("pyinstaller") == 0


def test_pyproject_includes_visible_root_runtime_packages() -> None:
    deps = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]

    assert "streamlit>=1.30.0" in deps
    assert "pydantic>=2.5.0" in deps
    assert "httpx>=0.27,<1.0" in deps
    assert "orjson>=3.9.0" in deps
    assert "keyring" in deps
    assert "ccxt>=4.0" in deps
    assert "PyYAML>=6.0" in deps


def test_desktop_requirements_carry_packaging_only_dependencies() -> None:
    desktop = Path("requirements/desktop.txt").read_text(encoding="utf-8")

    assert "-r ../requirements.txt" in desktop
    assert "pywebview" in desktop
    assert "pyinstaller" in desktop


def test_dev_requirements_carry_pytest() -> None:
    root_dev = Path("requirements-dev.txt").read_text(encoding="utf-8")
    compat_dev = Path("requirements/dev.txt").read_text(encoding="utf-8")

    assert "pytest>=7.4.0" in root_dev
    assert "pytest>=7.4.0" in compat_dev


def test_root_install_refuses_pyproject_fallback_without_requirements(monkeypatch, tmp_path, capsys) -> None:
    py = tmp_path / "python"
    calls: list[list[str]] = []

    monkeypatch.setattr(install_mod, "ROOT", tmp_path)
    monkeypatch.setattr(install_mod, "ensure_venv", lambda: py)
    monkeypatch.setattr(install_mod, "_run", lambda cmd, env=None: calls.append(list(cmd)))

    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")

    out = install_mod.main()
    stdout = capsys.readouterr().out

    assert out == 2
    assert calls == [[str(py), "-m", "pip", "install", "-U", "pip"]]
    assert "requirements.txt is required for the root baseline install path." in stdout
