# Conversation and bundle reconciliation

Date: 2026-10-02 (operator timezone). AUDITOR. Status: INCOMPLETE for
full-system acceptance; this reconciliation is not a deployment approval.

## Coverage and limits

Reviewed the visible conversation decisions and recent pasted responses,
including the c5dda720 attachment in full; read rev18 REVIEW_HANDOFF, the
current-equity and exact-symbol production diffs, config proposal, and audit
Addenda 7-8. Inventoried available ZIPs and compared numbered patch hashes
across revisions 9-18. Earlier reviews in this chat provide bounded proof for
older patches; they do not constitute an exhaustive reading of every file.
Read both attached spreadsheets' sheets/formulas and independently recomputed
daily totals and fee-scenario return gaps. No workbook edits or render audit.

Not completed: every historical attachment end to end, all GitHub discussions,
raw 2,304-signal replay, account database provenance reproduction, full-suite
claims, deployment/process inventory, Hetzner inspection, or profitability
validation. No claim of having read all files shared over three calendar days.

## Accepted direction and decisions preserved

- Profit/net economic value is a priority, not endless hardening. Intelligence,
  event awareness, archives and multi-asset capability remain agreed scope.
- Completed-daily-close crossover entry remains the user's chosen rule.
- Current paper equity was selected, not historical cost equity.
- Human acceptance of bounded corrections is distinct from applying a full
  series, merge, deployment, live activation or historical-state mutation.
- Do not clear records, hide account positions by narrowing risk scope, reset
  evidence cohorts, or restart campaigns without the applicable decision.
- Backlog item 29 requires campaign strict-config opt-in and an observed
  no-storm cycle before the code-default flip. Look-back is not that cycle.

## Material information missed or insufficiently surfaced

1. Current equity is no longer wholly unimplemented in the supplied work.
   Rev16-18 patch 0009 implements exact-symbol, fresh midpoint marking and
   common quote-currency checks. It is proposed code, not accepted/deployed
   system behavior. Our earlier unresolved status must include this proposal.
2. Account contamination is not just four positions. The external audit
   reports about 146,000 cash created by an unsupported BTC sale and current
   cash 148,245.72. CLAIMED here: database history not reproduced in this pass.
   Fresh prices alone cannot turn invalid opening cash into valid capital.
3. Wrong-symbol fallback is an inherited execution/data issue, not a strategy
   loss. Patch 0010 removes venue-level fallback and handles paper fetch
   exceptions. Historical-fill causation still needs transaction-specific proof.
4. Matching a quote to the signal price within 0.14 percent is not independent
   symbol provenance when both may share a source. Audit finding 36 and the
   workbook's 'Right symbol' sentence overstate that inference.
5. A low historical strict-block count does not establish zero false blocks,
   order-time safety, or future stability. Publisher coverage and the five-
   second price-age requirement differ from the 120-second strict guard cap.
6. Patch numbers changed. In rev15, 0008 was preset risk wiring. In rev18,
   0008 is the accepted invalid-valuation correction, 0009 current equity,
   0010 exact-symbol quotes, and 0011 the HELD preset risk wiring.
7. Our acceptance entries often stopped at recording approval rather than
   integration. Implementation in temporary folders is not operating progress.
   No current GitHub/deployment status was refreshed in this reconciliation.

## Latest series inventory

| Rev18 patch | Subject | Reconciled state |
|---|---|---|
| 0001-0003 | Cooldown, protective exits, PnL labels | Earlier bounded reviews; not a fresh deployment approval |
| 0004 | Multi-symbol rotation | Accepted cache correction was reimplemented; current form needs final review |
| 0005 | Pending entries count | Tested previously; reservation/concurrency coverage not established |
| 0006 | submitting/held lookup | Addresses our prior lookup gap; not blanket lifecycle proof |
| 0007 | Cost-basis percentages | Intermediate dependency, not the selected final equity contract |
| 0008 | Invalid valuation rejection | Human-accepted correction; latest-series tests are not byte-identity proof |
| 0009 | Current paper equity | Newly inspected/tested; account provenance and currency contract unresolved |
| 0010 | Exact-symbol lookup | Newly inspected/tested; downstream permissive guard behavior remains |
| 0011 | Preset risk wiring | HELD; excluded from this pass's test tree |

SHA256 comparison shows numbered patches 0001-0003 unchanged across rev9-18;
rev17 and rev18 have identical numbered patch contents. Rev18 adds review and
config/evidence packaging. Do not apply duplicate legacy copies from folders
1/5/6 on top of numbered integration patches.

## New local proof

VERIFIED_ENV: exported base 97c24c8e4884629347a5492ae848133becd9027b to
/tmp/cryptkeep-rev18.sxwiFy. Applied numbered patches 0001-0010 cleanly;
excluded 0011. No main production-source edits.

Python 3.12 with PYTHONDONTWRITEBYTECODE=1 and
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, pytest -q -p no:cacheprovider:
test_paper_equity_marking.py, test_runner_exposure_pct.py,
test_runner_multi_symbol.py, test_market_snapshot_readers.py,
test_tick_reader_exact_symbol.py: **161 passed in 4.48s**.
These are targeted tests, not a full-suite or live-path audit.

## Spreadsheet reconciliation

- Market-quality Daily: 119 rows, 2,304 checks, 2,301 pass, 2 newly stale,
  1 previously stale, zero other blocks. All row totals reconcile.
- Cohort: 103 days and 2,178 checks; six order days. This checks workbook
  arithmetic, not raw evidence authenticity or whole-sample median claims.
- Fee workbook explicitly derives from pasted backtest output, not a rerun.
  Recomputed strategy-minus-hold dollar gaps at 0/7.5/50/60/80/120 bps:
  +2546.75/+1797.11/-348.01/-564.18/-1546.68/-2823.16.
  Do not confuse this 2,868-day, 31-trade scenario with the separate
  1,095-day fixed-entry experiment or realized paper profit.
- Fee labels and old UNVERIFIED notes are historical, not current account
  fee evidence. Do not treat fee-scenario interpolation as a proven break-even.
- Workbook dates use 2026-10-03; audit snapshot times around 00 UTC may be
  October 2 in the operator timezone. Preserve source dates, not inferred drift.

## Remaining review priorities

1. Complete 0010 caller review and item-29 plan without changing defaults.
2. Review 0009 against verified cash currency/provenance. It infers currency
   from the entry symbol; it does not establish the denomination of stored
   cash. Pending notionals still use queue-time reference prices. Treat this
   as a contract gap, not a complete validated account-equity calculation.
3. Propose explicit account recovery/isolation options preserving originals;
   do not silently delete records or treat a new account as canonical history.
4. Integrate only specifically reviewed artifacts under an explicit merge/
   deployment scope. Keep 0011 held and economics separate from code readiness.
5. Superseded: the user supplied infrastructure cost under $10/month. Use the
   range, not a fabricated exact invoice; this alone does not close E01.

## Rev20 continuation: corrections and coverage

Active role: AUDITOR. Overall review: INCOMPLETE, not deployment approval.

- SHOWN: config_editor uses app_paths.config_dir(). The shell-resolved path is
  `.cbp_state/runtime/config/user.yaml`, not repository `config/user.yaml`.
  Read-only whitelisted inspection found execution.live_enabled, live.enabled,
  live_trading.enabled and risk.enable_live all false. Symbols are BTC/USD,
  ETH/USD and SOL/USD on coinbase; paper_trading.quote_currency is absent.
- Withdraw the recommendation to switch that local flag off. Running-process
  environment and Hetzner remain UNVERIFIED; local flags are not no-live proof.
- Folder 17 targets the wrong config for this loader. Do not apply it as an
  effective campaign change. Resolve the actual process/state root first.
- Rev20 0009 reads declared cash currency, defaulting to USDT when absent,
  and refuses mismatched entry/held/pending symbols. The paper-engine helper
  explicitly does not enforce order quote currency. Declaration is not cash
  provenance or FX conversion. Local USD symbols mismatch that default; do not
  relabel cash merely to make entries pass.
- CLAIMED: a further engine-currency patch was tested but lost on workspace
  reset. It is not delivered evidence. Rev21 was not supplied.
- Infrastructure cost under $10/month is now received. The later E01 correction
  leaves economics open pending the isolated trial and evidence limitations.
  Historical simulation and cadence estimates are not realized profit.

SHA256 inventory covered every non-directory member of rev17, rev18 and rev20:
60 unchanged files from 17 to 18, 56 from 18 to 20. Changed files include 0009,
regenerated 0010/0011 diffs, audit, workbook, manifest and handoff. Byte changes
do not necessarily mean behavioral changes. Read the new pasted continuation,
handoff, local Addendum 12, loader and revised valuation code. Earlier workbook
arithmetic checks are not a fresh recomputation of the revised workbook.

VERIFIED_ENV: clean archive of 97c24c8e4884629347a5492ae848133becd9027b at
/tmp/cryptkeep-rev20.6KJ4JB; numbered patches 0001-0010 applied, 0011 excluded.
Python 3.12 command, with PYTHONDONTWRITEBYTECODE=1 and
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1:
`python -m pytest -q -p no:cacheprovider tests/test_paper_equity_marking.py tests/test_runner_exposure_pct.py tests/test_runner_multi_symbol.py tests/test_market_snapshot_readers.py tests/test_tick_reader_exact_symbol.py`
Result: **190 passed in 5.64s**.

Not an exhaustive attachment review or full-suite rerun. Raw history, revised
workbook, running processes, Hetzner, account provenance, complete series
acceptance and end-to-end execution remain unverified in this continuation.
No config, credentials, account state, production source or deployment changed.
Next: review account-currency enforcement/provenance and a correctly targeted
item-29 proposal. Keep preset patch 0011 held.
