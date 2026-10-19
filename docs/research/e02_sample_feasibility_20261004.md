# E02 sample feasibility - 2026-10-04

AUDITOR (Claude). Read-only arithmetic on existing local artifacts. No new
backtest, no new data collection, no collector started or stopped, no
campaign, config or account change. Not a profitability finding and not
advice to allocate capital. This is the "sample feasibility" input that
roadmap item E02 requires before a frozen context comparison is registered.

## Question

E02 is "one frozen context comparison" of the unchanged baseline candidate
against context evidence (funding, basis, open interest, order book). Is
there, or will there soon be, enough overlap between the candidate's entries
and recorded context to compare anything?

## Inputs (SHOWN, local checkout, opened read-only)

- Context store: `.cbp_state/data/crypto_edge_research.sqlite`, last capture
  2026-10-04T00:06:13Z. Rows with `source='live_public'`:

  | Table | Venue / symbol | Rows | First | Days with data | Longest unbroken run |
  |---|---|---:|---|---:|---|
  | funding_snapshots | okx BTC/USDT:USDT | 11,346 | 2026-07-11 | 74 of 86 | 36 days, 2026-08-30 to 2026-10-04 |
  | basis_snapshots | okx BTC/USDT:USDT | 11,346 | 2026-07-11 | 74 of 86 | same |
  | open_interest_snapshots | okx BTC/USDT:USDT | 8,013 | 2026-07-11 | 43 of 86 | 36 days, 2026-08-30 to 2026-10-04 |
  | order_book_snapshots | coinbase BTC/USD, depth 5 | 8,018 | 2026-07-02 | 44 of 95 | 36 days, 2026-08-30 to 2026-10-04 |
  | quote_snapshots | coinbase and kraken BTC/USD | 23,245 | 2026-03-23 | 77 of 196 | not computed |

  The rows dated 2026-03-18 are `sample_bundle` fixtures (one per symbol),
  not market data. Funding and basis have a gap 2026-08-15 to 2026-08-22;
  open interest and order book have almost nothing before 2026-08-30.
- Candidate signal: `.cbp_state/data/research/daily_trend_recent_20260926/result.json`,
  arm `sma200_signal_only`, 2025-09-26 to 2026-09-25, MODELLED.
- Cadence: E01 audit Addendum 11 (`e01_paper_evidence_audit_20261002.md`),
  31 entries in 8.03 years on the 2018-2026 archive, MODELLED.

## Findings

1. SHOWN: the candidate made one entry in the last eleven months of that
   artifact, on 2026-08-20 (four earlier entries fall in 2025-09-26 to
   2025-11-01, before any context was recorded).
2. SHOWN: 2026-08-20 falls inside the 2026-08-15 to 2026-08-22 gap in
   funding and basis, and before open interest and order book have usable
   coverage. **The number of candidate entries with recorded context is
   zero.**
3. SHOWN: the only period with all four context series unbroken is the 36
   days from 2026-08-30. The candidate made no entry in it up to the
   artifact's end (2026-09-25); it was already long from 2026-08-20.
4. From Addendum 11 (MODELLED, descriptive of one history, not a forecast):
   3.86 round trips a year; median 154 days from an arbitrary day to the
   next entry; about four in five 30-day windows contain no entry.
   At that rate, context-tagged entries accumulate at roughly four a year:
   about 5 after 15 months and about 20 after 5 years, if collection never
   breaks again.
5. Consequence for E02: a comparison of this candidate with and without a
   context filter has no sample now and would have a handful of events after
   a year. Any result on that sample would be "insufficient evidence" by
   construction. At the operator's stated infrastructure range (under 10 per
   month), a year of waiting costs up to about 120, against a modelled net
   for the candidate at today's size of about 0.6 to 2.8 per month (E01
   Addendum 9).

## What follows, and what does not

- E02 as worded ("compare unchanged baseline") cannot produce a STOP, REVISE
  or ADVANCE result for the daily SMA200 candidate on any horizon shorter
  than years. The honest E02 outcome available today is "insufficient
  evidence", stated before any comparison is run.
- This does not show the context data is useless. It shows this candidate
  trades too rarely to test it. The same 36 unbroken days hold 7,784
  funding and basis observations and 7,786 open-interest and
  7,790 order-book observations, which is a usable
  sample for a question asked at that cadence (for example, whether funding
  or imbalance at time t relates to the Coinbase mid some hours later, net
  of the verified 50 bps taker fee per side). That would be a NEW registered
  question about a different, faster candidate, not E02 for this one, and
  36 days is one market regime.
- It does not recommend continuing, revising or retiring the candidate.
  That is E03, the operator's decision. The inputs now on record for it:
  E01 (not economically qualified on existing evidence), Addendum 11
  (evidence arrives slower than it costs to wait for), and this note (the
  planned context comparison has no sample).

## Limits

Laptop state only; the Hetzner host's stores were not inspected. Collector
cadence and gaps are described, not explained. The candidate artifact is a
signal-only model; the runner's rule set differs (E01 finding 11). Counts of
future entries are extrapolated from one eight-year history of one asset.
UNVERIFIED: whether an authoritative E02 scope document elsewhere defines a
different comparison.

## Addendum - scope correction (same day)

Every count in this note is from the LAPTOP archive
(`.cbp_state/data/crypto_edge_research.sqlite`). Repository records show a
second, systemd-supervised context collector on the Hetzner host since
2026-07-18 (`docs/checkpoints/hetzner_crypto_edge_runtime_ready_2026_07_18.md`;
last inspected 2026-09-01). I did not know of it when writing this note and
cannot reach the host. Finding 2 ("zero candidate entries with recorded
context") is therefore a statement about the laptop archive only: the
2026-08-20 entry fell in a laptop gap and the host may have recorded that
day. The conclusion is unchanged, since one entry would still not be a
sample. Details and the read-only checks that would settle it:
`e03_decision_brief_20261004.md`, Addendum 3.
