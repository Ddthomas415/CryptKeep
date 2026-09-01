# Crypto-Edge OKX Market-ID Filter - 2026-09-01

Status: local research-only crypto-edge collection recovered after laptop
restart; OKX public market rows with missing IDs are filtered during exchange
open.

## Scope

- SHOWN: local paper campaigns remained `2/2` running after the laptop reset.
- SHOWN: local crypto-edge cadence was stale before recovery.
- SHOWN: sandboxed collector restart attempts failed with exchange network
  errors, so network behavior was verified outside the sandbox.
- SHOWN: unsandboxed OKX public exchange open failed inside
  `ccxt.okx.load_markets()` with a TypeError from sorting mixed `None` and
  string market IDs.
- SHOWN: the affected OKX response contained `4541` public market rows and
  `3` rows with `id=None`; filtering those rows allowed `set_markets()` and
  public funding/open-interest/basis reads to succeed.
- SHOWN: this checkpoint did not change paper campaigns, promotion gates,
  live routing, live execution, order submission, risk gates, strategy configs,
  or host services.

## Code Change

`services/analytics/crypto_edge_collector.py` now catches only the observed
CCXT OKX `load_markets()` TypeError shape containing `NoneType` and `str`.
For that specific read-only collector failure, it calls `fetch_markets()`,
drops market rows whose `id` is `None`, and initializes the exchange with
`set_markets()`.

Unrelated `TypeError` exceptions still raise. Venues without callable
`fetch_markets()` and `set_markets()` still raise.

## Runtime Proof

Commands:

```bash
./.venv/bin/python scripts/data/run_crypto_edge_collector_loop.py --plan-file sample_data/crypto_edges/live_collector_plan.json --interval-sec 300 --max-loops 1
./.venv/bin/python scripts/check_edge_cadence.py --json
make status-live-crypto-edges-loop
```

Result:

- SHOWN: the one-shot collector completed with `status=stopped`,
  `reason=max_loops`, `loops=1`, `writes=1`, and `errors=0`.
- SHOWN: the one-shot collector wrote OKX funding, OKX open interest, OKX
  basis, Coinbase/Kraken quotes, and Coinbase order-book rows.
- SHOWN: edge cadence reported `ok=true`, `missing=[]`, and `stale=[]`.
- SHOWN: funding, open-interest, and basis snapshots were fresh at
  `2026-09-01T05:13:01+00:00`.
- SHOWN: the persistent local crypto-edge collector loop is running with
  `pid_alive=true`, `loops=1`, `writes=1`, and `errors=0`.

## Verification

```bash
./.venv/bin/python -m pytest -q tests/test_crypto_edge_collector.py tests/test_run_crypto_edge_collector_loop.py tests/test_edge_cadence.py tests/test_collect_live_crypto_edge_snapshot.py tests/test_crypto_edge_collector_service.py
git diff --check
```

Result:

- SHOWN: `30 passed`.
- SHOWN: `git diff --check` returned no output.

## Remaining Risk

- MEDIUM/HIGH operational: the changed path opens a read-only background
  research collector and affects funding/open-interest/basis capture cadence.
- The change does not approve OKX for live routing, derivatives execution,
  strategy promotion evidence, or live trading.
- Host-side Hetzner status was not verified in this checkpoint because
  Tailscale SSH required an interactive auth check.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
