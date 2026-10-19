# Rev36 / 0026 bounded review

Date: 2026-10-04. Role: AUDITOR.
Decision: ACCEPTED_WITH_RISK for patch 0026's bounded correction only.
Overall series/deployment readiness: INCOMPLETE.

## Findings and disposition

No new blocking defect found within the inspected correction and targeted
tests. Both rev35 findings are resolved by separating the selected venue
from entry permission and retaining the discovered venue set across turns.

SHOWN: all seven original probes pass unchanged (rev35 history 2, rev34 venue
2, rev32 malformed event 3). The supplied runner tests also exercise unreadable
history refusing entry, the corresponding readable-history control allowing
entry, an exit surviving the history-read failure, and multiple historical
kills counting down before a new buy is written.

This does not establish safe open-position ownership across venues or approve
the complete patch series. In particular, choosing a historical venue to work
through its hold is not proof that it owns a currently held position.

## Verification

SHOWN ZIP SHA256:
508f7d31a6deff0fee2f95bec112784c70c0bf54cb1b57f74e493b473f1cf5ad.
Existing patch bytes are unchanged from rev35. Added files are patch 0026 and
the received rev35 probe copy. Applied 0026 to the isolated reviewed rev35
tree, not to the user's checkout. Held 0011 and superseded 0019 remain excluded.

VERIFIED_ENV: local Python 3.12.10; /tmp/cryptkeep-rev32.NyLA3f;
temporary test databases and existing test doubles, not campaign state.

Command:

```sh
/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_runner_venue_switch_kill.py tests/test_review_rev35_history.py tests/test_review_rev34_venue.py tests/test_review_rev32_malformed_event.py tests/test_runner_exit_accounting_event.py
```

Result: 96 passed in 8.95s. No full-suite or large matrix run.

## Remaining risks and next step

- Venue discovery is cached after its first successful scan. These tests do
  not establish correctness for concurrent runners, externally introduced
  venue history, or partial restoration of state/queue snapshots. Approval
  does not cover those operating conditions without further evidence.
- Open-position ownership and stop-state handling across venue changes remain
  unresolved, as previously recorded. Do not infer operational approval for
  multi-venue position management.
- Quarantined/damaged evidence can indefinitely block entries; there is no
  reviewed operator recovery procedure. Do not delete or mark it unwritten
  merely to unblock a campaign.
- Cloud full-suite/mutation figures remain CLAIMED. CI, Hetzner, deployment,
  profitability, full-tree identity and full-series acceptance are UNVERIFIED
  by this bounded pass.

Next bounded task: define read-only quarantine inspection and the evidence
required for any subsequent repair. Any state mutation needs separate review
and operator authorization. Preserve the open-position ownership decision as
a separate unresolved operational gate; do not silently change stop policy.

Only this review and the visible work log were changed. No implementation,
config, account, push, merge, deployment or collector changes.
