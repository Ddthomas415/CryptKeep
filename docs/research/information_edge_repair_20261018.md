# Information-edge audit corrections and offline Module A repair

Date: 2026-10-18. ENGINEER stage. Risk: HIGH for financial-code candidate;
documentation reconciliation and public-source feasibility are separate outputs.
Implementation handoff: READY_FOR_INDEPENDENT_REVIEW; subsequent independent
GATE disposition: ACCEPTED_WITH_RISK for the exact offline code and synthetic
contracts only. No financial-model, integration or market-study approval.

## Scope And Preservation

Operator authorized treating the complete two pasted documents after the audit.
Read both end to end, including the company detour, read-only audit proposal,
Module A claims, operating-contract drafts and nine-step operator queue. This
is not a new exhaustive repository/security audit or permission to remove a lock.

Attachment SHA256:

- `1fe0b659-8a60-49dd-a584-e2ff76f32c96/Pasted text.txt`:
  `bb09f1fe7da761d1d5cad05300f063873a581b33f68c02804531bf1d6ff88d6d`.
- `05029ebc-1198-49ab-8387-5aabee3db856/Pasted text.txt`:
  `326ec9a7f61b8953e725edc9492657270d2abdccbcb391508f339c622ef58063`.

The external `Documents/cryptkeep_data_archive/module_a_draft_20261018/`
originals were not edited. Byte-identical snapshots are preserved under
`docs/review_artifacts/information_edge_repair_20261018/`:

- `original_module_a_sim.py.txt` SHA256
  `2be805171d14b37b232197974bc45de95fa289db528172990fe52bebb6896f12`.
- `original_test_module_a_sim.py.txt` SHA256
  `e93b9cfccd9f17fc7ed9163094cab7add1609eb425cf4d45da65ac3a2ce4ac44`.

No existing study script/result, raw archive, fee observation, schedule, trading
rule, risk limit, credential, service or account was changed. No commit/push,
cleanup or proposed operating-contract adoption occurred.

## What Changed And Why

1. Added separate `scripts/research/module_a_candidate.py`, not a replacement of
   an approved harness. It reuses the existing `rebalance()` without modifying it.
2. Removed future-close inspection from opening execution. A hand-checkable
   counterexample now reproduces the old draft: buy at100, plan a sale next open,
   then remove that later day's close. The old draft turns a100-dollar fixture
   into50 dollars via assumed recovery before the sale; the repaired candidate
   sells at the same opening price and retains100 dollars in either case.
3. Missing required open/held close prices stop with INCOMPLETE, retaining cash,
   quantities and phase/day. No stale executable prices, inferred delisting or
   invented recovery cash. Close incompleteness is detected after opening trades.
4. Added MODELLED fill/open/close trace. Reconcile each sells-first cash credit
   and debit, including fees/slippage, against the joint helper. Validate cash,
   not only positive NAV. Float ledger comparisons allow scaled1e-10 tolerance;
   returned helper cash must remain finite/nonnegative, not silently clipped.
5. New tests cover the original counterexample, current-close execution
   independence, account/decision-prefix causality and a leaky canary, missing
   prices, fee-inclusive affordability and a deliberately corrupted helper,
   target validation, turnover and synthetic helper parity within1e-6 dollars.
6. Reconciled the active queue: dated fees are not absent; old counts/secret
   clearances are historical claims; automatic commits and blanket second-fix
   stoppages were only proposals. Old queue wording remains as marked history.
7. Added `information_edge_assessment_20261018.md`: lawful public information,
   existing data/code, cost/latency fit, one candidate for later preregistration,
   and primary-source links. No companies named EDGE are proposed as the answer.

## Verification

VERIFIED_ENV: local `.venv` Python, isolated pytest with plugins and bytecode
cache disabled. Actual command, exit0, **52 passed in2.86s**:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
  tests/test_module_a_candidate.py tests/test_harness_contracts_wp4.py \
  tests/test_corrected_research_math.py
```

This command uses synthetic data only. Passing existing WP4 helper contracts
does not prove integration of this separate candidate into the full harness.
No broad suite rerun or claim of a green repository.

Financial source/test hashes frozen for separate review:

- `module_a_candidate.py`:
  `bd7139ff115efd743239a26f6d31be09766d622f90b8c1d89e449de958e6477c`.
- `test_module_a_candidate.py`:
  `0a6e2422be327f53f5927df5ada2f93a9ccaca1adb3c57cd36313982d420fd9d`.
- Unchanged `corrected_research_math.py`:
  `d07ae7171e2293cbe60d15ae9bc0973d3ef8bd31b9c7b99105f928c029e29047`.

## Still Not Established

- Module A contract/thresholds, point-in-time universe/eligibility, historical
  harness parity, carry-forward shared accounts and a matched-volatility benchmark.
  The original `matched_vol_exposure` helper was not ported or called complete.
- Delisting/settlement sensitivities: recovery0/0.5 remains preserved in the
  original draft. The corrected candidate refuses such undated payouts; a dated,
  separately frozen settlement policy is needed before this capability is added.
- Partial fills, capacity, venue settlement/precision, source/news alpha and net
  profitability. No information-source edge is demonstrated by documentation.
- Current product-specific all-in fees; the October8 account observation remains
  unchanged. $5,000 is a preserved fixture default, not approved user capital.
- Full secret clearance, recoverability/restore proof and ownership of the old
  zero-byte Git lock. No destructive action or checkpoint commit was performed.

## Independent Review Outcome

Separate reviewer `01a15051-95c8-7cf2-bd13-65d32c43d093` accepted the exact
source/test hashes WITH_RISK. Artifact:
`docs/review_artifacts/information_edge_repair_20261018/independent_code_review.json`.
Reviewer ran the same synthetic selection once:52passed2.79s, and additional
in-memory actual-allocator causality/next-day canary,100-fill cash reconstruction
and entry-day missing-close probes passed. No blocking defect found.

P3 `GATE-MA-001` remains openly nonblocking: the stored candidate prefix test
uses a simpler target; the actual multi-asset allocator prefix regression passed
as an independent probe but is not a persistent test. No reviewed source/test
was changed after the review. This risk is not hidden by the52-test total.

There were zero market-data strategy runs and no new scored symbol exposures;
the coverage registry and trial ledger are not incremented for synthetic cases.
The assessment proposes feasibility criteria, not a registered experiment.
Separate review is recorded in the artifact directory; none of these tests or
documents authorizes startup, retry, scoring, capital exposure or trading.
