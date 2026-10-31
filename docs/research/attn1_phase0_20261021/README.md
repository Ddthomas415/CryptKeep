# ATTN-1 Phase 0: Wikipedia mapping and data feasibility (2026-10-21)

**Result: BLOCKED_DATA.** Gate (a) fails: the mapped coins cover 55.6% of the primary sample's selections
(43.4% under the strict reading), against a required 70%. No pageview counts were requested. Nothing here is
committed. Prepared by Claude Cowork under the operator's "take care of whats needed" (2026-10-21), as Phase 0
only; the freeze and the pageview download were never started. An independent review was applied (below).

The ATTN-1 specification (hypothesis, gates, method) is section 9 of the Claude Doc "CryptKeep research audit,
revised brief and next experiments". Phase 0 asks for a mapping from each of the 147 host coins to one English
Wikipedia article or none, with a reason, and four gates that must all pass:
a) mapped coins cover at least 70% of the primary sample's selections; b) every mapped article is about the coin
itself, not a company, person or disambiguation page; c) Wikimedia's terms allow research use and the request
budget is stated; d) the user-agent series is available from 2020-04-29 on.

## Host (SHOWN; recomputed by `verify_coverage.py`)
- Source: `../coinbase_tradable_entrants_20261019/results_v1/result.json`, arm `altcoin_control` (read only).
- 147 coins, 4,209 selections, 100 four-week cycles (selection dates 2019-01-06 to 2026-08-09).
- Primary sample: the 79 cycles with selection on or after 2020-08-04 (first 2020-08-16): 3,922 selections.

## Method
1. Wikidata property P5777 ("CoinMarketCap cryptocurrency ID"), one SPARQL query: 131 items carry it; 20 of the
   147 archive slugs matched an item with an English article (`evidence/wd_p5777.json`).
2. 258 candidate titles for all 147 coins (`evidence/candidates.py`), checked in 6 MediaWiki API batches with
   redirects resolved, the disambiguation flag and the short description (`evidence/title_checks.json`).
3. For the 82 coins with no hit: one full-text search each (top 5 results; Coinbase name plus crypto terms;
   `evidence/search_results.json`; inputs `evidence/coins.json` and `evidence/nohit_ids.json`), then 63 more
   title variants in 2 batches (`evidence/title_checks2.json`).
4. Each coin classified by hand with a reason (`evidence/classify.py`, written out as `mapping.csv`).
5. Deletion logs for 43 likely titles of the 40 unmapped coins with at least 10 primary selections
   (`evidence/deletion_logs.json`), to catch articles that existed during the sample and were later deleted.
6. After the independent review: one more batch of 6 titles with their opening sentences
   (`evidence/review_fix_titles.json`) to confirm its corrections.

Classes:
- COIN: the article's subject is the coin or token.
- CHAIN: the blockchain or network whose native asset is the coin (e.g. Solana for SOL).
- APP: a protocol, application or service network whose token it is, where no token article exists
  (e.g. Uniswap for UNI, Chainlink for LINK).
- BRAND: an NFT collection or consumer brand linked to the token, not the token.
- REJECT: a title we tried exists, but its subject is a company or exchange, a different asset, a generic
  article, a disambiguation page or an unrelated subject.
- NONE: none of the titles we tried exists, and searches found only pages about other subjects.
The REJECT/NONE split depends on which titles happened to be tried, so it carries no weight: both fail gate (b).

Lenient mapping = COIN + CHAIN + APP. Strict mapping = COIN + CHAIN, because gate (b) says "about the coin
itself" and an APP article is about a protocol or service.

## Results (`coverage.json`)
| Class | Coins | Primary selections | Share |
|---|---:|---:|---:|
| COIN | 7 | 426 | 10.9% |
| CHAIN | 23 | 1,276 | 32.5% |
| APP | 13 | 478 | 12.2% |
| BRAND | 2 | 45 | 1.1% |
| REJECT | 23 | 515 | 13.1% |
| NONE | 79 | 1,182 | 30.1% |
| **Lenient (COIN+CHAIN+APP)** | **43** | **2,180** | **55.6%** |
| **Strict (COIN+CHAIN)** | **30** | **1,702** | **43.4%** |

The lenient mapping uses 42 distinct articles (MATIC and POL share "Polygon (blockchain)").

## Gates
- **a) FAIL.** 55.6% lenient, 43.4% strict; 70% (2,746 selections) required, so the lenient mapping is 566
  selections short.
  - The independent reviewer searched for articles on the 14 largest unmapped coins (ICP, QNT, CRV, RENDER, ARB,
    FLR, VET, SNX, SEI, FET, COMP, BONK, ONDO, TIA) under 50 more titles, phrase searches, 12 crypto categories
    and the Wikipedia lists of cryptocurrencies and blockchains, and found none (only a co-founder's biography
    for Celestia, which gate (b) excludes).
  - Deleted articles: the logs show three coins with an article at some point in the sample: ICP ("Dfinity",
    deleted 2022-12-11 after a deletion discussion), ZRX ("0x (decentralized exchange infrastructure)", deleted
    2025-10-10) and TAO ("Bittensor", speedy-deleted 2026-07-26). Counting all their primary selections
    (69 + 14 + 20 = 103) gives at most 58.2%. The other deletions (Arbitrum 2022-07, VeChain 2018-2021, OmiseGO
    2019-01, Ethereum Name Service 2017, Synthetix 2014, Fetch.ai redirects 2021) fall before the coin's first
    selection or were redirects only.
  - Borderline call: the "Dai (cryptocurrency)" article also covers MakerDAO and MKR at length; counting MKR as
    APP would give 57.2%.
  - The only way to reach 70% is to count articles about companies, exchanges, other assets or unrelated
    subjects, which gate (b) excludes by definition.
- **b) Lenient: no; strict: yes in my reading, but strict coverage is only 43.4%.** The 13 APP articles are about
  protocols or service networks, not coins. The reviewer confirmed no accepted article is a company, person or
  disambiguation page among the 22 accepted rows it checked; COIN-versus-CHAIN-versus-APP calls (e.g. WLD) remain
  judgement calls.
- **c) PASS on the documents** (`evidence/wikimedia_docs_excerpts.md`). Analytics API data is CC0 1.0; use is
  under Wikimedia's terms of use; a User-Agent is required and, per the 2026 rate-limit page, should carry
  contact details (an email or full URL), which the operator would have to choose; 200 requests a minute with a
  compliant User-Agent, at most 3 concurrent. Budget had it gone ahead: about 42 requests (one per article for
  the whole daily range), plus one per redirect title if redirect views were summed, because views of a
  redirect are counted under the redirect's title, not the target.
- **d) PASS on the documents.** The per-article endpoint's `agent` values are all-agents, user, spider and
  automated; "automated" was added on 2020-04-29; data starts 2015-07-01. Per-article completeness is UNVERIFIED
  until a download.

## What this changes
- Under the spec, BLOCKED_DATA means UNLOCK-1 or FRESH-1 becomes experiment 2.
- Not recommended: re-hosting ATTN-1 on mapped coins only. That is a new hypothesis (attention among coins
  prominent enough to have an article), selected on size and age, and would need its own spec and trial-ledger
  line.
- No returns were computed and no hypothesis was tested, so the trial ledger is unchanged.

## Requests made (all read-only metadata; no pageview counts)
- English Wikipedia API: 136 (9 title batches, 84 searches including 2 repeats after a timeout, 43
  deletion-log queries), sequential, at least 6.0 s apart, 2026-10-21 21:44:45Z to 22:30:00Z
  (`evidence/requests.log`).
- Wikidata: 3 (1 property search and 1 SPARQL query, not in `requests.log`; 1 SPARQL query refused with HTTP 429
  because the query service was rate-limiting to 1 request a minute during an outage, not retried).
- Documentation pages: 9 (doc.wikimedia.org 5, one of them a 404; mediawiki.org 1; gitlab.wikimedia.org 2;
  and `wikimedia.org/api/rest_v1/metrics/pageviews/api-spec.json`, the endpoint's OpenAPI description, which sits
  under the pageviews path but contains no view counts).
- User-Agent: "CryptKeep-ATTN1-Phase0/0.1 (research desk check: article mapping only, no pageview data)". It
  has no contact details, so it is not a compliant User-Agent for any later bulk use.
- The independent reviewer made 29 more API calls and 14 article-page reads under its own User-Agent (not in
  `requests.log`).

## Independent review (2026-10-21, separate agent, read-only)
Verdict: ACCEPTED_WITH_RISK; BLOCKED_DATA confirmed. Corrections applied here: BNB reclassified REJECT to CHAIN
("BNB Smart Chain (blockchain platform)", whose article names BNB as its native cryptocurrency); The Graph and
Chainlink COIN to APP; Injective COIN to CHAIN; World CHAIN to APP; SAND's reason now names "The Sandbox
(company)"; gate (b) wording; the robustness argument now rests on gate (b) instead of a 69.9% figure that
depended on the REJECT/NONE split; the request-gap figure; the missing search inputs added to `evidence/`.

## Limitations
- English Wikipedia only; other language editions were not checked.
- Article titles were checked as they stand on 2026-10-21. Deletion logs were checked only for the 40 largest
  unmapped coins; the other 39 unmapped coins hold 163 primary selections, too few to change the verdict.

## Files
`mapping.csv` (one row per coin), `coverage.json`, `verify_coverage.py` (read-only recomputation from
`mapping.csv` and the ENTR-CB-1 result), `evidence/` (raw API answers, request log, scripts, document
excerpts), `SHA256SUMS`.
