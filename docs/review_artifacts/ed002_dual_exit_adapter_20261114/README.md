# ED-002 dual-exit policy adapter: synthetic implementation

Bot relation: BOT_RULES; runtime configuration not checked. Final source disposition2026-11-14T23:33:17Z.
ENGINEER implementation followed by separate Nash GATE; risk HIGH; ACCEPTED_WITH_RISK for this first
per-policy adapter and synthetic proof only. See `INDEPENDENT_REVIEW.md`; whole-study readiness remains incomplete.

## Usable result and authority

SHOWN: the owner approved the next step after the reviewed proposal818f9067...ce3a6: adoption plus its named
FIRST versioned six-config/shared-state adapter implementation with synthetic proof. This delivers that per-policy
API, not the entire16-arm/32-trajectory study. No new market run or collection, dates/freeze, deployment/trading,
capital/risk change or R10 resumption. Earlier proposal/design/source/report artifacts remain intact.

Entry points in `services/backtest/dual_exit_bridge.py`:

- `policy_recipe(configuration, exit_model, source_manifest_sha256=...)`: six explicit default/unblocked names
  and S/R-H1D only; unchanged frozen snapshot plus exact literal-False overlay. Unknown recipes are refused.
- `DualExitBridge(...)`: caller-supplied symbols, observations, dated rules/marks, snapshot bytes and declared
  source-manifest hash. No files, network, scheduler or account operation is performed by the adapter.
- `simulate_dual_exit_bridge(frames, bridge, state=..., **profile)`: same shared-cash ledger and delayed execution;
  returns model wallet/equity/trades, original strategy action, effective exit reason and derived reference state.

Caller must verify the source manifest externally before relying on it. `source_manifest_sha256` is an identity
binding, NOT a signature, authenticity check or attestation of executing code. `SOURCE_MANIFEST.json` binds15
selected source/test/snapshot files; its SHA256 is
`27a243ac71638620be811739eee28ec946a521899ccb3bb476c2f0cf26116099`.
Tests use an explicitly synthetic caller-declared manifest marker, not a claimed venue/source attestation.

Outputs explicitly retain `scope=SYNTHETIC_DUAL_EXIT_POLICY_CORE`, `study_ready=False`,
`comparison_ready=False`, `event_policy_implemented=False`. COMPLETE means this component's model accounting
completed; it cannot be reported as a ready study, completed announcement policy or real-world profit.

## What changed and what was preserved

New module and63 synthetic cases. Two existing files have minimal opt-in changes:

- `shared_cash_research.py` adds `simulate_shared_with_trade_context`; the old public entry point remains
  unchanged. Only explicit opt-in adds the versioned profile marker, copied model trade/events, batch targets
  and pre-batch units. Disabled legacy context/profile/results remain identical on the preserved-source fixture.
- `frozen_signal_bridge.py` accepts an explicit Boolean `decision_trade_context=False`; default selects the old
  ledger API. The new adapter uses True. The old frozen family set/snapshot identity and seven-arm API are unchanged.

The old sources are retained under `before/`, SHA3625c91f...1333cc (ledger),7ca917d6...2639a (bridge).
`LEGACY_OPT_IN.diff` records only these two files. Other dirty worktree changes remain untouched.
The prior21-input DESIGN bindings intentionally remain historical: these two bound sources changed in this
approved implementation. Do not reseal the old design acceptance or pretend its source hashes still describe
the new adapter. The new implementation manifest/receipt supplies its own source boundary.

Reference state is separate from fee-inclusive financial basis. It uses actual modeled fills, weighted gross
execution prices for additions, original age, every-BUY reference clock, and eligible later completed closes
for peaks. Partial sells/additions are allocator quantity changes, not empirical exchange partial fills.
Equal-time/pre-fill prices cannot trigger price exits; time60 uses decisionT, not laterE, and can exit a recent
addition in an older position. The repository evaluator supplies stop/trailing/TP/time priority. Trigger levels
are not guaranteed fills or loss limits: one-hour-delayed market opens and declared costs govern settlement.

Trace retains strategy_actions separately from effective actions/targets/held_without_sell; stack exits cannot
be mislabeled incidental HOLD resizing. No raw observer action substitutes for the returned strategy action.
Required held exits excluded for unavailable permission/open yield INCOMPLETE, not a successful unsold account.
Known restricted holdings also fail closed in this core; this is not a completed announcement/timed-liquidation
policy. Diagnostic holdings are retained, never zeroed or assigned an invented recovery price.

## Carry proof and corrections

Saved peaks are not trusted. Resume validates the financial ledger, hourly grid, used frames against the bound
panel, closing valuation, and every recorded batch through the SAME existing batch/settlement functions.
It then reconstructs position reference/peak/age and compares the stored derived state. Finally it replays the
bound policy history through the SAME fresh adapter/ledger and compares the full canonical state, including
pending and executed targets. Two matching editable copies of a target are not sufficient provenance.
Changed recipes, source-manifest identities, past prices/rules/receipts or altered/omitted pending state refuse carry.

This replay is model carry validation, not another research trial, historical study, new engine or live order.
It may be expensive on long histories:182-day resource capacity/serialization/persistent operation remains
UNVERIFIED. There is no external authenticity claim for caller-supplied observations or arbitrary hidden processes.

Corrections found before acceptance, with no actual financial operation:

- O170: editing an execution price plus matching derived peak could pass initial aggregate validation. Replaying
  fills against bound data/costs fixes that; a second counterexample using an alternate internally valid frame/
  fill ledger and transplanted input binding required explicit historical source correspondence. Both cases
  failed before correction and pass after.
- O171: the old generic ledger's allowed missing-open exclusion could make this new required-exit component
  falsely COMPLETE. The new opt-in evidence and required-exit guard preserve unsold units but withhold economic
  completion. The regression failed before and passes after; the old ledger contract is not silently changed.
- O172: independent review injected a financially valid pending target never requested by the strategy. Added
  injected/altered/deleted pending and altered executed-target cases, including matching altered trace copies.
  All four failed before policy-derived replay and pass after. No unreviewed draft was deployed or accepted.
- Two earlier test fixtures mislabeled candle-open timestamps as close times; only their synthetic close arrays
  were corrected. No production threshold/price logic was changed to fit those fixtures.

## Verification

Final author focused command (VERIFIED_ENV for this existing local environment):

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tests/test_dual_exit_bridge.py tests/test_shared_cash_research.py \
  tests/test_frozen_signal_bridge.py tests/test_delayed_signal_bridge.py \
  tests/test_delayed_research_comparison.py tests/test_descriptive_report.py \
  tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

**273 passed in25.52s**, no failures/errors/skips. New core alone:63passed1.18s. Earlier262-pass slice preceded
the final source/pending-target corrections and is not substituted for final proof. No full-suite result claimed.
Tests exercise all12 real signal paths on invented flat data (no trades, not profitability), real mean-reversion
final-action overlay, actual shared-ledger entries/exits, gap-through-stop delay, incidental addition/original-age
time exit, full/split state equality,25invented assets sharing one wallet, malformed recipes/source bindings,
numeric range and missing evidence, and carry corruption/source-target provenance. Existing210 regression
cases exercise the original accounting/bridges/comparison/report interfaces; no market signals were evaluated.

Test-body socket/process guards are not an OS-wide/import/hidden-process guarantee. No acquisition, actual
runtime config/account/credentials, services/schedules/server, backup/cloud/tools, dependency install, deployment,
order, commit/push or memory operation was requested/performed by this task. Source contains no such operations.
Initial unaccepted core and failing-target regressions are retained under `initial_core/`; original models remain.

## Requirement disposition and next boundary

DONE, independently reviewed within stated risks: exact six-config/two-model recipe, per-policy delayed shared
wallet, fill-derived state, refusal of pre-fill prices and forged policy carry, old default compatibility,
synthetic proof, source/before preservation and explicit component readiness labels.

NOT DONE: sixteen-account orchestration, thirty-two trajectory/cost report, full official-event source/coverage
and venue-event/benchmark invalidation integration, gap-correct attribution/report extension, actual identity/
warmup/provider/host/cost/monitoring proof, future registration or acquisition/evaluation. These remain the
adopted plan's next demonstrated gaps, not abandoned or falsely completed. No registry/trial outcome changes
from these invented fixtures. No statistical qualification, edge, expected income or live/paper readiness claim.

Separate source/correction GATE completed: the four target-provenance regressions passed within the reviewer's
12-case correction selection; the original injected-target probe now rejects. Prior52-case and1-case source
checks were reused, not represented as a second independent273-case run. All15pins and two before copies
matched. `AUTHOR_HANDOFF.md` preserves the reviewed pre-closeout README bytes8c4792d0...4136f; source/test
files and manifest were not changed after acceptance. Only this status closeout and the receipt were added.

Next: only the next authorized orchestration/event/report gap in the same queue item. No new market study,
R10 work or operational successor follows automatically. Open facts include
long-history replay cost, reliable actual event/data coverage, changed source/environment, and future measured
execution/performance. Source tests alone cannot settle any of them.

What do I know that could change the owner's decision that I have not yet said? This is a tested per-policy
core, not the complete25-symbol study. Carry integrity required source-derived replay; its long-horizon cost
and the remaining event/orchestration/report path are still unproved.
