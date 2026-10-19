from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/manual_repo_audit.sh"


def _executable(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)
    return path


@pytest.fixture
def audit_sandbox(tmp_path: Path):
    repo = tmp_path / "repo"
    for directory in (
        "scripts", "tests", "tools", "services/strategies", ".github/workflows",
        "docs/governance", "docs/strategies", "config", "docker", "crypto-trading-ai",
    ):
        (repo / directory).mkdir(parents=True, exist_ok=True)
    script = repo / "scripts/manual_repo_audit.sh"
    script.write_text(SCRIPT.read_text())
    for filename in ("Makefile", "services/strategies/presets.py", ".github/workflows/test.yml"):
        (repo / filename).write_text("# fixture\n")

    bin_dir = tmp_path / "bin"
    git = _executable(
        tmp_path / "native tools/git",
        'printf "%s\\n" "$*" >> "$GIT_CALLS"\n'
        'printf "%s\\n" "$PATH" >> "$SEEN_PATH"\n'
        'if [ "$1" = "--version" ]; then echo "git version fixture"; exit 0; fi\n'
        'exit "${GIT_CHECK_RC:-0}"\n',
    )
    _executable(bin_dir / "git", 'echo "wrong PATH Git" >&2; exit 126\n')
    python = (
        'case " $* " in\n'
        '  *" --collect-only "*)\n'
        '    if [ "${COLLECT_RC:-0}" -ne 0 ]; then\n'
        '      echo "ModuleNotFoundError: No module named bs4" >&2\n'
        '    fi\n'
        '    exit "${COLLECT_RC:-0}";;\n'
        'esac\n'
        'exit 0\n'
    )
    _executable(bin_dir / "python3", python)
    _executable(repo / ".venv/bin/python", python)
    for tool in ("timeout", "gtimeout"):
        _executable(bin_dir / tool, 'shift; exec "$@"\n')
    _executable(bin_dir / "shellcheck", "exit 0\n")
    env = {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "HOME": str(tmp_path),
        "LANG": "C",
        "GIT_BIN": str(git),
        "GIT_CALLS": str(tmp_path / "git_calls"),
        "SEEN_PATH": str(tmp_path / "seen_path"),
        "CBP_STATE_DIR": str(tmp_path / "state with spaces"),
    }
    return repo, script, env


def _run_audit(script: Path, repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    # Only the fixture tree is inspected; Python is a stub, never nested pytest.
    return subprocess.run(
        ["/bin/bash", str(script), "quick"], cwd=repo, env=env,
        text=True, capture_output=True, timeout=20,
    )


@pytest.mark.parametrize("use_state_override", [False, True])
def test_manual_repo_audit_writes_required_artifacts(audit_sandbox, use_state_override: bool) -> None:
    repo, script, env = audit_sandbox
    if not use_state_override:
        env.pop("CBP_STATE_DIR")
    result = _run_audit(script, repo, env)
    assert result.returncode == 0, result.stderr
    state = Path(env["CBP_STATE_DIR"]) if use_state_override else repo / ".cbp_state"
    runs = list((state / "audit_reports").glob("repo_audit_*"))
    assert len(runs) == 1
    latest = runs[0]
    for name in ("00_summary.txt", "failed_checks.txt", "pytest_collect.txt", "git_status.txt", "git_log.txt"):
        assert (latest / name).is_file()
    assert (latest / "00_summary.txt").stat().st_size > 0
    assert (latest / "failed_checks.txt").read_text() == ""
    assert Path(env["GIT_CALLS"]).read_text().splitlines() == [
        "--version", "status --short", "log --oneline --decorate -10",
    ]
    assert set(Path(env["SEEN_PATH"]).read_text().splitlines()) == {env["PATH"]}
    if use_state_override:
        assert not (repo / ".cbp_state/audit_reports").exists()


def test_manual_repo_audit_preserves_git_and_collection_failures(audit_sandbox) -> None:
    repo, script, env = audit_sandbox
    env.update(GIT_CHECK_RC="73", COLLECT_RC="2")
    result = _run_audit(script, repo, env)
    assert result.returncode == 0, result.stderr  # Existing report-only exit contract.
    latest, = (Path(env["CBP_STATE_DIR"]) / "audit_reports").glob("repo_audit_*")
    assert (latest / "failed_checks.txt").read_text().splitlines() == [
        "git_status (exit=73)", "git_log (exit=73)", "pytest_collect (exit=2)",
    ]
    assert "# EXIT_CODE: 73" in (latest / "git_status.txt").read_text()
    assert "No module named bs4" in (latest / "pytest_collect.txt").read_text()
    summary = (latest / "00_summary.txt").read_text()
    assert "pytest_collect failed (exit=2)" in summary
    assert "git_status (exit=73)" in summary


@pytest.mark.parametrize("invalid", ["missing", "not_executable", "wrong_architecture"])
def test_manual_repo_audit_rejects_invalid_git_override(audit_sandbox, invalid: str) -> None:
    repo, script, env = audit_sandbox
    override = repo / "invalid git"
    if invalid == "not_executable":
        override.write_text("not executable\n")
    elif invalid == "wrong_architecture":
        _executable(override, 'echo "Bad CPU type in executable" >&2; exit 126\n')
    env["GIT_BIN"] = str(override)
    result = _run_audit(script, repo, env)
    assert result.returncode == 1
    assert "Git executable" in result.stderr
    assert not Path(env["GIT_CALLS"]).exists()
    latest, = (Path(env["CBP_STATE_DIR"]) / "audit_reports").glob("repo_audit_*")
    assert (latest / "failed_checks.txt").read_text() == "git_executable (exit=1)\n"


@pytest.mark.parametrize("native_available", [False, True])
def test_git_resolver_prefers_native_on_arm_macos(tmp_path: Path, native_available: bool) -> None:
    native = tmp_path / "native git"
    path_git = _executable(tmp_path / "bin/git", 'echo "git version path"\n')
    if native_available:
        _executable(native, 'echo "git version native"\n')
    text = SCRIPT.read_text()
    start = text.index("resolve_git_bin() {")
    end = text.index('\nGIT_BIN="$(resolve_git_bin', start)
    resolver = text[start:end]
    result = subprocess.run(
        ["/bin/bash", "-c", resolver + '\nuname() { case "$1" in -s) echo Darwin;; -m) echo arm64;; esac; }\nresolve_git_bin "" "$1"',
         "resolver-test", str(native)],
        env={"PATH": str(path_git.parent)}, text=True, capture_output=True, timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(native if native_available else path_git)
