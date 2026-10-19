# Rev26 entry-path review

AUDITOR / VERIFIED_ENV. Series acceptance: INCOMPLETE.

SHA256 comparison confirms rev26 changes only MANIFEST.txt, REVIEW_HANDOFF.md
and the folder21/folder22 READMEs relative to rev25. No numbered patch changed.
Reviewed current 0004/0005 behavior in the identical rev25 code tree at
/tmp/cryptkeep-rev25.ux4jrM; held 0011 excluded.

## P1: normal entry path misses in-flight statuses

SHOWN: strategy_runner's final open-intent scan (around lines 1796-1807)
recognizes only queued/submitted. The pending-position calculation excludes
the proposed symbol, relying on duplicate protection later. Existing submitting
or held intents therefore permit a second buy intent in the reproduced case.
The newer direct has_open_strategy_intent query recognizes these statuses but
is not used by that normal-path scan. This is not a reopening of the corrected
cooldown protective-exit lookup; it is the previously separate normal-path gap.

Extended the supplied own-pending-entry scenario across all four in-flight
statuses. queued/submitted pass; submitting/held fail by emitting a new buy.
Both queue discovery methods report the pending BTC/USD entry, and the direct
lookup returns true. The queue/account are test doubles: this proves runner
emission behavior, not actual duplicate exchange fills or a concurrency race.
Durable reproduction:
docs/review_artifacts/20261003_currency_config/pending_status_review_probe.patch.

Minimum next correction: use the reviewed non-truncated, fail-closed lookup
on the normal entry path, with regression coverage for all in-flight statuses,
old intents behind closed history and unreadable storage. That does not itself
create an atomic reservation; do not describe it as a concurrency solution.

## Bounded results and remaining proof

No additional blocking finding in 0004's current per-symbol price handling in
this pass. Rotation evaluates a symbol every N loops; this changes wall-clock
cadence and is not proof of unchanged multi-symbol strategy economics.
0005 counts serial queued entries but reads queue symbols, notionals and paper
positions separately, then enqueues later. The runner has a single-instance
lock; do not invent a demonstrated two-runner race. Cross-component reservation
and fill/reconciliation interleaving remain unverified. Neither concurrency
safety nor all portfolio limits are accepted on these tests alone.

Python 3.12; PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1:

```sh
python -m pytest -q -p no:cacheprovider tests/test_runner_multi_symbol.py tests/test_runner_pending_entry_exposure.py tests/test_runner_exposure_pct.py
# 65 passed in 3.76s
python -m pytest -q -p no:cacheprovider tests/test_review_pending_statuses.py
# 2 failed, 2 passed in 0.59s
```

No new repair, collector, config/account mutation, deployment or host access.
Prior accepted 0014/0015 dispositions stand. Do not stack a numeric-config
repair in this review; first close the reproduced entry-path gap. 0009 cash
provenance and overall series readiness remain unresolved.
