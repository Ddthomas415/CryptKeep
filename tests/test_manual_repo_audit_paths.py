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
    summary = latest / "00_summary.txt"
    failed = latest / "failed_checks.txt"
    collect = latest / "pytest_collect.txt"

    assert summary.is_file()
    assert failed.is_file()
    assert collect.is_file()
    assert summary.stat().st_size > 0
    assert failed.read_text().strip() == ""
    assert "No such file or directory" not in result.stderr
