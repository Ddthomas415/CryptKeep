from __future__ import annotations

import asyncio

from services.paper import main as paper_main



def test_paper_main_accepts_paper_run_mode(monkeypatch):
    monkeypatch.setenv("CBP_RUN_MODE", "paper")

    def _guard_store():
        raise RuntimeError("entered_paper_mode")

    monkeypatch.setattr(paper_main, "ExecutionGuardStoreSQLite", _guard_store)

    try:
        asyncio.run(paper_main.main())
    except RuntimeError as e:
        assert str(e) == "entered_paper_mode"
    else:
        raise AssertionError("paper main returned before entering paper mode")



def test_paper_main_rejects_non_paper_run_mode(monkeypatch, capsys):
    monkeypatch.setenv("CBP_RUN_MODE", "live")

    asyncio.run(paper_main.main())

    out = capsys.readouterr().out
    assert "Paper mode disabled" in out
