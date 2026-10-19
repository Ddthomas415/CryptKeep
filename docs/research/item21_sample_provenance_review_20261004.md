# Backlog item 21 (sample-data provenance): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Reviewed on master 97c24c8e.
State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or deployed; no
config or account change. Patch 0032 (commit 300753b6, cloud clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev43.zip`,
folder 40. SHA-256 of the zip:
70897c744d77e4e4d0cd06754a93bebf8de9f4f1087f929f27331ff8424060dd

## What holds

- Item 21's 24 tests pass.
- The runner labels evidence from the source actually used and holds the turn
  on a mismatch.
- This checkout's state, read-only: 8 current-format public snapshots, 3
  old-format ones in old stage-0 directories, 0 sample-labelled records and
  0 mismatch flags in canonical evidence. 30,053 older signal rows carry no
  source label.

## Findings

1. P2. `make paper-run-short` (listed in docs/GOLDEN_PATH.md) runs the
   canonical strategy id with `CBP_USE_SAMPLE_OHLCV=1` and no state directory.
   Run end to end in an isolated directory it wrote the intent queue, paper,
   position, trade-journal and strategy-state databases, 59 signal rows
   labelled `sample_ohlcv`, a session file, and a BTC/USDT 1d snapshot with
   source `sample_ohlcv`. Unfixed, those go into the canonical campaign.
2. P2. The four `paper-*` make targets call
   `scripts/dev/run_es_daily_trend_paper.py` directly; that file adds
   `scripts/`, not the repository root, to the import path, so they stop with
   `ModuleNotFoundError: services` unless the package is installed or
   PYTHONPATH is set. SHOWN in the cloud clone. Here: same file, and `.venv`
   has no install of the repo (site-packages listing only; the target was NOT
   run on this machine). This accident is why finding 1 has not happened.

## Correction in 0032

- Import path uses the repository root.
- `paper-run-short` sets `CBP_STATE_DIR=.cbp_state_challengers/dev_sample_short`.
- The script exits 2 on a sample run with no `CBP_STATE_DIR`, before the
  identity check and any child process.
- Side effect: `make paper-run`, `paper-status`, `paper-dry-run` import again.
  `paper-run` starts a real paper campaign in canonical state, as documented.

Results: 11 new test cases, 10 fail on the old code. Full suite on the final
revision: 4420 passed, 33 skipped, 19 failed (the same 19 as master). After
the fix `make paper-run-short` completed in the clone and the default state
directory's 1,590 files were unchanged (name, size, mtime).

## Reported, not changed

- a. The OHLCV snapshot store is shared; research readers (forward returns,
  selector backtest, correlation inputs, symbol scanner, dashboard views) do
  not check a snapshot's source. A forward return on sample rows returned
  `ok: True`.
- b. The paper engine copies five provenance fields to fills, so
  `ohlcv_sample_mode_origin`, `ohlcv_source_mismatch` and
  `ohlcv_sample_fallback` never reach a fill.
- c. Qualification's expected source falls open if a strategy config omits
  `signal_source`. All four current configs set it.
- d. The refusal checks that a state directory is named, not that it differs
  from the canonical one.
- e. Other files in `scripts/dev/` carry the same import-path line and work
  only through their wrappers in `scripts/`.

## Addendum, same day: gap (a) closed in patch 0033

Commit c5393e46 (cloud clone only), bundle rev44, folder 41. Zip SHA-256:
40345ccf6f13f80a6e577d68842a47f1f83240e0a16424f34b864590753387ed

- `_load_local_ohlcv` returns [] for a snapshot whose envelope source is
  `sample_ohlcv`, unless the caller passes `allow_sample=True`. Only
  `signal_quality` does, because it reports the source with the rows.
  Forward returns say `sample_ohlcv_snapshot`.
- This is a contract change: two existing tests asserted that sample rows are
  returned with no flag and were changed. 0032 does not depend on 0033, so it
  can be rejected on its own.
- 11 new cases, 7 fail on the previous code. Full suite: 4431 passed, 33
  skipped, 19 failed (the same 19 as master).
- Not changed: bare-list and `unknown` snapshots are still returned; how the
  selector and correlation callers treat a symbol with no usable snapshot was
  not reviewed.

Correction: finding (a) above lists "dashboard views". Dashboard views load
candles through `ohlcv_fetcher`, not this store. Only pages 42 and 46 reach
it, through the service functions now guarded.

## Addendum, same day: gap (b) closed in patch 0034

Commit 3be364a6 (cloud clone only), bundle rev45, folder 42. Zip SHA-256:
2b56239a3cf822eeaa6a16318f759ba4e1cbf2d1138f331fad1ec83a5a317415

- The paper engine forwards `ohlcv_sample_mode_origin`,
  `ohlcv_sample_mode_env`, `ohlcv_source_mismatch` and
  `ohlcv_sample_fallback` from intent meta to order and fill evidence.
- Fill qualification rejects an explicit mismatch or fallback flag; absent
  fields are judged as before. The report row shows the fields.
- Effect today is small: the runner already holds on a mismatch before an
  intent exists, and a fallback fill is already rejected as sample. The gain
  is that new fills record how their label was obtained.
- 8 new cases, 6 fail on the previous code. Full suite: 4439 passed, 33
  skipped, 19 failed (the same 19 as master).

Operator decisions left open:
- Fills whose label origin is `env` or absent still qualify. Every existing
  fill is in that group; rejecting them would disqualify all history.
- `scripts/check_promotion_gates.py` counts `local_snapshot` as public and
  does not look at the mismatch flag.
