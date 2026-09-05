# Hetzner Binance Challenger Recovery Proof

Date: 2026-09-05 UTC

Status: ACCEPTED_WITH_RISK host-side proof record.

## Scope

This record captures the post-merge Hetzner recovery of the isolated Binance
paper/research challenger after two fixes:

- `d79cb972` passed the configured Binance venue into managed paper child
  processes so the existing Binance guard sees `CBP_VENUE=binance`.
- `620ecbdf` allowed a stopped/exhausted collector to receive one audited
  same-day recovery attempt after a successful OHLCV preflight.

This did not restart unrelated services, change live routing, add exchange
credentials, submit orders, modify canonical `.cbp_state`, or count evidence
toward the canonical `es_daily_trend_v1` promotion gate.

## Repository Sync

Command shape:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && GIT_SSH_COMMAND="ssh -i ~/.ssh/cryptkeep_github_readonly -o IdentitiesOnly=yes" git fetch origin master && GIT_SSH_COMMAND="ssh -i ~/.ssh/cryptkeep_github_readonly -o IdentitiesOnly=yes" git merge --ff-only origin/master && git rev-parse --short HEAD'
```

SHOWN:

- Hetzner checkout fast-forwarded from `d79cb972` to `620ecbdf`.
- No service restart was performed.

## Recovery Command

Command:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_VENUE=binance CBP_ALLOW_BINANCE=1 ./.venv/bin/python scripts/restore_paper_campaigns.py --config configs/paper_evidence_campaigns.hetzner.binance_challenger.json --restore --preflight-ohlcv --restart-unhealthy --ohlcv-preflight-attempts 3 --ohlcv-preflight-attempt-delay-sec 2'
```

SHOWN:

- `ok=true`
- `all_running=true`
- `running_count=1`
- `action=already_running`
- campaign: `ema_cross_binance_btcusdt_paper_candidate`
- venue: `binance`
- symbol: `BTC/USDT`
- signal source: `public_ohlcv_5m`
- state dir:
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_binance_btcusdt_daily`
- PID: `1501788`
- status: `idle`
- reason: `waiting_for_next_day`
- last completed day: `2026-09-05`

## Completed Session Evidence

SHOWN from the same status payload:

- The challenger completed a 900 second session before returning to daily idle.
- `started_ts=2026-09-05T00:01:17.200083+00:00`
- `ended_ts=2026-09-05T00:16:24.818868+00:00`
- `runtime_sec=907.619550704956`
- `runner_status=stopped`
- `stop_reason=runtime_elapsed`
- `signal_action=hold`
- `fills_delta=0`
- `closed_trades_delta=0`
- `reason=completed`

## Boundaries

- This is an isolated paper/research challenger only.
- State remains under `.cbp_state_challengers`.
- The completed session is not canonical `es_daily_trend_v1` promotion evidence.
- No live trading, live routing, exchange credential, order submission, or
  canonical campaign behavior changed.
- Zero fills means this is a venue/session recovery proof, not a strategy
  performance proof.

## Next Checks

- Continue daily status checks for the isolated Binance challenger.
- Inspect future sessions for first fill/closed trade evidence.
- Keep Binance behind `CBP_VENUE=binance CBP_ALLOW_BINANCE=1` for guarded
  operations.
