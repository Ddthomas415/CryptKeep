"""
Substrate backlog #5 proofs: systemd deployment units.

Pins the authority boundary (units and env template never carry arming or
live-enable tokens), supervision policy (restart with backoff caps),
sandbox hardening directives, entry-point existence, and the install
helper's static verifier agreeing with these tests.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UNIT_DIR = REPO / "packaging" / "systemd"
UNITS = (
    "cbp-collector.service",
    "cbp-intent-consumer.service",
    "cbp-reconciler.service",
    "cbp-dashboard.service",
)
FORBIDDEN = ("CBP_EXECUTION_ARMED", "CBP_LIVE_ENABLED")


def _parse_unit(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            out.setdefault(k.strip(), []).append(v.strip())
    return out


def test_all_four_units_exist():
    for name in UNITS:
        assert (UNIT_DIR / name).exists(), name


def test_units_never_carry_arming_tokens():
    """Effective (non-comment) lines must never carry an arming token;
    comments documenting the prohibition are allowed."""
    for name in UNITS:
        text = (UNIT_DIR / name).read_text(encoding="utf-8")
        effective = "\n".join(
            ln for ln in text.splitlines() if not ln.strip().startswith("#")
        )
        for token in FORBIDDEN:
            assert token not in effective, f"{name} must not carry {token}"


def test_env_example_exists_and_carries_no_arming_assignment():
    env = UNIT_DIR / "cbp.env.example"
    assert env.exists()
    for line in env.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        for token in FORBIDDEN:
            assert not stripped.startswith(token), f"env example must not assign {token}"
    # the deliberate absence must be documented in the template itself
    assert "DELIBERATELY ABSENT" in env.read_text(encoding="utf-8")


def test_units_supervision_and_hardening_directives():
    for name in UNITS:
        parsed = _parse_unit((UNIT_DIR / name).read_text(encoding="utf-8"))
        assert parsed.get("Restart") == ["on-failure"], name
        assert parsed.get("RestartSec") == ["5"], name
        assert parsed.get("StartLimitIntervalSec") == ["300"], name
        assert parsed.get("StartLimitBurst") == ["10"], name
        assert parsed.get("User") == ["cbp"], name
        assert parsed.get("User") != ["root"], name
        assert parsed.get("NoNewPrivileges") == ["true"], name
        assert parsed.get("ProtectSystem") == ["strict"], name
        assert parsed.get("ReadWritePaths") == ["/var/lib/cbp"], name
        assert "EnvironmentFile" in parsed, name
        assert parsed.get("After") == ["network-online.target"], name


def test_exec_start_scripts_exist_in_repo():
    for name in UNITS:
        parsed = _parse_unit((UNIT_DIR / name).read_text(encoding="utf-8"))
        execs = parsed.get("ExecStart") or []
        assert len(execs) == 1, name
        m = re.search(r"crypto-bot-pro/(?:\.venv/bin/python)\s+(\S+)", execs[0])
        assert m, f"{name}: unexpected ExecStart shape: {execs[0]}"
        script = m.group(1)
        assert (REPO / script).exists(), f"{name}: {script} not in repo"


def test_install_helper_static_verify_passes_dry_run():
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "install_systemd_units.py")],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "static verify ok" in proc.stdout
    assert "dry run" in proc.stdout


def test_install_helper_fails_on_arming_token(tmp_path, monkeypatch):
    """The verifier must reject a unit that smuggles an arming variable."""
    import importlib

    sys.path.insert(0, str(REPO / "scripts"))
    try:
        mod = importlib.import_module("install_systemd_units")
        importlib.reload(mod)
        bad_dir = tmp_path / "systemd"
        bad_dir.mkdir()
        for name in UNITS:
            text = (UNIT_DIR / name).read_text(encoding="utf-8")
            if name == "cbp-intent-consumer.service":
                text = text.replace(
                    "EnvironmentFile=/etc/cbp/cbp.env",
                    "EnvironmentFile=/etc/cbp/cbp.env\nEnvironment=CBP_EXECUTION_ARMED=1",
                )
            (bad_dir / name).write_text(text, encoding="utf-8")
        (bad_dir / "cbp.env.example").write_text(
            (UNIT_DIR / "cbp.env.example").read_text(encoding="utf-8"), encoding="utf-8"
        )
        monkeypatch.setattr(mod, "_unit_dir", lambda: bad_dir)
        problems = mod._verify_units()
        assert any("forbidden arming token" in p for p in problems)
    finally:
        sys.path.remove(str(REPO / "scripts"))


def test_deployment_doc_names_the_authority_boundary():
    doc = (REPO / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8")
    assert "NEVER arms live trading" in doc
    assert "ceremony" in doc
    assert "cbp-intent-consumer" in doc
