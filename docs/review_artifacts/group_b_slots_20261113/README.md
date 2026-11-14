# Group B weekly slots - offline source integration

Bot relation: BOT_RULES. Runtime configuration not inspected or changed.
Checked current Git/work log 2026-11-14T04:18:17Z (November 13 New York).
HIGH risk; separate final correction GATE ACCEPTED_WITH_RISK at
2026-11-14T04:42:13Z. Four final reviewed hashes match SOURCE_SHA256SUMS;
complete artifact seal/current Git/work log checked 2026-11-14T04:44:19Z.
R10 remains STOPPED. No original commissioning criterion is waived.

## Decision served

Continue the approved simulation engineering item, using section 4 of
`docs/research/paper_simulation_spec_20261031/README.md`. The owner explicitly
adopted: missing, unreadable or invalid current ranking keeps exit management
and blocks new BUYs, without reusing last week's picks. A valid selection with
zero qualifiers is different: rotate out, then remain cash.

The existing ranker, signal library, generator and candidate-universe hashes
still match the October 31 specification. No weights, threshold, strategies,
frozen results, actual settings, universe support or queue priorities changed.
The producer uses the existing rank_market function; it does not substitute the
different hot-market rotation engine or the generic five-candidate planner.

## Implemented source contract

- A separate producer accepts already captured public inputs only. It never
  fetches market data, starts a job or imports execution. All 25 original bases
  are accounted for in frozen universe order as Coinbase USD pairs. Pair absence
  needs an explicit no_coinbase_usd_pair exclusion plus metadata evidence hash;
  a fetch failure is not an exclusion. No ticker-return default-to-zero.
- Each included market has exactly 200 contiguous completed hourly candles
  ending at the common hour preceding Monday 00:05 UTC. The existing ticker
  percentage input is retained; no substitute close-to-close return is invented.
  Observation timestamps must be in the 00:00-00:05 ranking window. This is a
  source input-validity contract, not proof that any actual feed met it.
- Top three scores at least 38 qualify; stable ties retain universe input order.
  Still-selected coins keep their slots; replacement coins take empty slots in
  rank order. Slots may be empty. Exact inputs, all scores, exclusions, previous
  slot/hash evidence, frozen source hashes and the new producer/contract/CLI
  hashes are included. Hashes provide integrity/identity, not authentication or
  proof that supplied public observations or exclusions are truthful.
- Weekly artifacts are immutable dated files, published by hard link only after
  complete write/fsync. Existing publications are never overwritten. The consumer
  derives the dated filename from the current UTC week, so no weekly config edit
  or last-good-file fallback is needed. Validity is Monday 00:05 inclusive to the
  next Monday 00:05 exclusive. A reader pins its first accepted hash; a changed
  same-week file is invalid, not a revised selection. A publication/fsync failure
  can leave the final file present: inspect it, do not blindly repeat/overwrite.
- Default-off `strategy_runner.group_b_selection` identifies policy
  group_b_weekly_v1, slot 1..3 and an absolute directory. Its reader never imports
  or executes a ranker. It requires the existing available_cash_v1 sizing,
  paper-enabled/live-disabled, strict snapshot/no-fallback, single-venue USD
  market-order, full-exit and position-aware guards. No such config was applied.
- Actual holdings, account-wide nonterminal orders/intents, retryable rejected
  exits and all retained symbol-accounting scopes precede switching or entry.
  New read-only ledger/queue queries have no newest-row cap; they avoid copying
  full fill history or acquiring the reconciliation snapshot's write lock.
  Unknowns block entry. Persistent slot identity and managed symbols survive
  restarts; cash, fee basis and per-symbol risk/signal history are never reset.
- A dropped holding rotates through the existing durable full-position SELL
  path with reason rotation. A strict current public quote is required, but
  rotation does not wait for strategy warm-up, a new crossover or an emission
  latch reset. Existing duplicate, accounting, kill/protective-exit and consumer
  safety gates remain; refused exits retain their identity. A queued SELL is not
  completion. No new target BUY until old positions, orders and accounting settle.
- The paper consumer's opt-in valuation uses the actual held coin, not its static
  original placeholder. Ambiguous ownership yields incomplete valuation and no
  new equity row. Ordinary mode behavior is unchanged.
- Execution revalidates BUY slot/rank/hash at consumption, engine submission
  (including existing orders) and the final ledger gate. Selection refusal uses
  the existing durable buy-terminal record before queue disposal. Filled receipts
  are not reclassified. A final savepoint permits provisional cash/position/fill
  writes to roll back before a terminal refusal is committed on the same connection.
  Marked fills require strict canonical quote evidence, not a stale engine mode.

The existing entry transition/latch is preserved, not replaced with a retry
policy: a BUY vetoed while ranking is unavailable can remain suppressed after
the file recovers if the same coin's signal never changes. The specification
already records non-retried refused/missed BUYs (BA-05/BA-18). This increment
does not promise automatic entry on recovery or reset per-symbol signal history.
The opt-in is not a complete cohort configuration validator; hourly source,
three unchanged strategy presets and all other required effective settings still
need profile/manifest verification before activation.

## Files and use

Producer: `services/analytics/group_b_weekly_selection.py`.
Data-only contract: `services/market_data/group_b_selection.py`.
Execution reader: `services/execution/paper_weekly_slot.py`.
Existing runner/consumer and two store APIs provide the integration.

Offline CLI, from the repo root, for already captured inputs only:

```sh
./.venv/bin/python -B -m scripts.research.build_group_b_weekly_selection \
  --inputs /absolute/public_inputs.json --rank-at YYYY-MM-DDT00:05:00Z \
  --previous /absolute/last_selection.json \
  --output-directory /absolute/existing_selection_directory
```

Omit --previous only for an initial fresh bootstrap. Input JSON has an inputs
array; the synthetic fixture in test_group_b_weekly_selection.py demonstrates
its exact shape. These command placeholders are not an approved market capture,
job installation, operational invocation or activation. Generated time is the
actual clock, not a caller-supplied historical timestamp. The CLI cannot make
late data contemporaneous; receipt truth still needs collection review.

## Evidence and limits

Pre-increment source copies are preserved here. Three actual-runner tests fail
against the saved runner: it emits a BUY without ranking, lacks cash-week
rotation, and lacks holding-to-replacement rotation. An initial replay command
used a .before extension that importlib could not load (three setup errors, not
behavior evidence); the identical saved bytes under strategy_runner_before.py
yield the three expected behavior failures. No production guard was bypassed.

Initial new tests: 25 passed/5 failed; four exposed a desired-symbol versus held
symbol service-list mismatch, one reused a synthetic seed identity and therefore
did not create a second holding. Corrected ownership reconciliation and fixture
identity. A fixture clock/cache timestamp mismatch was also corrected before the
valid-entry/failing-before checks. Subsequent expanded selection: 36 passed in
2.01 seconds. The initial consolidated349-case run still missed three independent
review findings. A subsequent361-case run passed after those corrections, but
independent timing injection exposed another final-gate defect. Initial source,
failures and reviews are preserved; they were not accepted as first-pass success.

Final author verification: **606 passed in26.04seconds**, no failures, errors or
skips. This is a targeted15-file selection, NOT a whole-repository suite:

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_group_b_weekly_selection.py tests/test_paper_weekly_slot.py \
  tests/test_strategy_discovery_hygiene_contract.py tests/test_paper_cash_entry.py \
  tests/test_runner_multi_symbol_integration.py tests/test_cooldown_runner_integration.py \
  tests/test_strategy_runtime_runner.py tests/test_runtime_execution_identity.py \
  tests/test_execution_identity.py tests/test_paper_reconciler_recovery.py \
  tests/test_paper_account_reconciliation.py tests/test_paper_snapshot_quote.py \
  tests/test_paper_buy_fill_expiry.py tests/test_paper_buy_before_boundary.py \
  tests/test_paper_buy_lifecycle.py --tb=short
```

Independent GATE initially BLOCKED O157-O159: wrong mapped quote, forgotten old
accounting during ranking failure and queued execution past week authority.
All three author regressions failed before the fixes. Correction review independently
passed7focused cases but found O160: authorization I/O could age a quote/TTL/week
past the last check. Three additional regressions failed before correction.
The final gate now samples time AFTER authorization I/O and checks cached quote,
TTL and week bounds without further authorization I/O before logical commit.
Author also reproduced/fixed O161: fence-write error must leave BUY unresolved
without aborting unrelated exits. Independent final diff review reports all
three timing cases plus the fence-error case passed and ACCEPTED_WITH_RISK.
See INDEPENDENT_REVIEW.md;606total remains author-observed.

New tests use synthetic markets, temporary real SQLite stores and actual runner
loops. The runner fixture's consume driver is deliberately minimal and fee-free;
it is NOT a real exchange or full consumer/reconciler lifecycle. The separate
paper-consumer MTM test runs the actual loop and real mark_to_market method but
stubs queue work/reconciliation and prices. Existing cash/fill/recovery tests
provide additional focused regressions, not whole-system proof.

Two material assumptions for this source model:
1. Each slot has the existing single runner ownership/lock and a dedicated paper
   state directory/consumer. Read snapshots plus a pre-emission recheck are not
   cross-database reservations; unauthorized concurrent writers remain a risk.
2. Captured input timestamps, ticker percentage basis and product-identity/absence
   evidence are independently verified before actual publication. A metadata
   hash or a self-consistent JSON file alone cannot establish those facts.

NOT DONE: live public-input acquisition, fresh quote coverage for selected AND
still-held coins, account-local public rules refresh/provisioning, approved
effective profiles/paths, intended-host capacity, jobs/permissions/activation,
following-week returns/universe/BTC comparisons, 26-week evaluation, original
R1-R12 operational acceptance or commissioning. U-07 is not closed. The full
simulation remains INCOMPLETE, and no forward edge or live readiness is claimed.
Existing BA-24 proposed-order exposure enforcement is not repaired or waived.

Claude's November 13 23:54:39Z observation is relevant: available-cash entry reads
a six-hour account-local metadata cache and never refreshes it. The existing
scripts/refresh_market_rules.py can fetch/cache public rules, but it was not run
or scheduled here; its default BTC/ETH list is not all Group A or Group B coins.
Actual refresher operation remains UNVERIFIED. If the cache expires, BUYs refuse
and an unchanged signal is not automatically retried. That is an activation
dependency, not a demonstrated current operating failure in an inactive mode.

What do I know that could change the owner's decision that I have not yet said?
The source can now express a weekly selection/rotation, but the specified Group B
study is not running and its following-week performance/evaluator is still
unbuilt. Starting a job now would not meet the original experiment or commission
it; the remaining public-input/provisioning/operational approvals are real work,
not evidence that the source tests established profitability.
