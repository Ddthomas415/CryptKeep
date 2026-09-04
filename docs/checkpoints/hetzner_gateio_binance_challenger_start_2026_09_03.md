# Hetzner Gate.io/Binance Isolated Challenger Start Proof

Date: 2026-09-03

Status: ACCEPTED_WITH_RISK host-side proof record.

## Scope

This record captures the host-side Git pull-auth fix, repository sync, and
isolated paper/research challenger starts for Gate.io and Binance on Hetzner.

This did not restart existing services, change live routing, add exchange
credentials, submit orders, modify canonical `.cbp_state`, or count evidence
toward the canonical `es_daily_trend_v1` promotion gate.

## Hetzner Pull Auth

Approved operator text:

```text
I approve provisioning a read-only GitHub deploy key on Hetzner for
/srv/cryptkeep/app pulls, adding the public key to Ddthomas415/CryptKeep
without write access, switching the Hetzner repo remote to SSH, and
fast-forwarding the checkout with no service restart.
```

SHOWN:

- Hetzner checkout user: `cryptkeep`.
- Previous remote: `https://github.com/Ddthomas415/CryptKeep.git`.
- Existing deploy key: absent before provisioning.
- New host key fingerprint:
  `SHA256:CWCOSIlJzVIGs4mf7VRGcC7KzBjYw9x52cA/iDdKLVI`.
- GitHub deploy key list reported key id `162142842`, title
  `cryptkeep-hetzner-readonly-ubuntu-4gb-nbg1-3-2026-09-03`, access
  `read-only`.
- GitHub SSH host-key verification matched GitHub's published Ed25519
  fingerprint:
  `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`.
- Hetzner repo remote changed to:
  `git@github.com:Ddthomas415/CryptKeep.git`.
- Hetzner `git fetch origin master` and `git merge --ff-only origin/master`
  succeeded over the read-only SSH deploy key.
- Hetzner checkout fast-forwarded to `02b512af`.

## Venue OHLCV Preflights

Gate.io direct Hetzner preflight:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_ohlcv_preflight.py --venue gateio --symbol BTC/USDT --signal-source public_ohlcv_5m --json'
```

SHOWN:

- `status=ok`
- `reason=public_ohlcv_reachable`
- `row_count=5`

Binance direct Hetzner preflight:

```bash
ssh -o BatchMode=yes cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_VENUE=binance CBP_ALLOW_BINANCE=1 ./.venv/bin/python scripts/check_ohlcv_preflight.py --venue binance --symbol BTC/USDT --signal-source public_ohlcv_5m --json'
```

SHOWN:

- `status=ok`
- `reason=public_ohlcv_reachable`
- `row_count=5`

## Gate.io Challenger Start

Command:

```bash
make restore-hetzner-gateio-challenger
```

SHOWN restore result:

- `ok=true`
- `action=restore`
- `running_count=1`
- campaign: `ema_cross_gateio_btcusdt_paper_candidate`
- venue: `gateio`
- symbol: `BTC/USDT`
- signal source: `public_ohlcv_5m`
- state dir:
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_gateio_btcusdt_daily`
- preflight: `public_ohlcv_reachable`, `row_count=400`
- launched PID: `1499165`

SHOWN status after start:

- `Campaigns: 1/1 running`
- `ema_cross_gateio_btcusdt_paper_candidate: running`
- reason: `collecting`
- fills: `0`
- closed: `0`

## Binance Challenger Start

Command:

```bash
make restore-hetzner-binance-challenger
```

SHOWN restore result:

- `ok=true`
- `action=restore`
- `running_count=1`
- campaign: `ema_cross_binance_btcusdt_paper_candidate`
- venue: `binance`
- symbol: `BTC/USDT`
- signal source: `public_ohlcv_5m`
- state dir:
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_binance_btcusdt_daily`
- preflight: `public_ohlcv_reachable`, `row_count=400`
- launched PID: `1499247`

SHOWN status after start:

- `Campaigns: 1/1 running`
- `ema_cross_binance_btcusdt_paper_candidate: running`
- reason: `collecting`
- fills: `0`
- closed: `0`

## Boundaries

- These are isolated paper/research challengers only.
- Their state is under `.cbp_state_challengers`.
- Their evidence must not count toward the canonical `es_daily_trend_v1`
  promotion gate.
- No live trading, live routing, exchange credential, order submission, or
  canonical campaign behavior changed.
- Existing Hetzner `ema_cross_default` remains separately owned by
  `configs/paper_evidence_campaigns.hetzner.example.json`.

## Next Checks

- Continue daily status checks for both isolated challengers.
- Inspect each challenger after its first completed day to confirm evidence
  files and `last_completed_day` advance.
- Keep Binance behind `CBP_VENUE=binance CBP_ALLOW_BINANCE=1` for guarded
  operations.
