# CMC evaluation timing gap

Active role: AUDITOR. Original evaluation remains unchanged.

SHOWN: the v1 logger header registers first appearance within any 30-day window,
Coinbase ask entry, closest-snapshot bid exits at 1/7/30 days, 1.2% fees per side,
matched BTC times/costs and primary 7-day mean excess with a 90% entry-day
bootstrap interval above zero after at least 90 days of logs.

The header gives no maximum exit-time deviation. A delayed snapshot can therefore
be mislabeled as a horizon it does not measure. It also leaves ties, multiple
manual runs on one day, missed-list observations, identity eligibility timing,
quote freshness and overlapping-cohort statistical dependence unspecified.
Ninety collection days alone do not ensure all 30-day cohorts have matured.

Recommended amendment, not applied: select the valid snapshot closest to each
target, require it to fall within plus/minus 12 hours, prefer the earlier snapshot
on an exact tie, and mark absent endpoints missing rather than extend the horizon.
Report actual elapsed time and all excluded/missing counts. The tolerance is a
proposed operational choice, not an empirically optimal parameter.

Preserve the original 1.2% primary fee and primary 7-day objective; observed-tier
fee sensitivity must be separately labeled. Preserve every original snapshot.
Identity verification cannot retroactively make an unverified entry executable.
Do not treat overlapping coin/day events as independent observations.

Operator approved the recommended plus/minus 12-hour tolerance on October 9.
Separate helper `scripts/research/cmc_endpoint_timing.py` implements inclusive
boundaries, nearest selection, earlier exact ties and explicit missing outcomes.
It rejects naive timestamps and duplicate observation times rather than silently
resolving ambiguous records. Seven targeted tests pass.

The helper accepts already validated observations; it does not establish quote
freshness, identity, cohort eligibility, maturity, fees or statistical acceptance.
It is not connected to a scoring pipeline yet. Other gaps above remain open.
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Logger, schedule, dataset, strategy and
account remain unchanged.
