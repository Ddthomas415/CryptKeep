# Prototype account-binding enforcement checkpoint

Active role: ENGINEER. Isolated candidate:
/private/tmp/cryptkeep-cooldown-review-9wbPbN.

SHOWN: SpotExitReservations requires explicit account context and an existing
matching binding before creating prototype tables. Reconciliation, reservation,
receipt recording and settlement recheck binding inside their write transaction;
venue must match. Receipt adapter checks binding before transport. Test fixtures
bind new empty databases before populating history. Unbound historical databases
are not adopted. Every public operation is covered by mismatch regression.

VERIFIED_ENV: existing Python interpreter, isolated files and temporary DBs.
Command: original .venv/bin/python -m pytest -q -p no:cacheprovider
tests/test_spot_exit_account_enforcement.py tests/test_execution_account_binding.py
tests/test_spot_exit_owned_boundary.py tests/test_spot_exit_receipt_probe.py
tests/test_spot_exit_real_schema.py tests/test_spot_exit_reservations.py.
Result: 64 passed in 1.86s.

UNVERIFIED: account context still supplied by trusted caller, not authenticated
venue evidence. Legacy production readers/writers do not enforce binding. No
live bypass, real credential rotation, remote reconciliation, full suite or
deployment proof. Existing behavior, credentials, accounts and collectors unchanged.

Acceptance: READY_FOR_INDEPENDENT_REVIEW; Hume requested.
Review outcome: Hume found selected cross-venue intent could reach transport.
Added explicit pre-fetch venue rejection and no-fetch regression. Final result:
65 passed in 1.98s, exit 0. Hume correction/prototype enforcement review:
ACCEPTED_WITH_RISK, static review; no independent test rerun or live approval.
Next requirement is a venue-specific trusted account-context producer. Do not
manufacture account identity from operator labels or key fingerprints; stop
integration if the venue/account identity mechanism is not established.
