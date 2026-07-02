from __future__ import annotations

import json

from scripts import report_paper_campaign_status as script


def test_build_report_is_read_only_and_summarizes_campaigns(monkeypatch) -> None:
    monkeypatch.setattr(script, "load_campaign_specs", lambda *args, **kwargs: ("spec",))

    seen: dict[str, object] = {}

    def _manage(specs, *, restore, selected_names):
        seen["specs"] = specs
        seen["restore"] = restore
        seen["selected_names"] = selected_names
        return {
            "ok": True,
            "all_running": True,
            "campaign_count": 1,
            "running_count": 1,
            "campaigns": [
                {
                    "name": "ema_cross_default",
                    "ok": True,
                    "running": True,
                    "status": "idle",
                    "reason": "waiting_for_next_day",
                    "strategy": "ema_cross",
                    "session_strategy_id": "ema_cross_default",
                    "state_dir": "/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily",
                    "last_completed_day": "2026-06-21",
                    "pid": 1287182,
                    "collector": {
                        "summary_text": "Paper evidence collector is idle.",
                        "last_result": {
                            "results": [
                                {
                                    "latest_fill_ts": "2026-06-19T00:00:10+00:00",
                                    "fills_total": 5,
                                    "closed_trades_total": 2,
                                    "net_realized_pnl_total": -0.0076,
                                    "signal_action": "hold",
                                    "runner_status": "stopped",
                                }
                            ]
                        },
                    },
                }
            ],
        }

    monkeypatch.setattr(script, "manage_campaigns", _manage)

    out = script.build_report(selected_campaigns=["ema_cross_default"])

    assert seen == {
        "specs": ("spec",),
        "restore": False,
        "selected_names": ["ema_cross_default"],
    }
    assert out["read_only"] is True
    assert out["all_running"] is True
    assert out["campaigns"][0]["name"] == "ema_cross_default"
    assert out["campaigns"][0]["fills_total"] == 5
    assert out["campaigns"][0]["closed_trades_total"] == 2
    assert out["recommendations"] == ["continue_paper_observation"]


def test_main_outputs_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_report",
        lambda **kwargs: {
            "ok": True,
            "read_only": True,
            "campaigns": [],
            "recommendations": ["continue_paper_observation"],
        },
    )

    assert script.main(["--json", "--campaign", "ema_cross_default"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["read_only"] is True
    assert out["recommendations"] == ["continue_paper_observation"]


def test_main_formats_existing_status_payload(tmp_path, capsys) -> None:
    status_path = tmp_path / "status.json"
    status_path.write_text(
        json.dumps(
            {
                "ok": True,
                "all_running": True,
                "campaign_count": 1,
                "running_count": 1,
                "campaigns": [
                    {
                        "name": "ema_cross_default",
                        "ok": True,
                        "running": True,
                        "status": "idle",
                        "reason": "waiting_for_next_day",
                        "strategy": "ema_cross",
                        "collector": {"last_result": {"results": [{"fills_total": 5}]}},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert script.main(["--json", "--from-json", str(status_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["campaigns"][0]["name"] == "ema_cross_default"
    assert out["campaigns"][0]["fills_total"] == 5


def test_main_from_json_rejects_malformed_status_payload(tmp_path, capsys) -> None:
    status_path = tmp_path / "status.json"
    status_path.write_text(json.dumps({"ok": True}), encoding="utf-8")

    assert script.main(["--strict", "--json", "--from-json", str(status_path)]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "status_payload_missing_campaigns" in out["reason"]
    assert out["input_preview"] == '{"ok": true}'


def test_main_from_json_preserves_failed_status_reason(tmp_path, capsys) -> None:
    status_path = tmp_path / "status.json"
    status_path.write_text(
        json.dumps(
            {
                "ok": False,
                "all_running": False,
                "campaign_count": 1,
                "running_count": 0,
                "campaigns": [],
                "reason": "tailscale_ssh_auth_required",
            }
        ),
        encoding="utf-8",
    )

    assert script.main(["--strict", "--json", "--from-json", str(status_path)]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["campaign_count"] == 1
    assert out["reason"] == "tailscale_ssh_auth_required"


def test_human_report_prints_failure_reason(capsys) -> None:
    script.print_report(
        {
            "ok": False,
            "read_only": True,
            "reason": "report_failed:ValueError:bad status",
            "recommendations": ["investigate_report_failure"],
        }
    )

    out = capsys.readouterr().out
    assert "Reason: report_failed:ValueError:bad status" in out
    assert "Recommendations: investigate_report_failure" in out


def test_human_report_prints_failure_previews(capsys) -> None:
    script.print_report(
        {
            "ok": False,
            "read_only": True,
            "reason": "tailscale_ssh_timeout:5s",
            "stdout_preview": "partial stdout",
            "stderr_preview": "# Tailscale SSH requires an additional check.\n# authenticate",
            "recommendations": ["investigate_report_failure"],
        }
    )

    out = capsys.readouterr().out
    assert "Stdout preview:" in out
    assert "  partial stdout" in out
    assert "Stderr preview:" in out
    assert "  # Tailscale SSH requires an additional check." in out
    assert "  # authenticate" in out


def test_main_strict_returns_one_for_invalid_status_payload(tmp_path, capsys) -> None:
    status_path = tmp_path / "status.json"
    status_path.write_text("not-json", encoding="utf-8")

    assert script.main(["--strict", "--from-json", str(status_path)]) == 1
    out = capsys.readouterr().out
    assert "Recommendations: investigate_report_failure" in out


def test_main_strict_returns_one_when_report_not_ok(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_report",
        lambda **kwargs: {
            "ok": False,
            "read_only": True,
            "campaigns": [],
            "recommendations": ["investigate_campaign_status"],
        },
    )

    assert script.main(["--strict", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
