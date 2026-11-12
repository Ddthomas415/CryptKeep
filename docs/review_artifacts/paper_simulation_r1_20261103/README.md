# Paper simulation prerequisite R1 - 2026-11-03

Bot relation: BOT_RULES; runtime configuration not checked. No campaign started.

Role: AUDITOR (records separate GATE). HIGH risk. Author implementation ended READY_FOR_INDEPENDENT_REVIEW;
separate R1 source review ACCEPTED_WITH_RISK. Full simulation/operational readiness INCOMPLETE.

Final separate review: 77 R1 cases and 12 additional probes passed; the same 37 integration cases failed before
the fix. Reviewer checked frozen hashes and inspected, but did not rerun, the author's 274-case receipt.
See independent_review.md. This completes R1 source scope, not R12 or the paper simulation.

## Decision and implementation

This is engineering queue item 2's first protective prerequisite, not completion of the server paper simulation. Rebase October patches 0001/0002, retaining the accepted four-status lookup correction 0006 and finite position-reducing quantity treatment documented on 2026-10-07. Do not change frozen strategy rules or install/start services.

SHOWN source changes:
- Persist cooldown evaluations remaining under kill_remaining:<venue>:<symbol>:<strategy>, instead of carrying an absolute process-local loop number across restart. Both risk-block and performance arming sites use the count. Legacy conversion writes before clearing and caps the debt at the longest configured cooldown minus one.
- During an active cooldown only, permit a closing sell if position/proposed quantity are finite, positive and proposed quantity does not exceed held quantity; require no duplicate sell latch and no in-flight strategy intent. An unreadable queue refuses the exception. No silent resize of an oversized partial-mode sell.
- The lookup is a direct SQLite existence query for queued/submitting/submitted/held, without a newest-row window. LIMIT 1 stops after finding a match; it is not a 200-row scan.
- Ordinary no-cooldown duplicate-intent policy, strategy decisions, entry signal-change consumption and performance bookkeeping are not redesigned here. Multi-symbol isolation from accepted item 1 is retained.

Earlier work inspected: frozen paper_simulation_spec_20261031 sections 1/6/9/12, patch inventory, original 0001/0002/0006, cooldown_protective_combined_review_20261007.md, cooldown_exit_quantity_treatment_20261007.md, current full runner context and affected arm/emission sites, kill/performance helpers, intent queue, paper engine, consumer/reconciler interfaces, existing tests. Before sources, original patches and incremental diffs are preserved here; unrelated dirty work is not reverted.

## Evidence and limitations

VERIFIED_ENV: local repository venv, isolated pytest environment, no package installation. Restored original tests from 0001/0002 plus 0006: **40 passed in 4.14s** using:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_kill_cooldown_sessions.py tests/test_kill_gate_protective_exit.py --tb=short
```

SHOWN additional integration: the new test_cooldown_runner_integration.py uses the accepted multi-symbol harness and
real temporary SQLite stores. All **37 cases fail against strategy_runner.before.py** (37 failed in 2.55s), including
the four stop/trailing fill cases blocked at the original runner gate. The saved command explicitly selects the
before-runner; the working queue class remains current, so this is before/after runner evidence, not a pristine
checkout/full-tree comparison.

SHOWN final combined targeted verification: **274 passed, zero failures/errors/skips in 14.72s**, covering the 37 new
integration cases, 40 restored cooldown/lookup cases and 197 prior runner/exit regressions. Complete command/environment
and outputs are in focused.final.command.json/focused.final.txt/focused.final.xml; baseline equivalents use the
integration.before prefix. The new test driver uses real queue claiming and submitted/filled transitions and actual
PaperEngine submission/evaluation/fill accounting, verifying full/partial quantity, fee, cash, realized PnL and holdings.
Quotes, configuration, external safety verdicts and freshness are synthetic passing inputs; production router,
reconciler/service behavior and stale/rejected retry are not established. Fee input 50 bps is a test value from the
frozen spec, not a refreshed account-tier check. This receipt preceded separate review. No full-suite, host, real exchange,
process, runtime config, private account or financial evidence is claimed. Separate GATE subsequently returned
ACCEPTED_WITH_RISK for R1 source scope, with the explicit timing and concurrency limitations below.

Cooldown counts are evaluations reaching the gate, not elapsed time. The inherited single-symbol arm blocks 19/49 later evaluations for nominal 20/50-loop policies; caps and threshold configuration are unchanged. Legacy 51 converts to 49 once. Missing quotes/config/early errors do not serve the gate; multi-symbol debt is served on that symbol's round-robin visits. Intended manifest recording must retain nominal settings and actual count/cadence. No operational manifest is fabricated here.

**Dated reporting correction, 2026-11-03:** this report initially estimated 285/735 seconds by multiplying 19/49 by
15 seconds. That estimate is withdrawn: kill_cooldown early-continue skips the configured end-of-turn sleep (inherited
behavior), so even nominal pause length cannot be inferred from that setting. Network/processing determine blocked
turn duration; fast responses can serve the count much sooner. The counter fix does not repair cadence. The earlier
spec/BA-17 5/12.5-minute claims likewise need this qualification. Record measured blocked cadence before operation;
no new policy or sleep behavior is silently introduced in this R1 patch.

Open limits: a blocked or failed exit still has the existing bookkeeping/latch/lifecycle problems outside this bounded exception; R12 is needed before operation. Queue existence and paper holding are not an atomic reservation against concurrent order writers. Downstream gates are not bypassed by this runner repair. State read/write errors must not open a buy; corrupt state or missing prices can leave the affected symbol unmanaged. Reverting to old source ignores kill_remaining and could drop a remaining block; rollback must preserve stopped operation and state, not silently resume old source.

## Frozen requirement disposition

- R1 cooldown and protective runner exception: implemented; focused before/after and combined tests passed; separate GATE ACCEPTED_WITH_RISK.
- R12 persistent rejected/stale exit retries: NOT DONE; next part of protective stage 1, not abandoned.
- R2-R11, R4/R6/R8/R9 recording/data/lifecycle/operations/monitoring/backups, owner evaluation/provider decisions and 72-hour commissioning: not completed by this change. Existing components remain to be reused and assessed at their staged turn.
- Official simulation start, deployment, server operations and trading: not authorized by this source change and not performed.

What could overturn source completion: independent review finding a dropped cooldown debt, a blocked valid protective sell, a duplicate/oversized sell, or new divergence from the retained entry/sizing contracts. Runtime approval requires all frozen prerequisites and its separately specified commissioning/review/owner start, not only R1 tests.

What do I know that could change the owner's decision that I have not yet said?
