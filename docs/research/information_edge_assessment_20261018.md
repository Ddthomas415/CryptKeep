# Information advantages for CryptKeep: feasibility, not trading results

Date: 2026-10-18. Active role: AUDITOR. Research-only; no market-data test run.

## Answer

Question: which lawful information could give CryptKeep an actionable advantage
beyond price/volume, without enterprise data spending or another platform build?

Public information combined more accurately or earlier is a plausible research
direction. Exclusivity is neither established nor required. No inspected source
demonstrates that CryptKeep currently has profitable informational superiority.
Do not replace this question with a search for companies named EDGE.

The best-fitting first information-specific candidate is structured official
venue event context joined to existing price/volume/quote observations. This is
a data-feasibility recommendation, not a claim that status announcements predict
returns. Public operational notices and actual product status must be separated;
neither a service-health page nor an asset review means trading is enabled.

## Access, Existing Assets And Fit

| Information | Evidence and potential use | Limits and recommendation |
| --- | --- | --- |
| Official venue incidents and product-state changes | Coinbase publishes a status API; Exchange documents product status flags. Proposed context: distinguish operational disruption from ordinary market activity. | Source publication can lag the market; announcements can be revised. No exclusive or speed advantage shown. First check point-in-time archive and market-response join feasibility, not profitability. |
| Public quotes, trades and order books | Coinbase documents timestamped ticker messages, sequence/heartbeat fields and reconstruction requirements. Existing context/collector code records quotes and books. | Existing runner observation is explicitly not exchange receive-time proof. A feed's documented capability does not prove this repo records a gap-free stream. Prefer execution-cost measurement; do not call book imbalance independent alpha. |
| Funding, open interest and basis | Existing collector source decision and row appenders already cover derivatives context, with OKX as the recorded public source. | Source access is not execution eligibility. E7's failed funding overlay stays failed; collection does not authorize rerunning it or establish a new carry edge. |
| Enterprise alternative data and confidential flows | The pasted company material supplies no CryptKeep access contract, usable quote, licensing assessment or validated strategy. | Do not buy a subscription, collect confidential information or expand into commodities/equities. Cost-effectiveness is UNVERIFIED, not assumed affordable from the operator's monthly funding capacity. |

Primary sources opened on 2026-10-18:

- [Coinbase Exchange channels](https://docs.cdp.coinbase.com/exchange/websocket-feed/channels):
  heartbeat/sequence monitoring, product-state fields, ticker fields and full-book
  synchronization. SHOWN documentation, not observed delivery or alpha.
- [Coinbase status API](https://status.coinbase.com/api): machine-readable status,
  component and incident interfaces. SHOWN interface documentation, not a
  complete historically immutable incident archive or Exchange-only scope.
- [Coinbase listings](https://www.coinbase.com/listings): the issuer describes
  review and liquidity-dependent trading activation. CLAIMED publisher process,
  not evidence a particular market was tradable or that listing alpha exists.

No promotional offers or testimonials are used as research evidence. Initial
non-www Exchange-status and book-document URLs failed to fetch; these failures
do not establish that the interfaces are absent. The sources above were opened.

Local source inspection, without imports or service calls:

- `phase1_research_copilot/news_ingestion/main.py` already parses source
  publication/update times and sends documents to the existing memory path;
  it is marked an isolated candidate, not wired into startup. `_seen` is
  in-memory deduplication, not a durable first-seen ledger.
- `phase1_research_copilot/shared/models.py` declares `published_at` and
  `fetched_at`; memory source retains hashes and source identity. Field presence
  does not prove current ingestion, event completeness or a first-receive time.
- `services/strategies/market_context_capture.py` explicitly records runner
  observations with absent exchange-event/quote-received timestamps. That stream
  alone cannot certify high-frequency timing or executable returns.
- `docs/research/crypto_edge_source_decision.md` and the collector service show
  reusable public context paths. No collector or service was started here.

## Proposed Candidate For Later Preregistration

Status: INCOMPLETE, not registered, not activated, no market observations scored.

Hypothesis: independently observed official operational/product-state events add
information about subsequent executable dislocation or recovery beyond a frozen
price/volume/spread baseline. Directional profit and execution-cost avoidance are
distinct outcomes; do not substitute a successful risk warning for return alpha.

Before any run, freeze one event class and primary outcome, supported market
mapping, observation/decision/arrival timing, target/exit or forecast definition,
cash/sizing, costs, benchmark and minimum detectable effect. Consider the existing
25-symbol scope; any venue-eligible experimental subset needs a dated exclusion
record. Current scope membership is not point-in-time trading eligibility.

Required evidence chain: immutable source bytes/hash and revision identity;
publisher time; our first confirmed receive time; parse/feature-ready time;
decision time; arrival-time executable book; subsequent outcomes. Feature
availability is no earlier than confirmed receipt and parse completion. Never
enter at a backdated publication time or reconstruct an old event from its final
edited page. Preserve neutral events, false alarms, deletions and data failures.

Compare identical eligible opportunities with and without event context; keep
the baseline fixed. Use paired chronological blocks and untouched prospective
observations, count event-class/horizon/threshold selection, and include missing
and overlapping windows. Numeric horizons, sample targets and pass thresholds
remain undecided; this note does not manufacture a completed statistical plan.

Fail feasibility first if timestamps, event count, eligible quotes or historical
revisions cannot support the intended question. Estimate observations/day,
required sample and calendar time before collection. Rare events may make this
impractical; do not launch an indefinite low-power study to appear productive.

## Economic And Operational Boundary

The operator's $1,000/month is funding capacity, not an approved account balance,
loss budget or expected income. The roughly $20/month infrastructure figure is
an operator estimate, not an invoice. No return projection is justified.

This proposal uses existing public interfaces and code; no new paid data,
subscription or infrastructure purchase is proposed. Incremental storage,
requests and labor still have costs, and access terms/limits must be checked
before collection. No claim that a feed is free forever or has zero operating
cost is made. No exclusive-feed or low-latency race is recommended without
measured access/latency and a cost-capacity case.

Existing fees supply a dated account-level baseline (25bps maker/50bps taker on
October8), not verified current per-product all-in execution. A future comparison
needs explicit applicability plus spread/slippage and stress assumptions.

Existing rejected studies, source archives, schedules and symbol coverage stay
unchanged. No new comparison registration, market run, scoring, trading, private
account access, collector or service change was performed. Restoration remains
a separately scoped operational task, not permission to add another platform.
