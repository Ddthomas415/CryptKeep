# Trading config fail closed (live-money backlog item 2): paper engine cost settings

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0040 (commit 714b38ae, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev51.zip`,
folder 48. Zip SHA-256:
53252353ee9fa34191488ab6021afcc1e842a0ad942c957e337b7f3ee7b22e3f

Scope: the item is a sweep. This covers only the surface that feeds the
running paper campaign's PnL.

## What holds

An unreadable `user.yaml`, or a `paper_trading` section that is not a mapping,
refuses paper buys (`paper_config_invalid`) and keeps sells.

## Findings (real engine)

Flat price 100, one buy and one sell of 1 unit. Valid 7.5 / 5 bps config:
realized -0.25.

| Setting | Result on the previous code |
|---|---|
| `fee_bps: -100` | realized +1.90 |
| `slippage_bps: -500` | realized +9.85 |
| `starting_cash_quote: nan` or `inf` | written as the balance; every cash check passes |
| `fee_bps: nan` | the fill raised IntegrityError |
| `fee_bps: "abc"` | engine could not be built; exits blocked too |
| `fee_bps: true` | traded at 1 bps |

## Current state of this checkout (read-only)

Canonical config: `fee_bps: 7.5`, `slippage_bps: 5.0`, other paper settings
absent. None of the above is occurring.

## Correction in 0040

`fee_bps`, `slippage_bps`, `max_order_qty` must be finite numbers >= 0;
`starting_cash_quote` finite > 0; booleans and non-numbers are refused. An
unusable value is replaced by the code default, the config is marked invalid
(`config_error = invalid_value:<keys>`), buys are refused
`paper_config_invalid`, sells stay available at the default costs. An unusable
starting balance is never written to a new account.

25 new cases, 23 fail on the previous code. Full suite: 4520 passed, 33
skipped, 19 failed (the same 19 as master).

## Not changed

- No upper bound: a 20000 bps fee is accepted.
- Exits under an invalid config use the code defaults, not the last valid
  values.
- The rest of the sweep (live executor, reconciler, admin live controls) was
  not reviewed here.
