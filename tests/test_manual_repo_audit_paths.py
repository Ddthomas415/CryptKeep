from pathlib import Path
import subprocess

def test_manual_repo_audit_writes_required_artifacts() -> None:
    result = subprocess.run(
        ["./scripts/manual_repo_audit.sh", "quick"],
        check=True,
        text=True,
        capture_output=True,
    )
    runs = sorted(Path(".cbp_state/audit_reports").glob("repo_audit_*"))
    latest = runs[-1]
    assert (latest / "00_summary.txt").is_file()
    assert (latest / "failed_checks.txt").is_file()
    assert (latest / "pytest_collect.txt").is_file()
    assert (latest / "00_summary.txt").stat().st_size > 0
    assert "No such file or directory" not in result.stderr
