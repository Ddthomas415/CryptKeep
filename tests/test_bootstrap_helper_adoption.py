from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_scripts_use_shared_bootstrap_helper():
    expected = [
        "scripts/validate.py",
        "scripts/preflight_check.py",
        "scripts/op.py",
        "scripts/doctor.py",
        "scripts/pre_release_sanity.py",
        "scripts/preflight.py",
        "scripts/start_bot.py",
        "scripts/stop_bot.py",
        "scripts/start_supervisor.py",
        "scripts/stop_supervisor.py",
        "scripts/supervisor_status.py",
        "scripts/supervisor_ctl.py",
        "scripts/bot_status.py",
        "scripts/bot_ctl.py",
        "scripts/run_intent_executor.py",
        "scripts/run_intent_reconciler.py",
        "scripts/run_live_intent_consumer.py",
        "scripts/run_live_reconciler.py",
        "scripts/run_strategy_runner.py",
        "scripts/run_paper_engine.py",
    ]
    for rel in expected:
        txt = _text(rel)
        assert "from _bootstrap import add_repo_root_to_syspath" in txt, rel


def test_tools_use_shared_bootstrap_helper():
    expected = [
        "tools/repo_doctor.py",
        "tools/align_gold_layout.py",
        "tools/phase83_apply.py",
        "tools/repair_repo.py",
    ]
    for rel in expected:
        txt = _text(rel)
        assert "_bootstrap" in txt, rel


def test_no_inline_find_repo_root_in_scripts():
    offenders: list[str] = []
    for p in (ROOT / "scripts").rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "def _find_repo_root(start: Path) -> Path:" in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Inline _find_repo_root still present:\n" + "\n".join(sorted(offenders))


def test_no_inline_find_repo_root_in_tools():
    offenders: list[str] = []
    for p in (ROOT / "tools").rglob("*.py"):
        if p.name == "_bootstrap.py":
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "def _find_repo_root(start: Path) -> Path:" in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Inline _find_repo_root still present in tools:\n" + "\n".join(sorted(offenders))


def test_bootstrap_marker_contract_in_scripts():
    offenders: list[str] = []
    for p in (ROOT / "scripts").rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "CBP_BOOTSTRAP_SYS_PATH" not in txt:
            continue
        if "add_repo_root_to_syspath" not in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Bootstrap marker without shared helper usage:\n" + "\n".join(sorted(offenders))


def test_bootstrap_marker_has_package_fallback_in_scripts():
    offenders: list[str] = []
    for p in (ROOT / "scripts").rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "CBP_BOOTSTRAP_SYS_PATH" not in txt:
            continue
        if "from scripts._bootstrap import add_repo_root_to_syspath" not in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Bootstrap marker missing package fallback:\n" + "\n".join(sorted(offenders))


def test_scripts_package_init_is_side_effect_free():
    txt = _text("scripts/__init__.py")
    assert "add_repo_root_to_syspath" not in txt
    assert "sys.path" not in txt
