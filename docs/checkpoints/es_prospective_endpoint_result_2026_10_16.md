# Corrected ES trial endpoint: observed result

Active role: AUDITOR. Observed October16 04:48 UTC (00:48 New York).
Endpoint-report review: ACCEPTED_WITH_RISK by separate Helmholtz GATE.
Trading efficacy: INCOMPLETE because no trades occurred.
Original October13 report template and trial records remain unchanged.

## Result First

The fixed September13-October13 trial finished with no orders, fills or positions.
Paper cash remains10000 USDT; fill-derived trading PnL and fees are zero.
This is neither evidence of profitable trading nor evidence that the strategy
loses when it trades. It is a zero-exposure, insufficient-trading-sample result.
No reset, forced entry, extension, deployment or promotion follows.

## SHOWN On The Actual Host

Read-only SSH accessed only the isolated
`/srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1` trial.
SQLite connections used mode=ro and a coherent read transaction per database;
no runtime modules were imported for accounting extraction.

| Measurement | Observed result |
| --- | --- |
| Required daily sessions, September13 through October12 | 30 files; each has two session records and a completed end record |
| Missing required session files | 0 |
| Trial-window signal records | 448 long; all kernel_action null |
| Pre-trial signals retained but excluded | 8 |
| Signals after September21 01:27:11 capture activation | 331 captured; verifier331 selected/331 verified, no problems, exit0 |
| Earlier trial-window signals | 117; not certified by the capture-window replay |
| Intents / orders / fills / journal fills / positions | 0 / 0 / 0 / 0 / 0, all-history trial-store counts |
| Paper cash | 10000 USDT |
| Trial-window equity observations | 714; every recorded cash and equity value10000, realized/unrealized PnL0 |
| Last equity mark | October12 00:02:14 UTC; no invented endpoint mark |
| Observed marked drawdown | 0 with no exposure; not risk-management efficacy |
| Current service state | inactive/dead; MainPID0 |
| Deadline stop service | success, exit0; start and exit October13 00:00:00 UTC |
| Seed config SHA256 | 81accfe4d0acf86d7bcc11c771899c977c3c04893f9093500b073a535e92a1f8, matching launch |

Current deployed runner, paper engine and verifier hashes also match the October7
checkpoint. This is present identity evidence, not proof of every historical
child's resolved memory. Signal logs are operational observations, not orders.
Session booleans such as kill_switch_tested are reported flags, not independent
proof of a kill-switch or recovery drill. No claim of orphan-process absence.

The service properties corroborate the deadline-stop journal inspected October15.
No service restart or stop was performed during these checks. Separate database
transactions are not a cross-database atomic snapshot, although all inspected
execution tables are empty and the trial service is inactive.

## Economics And Limits

- Paper trading PnL:0 USDT; cash comparator0 USDT. No actual user profit.
- Buy-and-hold comparator: UNVERIFIED. The required original endpoint price
  has not been established; the last October12 signal is not an October13
  endpoint price. Do not substitute a later finalized candle or stale mark.
- Infrastructure: operator estimate approximately20 USD/month, not an invoice.
  Under full30-day allocation this trial has20 USD estimated expense and zero
  trading contribution. The cost is shared with other workloads; do not charge
  it again elsewhere or silently equate nonzero USD and USDT amounts.
- Zero fills make duplicate-fill matching vacuous; they do not validate execution,
  fee/slippage mechanics, reconciliation under activity or capital readiness.
- Thirty completed daily samples do not establish continuous market recording.
  Earlier signals remain non-replayable; actual endpoint price and comprehensive
  historical config enforcement remain UNVERIFIED.

Recommendation: close this fixed trial as economically INCOMPLETE. Preserve the
crossover rule and evidence; do not automatically extend or launch another cohort.
This conclusion does not narrow the multi-symbol project or reject other symbols.
The broader continue/revise/retire investment decision is not made by this report.

## Evidence

`docs/checkpoints/es_endpoint_20261016_host_evidence.json` preserves the host
query output, all30 session end records, source-file hashes, accounting counts,
service properties and replay stdout/exit status. SHA256:
`bd57291f0e00b5361d8ed63fb937f4131a97a958ef00116d5fad5706129a3027`.

The existing host verifier ran with PYTHONDONTWRITEBYTECODE=1 / Python -B,
state-dir as above, since2026-09-21T01:27:11Z, until2026-10-13T00:00:00Z.
No private credentials/account access, remote writes or campaign changes.
Separate Helmholtz GATE accepted faithful reporting of the saved evidence with
risk; deterministic JSON assertions and the evidence hash passed, no blockers.
This is not a second host inspection or trading-efficacy acceptance. Nine daily
zero_trade_run flags were false; empty execution-table counts, not those flags,
support the zero-trade result. Original template remains a historical plan.
