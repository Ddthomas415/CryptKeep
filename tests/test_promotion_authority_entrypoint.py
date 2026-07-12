from __future__ import annotations

import sys


def test_promote_entrypoint_blocks_when_gate_not_ready(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from scripts import check_promotion_gates as gates
    from scripts import show_control_kernel_status as status

    called: list[bool] = []
    monkeypatch.setattr(
        gates,
        "run_check",
        lambda stage_override=None: {
            "ready": False,
            "stage": stage_override,
            "current_stage": "paper",
            "summary": {"fail": 1, "unknown": 0},
            "manual_review_required": True,
        },
    )
    monkeypatch.setattr(status, "stage_summary", lambda strategy_id: {"stage": "paper"})
    monkeypatch.setattr(status, "promote", lambda *args, **kwargs: called.append(True))
    monkeypatch.setattr(
        sys,
        "argv",
        ["show_control_kernel_status.py", "--promote", "es_daily_trend_v1", "--json"],
    )

    assert status.main() == 1
    assert called == []
    out = capsys.readouterr().out
    assert "promotion_gate_not_ready" in out


def test_promote_entrypoint_allows_when_gate_ready(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from scripts import check_promotion_gates as gates
    from scripts import show_control_kernel_status as status

    called: list[tuple] = []
    monkeypatch.setattr(
        gates,
        "run_check",
        lambda stage_override=None: {
            "ready": True,
            "stage": stage_override,
            "current_stage": "paper",
            "summary": {"fail": 0, "unknown": 0},
            "manual_review_required": False,
        },
    )
    monkeypatch.setattr(status, "stage_summary", lambda strategy_id: {"stage": "paper"})

    def fake_promote(strategy_id, *, reason, actor):
        called.append((strategy_id, reason, actor))
        return {"ok": True, "stage": "shadow", "previous": "paper"}

    monkeypatch.setattr(status, "promote", fake_promote)
    monkeypatch.setattr(
        sys,
        "argv",
        ["show_control_kernel_status.py", "--promote", "es_daily_trend_v1", "--json"],
    )

    assert status.main() == 0
    assert called == [("es_daily_trend_v1", "manual_operator_action", "operator_script")]
    out = capsys.readouterr().out
    assert '"stage": "shadow"' in out


def test_promote_entrypoint_blocks_unsupported_strategy(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from scripts import show_control_kernel_status as status

    called: list[bool] = []
    monkeypatch.setattr(status, "promote", lambda *args, **kwargs: called.append(True))
    monkeypatch.setattr(
        sys,
        "argv",
        ["show_control_kernel_status.py", "--promote", "other_strategy", "--json"],
    )

    assert status.main() == 1
    assert called == []
    out = capsys.readouterr().out
    assert "promotion_gate_unsupported_strategy" in out
