# One bounded public execution diagnostic: INCOMPLETE

Bot relation: STANDALONE public observations and hypothetical execution. Runtime trading configuration not checked; no account data/orders/fills.

**Answer:** collection feasibility is shown, but the paired diagnostic is **INCOMPLETE**, not an execution-cost result. Both products returned public metadata and three books; ETH's returned trade page contained no timestamps inside its local observation window. No retry or repair was made. This does not demonstrate maker fill rates, a Monday cost sample, E1 qualification, strategy profit or readiness for a two-week bot build.

## 1. What actually ran

One foreground invocation **2026-11-13T17:31:28.346712Z to17:31:37.783562Z**, elapsed9.436seconds, under the separately reviewed source and an external75second subprocess timeout. Exactly10GETs, allHTTP200, 4,332,592rawbodybytes; largest971,241bytes below1MiB. No retries, redirects, login, account read, order, transfer, new service/schedule or deployment. Source hash unchanged after execution. No report of process liveness is inferred beyond this returned invocation.

[Invocation receipt](public_diagnostics/20261113T173128Z_b7514447_invocation.json), [report](public_diagnostics/20261113T173128Z_b7514447/report.json), [receipt checks](diagnostic_proof_20261113/capture_receipt_checks.json). All ten raw payload hashes and receipt-file bodies match. Original raw bytes/metadata/trade pages and failures are retained, not rewritten to obtain a valid result.

This was a Friday diagnostic. **Monday primary observations added: zero.** Completion before the18:00UTC stop deadline does not create any future attendance/scheduler promise or freeze the26-week criteria.

## 2. Public observations, not account executions

| Product | Initial bid / ask, USD | Local initial receipt UTC | Full quoted spread, initial to final | Retained data |
| --- | --- | --- | --- | --- |
| BTC-USD | 68,658.49 / 68,658.50 | 17:31:28.587746 | 0.001456 to0.001457bps | Three books,100returned prints;24-hour/global volume not requested |
| ETH-USD | 1,930.95 / 1,930.96 | 17:31:33.213300 | 0.051788 to0.466132bps | Three books,100returned prints; none in its selected local window |

Metadata reported online and all captured disabled/cancel/post/limit/auction flags false. These are isolated public observations, not evidence of continuous tradability or actual order acceptance. Visible initial depth within10bps of midpoint: BTC bids$1.829million/asks$1.962million; ETH bids$0.790million/asks$0.964million. These are displayed snapshot dollars, not guaranteed executable funds; aggregated sizes were not multiplied by order counts.

All book source timestamps were retained. **Source-clock/receipt alignment remains UNVERIFIED.** Local minus reported source times cannot be treated as proven latency without clock qualification. The books and trade pages are not synchronized streams; do not label arrival as exact or trade coverage complete.

ETH selected local window was17:31:33.213300 to17:31:37.433671. Its latest returned print was17:31:32.804163, before that window. This proves that the returned page supplies no in-window print under the declared local-time filter. It does **not** prove there were no exchange trades, identify caching/server-lag causation, or justify replacing the page. BTC's100prints overlapped its window, but one page still does not prove complete interval coverage.

Short-window price dispersion and mid changes are descriptive only; neither asset received a historical high/low-volatility regime label. Selected print `side` is maker side, not aggressor side; [official source semantics](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-trades) were opened before implementation.

## 3. Conditional BTC shadow examples, not a cost-saving finding

The source's BTC-only arithmetic could be computed; it assumes provisional25bps maker/50bps taker fees and quantity0.00728242BTC from a $500 initial reference, rounded down to the observed base increment. No trade was placed, no portfolio was funded, and no actual fee was observed. It is not the26-week account's allocation or a short position.

- BUY: initial bid would cross the arrival-proxy ask, so the model marks hypothetical post-only rejection, not a maker fill. Immediate arrival-taker cost49.543bps versus final-taker fallback47.953bps under this falling short path. This is a scenario comparison, not an accepted/rejected order acknowledgement.
- SELL: optimistic **assumed full** maker-fill cost24.999bps; immediate arrival-taker50.454bps; no-maker-fill final-taker52.028bps. Waiting can therefore erase part of the assumed fee saving or cost more than immediate execution. The favorable maker case is not a probability, verified bound or fill inference.
- All costs use the same base quantity and initial-midpoint reference for each side. Visible depth/minimum/precision checks are basic model conditions, not complete exchange order validation. Unobserved queue, cancellation, price impact, source freshness and product/account fee exceptions remain unknown.

No ETH shadow cost is published from this incomplete event. No two-asset average, confidence interval, maker-supported verdict, annual saving or strategy return is inferred. Keep the valid public books visible alongside the missing execution evidence; do not silently discard the failure or call it a market loss.

## 4. Source and independent proof

Isolated research tool: `scripts/research/capture_candidate_execution_diagnostic.py`, SHA256 `4ac85819a81ee00d10307550dfc2bd532c2d1b2e676d57080e848c6c788dff88`; tests SHA256 `b8f587ad74330bb7c165786cfdb4e4f97c9a7b5869777d97ab99e562dc017ac3`; [protocol](PUBLIC_SHADOW_PROTOCOL_20261113.md) SHA256 `66714449e9014bced2e855afd0711fc1704d4111de12216f249e92c08becdf0a`.

Nash GATE initially rejected an execution-minimum gap despite30passing tests. Two regressions failed before the five-line correction; the rejected source is preserved as [before-fix control](diagnostic_proof_20261113/capture_before_minimum_fix.py). Independent diff-only acceptance through17:30:15Z: **ACCEPTED_WITH_RISK, source/synthetic scope and at most this one bounded public diagnostic**,32tests passed0.30s. The external75second bound and no-retry rule were conditions, not features inferred from socket timeouts. No full-suite or market-strategy test was run.

Public-data outcome is separately **INCOMPLETE**. Source acceptance is not data qualification. A separate read-only receipt review was requested; its result, if available, is recorded in the final package receipt rather than assumed here. Actual account fills stay **UNVERIFIED** in every lane.

## 5. Finite disposition

WP2 research preparation/synthetic proof and the single budgeted diagnostic are finished; the data question is not solved. No more calls or code changes follow from this result. A future proposal would have to address trade interval coverage, source/arrival clock qualification and Monday attendance without changing E1 or primary criteria silently. It is not authorized by this diagnostic, and no new collector/schedule has been created.

Together with the [economic/evidence assessment](ECONOMICS_AND_EVIDENCE_20261113.md), this supports inexpensive, bounded evidence work, not committing to full bot integration or real money. That is an inference from inspected evidence, not a new owner decision or a claim that no profitable system is possible.

What do I know that could change the owner's decision that I have not yet said?

All ten HTTP requests succeeded, yet one product still lacked even a single correctly timed trade for this local window. Merely logging "collection succeeded" would hide the central failure. Fixing source coverage/clock alignment is a real missing capability if execution-cost evidence is the next objective; extending this tiny diagnostic or its favorable maker assumption would not establish an edge.

## Independent receipt verification

Nash, separate GATE `01a1cee8-b4ec-7343-9992-b771df07aba1`, checked through **2026-11-13T17:33:53Z** and returned **ACCEPTED_WITH_RISK for receipt integrity and faithful reporting only**. The diagnostic's **INCOMPLETE** outcome is unchanged. Reviewer independently matched ten raw hashes/byte counts/receipts/intents, fixed public URLs and HTTP200responses,6books/200prints,4,332,592bytes/bounds,9.436seconds/return2,sourcehash and the ETH timestamp failure. No model/code rerun, edits or network. This supersedes the earlier pending-receipt-review sentence only; it is not source-clock, maker-fill, E1, Monday-sample or economic acceptance.

What do I know that could change the owner's decision that I have not yet said? The independent review confirms the evidence is faithfully retained, not that the evidence answers the execution question; no missing ETH trade was inferred as no trading or silently replaced.

## Dated offline follow-up: 2026-11-13T18:32:13Z

The separately owner-authorized [offline diagnosis](ETH_OFFLINE_DIAGNOSIS_20261113.md) reproduces the unchanged validator's BTC83/ETH0 outcome. It adds source-book/local-receipt timestamp differences and diagnostic-only alternate-interval overlap; these are not a repair or rescue of this capture. Separate Nash GATE18:31:51Z ACCEPTED_WITH_RISK for diagnosis/reporting only. No demonstrated filter defect; upstream cause remains UNVERIFIED and original capture remains INCOMPLETE. All raw/receipt bytes, report.json, diagnostic source and frozen criteria are unchanged. No network request or new observation was made.

What do I know that could change the owner's decision that I have not yet said? Book/trade source alignment remains unqualified for BTC as well as ETH; matching some timestamps alone is not complete interval or fill evidence.

## Source provenance update: 2026-11-13T18:41:15Z

Subsequent owner-authorized instrumentation changes the current script, not this event. The source that actually made the ten requests is preserved as [before_freshness_instrumentation.py](diagnostic_proof_20261113/before_freshness_instrumentation.py), retaining the SHA256 stated in section4. Original raw/receipt/report.json and qualification are unchanged. [Instrumentation proof](FRESHNESS_INSTRUMENTATION_20261113.md) is synthetic/source evidence only; no new capture was invoked.

What do I know that could change the owner's decision that I have not yet said? Historical source acceptance does not automatically accept a revised collector or permit another live request.
