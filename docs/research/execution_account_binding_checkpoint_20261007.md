# Dedicated account database binding checkpoint

Active role: ENGINEER. User selected the recommended dedicated database path.
Implemented only the initial unwired storage primitive in isolated candidate
/private/tmp/cryptkeep-cooldown-review-9wbPbN.

SHOWN: explicit venue/environment/account/portfolio binding, transactional first
initialization, mismatch rejection, refusal to adopt any populated application
table, persistent reopen validation, and read-only checks that do not create
missing databases. Update/delete triggers protect routine accidental mutation;
they are not a security boundary against privileged raw database access.

VERIFIED_ENV: existing Python interpreter, isolated source, temporary databases.
Verification: original .venv/bin/python -m pytest -q -p no:cacheprovider
tests/test_execution_account_binding.py tests/test_spot_exit_owned_boundary.py
tests/test_spot_exit_receipt_probe.py tests/test_spot_exit_real_schema.py
tests/test_spot_exit_reservations.py. Result: 56 passed in 1.47s.

UNVERIFIED: trusted account-context producer, authenticated venue verification,
actual key rotation, remote holdings reconciliation, all-writer enforcement,
production integration and live authority. Test account identifiers are fixtures.
The new primitive is not called by the receipt adapter or production stores.
No existing database, credentials, config, collector or account changed.

Acceptance: READY_FOR_INDEPENDENT_REVIEW; Hume requested.
Review outcome: Hume found INSERT OR REPLACE bypassed update/delete guards.
Added BEFORE INSERT guard and replacement regression; final run 56 passed in
1.92s. Independent correction review ACCEPTED_WITH_RISK, static only. An initial
review message misstated final timing as 1.52s; corrected to measured 1.92s.
Next bounded implementation must connect verified context checks to prototype
operations; it must not pretend caller-provided strings establish ownership.
