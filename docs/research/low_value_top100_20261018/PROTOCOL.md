# Low-value top-100 and emerging-entrant screen

Frozen before computing this study's returns, 2026-10-18 New York.
User approved testing low unit price and lower market capitalization separately.
Role: DIRECTOR. Risk: HIGH (financial research, not trading). Implementation
must receive separate review. Original data and earlier studies stay unchanged.

## Question and fixed comparisons

Using historical CMC membership, do inexpensive tokens, the lower half of the
top 100, or new entrants grow more over four weeks than a broad altcoin basket?
This is an exploratory reference-price screen, not an executable backtest or
untouched holdout. Previously used years remain previously used years.

Three hypotheses, one fixed horizon, no parameter search:
1. `under_1`: raw CMC top-100 assets priced strictly below USD1 at selection.
2. `ranks_51_100`: raw CMC ranks 51 through 100 at selection.
3. `new_entrants`: raw top-100 assets observed outside the top 100 in each of
   the preceding four weekly snapshots. Absence from a snapshot is unknown,
   not proof of being outside the top 100. This is a prospect proxy, not a
   claim about a project's age, fundamentals or future success.

Common control: all eligible raw top-100 altcoins, equal weighted. Cash returns
zero before inflation. BTC (CMC ID1) and ETH (ID1027) are never purchased.
Rank is CMC rank, not independently reconstructed pure market-cap order.

## Data, eligibility and timing

Read only `cmc/weekly/*.json` from the SHA256-pinned archive
`docs/research/raw_archives_20261009/cmc_weekly_and_trending.tar.xz` and verify
each member against the existing input manifest. Join by numeric CMC ID, never
by ticker. Validate dates, consecutive seven-day coverage and row schemas.
Selection dates start with the first available snapshot on/after 2019-01-01
and recur every four weeks, only while an entry and exit are available.
Enter at the next weekly reference price (seven-day information delay), exit
four weeks after entry. Select weights once using selection-time data only.

At selection require positive finite price and cap, global 24h USD volume at
least USD1m, and raw rank 1..100. Exclude stablecoin, wrapped, tokenized and
liquid-staking-derivative categories using the archived tags plus the earlier
CMC study's near-dollar stable-price heuristic (0.97..1.03 and abs(7d change)<1).
Tags/CMC history may be retrospectively revised and truncated; historical
exchange tradability, supply changes and corporate actions are not verified.

## Capital and costs

Each cycle is a separate fully funded USD1,000 basket, equal dollars across
selection-time members. No leverage, shorting or overlapping cycle exposure;
one cycle exits when the next enters. Results are per-cycle dollars, NOT the
sum or compounded return of a continuous account. No individual winner ranking
is used to choose the next cycle. Empty baskets remain entirely in cash.

Primary scenario: 0.50% fee each side plus 0.25% adverse reference-price
adjustment each side. Quantity = allocation / (entry_price * 1.0025 * 1.005).
Exit cash = quantity * exit_price * 0.9975 * 0.995. These are assumed friction,
not observed spreads, fills or a fee claim for every exchange. Also show gross
reference-price returns and a fixed stress scenario of 1.20% fee each side
with the same price adjustment. Do not choose a preferred rule from stress.

Missing entry: that member's assigned dollars stay cash, do not redistribute.
Missing exit: retain unknown value explicitly. Report a zero-recovery lower
bound for the missing allocation, NOT an asserted trade or a point estimate;
there is no finite upper bound. Do not drop failed/disappeared assets or carry
stale prices. Report unresolved counts. If any exit is missing, full-series
average is at best a lower bound and complete-only statistics are conditional.

## Outcomes and inference

For each hypothesis and control report selections, unique IDs, funded/missing
entries, unresolved exits, mean/median net dollars per USD1,000 cycle, profitable
cycle fraction, worst cycle, gross and stress results, both chronological
segments (2019..2022 and 2023..last available). Preserve all member-level rows,
including losers. No cherry-picked coin constitutes a recommended investment.

Paired differences versus the control use ONLY jointly fully valued cycles;
show how many were excluded. 4-cycle moving-block bootstrap, 4,000 replicates,
fixed seed 20261018; show 95% intervals and conservative simultaneous intervals
at 1-0.05/3 for the three registered comparisons. No DSR, power, independence
or live-profitability claim. Intervals are exploratory and do not correct the
entire prior project search. Repeated symbols count as selections, not distinct
independent samples; record per-arm distinct assets and the union exposure.

No promotion from this screen. A promising group requires verified venue/ID
mapping, executable higher-frequency data and separate forward validation.
No scheduler, service, account, credential, strategy or trading changes.

Material operational assumptions: new prospects means the explicit entrant
proxy; unobserved execution friction is the fixed scenario above.
