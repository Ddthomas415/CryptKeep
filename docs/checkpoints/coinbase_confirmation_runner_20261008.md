# Coinbase confirmation runner handoff

ENGINEER HIGH. READY_FOR_INDEPENDENT_REVIEW.

Objective: support the separately reviewed Coinbase contract without changing
the frozen OKX runner/core. New script scripts/research/run_coinbase_confirmation.py
reads explicit plan and archive paths; never fetches data, accesses credentials,
places orders, changes campaigns or creates background work.

Modes: coverage(default),register,freeze,simulate. Register emits an exclusive
plan/snapshot/fee/runner-hash-bound preregistration only before study start.
This is a local evidence receipt, not cryptographic anti-tampering proof or
live activation. Freeze/simulate require the matching receipt. Both enforce
completed-hour endpoints; warmup cannot be scored. Coverage before start
checks only currently completed warmup hours and labels full_phase_completedFalse.

Timing correction to draft: complete300hour warmup ends at study start and
cannot be verified earlier. Registration stays strictly before start; warmup
integrity is verified after its final candle closes, before evaluation scoring.
No dates, thresholds, strategies or cost assumptions changed. This resolves an
impossible pre-start full-warmup prerequisite without backdating registration.

Read all5markets strictly before signals. Sequential content manifests preserve
warmup/checkpoint/final prefixes with exact bar counts and previous hashes.
Checkpoint account is carried into final via full-prefix replay, no checkpoint
liquidation; final forced exit costs and its equity adjustment explicit.
Natural cycle count excludes terminal sells.75strategy/control/slippage outcomes
retained; no candidate/uncertainty decision implemented by this runner.

SHOWN VERIFIED_ENV: isolated targeted selection40passed in0.39s (new runner,
old archive runner and next-open core). Synthetic tests prove current fees,
next-open prices,continuity,deadline/future refusal,wrong-venue refusal,source
identities,changed prefixes,incomplete markets,natural/terminal distinction.
Actual Coinbase history/registration/simulation not run. Fullsuite/CI not run.
New report/calendar/uncertainty adapter remains future work; old reporting
tools are not silently declared compatible with this new contract.

Next proof: separate reviewer inspect code/timing correction and run targeted
tests. After acceptance, bounded exact-product history preflight only; no
prospective simulation before its registered checkpoint and full coverage.

Separate GATE: ACCEPTED_WITH_RISK for runner support only; independent40tests
passed in0.35s. Actual public warmup preflight subsequently found USDT ADA2/XRP83
missing buckets in275completed hours, while BTC/ETH/SOL grids pass. Direct
public responses confirm those omissions. All five USD products have complete
sample timestamp grids. See docs/research/coinbase_warmup_coverage_20261008.md.
No registration, activation or scoring; quote-change decision remains with user.
