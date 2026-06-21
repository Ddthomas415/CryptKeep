# Remaining Tasks

This file is a lightweight index only.

## Current state
As of 2026-06-21, the active operating state is paper-evidence collection, not
live launch.

SHOWN:
- `master`, `origin/master`, and `review-stabilized` are kept aligned through
  reviewed PRs.
- Laptop-owned paper campaigns are healthy:
  - `es_daily_trend_v1`
  - `breakout_default`
- Hetzner-owned `ema_cross_default` is healthy and must be checked with the
  Hetzner campaign manifest, not the laptop shortcut.
- Canonical `es_daily_trend_v1` paper promotion remains blocked at `1/10`
  provenance-qualified round trips, with `9` remaining.
- Raw all-history currently reports `8` closed trades, but those remain
  diagnostic unless both entry and exit fills carry the required non-sample
  public-OHLCV provenance.

Current accepted checkpoint:

- docs/checkpoints/paper_gate_status_2026_06_21.md

## Canonical blocker list
Root-runtime launch blockers are tracked separately. They are not the same as
the current paper-evidence campaign blocker.

- docs/checkpoints/launch_blockers_root_runtime.md

Strategy-evaluation work is tracked separately:

- docs/checkpoints/strategy_signal_quality_plan_2026_05_22.md
- docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md
- docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md

## Master integration TODO
Master integration completed through
[#49](https://github.com/Ddthomas415/CryptKeep/pull/49) on 2026-06-06.

SHOWN on 2026-06-06:
- PR #49 merged as `5ab9732a2`.
- All eight GitHub checks passed before merge.
- `origin/master...origin/review-stabilized = 0 / 0` after branch alignment.
- The prior 25-file conflict plan is obsolete and closed.

Next action:
- Keep new accepted work on focused branches or `review-stabilized`.
- Integrate future batches through reviewed pull requests without allowing
  `master` and the integration branch to accumulate avoidable divergence.

## Interpretation
Current paper-campaign path:

1. use `make status-paper-all` for the daily check-in: laptop campaign health,
   canonical paper-gate progress, and Hetzner-owned `ema_cross_default` status
2. use `make status-paper-soak` or `make status-paper-hetzner` only when you
   intentionally want one side of the split-host status
3. use `make status-paper-campaigns` only when you need raw laptop process
   restore/status detail
4. wait for `es_daily_trend_v1` to reach 10 provenance-qualified round trips,
   then perform the manual performance review

Root-runtime launch path:

1. use the frozen canonical root-runtime path recorded in `docs/checkpoints/root_runtime_scope_record.md`
2. obtain one reachable supported sandbox/testnet venue from the operator environment
3. prove private lifecycle runtime flow on that reachable venue
4. or make an explicit human launch decision accepting the current environment-blocked exception

Already completed on the frozen canonical path:
- private authenticated connectivity for one supported venue
- singular live-mode source of truth
- boundary-governed live lifecycle authority
- hidden-default fencing for the chosen launch path

## Notes
Do not mix:
- launch blockers
- strategy signal-quality / paper-evaluation work
- conditional broader-scope controls
- non-blocking architectural debt

Do not treat raw all-history trade count as promotion progress. The actionable
paper gate is the provenance-qualified count reported by `make
status-paper-all`, `make status-paper-soak`, or
`scripts/check_promotion_gates.py --json`.
