# Local paper-profile and public-cache check

Bot relation: BOT_RULES. Two local configuration files were inspected through
whitelisted policy projections; actual loaded process/server configuration was
NOT inspected. Primary observation2026-11-14T10:56:26Z; source precedence checked
10:58:47Z. Local observations are author-checked, not independently reread.
Separate Nash10:58:53Z ACCEPTED_WITH_RISK for the bounded interpretation after
checking loader/path source; simulation-target qualification stays INCOMPLETE.

**Result: neither inspected local file is a qualified target for the approved
simulation or the new paper-only metadata provisioner. Do not refresh this shared
state and call the nine-account simulation provisioned.**

## SHOWN observations

| Evidence | Observation and limit |
|---|---|
| `.cbp_state/runtime/config/user.yaml` | CoinbaseBTC/ETH/SOL, momentum, synthetic_mid_ohlcv, fees7.5bps and slippage5bps. live_enabled=false; armed/paper-enabled/strict-quote/no-fallback/USD/start-cash fields not explicitly established. No available_cash_v1 or GroupB option. This is not the specified isolated hourly/default-strategy/50bps study profile. Unspecified fields are not asserted false or resolved defaults. |
| `config/user.yaml` | live_enabled=true and armed=true in this separate file. The inspected strategy/paper fields do not establish a suitable simulation profile. This is not evidence of active live trading. |
| Loader source | config_editor.CONFIG_PATH is config_dir()/user.yaml; config_dir uses state_root/runtime/config. The normal non-frozen default is .cbp_state, overridable by CBP_STATE_DIR. Thus the inspected runner's default file is the runtime copy, not the root copy. Other entrypoints, process overrides and loaded state were not inspected; root copy is not declared universally unused. |
| Names-only search | Within this repo's .cbp_state subtree, one user.yaml and one execution.sqlite found; root config/ has another user.yaml. No separate nine-account config/cache copies were found in that searched subtree. This is not an inventory of the Mac or intended server. |
| Public cache query | Only market_rules_cache, venuecoinbase/coinbase_adv, and the25declared USD markets were queried. One relevant row: coinbaseBTC-USD, updated2026-04-11T23:27:00.520475Z; age5195.49hours, beyond six-hour TTL. No ETH-USD/SOL-USD or other declared CoinbaseUSD rows in this scope. Other venues/quotes/tables were not read. |
| BTC row projection | active=true; quantity step1e-8, price tick0.01, min quantity1e-8, min notional1. Product-mode fields incomplete, product status/identity proof incomplete, native increment provenance absent. This is insufficient current metadata, NOT proof that BTC's numeric increment is wrong or that an order used it. |

The intended study is on the server. No SSH, process inspection, accounts,
credentials, orders, positions or ledger tables were accessed. No HTTP, real
cache refresh, source/configuration change, job, deployment or trading occurred.
R10 remains STOPPED and original commissioning criteria are unchanged.

## Read bounds and side effects

YAML reads were size-limited and only public trading-policy fields were emitted;
no secret values or full configuration were copied. Both files' size/mtime were
unchanged during inspection. Cache query used SQLite URI mode=ro, query_only,
memory temp storage, one-second lock timeout, five-second query progress bound
and a51-row cap. Table existence was checked as an actual table before selection.
No row-update/schema/order/position query was issued.

DB size204800bytes/mtime1790136929971311696 and zero-byte WAL/mtime
1793434219353403822 were unchanged. Existing32768-byte SHM mtime changed from
1793434219362905560 to1794653786251010387 during the read. This is compatible with
SQLite read coordination; another writer cannot be excluded. It is not evidence
of a metadata-row update. No byte-for-byte comparison, sidecar restoration or
deletion was attempted. No claim of zero filesystem metadata effects is made.

## Recommended next scope

Prepare an **inactive review artifact**, not an applied configuration: nine
isolated GroupA paper profiles for the three frozen default strategies on
BTC/ETH/SOL, carrying the already adopted cash-sizing and specified hourly/cost/
quote guards. Verify them in temporary synthetic state using existing runner,
consumer and metadata checks; record paths, public settings and hashes.

Proposed output: `docs/review_artifacts/paper_profile_candidate_20261114/` only,
plus existing work log. Do not overwrite either inspected user.yaml, repurpose
this shared cache, add jobs/controllers, select live arming, or deploy a target.
GroupB remains staged after GroupA capacity, not dropped. This proposal creates
no new commissioning waiver, R7adoption or runtime authority.

INFERRED from the projected fields and reviewed guard source: a refresh cannot
solve a missing/incorrect profile and would fail the explicit paper-only/single-
account checks. The refresh command was NOT invoked. The original full target
also still requires stopped R10. Those are distinct from whether a separately
approved narrower diagnostic could eventually operate.

What do I know that could change the owner's decision that I have not yet said?
There is no verified local nine-account target to refresh in the inspected
locations. The root copy's live flags require care, but the default loader points
elsewhere and no active live process was established. Provision isolated paper
profiles first rather than changing or refreshing an ambiguous shared state.
