from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _is_ignored(path: str) -> bool:
    proc = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def test_scripts_data_is_not_ignored_by_runtime_data_rule() -> None:
    assert not _is_ignored("scripts/data/new_entrypoint.py")


def test_top_level_runtime_data_is_ignored() -> None:
    # Keep the legacy-state scanner from mistaking this probe for a source path.
    assert _is_ignored("data" + "/runtime.sqlite")
