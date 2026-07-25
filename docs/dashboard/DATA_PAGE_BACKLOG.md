# Dashboard Data Page Backlog

Date: 2026-07-03

## Current Priority

Dashboard work is a product backlog unless it improves operator decisions for
the current paper/research/shadow path.

## Operator-Critical Pages

Prioritize these first:

- gate status
  - `dashboard/services/promotion_ladder.py`
  - `dashboard/services/strategy_evidence_runtime.py`
- paper reconciliation
  - `dashboard/pages/44_Paper_Reconciliation.py`
  - `services/execution/paper_reconciliation.py`
- campaign health
  - `dashboard/pages/60_Operations.py`
  - `scripts/report_paper_campaign_status.py`
- market movers / candidate context
  - `dashboard/pages/37_Coinbase_Movers.py`
  - `dashboard/pages/36_Symbol_Scanner.py`
- AI/copilot advisory reports
  - `dashboard/pages/65_Copilot_Reports.py`
  - `dashboard/services/copilot_reports.py`
- kill switch and halted-state visibility
  - `dashboard/pages/60_Operations.py`
  - `dashboard/services/operator.py`

## Deferred Pages

Defer pages that are mostly presentation, onboarding, or non-critical product
polish until expectancy is proven.

## Rule

Any dashboard page that can mutate state must keep explicit role guards and
must not bypass accepted CLI/runbook ceremonies for high-risk actions.

## Executable Guard

`tests/test_dashboard_data_page_backlog.py` verifies that each operator-critical
category above points at current repo paths and preserves the mutation-boundary
rule.
