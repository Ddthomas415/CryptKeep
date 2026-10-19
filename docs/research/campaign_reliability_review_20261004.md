# Paper campaign reliability (backlog item 1 slices): independent review

2026-10-04. AUDITOR then ENGINEER (Claude). Master 97c24c8e plus the patch
series. State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or
deployed; no config or account change. Patch 0050 (commit 84fe6413, cloud
clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev61.zip`,
folder 58. Zip SHA-256:
9d3d68b1806d7167930d33365f1d40bca4ac1097fae5b0b71f168c9970632916

## What holds

An unreachable source before a session writes `blocked /
ohlcv_source_unreachable` and does not use a daily attempt. A later successful
probe lets the loop proceed. Restore with `--preflight-ohlcv` does not start a
collector while the probe fails.

## Does it work in practice (session evidence here, read-only)

| Cohort start 2026-06-16 to 2026-10-04 | Days |
| --- | --- |
| Total | 111 |
| With a session record | 111 |
| With a completed session | 105 |
| Without one (2026-07-12 to 07-17, two failed attempts each, four on 07-17) | 6 |

The outage handling landed on 2026-07-18. No day has been lost since. Recent
sessions start between 00:01 and 00:13 UTC.

## Finding (P3)

Any exception from the probe was reported as `ohlcv_source_unreachable`,
including the venue refusing the request (`ccxt.BadSymbol`, `BadRequest`,
`NotSupported`, `ArgumentsRequired`, `AuthenticationError`). The collector
turns that status into "blocked, retry later" without using an attempt, so a
wrong symbol or timeframe would wait for ever looking like an outage.

## Correction in 0050

A refused request is `invalid_preflight_config` and is not retried. The
collector then runs the campaign, which fails visibly. Transport errors and
generic venue errors are still an outage.

14 new cases, 6 fail on the previous code. Full suite: 4636 passed, 33 skipped,
19 failed (the same 19 as master).

## Not changed

- The collector probes 5 rows while the runner fetches up to 400.
- Two failed attempts close together still end the day when the failure is not
  the unreachable class.
- Each guarded restore grants one more same-day attempt, with no upper bound.
