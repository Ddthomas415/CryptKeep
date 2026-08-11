from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "architecture" / "compat_script_surfaces.md"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8", errors="replace").split())


def test_every_tracked_compat_script_is_classified() -> None:
    doc = DOC.read_text(encoding="utf-8", errors="replace")
    compat_scripts = sorted((ROOT / "scripts" / "compat").glob("*.py"))

    assert compat_scripts, "scripts/compat/*.py classification set unexpectedly empty"
    for path in compat_scripts:
        rel = path.relative_to(ROOT).as_posix()
        assert f"| `{rel}` |" in doc, rel


def test_compat_classification_does_not_authorize_runtime_expansion() -> None:
    text = _flat(DOC)

    assert "classification record only" in text
    assert "does not promote, retire, or change any runtime entrypoint" in text
    assert "does not make a script canonical operator control" in text
    assert "campaign control" in text
    assert "promotion authority" in text
    assert "live-execution authority" in text
    assert "New work must not infer canonical authority from a `scripts/compat/` file name" in text


def test_compat_intent_consumer_retirement_is_documented_and_executable() -> None:
    doc = _flat(DOC)
    script = (ROOT / "scripts" / "compat" / "run_intent_consumer.py").read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert "`scripts/compat/run_intent_consumer.py` | `retired_run_mode_with_stop_compat`" in doc
    assert "legacy_intent_consumer_retired" in doc
    assert 'RETIRED_REASON = "legacy_intent_consumer_retired"' in script
    assert 'CANONICAL_ENTRYPOINT = "scripts/run_intent_consumer_safe.py"' in script


def test_compat_classification_is_linked_from_repo_layout() -> None:
    layout = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert "docs/architecture/compat_script_surfaces.md" in layout
    assert "current ownership/classification details live in:" in layout
