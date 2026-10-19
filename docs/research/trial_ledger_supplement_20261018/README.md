# VOLFC-1 trial and data-reuse supplement

Recorded 2026-10-18T23:57:29Z. Active role: ENGINEER. This is a retrospective
bookkeeping completion, not a pre-run record or a new experiment.

## Disposition

SHOWN in the saved protocol and result: family VOLFC evaluated one candidate
configuration (Chronos-2) against two fixed baselines (trailing 60-day standard
deviation and EWMA lambda 0.94). The registered verdict remains FAIL: **did not
qualify**, not "Chronos was below the incumbent". Its point estimate was slightly
above the incumbent but failed all three registered criteria. No model adoption,
strategy change, profitability claim or new experiment follows.

`trial_additions.csv` records the candidate and baselines separately.
`data_reuse_additions.csv` appends the D_XS reuse declaration without editing the
October 15 `data_overlap.csv`. Read this supplement alongside, not instead of,
the dated reconciliation. Do not count it again as a new study.

## Counting units

- One candidate configuration is not 4,999 independent trials.
- Two baselines are comparators, not additional candidate configurations.
- There were 214 distinct evaluated markets, 4,999 market-week observations and
  50 weekly clusters. Symbol-selection exposure remains relevant even with one
  pooled configuration. These counts are not interchangeable or additive.
- Do not turn the old convention-specific floor of 747 plus this forecast study
  into a validated strategy-trial total, effective N or DSR input. This study
  measures volatility-ranking quality, not trading returns.

## Evidence and limits

Local saved CSVs establish the counts and saved metrics. The preceding read-only
audit independently recomputed the baselines, targets, ranks and bootstrap from
the archived candles. This supplement does not rerun those calculations or
Chronos inference. The original model execution, installed package versions and
checkpoint identity remain CLAIMED by the run artifacts, not regenerated proof.
The runner hard-codes a model revision and hashes weights after forecasting;
its output alone does not prove pre-run model or input enforcement.

The original protocol cited an October 20 release date. The saved disclosure
records first weights upload on October 30, after week 1 began. Keep the original
50-week FAIL and its labeled 49-week sensitivity. Neither is clean forward
confirmation, and this supplement does not certify absence of training overlap.
D_XS was already seen by E6. Its new volatility target does not make it untouched.

## Pinned sources (unchanged)

Paths below are relative to the repository root.

| Source | SHA256 |
| --- | --- |
| `docs/research/chronos_vol_forecast_20261018/PREREGISTRATION.md` | `501723e7203da0ff975c9b97ae1514f90a18d0f44418da7e0c9ab0d92eca59e1` |
| `docs/research/chronos_vol_forecast_20261018/run_volfc1.py` | `699698aae8a769e27c2026dddc81d4048ff36bea36da8f215b2614be9a715136` |
| `docs/research/chronos_vol_forecast_20261018/result.json` | `e8f47f59223f922cee119fa918b1ff499e6b4c41ba2391a1c126b2e7806c3320` |
| `docs/research/chronos_vol_forecast_20261018/forecasts.csv` | `7ef87e20d3277950a88010a5a9c60cef48ffdc1004eaafb4e0211c62138dd47e` |
| `docs/research/chronos_vol_forecast_20261018/weekly.csv` | `a6ace4314b86751959003f8d65f8f37998699edd3ca39f862714d76321936a13` |
| `docs/research/trial_ledger_reconciliation_20261015/data_overlap.csv` | `3fd7ec5766e9631738c4484914070b282e6e4defa8465710c6e7d851a0418cb8` |
| `docs/research/trial_ledger_reconciliation_20261015/pass2_family_counts_20261015.csv` | `770f46efef30d341ca051788049d6a8156c6d382ceb1c1c077b45e1e79099f5d` |

Frozen study files, old ledger files and their checksum manifests are unchanged.
The new SHA256SUMS covers only this supplement and excludes itself.
