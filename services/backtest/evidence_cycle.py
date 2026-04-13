"""services/backtest/evidence_cycle.py — public API facade."""
from __future__ import annotations
from services.backtest.evidence_shared import (  # noqa: F401
    default_trade_journal_path,
)
from services.backtest.evidence_paper import load_paper_history_evidence  # noqa: F401
from services.backtest.evidence_windows import default_evidence_windows    # noqa: F401
from services.backtest.evidence_run import run_strategy_evidence_cycle     # noqa: F401
from services.backtest.evidence_persist import (  # noqa: F401
    evidence_dir,
    build_evidence_comparison,
    persist_strategy_evidence,
    render_decision_record,
    write_decision_record,
)
