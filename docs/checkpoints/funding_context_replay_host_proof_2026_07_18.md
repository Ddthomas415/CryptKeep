# Funding Context Replay Host Proof - 2026-07-18

Active role: ENGINEER

## Scope

This is a read-only research proof for `funding_extreme` signal replay over
stored crypto-edge funding snapshots on Hetzner.

This proof is not:

- PnL evidence;
- expectancy evidence;
- promotion evidence;
- approval for a persistent `funding_extreme` campaign;
- approval for live trading, derivatives execution, or order routing.

## Environment

SHOWN:

- Local `master` and `origin/master` were aligned at
  `5bfece3267987fab35f669958204793beac84300`.
- Hetzner `/srv/cryptkeep/app` was fast-forwarded to
  `5bfece3267987fab35f669958204793beac84300`.
- The replay was run as the `cbp` service user with
  `CBP_STATE_DIR=/var/lib/cbp`.

## Command

```bash
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/research/run_funding_context_replay.py \
  --limit 50 \
  --min-rows 1 \
  --output /var/lib/cbp/data/funding_context_replay/funding_context_replay.latest.json
```

## Result

SHOWN:

- `ok=true`
- `reason=ok`
- `artifact_type=funding_context_signal_replay_v1`
- `research_only=true`
- `row_count=16`
- `dataset_hash=84eda056e7db868e01b44fcc7bc05322cfa37675ae14d1035212f588b6f54b9c`
- `first_capture_ts=2026-07-18T20:25:49Z`
- `last_capture_ts=2026-07-18T21:42:50Z`
- `action_counts={"hold": 16}`
- `reason_counts={"funding_neutral": 16}`
- Artifact written:
  `/var/lib/cbp/data/funding_context_replay/funding_context_replay.latest.json`

The replay shows the stored OKX funding context can drive deterministic
`funding_extreme` signal artifacts. It also shows the current captured funding
levels were neutral under the configured/default thresholds.

## Runtime Health

SHOWN:

- `make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=20 HETZNER_EDGE_EXPECTED_COMMIT=5bfece326`
  reported `hetzner_crypto_edge_runtime_ready`, `ok=True`, and
  `blocking_checks=0`.
- `CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json`
  reported `ok=true`, `missing=[]`, and `stale=[]`.
- Fresh cadence timestamps were present for funding, open-interest, and basis:
  `2026-07-18T21:48:01+00:00`.
- `make status-paper-hetzner HETZNER_STATUS_TIMEOUT_SEC=30` reported
  `ema_cross_default` running/idle and waiting for the next UTC day.

## Remaining Work

- A price-joined context walk-forward is still required before any
  `funding_extreme` expectancy or persistent campaign decision.
- Continue host crypto-edge collection so the funding replay gains enough
  history to show actual threshold crossings, if they occur.
