from __future__ import annotations

import json
from pathlib import Path

from scripts import check_hetzner_paper_host_health as health


def _preflight_report(*, ok: bool) -> dict:
    return {
        "ok": ok,
        "checks": [
            {
                "name": "storage_health",
                "ok": ok,
                "status": "ready" if ok else "backup_dir_missing",
                "details": {"backup_dir": "/srv/cryptkeep/backups"},
            },
            {
                "name": "tailscale",
                "ok": True,
                "status": "running",
                "details": {"tailscale_ips": ["100.86.128.9"]},
            },
        ],
    }


def test_build_health_report_surfaces_failed_preflight_checks(tmp_path: Path) -> None:
    report = health.build_health_report(
        preflight_report=_preflight_report(ok=False),
        artifact_path=tmp_path / "health.json",
    )

    assert report["ok"] is False
    assert report["status"] == "hetzner_paper_host_blocked"
    assert report["read_only"] is True
    assert report["ssh_invoked"] is False
    assert report["restore_invoked"] is False
    assert report["collector_mutation_invoked"] is False
    assert report["failed_checks"] == [
        {
            "name": "storage_health",
            "status": "backup_dir_missing",
            "details": {"backup_dir": "/srv/cryptkeep/backups"},
        }
    ]


def test_main_writes_artifact_and_local_alert_on_failure(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    artifact = tmp_path / "health.latest.json"
    alerts: list[dict] = []

    monkeypatch.setattr(
        health.preflight,
        "build_report",
        lambda **_kwargs: _preflight_report(ok=False),
    )
    monkeypatch.setattr(
        health,
        "send_alert",
        lambda **kwargs: alerts.append(kwargs) or {"ok": True, "local_written": True},
    )

    rc = health.main(["--artifact-path", str(artifact), "--json"])

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert rc == 1
    assert payload["ok"] is False
    assert payload["status"] == "hetzner_paper_host_blocked"
    assert payload["alert_result"] == {"ok": True, "local_written": True}
    assert alerts[0]["level"] == "error"
    assert alerts[0]["payload"]["failed_checks"][0]["name"] == "storage_health"
    assert json.loads(capsys.readouterr().out)["artifact_path"] == str(artifact)


def test_main_does_not_alert_when_preflight_passes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "health.latest.json"

    monkeypatch.setattr(
        health.preflight,
        "build_report",
        lambda **_kwargs: _preflight_report(ok=True),
    )
    monkeypatch.setattr(
        health,
        "send_alert",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected alert")),
    )

    rc = health.main(["--artifact-path", str(artifact)])

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["ok"] is True
    assert payload["failed_checks"] == []


def test_main_can_disable_alert_on_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "health.latest.json"

    monkeypatch.setattr(
        health.preflight,
        "build_report",
        lambda **_kwargs: _preflight_report(ok=False),
    )
    monkeypatch.setattr(
        health,
        "send_alert",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected alert")),
    )

    rc = health.main(["--artifact-path", str(artifact), "--no-alert"])

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert rc == 1
    assert payload["alert_enabled"] is False
    assert payload["alert_result"] == {}
