# Runtime Check - 2026-08-24

## Scope

Read-only check-in for the current local checkout, local paper campaigns, local
operator reports, and Hetzner crypto-edge runtime. No services were started,
stopped, restarted, configured, deployed, or mutated by this checkpoint.

## Local Repo

Commands:

```bash
gh pr checks 529
gh pr merge 529 --squash --delete-branch --admin
git status --short --branch
git log --oneline -5 --decorate
gh pr list --state open --json number,title,headRefName,baseRefName,mergeStateStatus
```

Result:

- PR `#529` had all required checks passing before merge.
- PR `#529` merged as `db8bd11d3`:
  `feat: include edge cadence in Hetzner runtime status (#529)`.
- Local checkout: `master`.
- Local/remote state: clean and aligned with `origin/master`.
- Open PRs: none.

## Local Paper Campaigns

Command:

```bash
make status-paper-campaigns
```

Result:

- `all_running=true`
- `running_count=2`
- `es_daily_trend_v1`: running, `idle`, reason `waiting_for_next_day`,
  `last_completed_day=2026-08-24`, `fills_total=20`,
  `closed_trades_total=10`, `net_realized_pnl_total=31.4368625683357`
- `breakout_default`: running, `idle`, reason `waiting_for_next_day`,
  `last_completed_day=2026-08-24`, `fills_total=22`,
  `closed_trades_total=11`, `net_realized_pnl_total=4.277597190923208`

## Local Paper Gate

Command:

```bash
make status-paper-gate-velocity-json
```

Result:

- `policy_id=slow_daily_single_symbol_v1`
- `thresholds_ready=false`
- Round trips: `3/5` qualified, `2` remaining
- Qualified bars: `63/60`, ready
- Overall blocking threshold: `round_trips`
- Projected completion: `2026-09-14T01:47:00Z`
- Diagnostic-only legacy/all-history round trips: `7`

## Local Cost Assumptions

Command:

```bash
make check-cost-assumptions-json
```

Result:

- Exit code `2` because the report is a warning.
- Paper-fill execution costs are configured and valid:
  `paper_trading.fee_bps=7.5`, `slippage_bps=5.0`.
- Modeled round-trip cost is `25.0` bps, above the policy floor `5.0` bps.
- Warnings remain for separate evidence/backtest cost surfaces:
  evidence scoring default fee `10.0` differs from paper engine fee `7.5`;
  walk-forward defaults are fee `10.0`, slippage `5.0`.

## Local Soak/Gate Status

Command:

```bash
make status-paper-soak-json
```

Result:

- `all_running=true`
- `campaigns_ok=true`
- Gate `machine_ready=false`
- Gate `manual_review_required=true`
- Gate blocker: `3/5` qualified round trips, `2` remaining.
- Evidence writer status: `ok`, consecutive failures `0`.

## Roadmap Tracking

Command:

```bash
make roadmap-tracking-status-json
```

Result:

- `ok=true`
- All `13` roadmap-listed commands exist in `Makefile`.
- All `12` linked source docs exist and are linked.
- Boundaries present: current phase is paper evidence collection and read-only
  research; deterministic trading/risk engine remains the only capital-moving
  authority; batch only same-lane work.

## Operator Queue

Command:

```bash
make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20
make operator-next-actions-passive-json
```

Result:

- Full generated queue: `28` operator-proof actions.
- Summary by reason: `15` host-side references, `10` remaining capped-live
  proofs, `3` remaining coverage proofs.
- Passive local operator evidence queue: `0` available actions after excluding
  host-side, capped-live-proof, and coverage-only items.

## Hetzner Crypto-Edge Runtime

Command:

```bash
HETZNER_STATUS_TRANSPORT=ssh HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
  make status-hetzner-edge-runtime
```

Result:

- `status=hetzner_crypto_edge_runtime_ready`
- `ok=True`
- `blocking_checks=0`
- Remote checkout: `master`
- Remote head: `a10aca01fc37de181cc32d17a30e5d677050f901`
- Recommendation: keep collector and cadence checker schedules under host
  monitoring.

## Hetzner Paper Campaign

Command:

```bash
HETZNER_STATUS_TRANSPORT=ssh HETZNER_SSH_TARGET=cryptkeep@100.86.128.9 \
  make status-paper-hetzner
```

Result:

- Campaigns: `1/1` running
- `all_running=True`
- `ema_cross_default`: `idle`, reason `waiting_for_next_day`,
  strategy `ema_cross`, fills `15`, closed trades `7`,
  net PnL `-2.3016`
- Latest fill: `2026-08-24T00:01:55.857611+00:00`
- Recommendation: `continue_paper_observation`

## Remaining Active Shape

- The current local implementation/PR queue is clear.
- The paper gate remains blocked by qualified round trips, not bars.
- The safe local passive queue is empty.
- Remaining generated actions are host-side proof, capped-live proof, or
  coverage proof items.
- Hetzner `ema_cross_default` paper campaign is running and idle after the
  2026-08-24 daily cycle.
- Hetzner dependency-pin alignment remains open; this checkpoint did not mutate
  the host virtualenv or restart services.
