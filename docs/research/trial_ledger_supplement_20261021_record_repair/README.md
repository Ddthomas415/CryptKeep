# Trial-ledger record repair (2026-10-21)

Recorded 2026-10-21 by Claude (Cowork), operator-requested ("take care of what's needed"). Bookkeeping only:
no experiment was run, no data was downloaded, and no existing ledger, verdict or artifact was changed.
Read this alongside, not instead of, `../trial_ledger_reconciliation_20261015/` and the 20261018 and
20261019 supplements. Gaps found by the 2026-10-20 coverage audit and its independent fact-check.

## What this adds

- `trial_additions.csv`: two studies that ran but have no trial row.
  - LOW_VALUE_TOP100 (v1 and v2, 2026-10-18): 3 hypotheses (under USD 1, ranks 51-100, new top-100
    entrants), 1 horizon, 1 common control. v1 is superseded by v2 (instrument-classification correction),
    so the same 3 specifications are counted once. The 20261019 supplement names this study as prior use of
    D_CMC but deliberately did not count it.
  - LIQ_MARKOUT_20261012: one descriptive diagnostic (5-minute primary horizon, fixed before calculation;
    1- and 15-minute horizons reported). Not a trading test.
- `corrections.csv`: one stale ledger field. ES_TRIAL says "result NOT found in repo"; the endpoint result
  is recorded in `docs/checkpoints/es_prospective_endpoint_result_2026_10_16.md`.

## Counting

The configuration floor after this repair: at least 747 (pass 2, 2026-10-15) + ENTR-CB-1 (1) + low-value
screens (3) + liquidation diagnostic (1) = at least 752 configurations. The diagnostic counts as 1, like
MONDAY_DIAGNOSTIC, which pass 1 counts inside the 113 (`count_reconciliation.md` section 3). VOLFC-1 stays
recorded separately, as its supplement requires. The effective independent trial count remains unresolved.

Correction, same day: the first version of this README said the liquidation diagnostic was not a strategy
configuration and gave a floor of 751. An independent fact-check found that inconsistent with how the
Monday diagnostic is counted; corrected above before anything else relied on it.

Data reuse: `data_reuse_additions.csv` records the low-value study's use of D_CMC (not listed in the
2026-10-15 `data_overlap.csv`, which names only CMC_PROXY) and the liquidation sample. LOW_VALUE's
market_week_observations is left blank: the study README gives 3,900 / 4,299 / 134 hypothesis selections
and 8,418 control selections, while RESULTS_V2 and ENTR-CB-1 report 133 entrant and 8,382 control
selections for v2; the difference is not resolved here.

Units differ between studies (cycles, selections, event minutes); the columns are not additive.
