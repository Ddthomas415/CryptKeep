from __future__ import annotations

from pathlib import Path


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
    assert "`requirements.txt` is the dependency source of truth used by the installer when present" in install


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
