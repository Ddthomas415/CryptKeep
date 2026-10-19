# E03 decision brief - 2026-10-04

AUDITOR (Claude). An input for the GATE, not the gate decision: E03 is the
operator's, and the roadmap requires independent review before it is taken.
Read-only arithmetic on figures already on record; no new backtest, data,
campaign, config or account change. Not a profitability finding and not
financial advice; I am not a financial adviser.

## The question

Roadmap E03: "Explicit continue/revise/retire decision with costs and risks;
no parameter rescue on same holdout, automatic promotion or capital
increase." Candidate: daily SMA200 trend on BTC/USD (`es_daily_trend_v1`),
0.001 BTC per entry (about 84.5 USD at the 2026-10-03 quote).

## What is on record (sources in brackets)

| Fact | Figure | Class |
|---|---|---|
| Paper results since cohort start | 3 round trips, all losses; -5.94 USD at the verified taker fee | SHOWN [E01 A9, item 38] |
| Those 3 trades' exit rule | a trailing stop the strategy no longer has | SHOWN [E01 finding 12] |
| Modelled net at today's size | 0.57 to 2.84 USD a month (6.8 to 34 a year) | MODELLED [E01 A9, item 40] |
| Modelled edge rests on | one winner in three years; an unrealised position in the recent year | MODELLED [E01 A9, item 39] |
| Infrastructure | "under 10 USD a month" (operator, a range not a bill) | CLAIMED |
| Entry rate | 3.86 round trips a year; median 154 days to the next entry | MODELLED [E01 A11] |
| Paper gate | 3 of 5 qualified; two more took a median of 245 days in the history | MODELLED [E01 A11] |
| Context comparison (E02) | zero candidate entries with recorded context | SHOWN [e02 note] |
| Faster candidate (FC-01 draft) | 3 usable entries as written; fee load about 190% of notional a year | SHOWN / arithmetic [fc01 note] |

## The arithmetic that decides it

1. Waiting costs more than the candidate is modelled to earn. At 5 to 10 USD
   a month, a year of observation costs 60 to 120 USD. The modelled net at
   today's size is 6.8 to 34 USD a year. Expected position after a year of
   "continue as is": **about -26 to -113 USD**, on the candidate's own
   favourable model, before any actual loss.
2. More evidence will not arrive soon. Two more gate trades: median about 8
   months. A context comparison: years. So "continue" buys little information
   per dollar.
3. Size is what the fixed cost is measured against, not the strategy. On the
   modelled figures the entry size that merely covers 10 USD a month is
   about 300 USD (three-year sample) to about 1,490 USD (recent year)
   [E01 A9, item 40]. No actual trade supports increasing size, and E03
   itself forbids a capital increase as a rescue.

## Options

| Option | What it means | Cost per year | What you learn | Main risk |
|---|---|---|---|---|
| A. Continue as is | keep the paid host observing this candidate | 60 to 120 USD | about 4 modelled round trips | paying more than the modelled return; slow evidence |
| B. Continue at near-zero cost | keep the candidate, stop paying a 24/7 host to watch a once-a-day signal (for example evaluate it daily on a machine already running) | near 0, if the host has no other job | the same about 4 round trips | operational: a missed daily run; needs its own small design and review |
| C. Shelve | stop observing; keep code, history and evidence intact; no retirement of anything | 0 for this candidate | nothing new | none financial; the gate count stops |
| D. Revise | register a NEW candidate with new untouched data | depends | depends on the candidate | E02/FC-01 show the current data cannot test one quickly; fee load rules out frequent taker trading |

## Recommendation (mine; the operator decides)

- **Not A.** It has a negative expected result on its own model and buys
  little evidence.
- **B if the host exists only for this candidate, otherwise C.** Both stop
  the loss from waiting. B keeps the evidence clock running at no cost; it
  is only worth doing if moving the daily evaluation is simple, because an
  unreliable observer produces evidence nobody can use.
- **Do not increase size.** Nothing actual supports it.
- **D only as a separately registered question**, and only for a design that
  survives the fee arithmetic before any data is collected: it trades rarely,
  or is built around resting orders with a fill-risk model, or uses a venue
  with verified lower fees.
- **FC-01:** stop as drafted (see the fc01 note, items 5-8).

The Hetzner isolated trial's fixed end is 2026-10-13 00:00 UTC (work log).
That date is the natural point to apply whichever option is chosen; ending
it early or extending it is a campaign change and is not proposed here.

## What I could not verify

- The actual infrastructure bill, and whether the Hetzner host does anything
  besides observe this candidate. Option B versus C turns on that.
- Anything on the Hetzner host: its state, fills and config were not read.
- The modelled figures' underlying simulations, which were not rerun.
- Whether the account's fee tier is unchanged since 2026-09-26.

## What would change this brief

A net-winning actual trade at real fees; a verified infrastructure cost well
below 2 USD a month; or a verified fee tier materially below 50 bps taker.

## Addendum - CORRECTION: the host is shared, so the cost framing above is wrong for option A (same day)

Read-only, from the repository's own records. I asked the operator whether
the Hetzner host does anything besides this candidate's trial; the record
answers it, and I should have read it before writing the brief.

13. SHOWN (work log, "2026-09-28 UTC - Post-update paper collector health
    and uptake path", a read-only host inspection by the AUDITOR): three
    collectors run on the host, each with its own state directory:
    - `ema_cross` on Gate.io BTC/USDT (PID 1541537 at that time),
    - `ema_cross` on Binance BTC/USDT (PID 1541539),
    - the corrected ES trial, `sma_200_trend` on Coinbase BTC/USDT.
    All three are once-a-day sessions (idle, waiting_for_next_day). That is
    the last host inspection on record; nothing later is verified, and I
    cannot reach the host.
14. SHOWN (same entries, 2026-09-19 and 2026-09-28): all three completed
    their daily sessions with zero new intents, fills or closes. The venue
    challengers reported HOLD; the ES trial BUY with no order (the
    transition-only entry latch, diagnosed 2026-09-28).
15. SHOWN (`docs/HETZNER_PAPER_HOST.md`, Purpose): the host exists "to
    improve paper-campaign uptime". So the laptop was moved away from for a
    reason.

What this corrects in the brief above

- Item 1 and option A charged the whole infrastructure cost (60 to 120 USD a
  year) to the SMA200 candidate. That is right only if the host would be
  switched off without it. With two other collectors on the same host, the
  candidate's MARGINAL cost of being observed is close to zero while the
  host stays up. "Continue as is: about -26 to -113 USD a year" is therefore
  WITHDRAWN as a statement about this candidate alone.
- Option B (move the daily evaluation to a machine already running) is
  weaker than I presented: the host was adopted because laptop uptime was
  the problem. I withdraw B as a preferred option.
- The modelled-return figures, the entry rate, the gate timing and the "do
  not increase size" point are unchanged.

What the decision actually is

The unit that costs money is the host, not one candidate. The question for
the operator is whether the three collectors TOGETHER produce
decision-relevant evidence worth the host's cost:

| On record through 2026-09-28 | |
|---|---|
| Collectors on the host | 3 |
| Fills produced by them since 2026-09-12 | 0 (CLAIMED from the work log) |
| SMA200 trial fixed end | 2026-10-13 00:00 UTC |
| Host cost | "under 10 USD a month" for all infrastructure (CLAIMED, a range, not a bill) |

Revised recommendation (mine; the operator decides)

1. For the SMA200 candidate alone: let the trial run to its fixed end on
   2026-10-13 as approved. It costs nothing extra while the host is up, and
   ending it early would be a campaign change. Do not increase size. Do not
   extend it as a rescue.
2. At 2026-10-13, review the HOST, not the candidate: for each of the three
   collectors, the fills and closes actually produced, against the verified
   bill. If none has produced a fill, the honest statement is that the host
   is buying uptime for campaigns that are not trading, and the choice is
   between keeping it as cheap standby and switching it off until a
   candidate exists that trades.
3. Two inputs are needed for that review and neither is in the repository:
   the actual monthly bill, and a current read-only inspection of the three
   state directories on the host.

Limits: everything about the host here is from work-log entries dated
2026-09-19 and 2026-09-28; the EMA challengers' economics were not examined.

## Addendum 2 - the two EMA challengers on the host, examined (same day)

Read-only: configuration, code and one existing artifact. No return was
computed here; the net figures quoted are the artifact's own. No host access.

16. SHOWN (`configs/paper_evidence_campaigns.hetzner.gateio_challenger.json`
    and the Binance twin): each challenger is `ema_cross` on BTC/USDT with
    `signal_source: public_ohlcv_5m`, `runtime_sec: 900`,
    `poll_interval_sec: 300`. It looks at the market for about fifteen
    minutes once a day (work log: sessions start about 00:04 UTC), three or
    four five-minute bars out of 288.
17. SHOWN (`services/strategies/ema_cross.py::signal_from_ohlcv`, master):
    the signal is a cross between the last two bars. A cross that happened
    an hour before the session is "no_cross" when the session looks. So a
    challenger can only enter on a cross that lands on one of the few bars
    it evaluates.
18. SHOWN (existing artifact
    `.cbp_state/data/research/frozen_comparison_20260926`, Coinbase BTC/USD
    five-minute bars, 2026-08-26 to 2026-09-26, 8,740 bars): raw EMA 12/26
    up-crosses 169 in 30.0 days, 5.6 a day; 5 of the 169 fall on bars
    starting 00:00 to 00:19 UTC. With the preset's filters the artifact
    records ONE entry in the 30 days (2026-09-15 17:35 UTC), evaluated
    continuously.
19. Arithmetic. Evaluated continuously, the filtered rule entered about once
    a month. A session that sees about 1.4% to 3% of the day would catch
    such an entry about once every three to six years per challenger. Zero
    fills since launch is therefore the expected outcome of the
    configuration, not a sign of a fault and not evidence about the
    strategy.
20. For reference, the same artifact's own results for `ema_cross_default`
    evaluated continuously (signal-only, $100 entry, exploratory, no
    holdout): 1 closed trade, a loss, net -1.82 / -2.12 / -2.81 USD at
    10 / 25 / 60 bps per side, against buy-and-hold +6.10 / +5.79 / +5.07.
    One trade is not a sample.

Reading for the 2026-10-13 host review

- As configured, the three collectors on the host can be expected to
  produce, between them, about four SMA200 round trips a year and
  essentially no EMA entries. The host is reliable at running sessions that,
  by construction, almost never trade.
- That is a design property of the challengers (a once-a-day fifteen-minute
  look at a five-minute crossover), not a tuning problem. Changing the
  session length or the entry rule would be a new, separately reviewed
  campaign; it is NOT proposed here, and E03 forbids rescuing a candidate by
  changing parameters.
- So the host review has a clear question: is uptime for these three
  sessions worth the bill, given what they can produce? On this record the
  answer the evidence supports is "not for evidence generation"; whether to
  keep the host as cheap standby is the operator's call.

Assumptions and limits: Coinbase BTC/USD bars stand in for Gate.io and
Binance BTC/USDT; the challengers are assumed to run the default preset's
filters; the once-a-month rate rests on a single filtered entry in one
30-day window, so "three to six years" is an order of magnitude, not an
estimate. Session start time is from the work log, not from the host.

## Addendum 3 - CORRECTION: the host also runs a context collector, and the laptop archive is the weaker copy (same day)

Read-only, from repository records. Found while looking at why two laptop
collectors died unnoticed for sixteen hours.

21. SHOWN (`docs/checkpoints/hetzner_crypto_edge_runtime_ready_2026_07_18.md`):
    on 2026-07-18, after operator approval, the Hetzner host was given
    `cbp-crypto-edge-collector.service` and `cbp-edge-cadence.timer` under
    systemd, state directory `/var/lib/cbp`, read-only research collection
    (OKX funding, open interest, basis; PR #346 "persist all crypto edge
    collector families" added open-interest and order-book rows).
22. SHOWN (work log, "2026-09-01T05:40:21Z - Hetzner Read-Only Status
    Checkpoint"): on 2026-09-01 the service was active/running, the cadence
    timer active/waiting, and cadence fresh for OKX funding, open interest
    and basis. That is the last inspection of it on record.
23. SHOWN (laptop archive, read-only, today): the laptop's own context
    collector is a plain background process with no supervisor. Its OKX
    funding series since 2026-07-11 has 330 gaps longer than an hour,
    totalling about 975 of 2,042 hours: **48% of the period is missing.**
    Since 2026-08-30: 54 such gaps, about 141 hours, the longest 23 hours;
    43 of the 54 last one to two hours, the pattern of a laptop sleeping.

What this corrects

- Addendum 2 said the host runs three collectors that "almost never trade"
  and that it is "not worth its bill for evidence generation". The first
  part stands. The conclusion does not: the host has a fourth job, the only
  supervised, monitored context collection the project has. Context data
  cannot be backfilled, so that job has value the three paper sessions do
  not. I WITHDRAW "not for evidence generation".
- Every context analysis today (my E02 feasibility note, my FC-01 counts,
  Codex's FC-01-r1 pilot) used the LAPTOP archive. None used the host's.

What is NOT known (and decides how much this matters)

- Whether the host collector has kept running since 2026-09-01.
- Whether its plan includes the Coinbase BTC/USD order book and quotes that
  FC-01 used, or only the OKX derivative series (the 2026-07-18 proof names
  only OKX snapshots; the 2026-07-18 gap note says the host's plan was then
  still an older one).
- How continuous it is. A systemd service with a cadence timer should be far
  better than 48% missing, but that is an expectation, not a measurement.

Consequences, stated carefully

- E02 feasibility note, finding 2 ("zero candidate entries with recorded
  context") is true of the laptop archive. The SMA200 entry of 2026-08-20
  fell in a LAPTOP gap; the host may have recorded that day. The note's
  conclusion (far too few entries to compare) does not change: one entry is
  still not a sample.
- FC-01-r1 is closed and stays closed. More rows from the same period are
  not untouched data, and nothing here is a reason to reopen it. If the host
  holds Coinbase book data from 2026-07-18 to 2026-08-29, that earlier
  stretch has not been looked at by anyone; whether to use it is a new
  registered question, not a rescue.
- For the 2026-10-13 host review: the question is no longer only "are the
  three sessions worth the bill" but also "is the host the project's
  reliable context collector". On the record it is the only candidate for
  that role.

Read-only checks that would settle the unknowns (need host access; not run
by me, and none of them changes anything on the host):

```sh
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=20
ssh cryptkeep@<host> 'CBP_STATE_DIR=/var/lib/cbp /srv/cryptkeep/app/.venv/bin/python \
  /srv/cryptkeep/app/scripts/check_edge_cadence.py --json'
# row counts and date range per table, opened read-only, in /var/lib/cbp/data/crypto_edge_research.sqlite
```
