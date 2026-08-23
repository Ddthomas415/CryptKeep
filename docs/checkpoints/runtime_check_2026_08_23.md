# Runtime Check - 2026-08-23

## Scope

Read-only check-in for the current local checkout and Hetzner paper/edge
runtime. No services were started, stopped, restarted, configured, deployed, or
mutated by this checkpoint.

## Local Repo

- Local checkout: `master`
- Local/remote state: clean and aligned with `origin/master`
- Current HEAD: `f2e49842f` (`docs: refresh roadmap task snapshot (#522)`)
- Open PRs: none returned by `gh pr list --limit 20`

## Local Paper Campaigns

Command:

```bash
make status-paper-campaigns
```

Result:

- `all_running=true`
- `running_count=2`
- `es_daily_trend_v1`: running, `idle`, reason `waiting_for_next_day`,
  `last_completed_day=2026-08-23`, `fills_total=20`,
  `closed_trades_total=10`, `net_realized_pnl_total=31.4368625683357`
- `breakout_default`: running, `idle`, reason `waiting_for_next_day`,
  `last_completed_day=2026-08-23`, `fills_total=22`,
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
- Qualified bars: `62/60`, ready
- Overall blocking threshold: `round_trips`
- Projected completion: `2026-09-13T04:56:53Z`
- Diagnostic-only legacy/all-history round trips: `7`

## Local Crypto Edge Cadence

Command:

```bash
make check-edge-cadence-json
```

Result:

- `ok=true`
- Checked families: `funding`, `open_interest`, `basis`
- Missing families: none
- Stale families: none

## Pullback Stage 0 Proof

Command:

```bash
make pullback-stage0-verify
```

Result:

- `status=passed`
- `read_only=True`
- `strategy=pullback_recovery`
- `session_strategy_id=pullback_recovery_default`
- `expected_commit=2953af16a`
- `blocking_checks=0`
- Latest JSON artifact:
  `.cbp_state/data/pullback_stage0_verification/pullback_stage0_verification.latest.json`
- Latest Markdown artifact:
  `.cbp_state/data/pullback_stage0_verification/pullback_stage0_verification.latest.md`

## Funding Extreme Stage 0 Proof

Command:

```bash
make funding-stage0-verify
```

Result:

- `status=failed`
- `read_only=True`
- `strategy=funding_extreme`
- `session_strategy_id=funding_extreme_default`
- `blocking_checks=1`
- Blocking check:
  `completed_session_expected_commit`, `expected=fd7f11e9c`,
  `actual=1920d13b0`
- Non-blocking supporting facts from the generated artifact:
  completed session exists after baseline; reconciliation passed; no critical
  error; session used `public_ohlcv_5m`; strategy context was `live_public`
  OKX `BTC/USDT:USDT`; signal was evaluated as `funding_neutral`; canonical
  fill count was unchanged (`before=176 after=176`).
- Latest JSON artifact:
  `.cbp_state/data/funding_stage0_verification/funding_stage0_verification.latest.json`
- Latest Markdown artifact:
  `.cbp_state/data/funding_stage0_verification/funding_stage0_verification.latest.md`

## Hetzner Access

Initial SSH attempts with users `baitus` and `ubuntu` were rejected by the
tailnet policy. The documented repo default is `cryptkeep@100.86.128.9`.

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && git rev-parse --short HEAD && git status --short'
```

Result:

- Tailscale SSH required browser re-authentication first.
- After authentication, the host returned remote short SHA `a10aca01`.

## Hetzner Paper Campaign

Command:

```bash
make status-paper-hetzner HETZNER_STATUS_TRANSPORT=ssh
```

Result:

- `all_running=true`
- `ema_cross_default`: running, `idle`, reason `waiting_for_next_day`
- Strategy: `ema_cross`
- Fills: `14`
- Closed trades: `7`
- PnL: `-2.2432`
- Latest fill: `2026-08-23T00:16:04.859215+00:00`
- Recommendation: `continue_paper_observation`

## Hetzner Crypto Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime HETZNER_STATUS_TRANSPORT=ssh
```

Result:

- `ok=true`
- `status=hetzner_crypto_edge_runtime_ready`
- `remote_branch=master`
- `remote_head=a10aca01fc37de181cc32d17a30e5d677050f901`
- `blocking_checks=0`

## Hetzner Edge Cadence

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
```

Result:

- `ok=true`
- Checked families: `funding`, `open_interest`, `basis`
- Missing families: none
- Stale families: none
- Funding/OI/basis capture timestamp: `2026-08-23T04:56:02+00:00`
- Observed age at check time: about `260.6` seconds
- Quote and order-book cadence checks were disabled by configuration.

## Remaining Risk

- This checkpoint is status evidence only. It does not close capped-live proof,
  launch readiness, deployment installation, backup/restore drill, secrets
  rotation, or audit-journal coverage requirements.
- Funding Stage 0 remains unaccepted as a proof until the expected-commit
  mismatch is resolved by an approved rerun or an explicit evidence decision.
- Future host proofs should use the documented target
  `cryptkeep@100.86.128.9`; other users are not authorized by the tailnet
  policy in this environment.
