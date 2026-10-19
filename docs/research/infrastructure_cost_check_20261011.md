# Infrastructure cost check - 2026-10-11 (report only; nothing changed)

Claude (cloud session), at Damian's request after strategy_decision_report_20261011.md found no candidate that pays
for ~$240/year. Sources: repo docs/work log only. The live Hetzner host was NOT inspected (SSH needs Damian's Mac /
Tailscale), and no invoice was seen, so cost figures are the operator's estimates.

## What is known about the cost
- 2026-10-02 the operator gave "under $10/month"; 2026-10-08 "approximately $20/month" (platform total, not invoice-
  verified). The repo does not record the Hetzner server type or what else (if anything) the $20 includes.

## What runs where (last recorded state)
| Where | Job | Needed by the one remaining candidate (BTC+ETH 28d trend)? |
|---|---|---|
| Laptop | Weekly BTC+ETH paper test (scheduled task, Mon 00:47 UTC) - recomputes from public Coinbase prices | YES - and needs no server |
| Laptop | Daily CMC trending log (scheduled task 13:52 UTC) | No (CMC study, blocked until Feb 2027) |
| Laptop | ES SMA-200 paper collector (restarted 10-09) | No (ES trial ends 2026-10-13) |
| Laptop | Coinbase USD confirmation study hourly backfills; market-context collector (restarted 10-11 by Codex) | No |
| Hetzner | crypto-edge collector, 5-min: OKX BTC funding/basis/open interest, Coinbase+Kraken BTC quotes and Coinbase order book (since 2026-07-18; healthy at 10-08 check) | No |
| Hetzner | Paper campaign (ema_cross_default, last recorded 09-01: 8 closed trades, net -$2.32) and proposed Gate.io/Binance challengers | No |
Funding/basis research (2026-09-01) found no actionable candidate; the funding_extreme campaign decision is still open.

## Options for Damian
1. Keep everything (status quo): ~$240/yr buys continued BTC context data with no strategy currently using it.
2. Pause the Hetzner server, keeping a snapshot/backup of /var/lib/cbp first: saves most of the cost. Loss: the
   continuous 5-minute quote/order-book history cannot be backfilled later (funding history partly can, from OKX).
   The remaining candidate is unaffected.
3. Downsize to the cheapest server that runs only the crypto-edge collector: keeps the data, cuts part of the cost.
Before choosing: confirm the real monthly bill and what it covers. Any stop/backup/downsize needs explicit approval
and is an operational step on the host, not code.

## Superseded in part (added 2026-10-11, after Codex's live inventory)
`server_workload_inventory_20261011.md` (read-only SSH observations 22:29-22:30 UTC, ACCEPTED_WITH_RISK) replaces the "What runs where" table above, which came from repo records only.

Corrections:
- **Corrected ES prospective trial:** runs on Hetzner, with its Oct 13 endpoint timer there. It is not on the laptop.
- **Gate.io and Binance daily paper collectors:** running on Hetzner as detached processes. They are not just "proposed".
- **Backups:** the only visible backups on the server date from June 20. Off-host backup and restore coverage is unverified.

The options above remain, but none is decision-ready until a verified off-host backup exists.
