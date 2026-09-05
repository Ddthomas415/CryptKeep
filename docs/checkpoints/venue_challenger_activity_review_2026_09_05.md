# Venue Challenger Activity Review

Date: 2026-09-05 UTC. Active role: AUDITOR. Environment: VERIFIED_ENV.

## Scope and Current Results

Read-only Hetzner checks completed at approximately `18:43-18:45 UTC` against
`/srv/cryptkeep/app` at `e38c342de9eb8209bdd7fdd44ca75cf757901fa2`.
The Tailscale identity check completed before the remote inspection ran.
Local comparison used the laptop-specific campaign manifest. The generic
manifest also references the Hetzner-owned EMA campaign and must not be used
to infer that this campaign needs starting on the laptop.

SHOWN from collector results:

| Campaign / host | Collector | Latest session | All-history fills / closed trades | Session change |
| --- | --- | --- | --- | --- |
| Binance EMA / Hetzner | Running, daily idle | Sep 5 completed | 0 / 0 | 0 fills |
| Gate.io EMA / Hetzner | Running, daily idle | Sep 5 completed | 0 / 0 | 0 fills |
| Coinbase EMA / Hetzner | Running, daily idle | Sep 5 completed | 18 / 9 | 1 fill, 1 closed trade |
| Coinbase ES / laptop | Running, daily idle | Sep 5 completed | 20 / 10 | Latest recorded fill July 9 |
| Coinbase breakout / laptop | Running, daily idle | Sep 5 completed | 24 / 12 | Latest recorded fill Sep 2 |

The Coinbase EMA session reported a net realized PnL change of
`2.1496924001243762`, bringing its all-history total to `-0.22661180559555527`.
These are recorded paper-accounting results, not comparable performance
rankings: the campaign histories, positions, and data coverage differ.
The canonical ES gate remains at **3/5 provenance-qualified round trips**;
the all-history counts above do not replace gate-qualified counts.

## Data and Session Findings

- SHOWN: Binance and Gate.io final runner statuses both report
  `signal_ok=true`, `signal_action=hold`, `signal_reason=no_cross`, and
  `enqueued_total=0`. This describes the latest runner status; it is not an
  assertion that every loop had the same reason.
- SHOWN: both evidence writers report `ok` and zero total write failures.
- SHOWN: Gate.io completed sessions on Sep 3, 4, and 5. Binance recorded four
  `no_public_ohlcv` failures across Sep 3-4, a stopped session on Sep 4, and a
  completed session on Sep 5. The prior failures remain historical evidence;
  the Sep 5 result supports the already-recorded recovery, not a new failure.
- SHOWN: each new venue's latest stored snapshot has 400 rows labeled
  `public_ohlcv`, with every adjacent timestamp exactly 300,000 ms apart.
  This establishes continuity of that stored window, not all-day uptime.
- SHOWN: Coinbase's stored snapshot has 248 rows and 40 adjacent intervals
  different from 300,000 ms. This check alone does not identify whether those
  gaps originate at the venue, normalization, or collection.

## Observation Schedule

All three Hetzner manifests configure `public_ohlcv_5m`, `runtime_sec=900`,
and `poll_interval_sec=300`. The collector's daily loop runs a strategy window
only while no completed session exists for the UTC day; after completion it
writes `waiting_for_next_day` status. The 300-second collector poll does not
mean that it starts a new strategy window every five minutes.

Actual Sep 5 strategy windows:

- Binance: `00:01:17.200083` to `00:16:24.818868 UTC`, 907.62 seconds.
- Gate.io: `00:04:50.029151` to `00:19:59.571394 UTC`, 909.54 seconds.
- Coinbase EMA: `00:03:46.285633` to `00:18:49.658523 UTC`, 903.37 seconds.

The nominal strategy runtime is 15 minutes per successful day, about **1.04%**
of 24 hours. Fetching hundreds of historical candles gives indicator history;
it does not execute historical signals. `signal_from_ohlcv` tests the last two
EMA values for a crossover. This is a sampling limitation of the configured
trial, not a claim that the collectors are crashed or misconfigured.

Source references: `scripts/run_paper_strategy_evidence_collector.py` daily
loop, `services/strategies/ema_cross.py`, and the three existing
`configs/paper_evidence_campaigns.hetzner*.json` manifests.

## Offline Snapshot Diagnostic

Copied the three existing snapshots to
`.cbp_state/data/research/venue_challenger_review/20260905/` and called the
repository's `signal_from_ohlcv` over increasing prefixes. No new market fetch,
order, evidence fill, campaign change, or store write was performed by replay.

Used `PRESETS['ema_cross_default']['strategy']`: fast/slow EMA 12/26, filter
window 8, volatility floor 0.20%, volume ratio 0.95, trend efficiency 0.15,
and crossover-gap floor 0.02%. This is a preset diagnostic; it does not prove
every historical runtime override resolved to these values. Prefixes started
at 28 rows; the final snapshot candle was excluded because it may have been
open at capture. Earlier prefixes have shorter warm-up histories than live
fetches. The venue windows also differ in length and continuity.

| Venue | Prefix evaluations | Raw crossovers | Volatility rejection | Volume rejection | Passing preset signals |
| --- | --- | --- | --- | --- | --- |
| Binance | 372 | 13 | 11 | 0 | 2 sells |
| Gate.io | 372 | 11 | 9 | 1 | 1 sell |
| Coinbase | 220 | 10 | 9 | 0 | 1 sell |

Binance passing signal candle opens were Sep 3 at `22:20 UTC` and Sep 4 at
`12:30 UTC`. Gate.io and Coinbase each passed at Sep 4 `12:30 UTC`. These
candle times fall outside the recorded daily windows. They are hypothetical
signal observations, not missed executable trades: replay does not reproduce
position, risk, intrabar path, warm-up, execution, or fill state. In particular,
there were **no passing buys** in these replay windows, and the new challengers
reported flat positions. Longer observation alone is therefore not proven to
produce additional round trips.

SHA-256 of copied snapshot files:

- Binance: `784123eab01f268276487ee7a135f2ed3e74554d2a0c76746fe2f8ae3acc3176`.
- Gate.io: `59c90b11e2a1d61a0964eafca1bc35b42519a2c2422c25c3299fb287b0619b6f`.
- Coinbase: `cb848d12d97de89a26f532b96048f312d779a9853602c1d34d46c3cbf25ee9cf`.

## Recommendation and Verification

Next research step: assess a longer isolated observation trial over aligned
venue windows, retaining the current preset filters. Measure evaluated closed
bars, raw crossovers, each rejection reason, allowed entries/exits, and actual
paper fills separately. This distinguishes low signal incidence from limited
observation and filter effects. Do not infer profitability or loosen filters
from this short sample. Keep the ES campaign and its gate unchanged.

Before changing cadence, review component ownership, request pacing, daily
rollover, and position continuity across strategy-window boundaries. This
checkpoint authorizes no runtime configuration or deployment change.

Verification: direct host status/session/snapshot inspection; laptop-manifest
status; offline replay using repository strategy functions; `git diff --check`.
No source code changed and no application test suite was rerun.

Acceptance state: ACCEPTED_WITH_RISK (bounded observational research;
longer-window efficacy and comparative strategy performance remain UNVERIFIED).
