# FC-01-r1 exploratory result

2026-10-04. GATE. HIGH research analysis; ACCEPTED_WITH_RISK by human approval.
Disposition: STOP this unchanged candidate under the tested cost scenario;
no confirmation collection or promotion. Closure is scoped to this pilot,
not a universal claim that imbalance cannot work or that fees never change.
Human approved the design and input pinning before this run. This is a pilot,
not powered confirmation, actual fills, or authority to trade.

## Economic answer

For the pinned August 30 to October 4 archive, 101 windows have complete
paired inputs. The fixed imbalance rule selects 17 entries and cash in 84;
37 of 138 windows remain unavailable. No threshold/horizon changes made.

| Descriptive scenario | USD result |
| --- | ---: |
| Rule, $100 purchase notional per entry | -15.99 |
| Enter every complete six-hour window | -92.48 |
| Rule minus that comparator | +76.49 |
| Cash | 0.00 |
| Rule fees | 17.01 |

OBSERVED: selected-window midpoint movement averages +5.95 bps. CF-MODELLED:
entry ask / exit bid gives about +$1.01 before fees; fees on both leg notionals
turn it into -$15.99. This uses the dated 50-bps-per-side fee scenario,
zero additional slippage and no infrastructure expense. More realistic
slippage cannot rescue this optimistic scenario. Historical/current account
fee applicability remains unverified; no maker-fill alternative was tested.

The comparator closes/reopens each six hours and pays both leg fees; it is
NOT buy-and-hold. The +$76.49 improvement includes avoiding the rejected
windows' -$76.49 net outcome, not a demonstrated positive trading edge.
USD is both quote and reporting currency; no BTC-denominated return inferred.
Fixed entry notional is not total funded capital or an annualized ROI.

## Descriptive Uncertainty

10,000 resamples, seed 20261004, keeping eligible windows together by calendar
day and retaining days with no complete windows. Two-sided percentile 95%
intervals in bps per complete paired window (cash windows included):

| Block size | Rule minus comparator | Rule absolute net |
| --- | --- | --- |
| One day | +58.78 to +90.32 | -29.09 to -3.56 |
| Three days, circular | +62.06 to +89.10 | -27.12 to -4.93 |

These are exploratory intervals conditional on available windows and this
cost model. They do not correct the project's unverified historical trial
count, prove missingness harmless, or establish power/regime robustness.
Intra-window drawdown, actual executable capacity and live fills not measured.
Capture timestamps reflect storage after fetching, not exchange event time;
exact receive-time/staleness semantics remain unverified. No execution replay
or actionable lead-lag claim.

## Disposition and Reproduction

Does not meet the absolute-positive-net requirement in this pilot. Recommend
no promotion or 90-day confirmation collection for this unchanged rule on
this evidence. Any different fee venue/mechanism or hypothesis needs a new
registration and untouched data, not same-data threshold rescue. This does
not retire SMA200, change E02/E03, or stop shared collectors.

Artifacts: docs/review_artifacts/20261004_fc01/pilot_trial_registry.md,
fc01_r1_pinned_inputs.json and fc01_r1_exploratory_results.json. Input content
SHA256 cd106bd53cf045d6ae10a76d439777d96e832dedceb62b2ca53ad9795f7a60f7.
Output embeds reporter source hash. Reproduce without opening the live DB:

```sh
./.venv/bin/python docs/review_artifacts/20261004_fc01/report_fc01_r1.py docs/review_artifacts/20261004_fc01/fc01_r1_pinned_inputs.json
./.venv/bin/python -m pytest -q docs/review_artifacts/20261004_fc01/test_report_fc01_r1.py
```

SHOWN: five targeted tests pass (flat fees, spread counted once, exit fee
notional, input hash mismatch rejection, deterministic bootstrap).
Human accepted the report after the result was presented. Remaining limitations
above are retained; acceptance is not independent statistical confirmation.
