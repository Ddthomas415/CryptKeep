**Finding**
**P1, SHOWN: ambiguous queue metadata can alter provisional counters and admit new buys.** [intent_queue_sqlite.py:325](/Users/baitus/Downloads/crypto-bot-pro/storage/intent_queue_sqlite.py:325) uses permissive `json.loads`, silently accepting duplicate keys.

Independent probes stored two conflicting `exit_event` keys: a loss followed by a gain. Recovery selected the gain, applied `cum_pnl=+2`, reported `unsettled=False`, and the real runner subsequently queued a new buy. This violates the requirement that uncertain/corrupt accounting evidence block entries.

Use strict decoding that rejects duplicate keys, including nested duplicates, and preserve the original raw metadata as quarantined evidence. Do not silently select one interpretation.

**Independent Verification**
```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r8-accounting-gate.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_exit_event_journal.py tests/test_paper_exit_accounting.py --tb=short
```
- **137 passed in 12.12s:** 93 journal and 44 accounting cases.
- Additional probes: **two failed, one passed**. Failures demonstrated ambiguous accounting and consequent entry admission; acknowledgement-loss recovery passed.
- Saved-before runner: **two expected failures in 0.73s**.
- Initial unwritten-marker implementation: **one expected failure in 0.74s**.
- **11/11 final hashes matched** [final_hashes.json](/Users/baitus/Downloads/crypto-bot-pro/docs/review_artifacts/paper_exit_accounting_r8_20261103/final_hashes.json); whitespace check passed.

Author receipts were inspected, **not independently rerun**: consolidated **788 passed/one obsolete FakeDB-fixture failure**, followed separately by **21 passing cooldown cases**. The durable-queue fixture replacement preserves the assertions and does not justify claiming one all-green 789-case run.

**Disposition**
**Written-exit accounting prerequisite GATE: REJECTED pending the decoding correction and regressions.** Queue-first recovery, atomic counter application, permanent markers and provisional 49-count kill behavior have substantial passing evidence, but the fail-closed corruption boundary remains incomplete.

This accounting is intent-time/reference-price **provisional**, not realized P&L. Full R8, R4, operational readiness and economics remain unverified. The preserved stop-reset policy and ordinary 200-row scan were not redesigned. No implementation or operational changes were made during review.

What do I know that could change the owner's decision that I have not yet said?
