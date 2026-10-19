# Daily model timing and provenance checkpoint

AUDITOR, read-only source/artifact inspection. No strategy changes or new trial.

## SHOWN

Archived plan daily_trend_recent_20260926/plan.json declares prior completed
closes, next-open execution, 200-bar warmup. Result is explicitly exploratory
signal-only, not full campaign replay. Its August 20 buy is timestamped at
00:00 UTC. That timestamp is modelled bar-open execution, not observed intent
submission or local receive time.

Current scripts/research/compare_daily_trend_cash.py uses rows[i-200:i] closes
to decide at row i, prices execution from row i open, and timestamps it with
row i timestamp. Thus the inspected implementation excludes the current bar's
close from its decision. It does use same-day close for equity valuation.
No capture-time row later than the modelled open belongs in an as-of join.

However current comparator SHA256 is
605cda5fa3b73ac77ba46bfa35460b95c6379b448517bc4582eeb151e89f20b7,
while archived plan pins
fa0af1f418bd87ad177f0c37e4346e1293a52c53bab89c7086f9caf51b5cd8fd.
Current signal source SHA256 matches its pinned value:
2ba45323cdca392a321107784ee432827fbec91c16b869c9d784f7672a81b193.
Current comparator therefore cannot alone establish exact historical code
identity. No matching original comparator was recovered in this bounded pass.

## Rule distinction

Current comparator's default enters whenever flat with prior close above SMA;
its optional regime entry is off by default. The documented campaign contract
requires a completed-close crossing plus regime approval. The archived result
explicitly lacks full regime/exit/risk stack. These are different claims even
where particular trade timestamps happen to agree.

The host capture two seconds before modelled entry supports capture-time
availability only. It does not establish network receipt, computation latency,
real fill price, or full production eligibility. Treat it as observational
coverage, not actual execution or promotion evidence.

## Disposition and next step

Do not run an E02 profitability comparison against this artifact as though it
were the complete existing strategy. Preserve it as exploratory history.
First recover the comparator matching the pinned hash from supplied artifacts,
or explicitly version a new replay under the accepted crossover contract.
Do not overwrite old results or silently replace their source identity.
The alternative new replay requires a declared execution-timing/cost contract,
not a claim of exact live replay from candles.

Exact historical comparator provenance remains UNVERIFIED; production replay
and economic qualification INCOMPLETE. No tests run for source inspection.
