# Shared Review Findings - 2026-10-07

Active role: AUDITOR. Overall review/series acceptance: INCOMPLETE.

## Reproduced Accounting Findings

P1, SHOWN: patch 0058's assembled reconciliation can close a one-unit order
after accounting only 0.4 units when the venue returns a nonempty but incomplete
trade history. `_executor_reconcile.py:451-452` suppresses the remainder whenever
any trade quantity is returned. The independent probe records terminal `filled`
with only 0.4 accounted. Closed status is not proof of complete accounting.

P1, SHOWN: a canceled partially filled order becomes terminal after its canonical
fill sink refuses the trade. `_executor_reconcile.py:513-518` does not preserve
the retry condition used by the filled branch. Independent probe observes
`canceled` after refusal, leaving the fill outside tracked-order recovery.

P2, SHOWN: fallback pricing applies the whole-order average to the remaining
quantity instead of reconciling execution value. With 0.4 at 100 already
recorded and final quantity 1.0 at average 160, the independent probe accounts
136 total rather than 160. Quantity correctness alone does not validate basis.

Verification: isolated rev87 candidate, real SQLite execution store and mocked
venue/canonical sink; three independent tests fail in 0.79s. Command used main
venv Python, bytecode/cache disabled, temporary CBP_STATE_DIR and candidate/tests
PYTHONPATH. No real orders or production state access. Probe artifact:
docs/review_artifacts/rev87_review_20261005/test_partial_accounting_review_probes.py.

## Static Findings Requiring Reproduction Or Risk Disposition

The execution specialist fully read eleven requested patches, READMEs and
production diffs. Its report identifies additional gaps: recorded-total read
failure interpreted as zero; daily-risk commit preventing later retry of a
failed symbol-loss update; repair bypassing symbol-loss application; concurrent
replacement of a failure flag before unchecked unlink; and kill-switch release
published before required audit evidence. These are source-control-flow findings,
not observed laptop/Hetzner incidents or executed reproductions in this report.

The specialist rejects unconditional acceptance of that execution slice. This
does not revoke earlier bounded dispositions for different corrected artifacts.
Do not deploy or broaden acceptance from the author's full-suite count.

## Coverage And Chronology

The research specialist fully read twelve additional patch groups and reproduced
source predicates showing two P1 qualification gaps: inherited execution-database
overrides escape the proposed test sandbox, and a `capped_live` deployment-stage
stamp admits paper evidence without canonical live-fill provenance. Additional
P2 findings cover future stage timestamps, overlapping selection/holdout windows,
gapped fixed-horizon joins, modeled slippage labeled observed, and stale PID
ownership checks. These are bounded source-only probes, not full-suite or venue
reproductions. Do not run the full suite from an operator environment relying
solely on 0066's CBP_STATE_DIR isolation.

Historical sidecar fully read 69 historical-only human-facing documents and
verified their 92 archive references. It lists 28 historical-only code/data
artifacts outside its semantic coverage. Supporting sidecar fully read fourteen
unique Markdown documents with exact hashes. It identifies an unreconciled
ATR-stop/sizing specification versus the accepted managed-exit policy, and
separates superseded findings from unresolved integration evidence.

85 available review-family archives have been integrity checked and deduplicated
to 437 distinct contents. This does not mean all 437 were semantically reviewed.
The large historical work log, historical-only code/data and portions of raw
evidence remain explicitly incomplete. Saved exact coverage must be consulted;
no assurance that nothing was overlooked is warranted.

## Next Treatment

Highest-priority correction is the fill-accounting completion contract: do not
terminalize before complete durable accounting; preserve canceled-order recovery;
reconcile execution value, not just quantity. Use these independent probes and
obtain separate high-risk review. Keep symbol-loss/repair concurrency as explicit
subsequent proof obligations, not opportunistic changes inside the first patch.
Preserve research intelligence capability and the accepted economic objective.

No production source/config/campaign/account/collector changes, push, merge or
deployment. This review does not establish profit or current live disablement.

Saved specialist reports: specialist_execution_review.md,
specialist_research_review.md, supporting_documents_review.md and
historical_documents_review.md under docs/review_artifacts/rev87_review_20261005.
The all_review_family_coverage.csv ledger covers all 437 indexed contents and
keeps unread/code/data-only states explicit. This is not an all-clear certificate.

## Additional Bounded Numeric-Config Finding

P2 SHOWN on the assembled candidate: paper_engine._cfg's numeric conversion
does not catch OverflowError. Validly parsed, extremely large YAML integers
raise on fee, slippage, starting-cash and order-quantity settings instead of
returning controlled invalid-config state. The constructor calls this function
at line 264. An AST-isolated probe has one normal control passing and four
safety assertions failing. This verifies function failure, not a running
campaign outage. No corrective implementation or independent acceptance here.

Full artifact hashes, source trace and reproducible probe are in
early_dependency_continuation_review.md and test_config_numeric_overflow_probe.py
under docs/review_artifacts/rev87_review_20261005. These also record full reads
of 13 additional artifacts and preserve known multi-symbol/currency limitations.
