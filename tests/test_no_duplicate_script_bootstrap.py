from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_duplicate_bootstrap_markers_in_scripts():
    offenders: list[str] = []
    for p in (ROOT / "scripts").rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "CBP_BOOTSTRAP_SYS_PATH" in txt and "CBP_SCRIPT_BOOTSTRAP" in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Duplicate bootstrap markers found:\n" + "\n".join(sorted(offenders))


def test_no_legacy_script_bootstrap_marker():
    offenders: list[str] = []
    for p in (ROOT / "scripts").rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "CBP_SCRIPT_BOOTSTRAP" in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Legacy bootstrap marker still present:\n" + "\n".join(sorted(offenders))
