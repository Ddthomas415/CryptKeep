from __future__ import annotations

import json
import os
import subprocess
import sys
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
        "scripts/release/pre_release_sanity.py",
        "scripts/preflight.py",
        "scripts/start_bot.py",
        "scripts/stop_bot.py",
        "scripts/compat/start_supervisor.py",
        "scripts/compat/stop_supervisor.py",
        "scripts/supervisor_status.py",
        "scripts/compat/supervisor_ctl.py",
        "scripts/bot_status.py",
        "scripts/bot_ctl.py",
        "scripts/compat/service_ctl.py",
        "scripts/rotate_logs.py",
        "scripts/run_tick_publisher.py",
        "scripts/compat/run_intent_executor.py",
        "scripts/live/run_intent_executor_safe.py",
        "scripts/compat/run_intent_reconciler.py",
        "scripts/live/run_intent_reconciler_safe.py",
        "scripts/live/run_live_intent_consumer.py",
        "scripts/live/run_live_reconciler.py",
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


def test_no_legacy_inline_syspath_bootstrap_block_in_scripts():
    offenders: list[str] = []
    legacy_comment = "# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly"
    for p in (ROOT / "scripts").rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if legacy_comment in txt:
            offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, "Legacy inline bootstrap block still present:\n" + "\n".join(sorted(offenders))


def test_nested_data_scripts_execute_directly_from_repo_root(tmp_path):
    env = dict(os.environ)
    env["CBP_STATE_DIR"] = str(tmp_path)
    scripts = [
        "scripts/data/run_paper_strategy_evidence_collector.py",
        "scripts/data/run_crypto_edge_collector_loop.py",
    ]
    for rel in scripts:
        proc = subprocess.run(
            [sys.executable, rel, "--status"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0, f"{rel}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        assert isinstance(json.loads(proc.stdout), dict)


def test_nested_paper_collector_delegates_to_canonical_entrypoint():
    legacy = _text("scripts/data/run_paper_strategy_evidence_collector.py")
    makefile = _text("Makefile")

    assert "from scripts.run_paper_strategy_evidence_collector import main" in legacy
    assert "ArgumentParser" not in legacy
    assert "scripts/data/run_paper_strategy_evidence_collector.py" not in makefile
    assert makefile.count("scripts/run_paper_strategy_evidence_collector.py") == 3


def test_nested_paper_collector_exposes_canonical_daily_loop_help():
    proc = subprocess.run(
        [sys.executable, "scripts/data/run_paper_strategy_evidence_collector.py", "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "--daily-loop" in proc.stdout
    assert "--session-strategy-id" in proc.stdout
