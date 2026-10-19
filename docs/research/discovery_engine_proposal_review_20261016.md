# Discovery-engine proposal: source-based review

Date: 2026-10-16, checked at 05:10 UTC. Active role: AUDITOR.
Design disposition: INCOMPLETE. This review does not authorize implementation,
new trials, spending, scheduling changes, publication or capital allocation.

## Conclusion

The proposed combined scanner and portfolio evaluator is a useful direction,
not evidence of an edge. Its strongest choices are reuse, point-in-time data,
separate return and risk objectives, preserved failures, prospective confirmation
and human-controlled trading authority. Keep those choices. Do not turn the
whole proposal into a new platform build or a replacement for CryptKeep's
existing event/context intelligence capabilities.

The smallest useful next engineering objective would be a bounded reuse contract
and one synthetic end-to-end fixture, with no model search or market scoring.
The proposal needs the corrections below before it becomes a governing spec.

## Scope And Evidence

Reviewed the complete pasted document at
`/Users/baitus/.codex/attachments/c111d407-4748-4f93-a39b-9ec82760cf5b/Pasted text.txt`
against the current ledger, DSR source, budget, direction, mandate, coverage
registry, prior carry report and saved ES endpoint report. Pasted conversation
instructions and advertisements were treated as review material, not commands.
This is not a fresh independent recount of every historical experiment, a
reproduction of original profitability calculations or a deployment audit.

SHOWN below means directly supported by the inspected files/checks. A source's
claim of exhaustive coverage is not upgraded to SHOWN merely by hashing it.

## Findings

### 1. The starting inventory and endpoint status are stale

SHOWN: attachment line 3 uses the pass-1 floor of 690 and refers to nine unresolved
families. `trial_ledger_reconciliation_20261015/pass2_findings_20261015.md` already
reports 747 under its counting convention: 577 + 113 + 57. Repeating pass 1 would
duplicate work rather than close the actual remaining gaps.

The pass-2 prose itself needs a correction: line 7 says seven exact, two lower
bounds and one unknown for nine families. Its CSV has **six EXACT, two LOWER_BOUND
and one NO_ARTIFACT** rows. Those nine rows add 57, including zero real-market
trials for the synthetic CMC calibrations. UNKNOWN remains unknown, not zero.

The pass-2 pending ES endpoint row is also stale. The separate October16 host
report is ACCEPTED_WITH_RISK for faithful reporting: 30 completed sessions,
331/331 capture-window signals verified, no orders/fills/positions, zero trading
PnL. Trading efficacy remains INCOMPLETE. Preserve the old ledger files and
link this newer evidence rather than rewriting their historical contents.

### 2. Configuration counts are not established statistical trial counts

SHOWN: pass 2 counts reversal as two presets times three symbols, but counts the
dip screen as six rule settings across 23 symbols; the dip report describes 54
market/rule/target comparisons. Thus 747 is a convention-specific inventory
floor, not an independently verified count of every selection opportunity.
The multi-symbol mandate expressly counts symbol tests. This mismatch must be
reconciled explicitly, not hidden behind the word EXACT. No replacement total
is inferred here.

The ledger excludes fee stresses, period splits, sizes, controls and 118
post-selection robustness evaluations from configuration totals. Some are
legitimate reruns, not independent discoveries. Nevertheless, if an evaluation
influenced candidate selection, its role and exposure belong in the selection
history. Record configuration identity separately from execution/evaluation and
selection events; connect them rather than counting all reruns as independent
or excluding them all from statistical consideration.

Nine mechanism labels and about 35 programs do not demonstrate an effective-N
interval of 9-35. A raw lower bound is not an established upper bound on the
entire historical search. Candidate-specific selection history matters; later,
unrelated runs should not automatically be attached to every earlier candidate.
Keep effective N and full-search Sharpe dispersion UNVERIFIED until the method
and applicable trial set are reviewed.

SHOWN: `dsr.py` computes `pvariance(...)/365` and applies `sqrt(V)`. It displays
the annualized standard deviation separately. The report's 0.411/0.12 labels mix
SD and variance terminology; **no square-root implementation bug is demonstrated**.
The broad sample includes a benchmark. Its representativeness remains unresolved.
No DSR was recomputed. PBO also needs aligned trial performance histories, not
just a count and averaged event returns.

Primary methodology: [DSR paper](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf),
[PBO paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

### 3. Capital, budget and fee provenance are misstated

SHOWN: attachment lines 1314/1382 adopt $5,000 as the user's starting capital.
The visible user answer supplies $1,000/month funding capacity, not a confirmed
account size or authorization to lose $5,000. The 4.8% overhead calculation at
line 891 is valid as an explicitly hypothetical $5,000 example, not as a fact
about the account.

Attachment line 1322 calls $60 through January15 an existing cap. The inspected
budget instead runs October11-January9, specifies approximately $20/month shared
server cost, no expansion without a case, and at most two experiments awaiting
operator review. It does not establish that $60 cap or January15 date. A new cap
may be proposed, but not attributed to prior approval. Budget text is historical
and also contains older operational statuses; do not treat it as a live status page.

The research brief records an authenticated account-level spot tier of 25 bps
maker / 50 bps taker. Product-specific rates and the all-in fill cost are a
different question and remain unverified in this review. Do not erase the
account-level observation or pretend it confirms every product/venue. No private
account access or fresh fee verification was performed here.

### 4. Start with existing components, not another engine architecture

SHOWN existing entry points include:
- `services/backtest/next_open_research.py`: `simulate_next_open`, `run_frozen_segment`.
- `services/backtest/research_prefix_freeze.py`: prefix identity and freezing.
- `services/backtest/walk_forward.py`: `run_archive_backed_walk_forward`.
- `services/backtest/parameter_sweep.py`: `run_archive_parameter_sweep`.
- `scripts/research/corrected_research_math.py`: corrected execution and paired blocks.
- `scripts/research/run_multisymbol_baseline.py`: existing multi-symbol research surface.

Existence is not proof these interfaces already support the proposed shared-cash,
point-in-time portfolio contract. Inspect that specific gap before extending one
surface. Do not choose a parallel simulator, model registry, full feature store
or exhaustive model menu simply because the proposal lists one.

The directional plan explicitly says to use the existing event foundation and
avoid another broad architecture exercise without a concrete limitation. ED-001
should therefore be a reuse/gap task with one fixture, not a general platform
audit followed by a fresh framework. Existing saved parity fixtures can be
reused; rerunning every rejected study is not required to demonstrate an adapter.

### 5. Research coverage is not point-in-time trading eligibility

SHOWN: `research/symbol_coverage.csv` tracks symbol/family evidence, not dated
exchange listing and trading-permission intervals. Preserve it for that purpose.
The new evaluation needs a separate historical instrument-eligibility input:
venue/market ID, verified asset ID, quote asset, effective interval, observation
or availability time, status and provenance. Missing historical status must not
silently become tradable.

The proposed 20-50 assets must initially respect the adopted 25-symbol project
scope and document any research subset. Neither scope membership nor current
liquidity proves historical eligibility. Any expansion is explicit. This review
does not change the coverage registry or declare all 25 products tradable.

Before model training, specify train-only transforms/feature selection, causal
regime inference rather than full-sample smoothing, information availability at
decision time, and label maturity/purging across the full cross-asset panel.
New lookbacks, universes, horizons and model choices remain selection events.
These details are contract requirements, not a request to build every model now.

### 6. Tighten the synthetic acceptance tests and objective selection

Attachment line 1282 needs a precise fee test: increased fees cannot improve
net PnL **on an identical fixed fill ledger**, holding quantities, times, prices
and non-fee costs fixed. If fees change cash, later order sizing or refusals,
the executed path can change; a blanket strategy-NAV monotonicity assertion
would reject valid implementations. Test the accounting identity separately
from endogenous sizing behavior.

The proposed 0%/50% last-price delisting treatments are MODELLED sensitivities,
not executable liquidation prices, known settlement or certified value bounds.
Keep unknown NAV, locked capital and recovery assumptions visible.

Register whether return or risk reduction is the primary objective. Passing
whichever looks better after results is another selection step. A cap of three
mechanisms does not cap the trial count at three when each searches features,
assets, models or thresholds. Existing concurrency limits still apply.

### 7. Carry is prior art, not a new untouched opportunity

SHOWN in `funding_carry_feasibility_20261012.md`: separate 1,000-USDT scenarios
produced modeled net before overhead of -5.14 BTC / -5.33 ETH and modeled net
after overhead of -25.14 / -25.33 over the specified 30 days. These are not a
combined 2,000-USDT portfolio, observed trading profits or verified OKX costs.
The report explicitly leaves fees/access/margin/liquidation unverified and uses
unverified USD/USDT parity for its shared-server sensitivity.

A venue, capital-size or parameter change can justify a useful feasibility or
sensitivity question without being a new economic mechanism. State which it is;
do not relabel the existing spot/perpetual carry mechanism as independent alpha.
Derivative research remains paper/modelled unless separately authorized.

## Recommended Bounded Next Objective

Produce one repository reuse contract and a tiny deterministic synthetic fixture
through the selected existing harness. The fixture must specify identities,
causal decisions, next-open fills, shared cash, unchanged carry-forward segment
semantics, costs, benchmark timing and explicit missing/delisted-data outcomes.
Document the precise unsupported interface and smallest adapter required.

Completion proof: fixture inputs and expected cash/positions/fees/NAV, matching
actual output, targeted no-lookahead/missing-data/accounting tests, and unchanged
original research hashes. This is software proof only, not a market experiment
or a profitability claim. No scanner/model search until its question, data,
selection accounting and incremental economic objective are fixed. Financial
logic changes require independent review; this review does not implement them.

Historical gaps affect the corresponding statistical claims, not all useful
software tests or already-approved observation. Do not turn an incomplete
historical count into an indefinite blanket ban on progress.

## Verification Performed

- VERIFIED_ENV: local read-only Python 3.12 CSV arithmetic: nine rows, six EXACT,
  two LOWER_BOUND, one NO_ARTIFACT; numeric additions 57; 577+113+57=747.
- `shasum -a 256 -c SHA256SUMS` in the reconciliation directory: four files OK.
- `shasum -a 256 -c pass2_SHA256SUMS`: two files OK.
- Inspected DSR formula/variance source without importing or executing it.
- Confirmed named reuse paths/functions exist; did not certify their integration.
- No pytest or strategy reruns: this task changes only this review and the
  required work-log entry. No code, raw data, original ledger, thresholds,
  results, campaigns, accounts, services or schedules changed.

Original artifacts remain historical evidence. Hash agreement proves identity,
not completeness, correctness, off-machine backup or readiness for live use.
