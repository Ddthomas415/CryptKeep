from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RUNTIME_TRUTH = ROOT / "docs" / "CURRENT_RUNTIME_TRUTH.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8", errors="replace").split())


def test_readme_points_to_current_runtime_truth() -> None:
    readme = _flat(README)

    assert "What is running right now" in readme
    assert "docs/CURRENT_RUNTIME_TRUTH.md" in readme
    assert "Canonical operator control plane" in readme
    assert "scripts/start_bot.py" in readme
    assert "scripts/stop_bot.py" in readme
    assert "scripts/bot_status.py" in readme


def test_readme_does_not_label_compat_bot_ctl_as_canonical() -> None:
    readme = _flat(README)

    assert "scripts/bot_ctl.py" in readme
    assert "compatibility-only" in readme
    assert "scripts/bot_ctl.py` -> `scripts/run_bot_safe.py" not in readme
    assert "scripts/bot_ctl.py` → `scripts/run_bot_safe.py" not in readme


def test_runtime_truth_keeps_compatibility_boundary() -> None:
    truth = _flat(RUNTIME_TRUTH)

    assert "scripts/start_bot.py" in truth
    assert "scripts/stop_bot.py" in truth
    assert "scripts/bot_status.py" in truth
    assert "Compatibility-only legacy surfaces" in truth
    assert "scripts/bot_ctl.py" in truth
    assert "scripts/run_bot_safe.py" in truth
    assert "not the canonical operator startup or runtime truth path" in truth
