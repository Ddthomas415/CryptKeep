from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make(target: str, env: dict | None = None) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), env=env, text=True)
    return json.loads(out)


def _run_script(args: list[str], env: dict | None = None) -> dict:
    out = subprocess.check_output([sys.executable, *args], cwd=str(ROOT), env=env, text=True)
    return json.loads(out)


def _assert_top_parity(a: dict, b: dict) -> None:
    for k in ("schema_version", "mode", "ok"):
        assert a.get(k) == b.get(k), k
    assert isinstance(a.get("started_at"), str) and a.get("started_at")
    assert isinstance(b.get("started_at"), str) and b.get("started_at")
    assert isinstance(a.get("finished_at"), str) and a.get("finished_at")
    assert isinstance(b.get("finished_at"), str) and b.get("finished_at")
    assert isinstance(a.get("duration_seconds"), (int, float))
    assert isinstance(b.get("duration_seconds"), (int, float))


def test_make_vs_script_json_parity_matrix_smoke():
    pairs = [
        (
            ("check-alignment-list-json", None),
            ([str(ROOT / "scripts" / "check_repo_alignment.py"), "--list-tests", "--json"], None),
        ),
        (
            ("check-alignment-json-fast", None),
            ([str(ROOT / "scripts" / "check_repo_alignment.py"), "--json"], {**os.environ, "CBP_ALIGNMENT_SKIP_GUARDS": "1"}),
        ),
        (
            ("validate-json-quick", None),
            ([str(ROOT / "scripts" / "validate.py"), "--quick", "--json"], None),
        ),
        (
            ("validate-json-fast", None),
            ([str(ROOT / "scripts" / "validate.py"), "--json"], {**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"}),
        ),
        (
            ("pre-release-sanity-json-quick", None),
            ([str(ROOT / "scripts" / "pre_release_sanity.py"), "--json", "--skip-ruff", "--skip-mypy", "--skip-pytest", "--skip-config", "--skip-imports"], None),
        ),
        (
            ("pre-release-sanity-json-fast", None),
            ([str(ROOT / "scripts" / "pre_release_sanity.py"), "--json", "--skip-ruff", "--skip-mypy"], {**os.environ, "CBP_PRE_RELEASE_SKIP_PYTEST": "1"}),
        ),
    ]

    for (make_target, make_env), (script_args, script_env) in pairs:
        pm = _run_make(make_target, env=make_env)
        ps = _run_script(script_args, env=script_env)
        _assert_top_parity(pm, ps)

        if make_target.startswith("check-alignment"):
            if pm.get("mode") == "list-tests":
                gm = pm.get("guard_tests") or []
                gs = ps.get("guard_tests") or []
                assert isinstance(gm, list)
                assert isinstance(gs, list)
                assert len(gm) == len(gs)
            else:
                assert (pm.get("guard_tests") or {}).get("rc") == (ps.get("guard_tests") or {}).get("rc")
        else:
            sm = pm.get("steps") or []
            ss = ps.get("steps") or []
            assert len(sm) == len(ss)
            assert sm[0].get("label") == ss[0].get("label")
            assert sm[-1].get("label") == ss[-1].get("label")
