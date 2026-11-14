# Paper-account public market-rule provisioning

Bot relation: BOT_RULES. Current runtime configuration not inspected or changed.
Checked Git/latest work log2026-11-14T05:15:07Z. HIGH-risk source increment;
separate Nash GATE05:13:20Z ACCEPTED_WITH_RISK for exact paper-opt-in source
and synthetic scope; accepted five-file hashes match SOURCE_SHA256SUMS.
No refresh was run against an
actual account, no HTTP request was made, and no job or deployment was created.
R10 remains STOPPED.

**Dated correction2026-11-14T10:43:31Z:** the owner subsequently approved the
shared-provider source repair. Default and explicitFalse now use the validated
native-increment path, with separate ACCEPTED_WITH_RISK and220focused author/
121independent passes. Older statements below that the shared defect remains
unfixed describe the earlier paper-only scope, not current source. Original
source/test snapshots and seals remain preserved; current evidence is in
`../coinbase_precision_shared_20261114/`. Existing caches and operations remain
untouched/unverified; no global cache migration or trading permission follows.

## Purpose and delivered source

The existing cash sizer reads `<paper-state>/data/execution.sqlite`. The old
refresh command selects a database through ambient EXEC_DB_PATH/CBP_DB_PATH or
config/trading.yaml and defaults to BTC/ETH. That is not a verified provisioning
path for nine isolated accounts or GroupB's selected/still-held coins.

New default-off `--paper-state-dir` mode of the existing command:

- Requires an explicit existing absolute paper state directory and explicit
  Coinbase USD symbols; no automatic default BTC/ETH list. All requested symbols
  and target/config paths are validated before the first fetch or cache write.
- Reads only the specified user.yaml in memory and retains public policy fields:
  typed live disabled/unarmed, paper enabled, USD, strict quotes/no fallback and
  the existing cash-sizing/single-account/position-aware/full-exit market policy.
  No credential fields or raw configuration are printed, copied or persisted.
- Uses precisely that state's data/execution.sqlite; never invokes ambient
  database discovery or changes the process environment. Symlinks in target
  ancestry, non-regular/multiply-linked existing files, and SQLite sidecar links
  are refused. This is preflight validation, not protection against concurrent
  hostile path replacement during network I/O.
- Fixed-coin accounts may provision their configured coin. GroupB may provision
  any of its25 declared USD pairs, including a desired coin and a still-held old
  coin, rather than only its static placeholder. No project symbol support changed.
- Fetches through the existing public provider/cache path, then reads back the
  exact persisted rows through the cash sizer's reader. Identity, modes, TTL,
  finite minimums and positive quantity steps must be usable; persisted rules
  must equal the returned fetch result. Any failed/unusable symbol returns
  aggregate ok=false and nonzero exit. Partial successful writes are reported,
  not claimed rolled back. Failure details/configuration are not emitted.
- The reader's optional cache_path supports this explicit read-back; its normal
  sizing default still reads its own account-local path. The exact pre-change
  reader was reconstructed by reversing this small path-argument change and
  matches its accepted historical SHA256
  dd5a90fbb95026b3a3fd1fde5879c2604346521b6d3a71f64bd7bb45c8ed08a7.

Legacy mode and defaults are unchanged, including its old unconditional ok=true
reporting. The new truthful status guarantee is for the explicit paper mode only.
This is not a global repair of every metadata caller.

## Material native-increment finding

SHOWN installed environment: CCXT4.5.48, Coinbase precisionMode4=TICK_SIZE.
The installed coinbase.py declares that mode and parses amount from native
base_increment; price prefers price_increment then quote_increment.

SHOWN existing provider: a numeric precision1 is interpreted as one decimal
place, yielding step0.1. A synthetic public market with native base_increment1
reproduces the wrong legacy step. This could make a quantity model incompatible
with a whole-unit market. Actual affected cached products/orders are UNVERIFIED.

The paper mode now opts into strict Coinbase precision translation via a new
default-false fetch_and_cache flag. It preserves positive finite native increments
as increments, compares against raw native fields, refuses unknown modes or
unrepresentable/inconsistent increments, and retains native price-field precedence.
No global/live/default fetch behavior changes. Its remaining defect is parked for
the owner's separate decision, not silently treated as repaired everywhere.

No account, actual market snapshot, historical result or financial conclusion was
changed. Existing fetch-failure-to-fresh-inactive caching (BA50) also remains:
failure blocks sizing and the new command reports failure; it does not silently
preserve an old success or claim automatic recovery.

## Use after separately authorized operation

Illustrative command for one already provisioned paper account:

```sh
./.venv/bin/python -B scripts/refresh_market_rules.py \
  --paper-state-dir /absolute/existing/paper-account \
  --venue coinbase --symbols BTC-USD
```

For a GroupB account, explicitly list the desired and still-held pairs, e.g.
`--symbols BTC-USD,ETH-USD,SOL-USD`. GroupA needs the corresponding symbol in
each dedicated account, including SOL. These examples are not authority to run
a refresh or create recurring execution. No periodic job, six-hour cadence,
network deadline or account provisioning is supplied by this source increment.
The existing network fetch budget still needs an operating plan; no new
controller or scheduler was added to hide that missing proof.

## Verification

Initial explicit-mode synthetic file:36passed0.38s. Provider-mode expansion:
47passed0.41s. The four-file focused selection after the native-increment change:
138passed3.23s, no failures/errors/skips; NOT a full repository suite:

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_refresh_paper_market_rules.py tests/test_paper_cash_entry.py \
  tests/test_market_rules_decimal_validation.py tests/test_market_rules_validation.py \
  --tb=short
```

Inputs are synthetic; public fetches are substituted. The end-to-end fixture
uses a fake unauthenticated CCXT exchange, real rules/cache functions and the
actual sizing reader. A whole-unit fixture produces legacy0.1 versus strict1.
That verifies translation behavior, not that a particular actual Coinbase coin
currently has this increment. Existing CLI/default-path and decimal regressions
remain covered. No earlier market study or606-case GroupB suite was repeated.

DONE at source level: explicit target, input/account-scope guards,
strict opt-in translation, persisted usability, honest partial/failure reporting
and focused tests. Independent source review completed:47tests independently
passed0.40seconds; the138-case total remains author-observed. Receipt:
INDEPENDENT_REVIEW.md. Original source copies and four incremental diffs retained.
NOT DONE: actual public metadata capture, current product translation validation,
all account provisioning, periodic freshness, effective profiles/capacity,
activation, original commissioning or forward performance. R7minimum-trade and
drawdown approvals remain PENDING; no approval was inferred here.

Material assumptions: target directories/configuration remain under trusted
ownership throughout a future foreground invocation; actual public provider
observations are independently verified before operational acceptance. Neither
source inspection nor these tests establishes current process/host state.

What do I know that could change the owner's decision that I have not yet said?
The global metadata fetch still contains the whole-unit precision defect outside
this explicit paper mode. Also, a once-correct cache expires in six hours, and an
unchanged refused BUY is not automatically retried. This tool alone does not make
the simulation run reliably or establish an economic advantage.
