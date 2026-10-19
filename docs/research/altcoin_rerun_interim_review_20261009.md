# Altcoin rerun interim review

AUDITOR; reviewed current source only, while other session is building it.
No result artifact found in research/research_corrections_20261009 at inspection.
Do not interpret this as final review of a frozen handoff.

## Findings

1. P1 SHOWN: event_portfolio scheduled-exit branch defers an unavailable open
   irrespective of mode, and the subsequent held-candle loop skips pend_out.
   Strict mode can therefore finish with unknown NAV rather than INCOMPLETE.
   Synthetic five-day probe: close/open100,100,100,missing,110; signalday1,
   hold0, fees/slippage0, strict mode. Returned COMPLETE, nullNAVday3, exitday4.
   The declared strict contract requires stopping at the missing held day.
2. P1 SHOWN: original recovery.py/ideas.py compare the completed close with the
   trailing threshold. The new script executes whenever daily low touches it.
   A low crossing with a recovered close exits only in the new version. Preserve
   close-triggered signals and use next-open execution; alternatively label an
   intraday resting-stop amendment as a separate strategy with explicit approval.
3. P2 SHOWN: summarize compares a stopped strategy curve to the benchmark's full
   requested window endpoint. A strict incomplete path can appear beside a BTC
   return covering later days. Truncate benchmark to the same observed endpoint
   or withhold endpoint comparison for incomplete runs.

Additional limits: final-close liquidation remains a labeled approximation;
CM C proxy fee-only recomputation is not exchange execution validation. No full
suite or complete result reconciliation performed. One read-only synthetic probe
executed; no original script/results or active rerun file changed.

Acceptance: INCOMPLETE pending corrected frozen handoff and independent review.

## Executable regression handoff

Treatment update: user approved correction ownership. The runner now checks
held open/close data before strict exit handling, restores completed-close exit
signals with next-open fills, and reports BTC at the same curve endpoint.
All three reproductions pass; fourth probe verifies a60% loss at the actual next
open rather than a35% guaranteed stop cap. Four targeted probes pass.
Independent Ohm review requested; READY_FOR_INDEPENDENT_REVIEW for bounded fixes,
not acceptance of the full rerun or any new economic conclusion.

`docs/research/altcoin_rerun_review_probes_20261009.py` contains three isolated
contract probes. Run with repo Python/pytest; current result3failed in0.16s.
All three findings now reproduced, not just inferred. They require strict
missing-held-data refusal, preservation of close-triggered trailing signals,
and equal comparison endpoints. Synthetic arrays only, no archive/network writes.
Do not weaken assertions to accommodate a changed strategy. Original script is
being built in another session; no competing edits were made by this review.
