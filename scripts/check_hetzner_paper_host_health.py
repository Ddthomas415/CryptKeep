#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import argparse
import json
from pathlib import Path
from typing import Any

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts import hetzner_paper_host_preflight as preflight  # noqa: E402
from services.alerts.alert_dispatcher import send_alert  # noqa: E402
from services.os.app_paths import runtime_dir  # noqa: E402
from services.os.file_utils import atomic_write  # noqa: E402

DEFAULT_ARTIFACT_PATH = (
    runtime_dir() / "snapshots" / "hetzner_paper_host_health.latest.json"
)


def failed_preflight_checks(preflight_report: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in list(preflight_report.get("checks") or []):
        if not isinstance(row, dict) or bool(row.get("ok")):
            continue
        failures.append(
            {
                "name": str(row.get("name") or ""),
                "status": str(row.get("status") or "failed"),
                "details": dict(row.get("details") or {}),
            }
        )
    return failures


def build_health_report(
    *,
    preflight_report: dict[str, Any],
    alert_result: dict[str, Any] | None = None,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    alert_enabled: bool = True,
) -> dict[str, Any]:
    failures = failed_preflight_checks(preflight_report)
    ok = bool(preflight_report.get("ok")) and not failures
    return {
        "ok": ok,
        "status": "hetzner_paper_host_healthy" if ok else "hetzner_paper_host_blocked",
        "read_only": True,
        "ssh_invoked": False,
        "restore_invoked": False,
        "collector_mutation_invoked": False,
        "artifact_path": str(artifact_path),
        "alert_enabled": bool(alert_enabled),
        "alert_result": dict(alert_result or {}),
        "failed_checks": failures,
        "preflight": preflight_report,
        "recommendations": _recommendations(ok),
    }


def _recommendations(ok: bool) -> list[str]:
    if ok:
        return [
            "Use this latest artifact as scheduled host-health evidence.",
            "Still perform a separate backup restore rehearsal before canonical state migration.",
            "Rerun host health immediately before any stop-copy-verify-start operation.",
        ]
    return [
        "Do not restore, start, or migrate paper campaign state on this host until blockers are resolved.",
        "Inspect failed_checks and rerun the Hetzner host preflight after correction.",
    ]


def _emit_failure_alert(
    *,
    health_report: dict[str, Any],
    artifact_path: Path,
) -> dict[str, Any]:
    return send_alert(
        cfg={"alerts": {"enabled": False}},
        level="error",
        message="Hetzner paper host health preflight failed",
        payload={
            "status": health_report.get("status"),
            "artifact_path": str(artifact_path),
            "failed_checks": health_report.get("failed_checks") or [],
            "read_only": True,
            "ssh_invoked": False,
            "restore_invoked": False,
            "collector_mutation_invoked": False,
        },
    )


def _write_artifact(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the read-only Hetzner paper-host preflight as a scheduled-safe "
            "health check and write an operator-visible latest artifact."
        )
    )
    parser.add_argument("--config", type=Path, default=preflight.DEFAULT_CONFIG_PATH)
    parser.add_argument("--expected-campaign", default=preflight.DEFAULT_EXPECTED_CAMPAIGN)
    parser.add_argument(
        "--expected-commit",
        help="Require the checkout HEAD to start with this accepted commit SHA.",
    )
    parser.add_argument(
        "--require-state",
        action="store_true",
        help="Require configured state directories to exist; use after state transfer.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=preflight.DEFAULT_BACKUP_DIR,
        help="Backup directory expected on the paper host.",
    )
    parser.add_argument(
        "--min-free-gb",
        type=float,
        default=preflight.DEFAULT_MIN_FREE_GB,
        help="Minimum free disk space required on the repo filesystem.",
    )
    parser.add_argument(
        "--min-free-inodes",
        type=int,
        default=preflight.DEFAULT_MIN_FREE_INODES,
        help="Minimum free inodes required on the repo filesystem.",
    )
    parser.add_argument(
        "--artifact-path",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
        help="Path for the latest host-health JSON artifact.",
    )
    parser.add_argument(
        "--no-alert",
        action="store_true",
        help="Do not write the local critical-alert fallback when health fails.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, Any]) -> None:
    print("=== Hetzner Paper Host Health ===")
    print(f"status={report.get('status')}")
    print(f"ok={bool(report.get('ok'))}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"artifact_path={report.get('artifact_path')}")
    print(f"alert_enabled={bool(report.get('alert_enabled'))}")
    for row in list(report.get("failed_checks") or []):
        if not isinstance(row, dict):
            continue
        print(f"- failed {row.get('name')}: {row.get('status')}")
    recommendations = list(report.get("recommendations") or [])
    if recommendations:
        print("recommendations:")
        for item in recommendations:
            print(f"- {item}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    artifact_path = Path(args.artifact_path).expanduser()
    preflight_report = preflight.build_report(
        config_path=args.config,
        expected_campaign=str(args.expected_campaign),
        expected_commit=args.expected_commit,
        require_state=bool(args.require_state),
        backup_dir=args.backup_dir,
        min_free_gb=float(args.min_free_gb),
        min_free_inodes=int(args.min_free_inodes),
    )
    report = build_health_report(
        preflight_report=preflight_report,
        artifact_path=artifact_path,
        alert_enabled=not bool(args.no_alert),
    )
    if not bool(report.get("ok")) and not bool(args.no_alert):
        alert_result = _emit_failure_alert(
            health_report=report,
            artifact_path=artifact_path,
        )
        report = build_health_report(
            preflight_report=preflight_report,
            alert_result=alert_result,
            artifact_path=artifact_path,
            alert_enabled=True,
        )
    _write_artifact(artifact_path, report)

    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
