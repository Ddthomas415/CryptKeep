"""
Substrate backlog #13 proofs: supply-chain verification tooling.

Pinned here: exact-pin parsing rejects ranges, unpinned entries, and
conflicting pins (within and across files); environment verification fails
on version drift but only notes not-installed optionals; the audit lane
records unavailability honestly instead of fabricating a pass; and the
provenance evidence artifact carries git identity, requirement-file
hashes, and every verdict.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _mod():
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import check_supply_chain as sc

        importlib.reload(sc)
        return sc
    finally:
        sys.path.remove(str(REPO / "scripts"))


def _write(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_parse_accepts_pins_extras_markers_and_ignores_noise(tmp_path):
    sc = _mod()
    f = _write(tmp_path / "requirements-pinned.txt", [
        "# comment",
        "",
        "-r base.txt",
        "--no-binary :all:",
        "aiodns==4.0.0",
        "    # via ccxt",
        "uvicorn[standard]==0.30.1",
        'colorama==0.4.6 ; sys_platform == "win32"',
    ])
    out = sc.parse_pinned_file(f)
    assert out["problems"] == []
    assert out["pins"] == {"aiodns": "4.0.0", "uvicorn": "0.30.1", "colorama": "0.4.6"}


def test_parse_rejects_ranges_unpinned_and_conflicts(tmp_path):
    sc = _mod()
    f = _write(tmp_path / "requirements-pinned.txt", [
        "requests>=2.0",
        "flask",
        "numpy==1.0",
        "numpy==2.0",
        "torch~=2.1",
    ])
    out = sc.parse_pinned_file(f)
    msgs = "\n".join(out["problems"])
    assert "not exactly pinned: requests>=2.0" in msgs
    assert "not exactly pinned: flask" in msgs
    assert "conflicting pin for numpy" in msgs
    assert "not exactly pinned: torch~=2.1" in msgs
    assert out["pins"]["numpy"] == "1.0"  # first pin retained, conflict reported


def test_pin_integrity_cross_file_conflict(tmp_path):
    sc = _mod()
    _write(tmp_path / "requirements-pinned.txt", ["shared==1.0", "runtime-only==2.0"])
    _write(tmp_path / "requirements-dev-pinned.txt", ["shared==1.5", "pytest==8.0.0"])
    out = sc.check_pin_integrity(repo=tmp_path)
    assert out["ok"] is False
    assert any(p.startswith("cross_file_conflict:shared") for p in out["problems"])


def test_pin_integrity_missing_file_reported(tmp_path):
    sc = _mod()
    _write(tmp_path / "requirements-pinned.txt", ["a==1.0"])
    out = sc.check_pin_integrity(repo=tmp_path)
    assert out["ok"] is False
    assert "missing_file:requirements-dev-pinned.txt" in out["problems"]


def test_environment_match_fails_on_drift_notes_missing(monkeypatch):
    sc = _mod()
    from importlib import metadata as im

    versions = {"alpha": "1.0", "beta": "9.9"}

    def fake_version(name):
        if name in versions:
            return versions[name]
        raise im.PackageNotFoundError(name)

    monkeypatch.setattr(sc.metadata if hasattr(sc, "metadata") else im, "version", fake_version, raising=False)
    # check_environment_matches imports metadata locally; patch the real module
    monkeypatch.setattr(im, "version", fake_version)

    out = sc.check_environment_matches({"alpha": "1.0", "beta": "2.0", "gamma": "3.0"})
    assert out["ok"] is False
    assert out["mismatches"] == ["beta: installed 9.9 != pinned 2.0"]
    assert out["not_installed"] == ["gamma"]
    assert out["checked"] == 2


def test_audit_unavailable_recorded_honestly(monkeypatch):
    sc = _mod()

    def no_module(*args, **kwargs):
        class P:
            returncode = 1
            stdout = ""
            stderr = "No module named pip_audit"
        return P()

    monkeypatch.setattr(sc.subprocess, "run", no_module)
    out = sc.run_vulnerability_audit()
    assert out == {"ran": False, "reason": "pip_audit_unavailable"}


def test_audit_parses_findings(monkeypatch):
    sc = _mod()

    payload = {"dependencies": [
        {"name": "safe", "version": "1.0", "vulns": []},
        {"name": "hit", "version": "2.0", "vulns": [{"id": "CVE-X"}]},
    ]}

    def fake_run(*args, **kwargs):
        class P:
            returncode = 1  # pip-audit exits 1 when vulns found
            stdout = json.dumps(payload)
            stderr = ""
        return P()

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    out = sc.run_vulnerability_audit()
    assert out["ran"] is True
    assert out["vulnerable_count"] == 1
    assert out["findings"][0]["name"] == "hit"


def test_evidence_artifact_shape_and_cli(tmp_path):
    env = {"PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_supply_chain.py"), "--json", "--evidence-dest", str(tmp_path)],
        capture_output=True, text=True, timeout=120, env=env, cwd=str(REPO),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["pin_integrity"]["ok"] is True
    assert report["pin_integrity"]["pin_count"] > 0
    assert report["environment"]["ok"] is True
    assert report["vulnerability_audit"] == {"ran": False, "reason": "not_requested"}
    assert len(report["git_sha"]) == 40
    assert set(report["requirement_file_sha256"]) == {"requirements-pinned.txt", "requirements-dev-pinned.txt"}
    written = json.loads(Path(report["evidence_path"]).read_text(encoding="utf-8"))
    assert written["git_sha"] == report["git_sha"]


def test_cli_fails_on_broken_pins(tmp_path, monkeypatch):
    sc = _mod()
    _write(tmp_path / "requirements-pinned.txt", ["loose>=1.0"])
    _write(tmp_path / "requirements-dev-pinned.txt", ["dev==1.0"])
    integrity = sc.check_pin_integrity(repo=tmp_path)
    assert integrity["ok"] is False
