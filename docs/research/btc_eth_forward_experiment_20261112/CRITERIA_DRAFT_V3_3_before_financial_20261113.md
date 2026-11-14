# BTC+ETH prospective continuation: proposed criteria v3.3

Bot relation: STANDALONE for Q1/Q2, using the research tracker; Q3 is conditional BOT_PAPER, not activated. Runtime trading configuration not checked.

**Status: DRAFT, not adopted, not activated.** Prepared by Codex on 2026-11-13 under the owner's request to continue after the [independent audit](../second_stage_review_20261112/CODEX_VERIFICATION_20261113.md). This is a complete replacement proposal, not an amendment already in force. Original [v3.2](CRITERIA_DRAFT.md), its history and all ledgers remain unchanged.

**SHOWN source facts:** unchanged v2 computes scalar-cost modeled marks and records decision lag; it does not collect quotes, provide an ETH-hold account, implement the alternative-cost evaluator or notify at a missed-run deadline. Its restored schedule's dispatch/timezone remains unverified. **PROPOSED** below means a design choice awaiting owner adoption, not existing capability.

## 1. Changes requiring explicit adoption

The signal, volatility sizing, main 50/5-bps cost assumptions, 26/52-week dates, primary Q1/Q2 comparisons and existing data-quality thresholds are retained. The following are not disguised as wording-only changes:

1. Define this as an October-18-account **continuation window**, not fresh November cash accounts. Explicitly choose v3.2's fixed 25/25/50 comparator; do not substitute the second-stage report's exposure-matched mix.
2. Define quote eligibility, half-spread and evaluation cutoffs. Quote coverage permits a quote-based sensitivity calculation; it never becomes proof of measured total execution costs. Q1 retains a cost qualifier even with eight quotes.
3. Distinguish deadline-based missing classification from the actual later detection/notification time. No new observer or same-hour alert is promised by this contract.
4. No automatic restart/backdating or whole-project shutdown follows from this candidate's result. Any replacement window, development reprioritization or live-money decision needs the owner's direction.
5. Q3 remains an unactivated separate contract. Its explicit prerequisites cannot be silently waived by approving Q1/Q2.

## 2. Questions and unchanged strategy

Q1: does the modeled continuation-window return of `rule` meet or exceed `mix_25_25_50`, with identical timing and the same cost scenario?

Q2: does `rule` have a smaller daily-close maximum drawdown than `hold_btc` during a window containing a BTC drawdown of at least 20%?

Q3: can a separately approved paper integration reproduce the rule and account for execution reliably? It neither supplies nor rescues Q1/Q2 data.

The primary rule remains: on the close of each UTC Sunday candle, for each of BTC and ETH, hold weight `0.5 * min(1, 0.50 / vol30)` if its 28-day close return is positive, otherwise zero. `vol30` is population standard deviation of 30 daily simple returns times `sqrt(365)`. Cash is the remainder. Weekly decisions only, modeled next-day open execution, no additional stop/take-profit/trailing/hold exits, no parameter selection.

Primary account assumptions: no deposits or withdrawals; one shared cash balance per account; carry quantities and cash forward; post-cost joint rebalance; no forced end liquidation. Primary fee 0.005 and adverse price adjustment 0.0005 per side on traded notional. These are frozen **model inputs**, not a fresh confirmation of the account's actual fees or realized costs. Open positions are marked, not sold; reported net return includes modeled costs incurred, not an uncharged final exit fee.

Source identities read 2026-11-13:
```text
paper_btc_eth_trend_v2_20261012/tracker.py
572118ad9e829e3df7f508814ee79697d273e3b988e571a33eef87ed9761e0e2
scripts/research/corrected_research_math.py
d07ae7171e2293cbe60d15ae9bc0973d3ef8bd31b9c7b99105f928c029e29047
prior CRITERIA_DRAFT.md v3.2
9dc85f1ad05c57947e14c6df67991604b49041cb37da773f7165ddf3edd811d1
```

Any source change must be reviewed against this contract before its affected outcomes; a changed hash is not permission to repair historical ledgers or change criteria after inspecting performance.

## 3. Exact clock, inherited wallets and comparison base

All dates are UTC candle dates. A Sunday close means the end of that UTC day, at Monday 00:00 UTC.

- Proposed baseline A: **2026-11-16T00:00:00Z**, the close of candle dated November 15.
- The first included decision is November 15; its modeled execution is the November 16 daily open.
- Q1/Q2 first-window end T: **2027-05-17T00:00:00Z**, the close of candle dated May 16. The 26 included decisions are November 15 through May 9. A May 16 decision may exist in the ongoing tracker but is outside this decision cohort.
- If Q2 is UNTESTED, its only extension contains May 16 through November 7 decisions. Extended end U: **2027-11-15T00:00:00Z**, close of candle dated November 14. Q2 is then measured over the whole 52 weeks A to U; Q1 remains fixed at T.
- Freeze must occur before A. If it does not, keep this missed proposal visible and obtain a new future-dated proposal; do not backdate approval, quietly move dates, or treat observations already seen as unseen.

Use the existing October-18-initialized accounts `rule`, `rule_band10`, `hold_btc`, `mix_25_25_50` and `cash`. Their initial research allocation was $1,000 each; no new money is added at A. Inherited holdings and pre-A costs differ by account and remain part of the initial wallet. For account j:

`window_return_j(d) = NAV_j(d) / NAV_j(A) - 1`.

Freeze the A baseline's wallet, units, mark, pending November 15 targets and supporting ledger identities when those records become available. Underlying code/criteria are frozen before A; those future observation hashes are recorded afterwards, not fabricated in advance. Prior missed/reconstructed weeks remain labeled as such and are not converted into on-time evidence. They are outside the new decision cohort, but can affect inherited wealth/holdings and must be disclosed.

The primary fixed mix is 25% BTC, 25% ETH, 50% cash rebalanced weekly, **not** a hindsight exposure-matched allocation. `hold_btc` retains its original purchase and does not rebuy at A. `cash` remains a control. `rule_band10` is a descriptive comparator only, not an alternative candidate selected after results.

## 4. Q1: primary descriptive result and execution-cost sensitivity

At the primary 50-bps fee plus 5-bps adverse-price model, Q1 is PASS if `R_rule(T) >= R_mix(T)` and FAIL otherwise, subject to the data-quality rules. No statistical edge or real execution claim follows from PASS. Always label this **MODELED; execution-cost validity unverified**.

Q1's reported adjudication consists of the primary PASS/FAIL plus a separate cost-sensitivity state. It is never an unlabeled operational or profitability approval.

### 4a. Quote observations, if separately authorized

This draft does not obtain quotes or change a schedule. A future observation implementation requires separate scope and review; no historical quote is invented from candles.

For each included weekly Monday execution boundary E and asset:

- Use Coinbase USD product identity BTC-USD or ETH-USD; retain the exact public source, raw response/hash, request and response UTC times, bid, ask and any source timestamp.
- One eligible observation per asset/week: the **first valid response to a request initiated in [E, E+60 seconds] and received by E+60 seconds**. No best-spread selection, duplicate counting or later-day substitution.
- Bid/ask must be finite and positive, ask >= bid. If a source timestamp is supplied, require it not to be future-dated relative to receipt and no more than 10 seconds old. If unavailable, flag source-age UNKNOWN; receipt-time observation is eligible but does not establish exchange-source freshness. Report these separately, not as measured fills.
- With midpoint `m=(ask+bid)/2`, fractional half-spread `h=(ask-bid)/(2*m)`, reported percentage `100*h`. Do not confuse percent with bps. Report every accepted/rejected/missing observation, weekly identity, timestamps and exclusion reason, per-asset count, mean/min/max and source-age limitations.
- Minimum coverage is eight distinct included weeks **per asset**. The BTC and ETH means use their own observations; report different week coverage if applicable. This is the draft's chosen minimum, not a representativeness guarantee.

For a quote-based sensitivity, use fee 0.005 and per-asset adverse fraction `s_a=max(0.0005, arithmetic_mean(h_a))`. That is a spread-component sensitivity floor, **not measured total slippage**, market impact, order-book depth, maker fill rates or real execution. Preserve both assumed and quote-based outputs.

### 4b. Counterfactual accounting and a fixed evidence cutoff

A separate evaluator is **NOT IMPLEMENTED by this document**. It must preserve primary ledgers and pass synthetic/source review before any outcome evaluation is authorized. Its contract is:

- Start each scenario at A from the same account-specific inherited cash/units as the primary model; do not reset to $1,000, reprice pre-A costs, or subtract a fee estimate from saved NAV.
- Reuse the frozen primary decision targets/timing, aligned public execution opens and daily close marks. At each rebalance solve post-cost target equity jointly; buys spend `qty*open*(1+s_a)*(1+fee_a)`, sells receive `qty*open*(1-s_a)*(1-fee_a)`. Fees and price adjustment are distinct; never deduct half-spread twice. Resulting quantities and subsequent cash carry forward under that scenario. The primary scenario must reproduce tracker marks within $0.01 at every included daily mark before using alternatives.
- Resolve inherited wallets from a source-identified replay that reconciles to persisted primary evidence; do not treat rounded summary weights as exact positions. Required price/source/target/baseline records must be identifiable and internally consistent. Missing or contradictory required inputs make that scenario INCOMPLETE; no forward-fill, silent source replacement or changed targets.
- Quoted observations must occur inside A to T and satisfy 4a. Final source records/marks are accepted for adjudication only if received and preserved by **T+48 hours**. Evaluation may occur later, but only on that sealed input set; no later quotes, favorable new price versions or post-cutoff account-tier information may change Q1's verdict. The same U+48-hour cutoff applies to extended Q2 records.
- If both assets meet quote coverage and the reviewed evaluator/data are complete by the cutoff, report the quote-based PASS/FAIL. If primary PASS but the quote-based scenario FAILS, the proposed Q1 continuation screen is **not passed**. Do not suppress the primary result. If quotes/evaluator/data are insufficient, report **PROVISIONAL_COST / INCOMPLETE sensitivity**, not a definitive execution-adjusted PASS.
- The primary model and its cost-qualified screen are fixed from the T cutoff; no late conversion of PROVISIONAL into confirmed at a favorable time. Later work is a labeled new analysis, not a rescue of this registered result. Quotes alone never remove the overall modeled-execution limitation.

## 5. Q2: drawdown, qualifying market fall and extension

For each account, `DD_j(d)=1-NAV_j(d)/max(NAV_j(x): A<=x<=d)` using daily close marks only. Maximum drawdown is the largest DD in the window. Pre-A peaks do not count. Daily closes do not measure intraday drawdown.

Q2 uses the unchanged primary 50/5-bps model, not Q3 or the later quote-based sensitivity. If `MDD_hold_btc < 20%`, Q2 is UNTESTED regardless of which account otherwise has a smaller drawdown. Otherwise PASS if `MDD_rule < MDD_hold_btc`; FAIL on equality or worse. Report mix drawdown as well. The 20% level is a chosen criterion, not a validated universal crash threshold.

The Q2 extension is eligible only when Q1's primary result is PASS, its quote-based sensitivity has not FAILED, the first-window data-quality result is valid, and Q2 is UNTESTED. Cost-PROVISIONAL Q1 remains provisional during any extension; it is not rescued or finalized later. A Q1 primary FAIL, quote-sensitivity FAIL, INVALID or required-input INCOMPLETE does not trigger an automatic extension. This retains the earlier conditional continuation rather than extending a failed Q1 test. Any research outside that condition requires a separate owner decision.

An eligible extension runs Q2 once to U, with A unchanged. Use the whole A-to-U drawdown and 20% test. Q1 is neither extended nor rescued. Q2 still UNTESTED after U counts as not passed **for this candidate screen**, not proof that the rule is ineffective in crashes. A failed screen does not stop the existing tracker or other research without operational/scope authority.

## 6. Data quality, missed decisions and actual detection

For each included decision, require all expected noncash account records, with event identity and `recorded_utc`/`recorded_lag_hours`. For `hold_btc`, no further weekly decision is expected after its initial purchase; do not mark it missing. Use the worst lag among the expected `rule`, `rule_band10`, and `mix_25_25_50` decision rows; one absent required row makes the weekly decision missing. Check source timestamps against reported lag, using UTC, not the boolean `reconstructed` alone.

- ON_TIME: lag <=24 hours. This proves only recording within the research tolerance, not availability/tradability at the modeled Monday open.
- RECONSTRUCTED: lag >24 and <=48 hours. Used in modeled calculations but not on-time recording evidence.
- MISSING: any required decision was not recorded by E+48 hours, even if subsequently appended. At that deadline it is classified missing; later inspection records its **actual detection time**, not a fabricated notification at the deadline.
- More than three reconstructed included weeks, or any missing week, makes Q1/Q2 INVALID for the first window. Apply the same thresholds separately to the 26 extension decisions; an extension breach invalidates extended Q2, not the already fixed Q1. Report counts over each segment and all 52 weeks when applicable.
- Missing or contradictory required daily marks/baseline/execution evidence makes the affected calculation INCOMPLETE. Do not infer zero volatility, zero drawdown or zero P&L from missing observations. An INVALID result takes priority over PASS/FAIL; an INCOMPLETE metric is not a PASS.

**No new deadline observer or notification service exists through approving this text.** Retrospective deadline classification is possible from preserved recording times; timely detection/notification remains UNVERIFIED until a separately authorized observer is demonstrated. A later report must state detection lag. Existing tracking continues; the protocol does not pretend that a weekly process can alert on its own absence. If the owner requires timely alerts as a condition of starting Q1/Q2, that is a separate readiness decision, not presumed satisfied here.

Do not automatically restart a failed/invalid window, delete its outcome, change lag thresholds or move dates. A reliability repair and any replacement future window require their own owner decision, dated registration and preserved prior attempt. No interim performance tuning, early favorable stop or selective extension.

## 7. Q3: separate implementation contract, not authorized or frozen here

Approving Q1/Q2 does not start Q3 or waive the accepted full simulation safeguards. Before Q3 may begin, separately adopt a source-bound contract specifying the initial shared wallet, prior-close decision cutoff, actual paper order clock/lateness, targets-to-quantity sizing, precision/fee affordability, sell-proceeds availability, partial/rejected/unfilled legs, restart recovery, quote freshness/fill policy, complete two-asset valuation and independent review. Reuse existing portfolio/paper code; do not silently use the normal fixed-quantity, no-add/full-close runner as a target-resizing portfolio.

Retain the earlier proposed comparison tolerances: target weights within one percentage point, same-contract historical replay NAV within 0.5%, weekly cash/positions/fees reconciled to $0.01 and 100% of fills with source-identified contemporaneous bid/ask. The baseline, execution conventions and the replay source/data must be fixed before applying those tolerances; tolerance does not excuse a wrong rule or unexplained drift.

The Q3 contract must make any target-parity breach, accounting mismatch, missing required fill evidence or silent missed decision an explicit FAIL. At most one recorded missed decision is allowed over its 26-week period; two or more FAIL. Any stopping/restart action is exercised only under separately granted operational authority. No automatic fix/restart or source rewrite is authorized here. Preserve failed attempts; a new 26-week Q3 clock requires fresh approval. Q1/Q2 results are unaffected by Q3 success, failure, delay or restart.

## 8. Reporting and consequences

For every primary and complete sensitivity scenario report account start/end NAV, return, drawdown, all modeled orders/costs, holding/cash state, data-quality counts, source/code hashes, observation coverage and uncertainties. No annualized income projection from 26 weeks.

Report BTC/ETH legs as marked value change plus signed net trading cash flow since A, divided by that account's A NAV for contributions. Their dollar contributions must sum to account NAV change; do not assign the same cash balance to both legs or present them as independent $1,000 accounts. If the necessary prices/flows cannot be reconciled, label per-leg reporting INCOMPLETE.

Additional reports, not new deciding strategies: `hold_btc`, cash, `rule_band10`, and a hold-ETH control only when separately reproducible from $1,000 cash at October 18, modeled October 19-open purchase at the same costs, normalization at A and no later trades. It is not currently a tracker account. If not available, say NOT COMPUTED; do not silently compare a fee-free ETH index with the funded primary accounts.

Report the 0.90%-fee/0.05%-adverse-price stress scenario with the same A wallets and its own carried accounting. Report a separately verified account-tier scenario if evidence is available within the cutoff; neither changes the frozen primary settings. No credential/account access is granted. If the evaluator or required evidence is unavailable, report INCOMPLETE/NOT COMPUTED, not an unstated assumption that these reports already exist. Any failure of this required reporting means the overall package is incomplete even if primary Q1/Q2 metrics can be calculated.

Classify findings under POP: return edge, risk-adjusted edge, diversification benefit, risk reduction or no demonstrated advantage. Historical/model/paper evidence remains distinctly labeled. Any formal advantage claim still needs the ledger/trial-count and valid deflated-Sharpe requirement; these remain unresolved and no descriptive PASS waives them. No real fill, measured maker execution or durable profitability is established here.

Q1/Q2 PASS means only that this candidate met its declared descriptive continuation screen. It permits a recommendation about further paper research, not money movement, live readiness or an infrastructure/capital commitment. A cost-PROVISIONAL result remains provisional. Q1 FAIL, Q2 FAIL or final UNTESTED means this candidate did not pass that screen. Report failure causes using POP and propose the smallest justified action; do not force trades, relax criteria or automatically shut down the wider project. Fixed allocation is an alternative to evaluate, not an instruction to buy it. Multi-symbol support and other owner-approved objectives remain preserved.

## 9. Readiness and adoption boundary

**SHOWN existing support:** rule/benchmark primary accounting, append-only ledger timestamps and lag metadata. **PARTLY DONE:** primary Q1/Q2 evaluation inputs can be produced by the existing tracker, but the new window's baseline/future marks and unattended reliability are not yet observed. **NOT DONE:** new quote collection, alternative-cost/per-leg/ETH-control evaluator, timely observer and Q3 integration. This draft does not implement them or certify a usable scoring workflow.

Proposed adoption is Q1/Q2 **design only**, including its explicit modeled/provisional limits and reporting requirements. It does not authorize new data acquisition, a schedule, service/server access, a market replay, study activation, implementation, experiments on saved results, capital/risk changes or trading. Any follow-on work must be placed in the existing queue by the owner. Do not infer acceptance of unmet readiness from a signature.

Before an actual prospective registration: the owner identifies this exact version and scope; change its status/date to final FROZEN bytes; then compute and record **that final file's** SHA256, source hashes, UTC approval/freeze time before A, and outstanding readiness in the existing work log/PROJECT_STATE. Do not hash DRAFT and then edit the hashed file. If future observations arrive after A, their own hashes record those observations; they do not change the registered criteria. Do not amend criteria after seeing affected performance.

Two material assumptions for this proposal: the intended study is the existing carry-forward primary v2 account against the fixed 25/25/50 mix; the owner wants a corrected design now, not operational activation. If either is false, revise that explicit choice before freezing rather than quietly changing account history or scope.

What do I know that could change the owner's decision that I have not yet said?

The existing tracker can provide useful descriptive primary evidence without a new simulator. But its fills remain retrospective daily-open models, and the extra cost/reporting checks still need work. This proposal makes those limits visible; it does not make an executable trading system or a complete experiment merely by specifying one.
