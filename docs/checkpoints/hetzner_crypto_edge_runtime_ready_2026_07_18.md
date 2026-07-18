# Hetzner Crypto-Edge Runtime Ready — 2026-07-18

Active role: ENGINEER

Objective: record the completed host-side proof for scheduled read-only
crypto-edge collection on Hetzner.

## Boundary

- Host: `cryptkeep@100.86.128.9` / `root@100.86.128.9` over Tailscale SSH.
- App directory: `/srv/cryptkeep/app`.
- Remote commit: `370c8122deff6c33bf8d846d7937c98fc66c0c59`.
- State directory: `/var/lib/cbp`.
- Enabled units:
  - `cbp-crypto-edge-collector.service`
  - `cbp-edge-cadence.timer`
- Not enabled by this proof:
  - live trading arming
  - live intent consumer
  - live reconciler
  - dashboard
  - generic collector

## SHOWN

- PR #345 merged and synced to Hetzner before host bootstrap:
  - `fix: align hetzner crypto-edge runtime state dir`
  - remote state probing now uses `CBP_STATE_DIR=/var/lib/cbp`
- PR #346 merged and synced to Hetzner before final collector restart:
  - `fix: persist all crypto edge collector families`
  - `collect_once()` now persists `open_interest_rows` and `order_book_rows`
- Host bootstrap was executed after explicit operator approval:
  - created/verified `cbp` service identity
  - created `/var/lib/cbp`
  - created `/etc/cbp/cbp.env`
  - installed rendered systemd unit files
  - enabled/started only the read-only crypto-edge collector and cadence timer
- Runtime readiness after PR #346 sync/restart:
  - command: `make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=20 HETZNER_EDGE_EXPECTED_COMMIT=370c8122d`
  - status: `hetzner_crypto_edge_runtime_ready`
  - `ok=True`
  - `blocking_checks=0`
- Collector status after restart:
  - command: `CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/data/run_crypto_edge_collector_loop.py --status`
  - `status=running`
  - `pid_alive=true`
  - `writes=1`
  - `errors=0`
  - `last_reason=collected`
  - `execution_enabled=false`
  - `research_only=true`
- Fresh OKX snapshot evidence:
  - funding snapshot: `funding-1a71d9f1b1ef`
  - open-interest snapshot: `open-interest-802844860b66`
  - basis snapshot: `basis-500bb528b46d`
  - shared capture timestamp: `2026-07-18T21:16:48+00:00`
  - source: `live_public`
- Cadence check after PR #346 sync/restart:
  - command: `CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json`
  - `ok=true`
  - checked families: `funding`, `open_interest`, `basis`
  - `missing=[]`
  - `stale=[]`
  - exit code: `0`
- Paper campaign status after the read-only collector restart:
  - command: `make status-paper-hetzner HETZNER_STATUS_TIMEOUT_SEC=30`
  - campaigns: `1/1 running`
  - `ema_cross_default`: `idle`, `waiting_for_next_day`
  - `fills=8`
  - `closed=4`
  - `pnl=-2.2667`
  - latest fill: `2026-07-14T00:05:03.287310+00:00`

## Resolved Gap

The earlier `docs/checkpoints/hetzner_crypto_edge_runtime_gap_2026_07_18.md`
gap is resolved for the read-only crypto-edge runtime substrate:

- checkout/tooling/plan are current;
- the collector is supervised by systemd;
- the cadence timer is installed and active;
- funding/open-interest/basis are persisted from OKX under `/var/lib/cbp`;
- the cadence checker passes against stored live-public evidence.

## Remaining Boundaries

- This proof does not authorize live trading, live routing, live intent
  consumption, derivatives execution, or paper promotion from crypto-edge rows.
- The cadence timer is alert-only and does not auto-stop or auto-start trading.
- Continue monitoring the collector through `make status-hetzner-edge-runtime`
  and host `systemctl status cbp-crypto-edge-collector.service
  cbp-edge-cadence.timer`.

## Acceptance State

ACCEPTED_WITH_RISK
