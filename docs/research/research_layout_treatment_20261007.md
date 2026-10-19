# Preserve intentional research layout

Active role GATE. Risk LOW. State ACCEPTED for the layout correction.

## Correction

Repo Doctor now explicitly allows the optional research/ artifact root. It
remains outside the required runtime baseline. No directory, capability or
research record was removed. Strict unknown-directory detection remains in
place. Two regression tests cover the allowed research root and refusal of an
unrelated duplicate-runtime directory. Updated layout/workflow documentation
without changing the user-approved platform direction.

## Evidence

The preceding accounting verification found 33 identical failures in corrected
and controlled pre-treatment snapshots. Strict Repo Doctor output identified
research/ as non-canonical, causing downstream alignment/validation failures.
After this bounded correction, the guard in the disposable checkout returns
exit 0, includes research in allowed_top_level_present, and reports no unknown
directories or suspicious files. No financial production code changed.

Full pytest completed in /private/tmp/cryptkeep-full-suite-4sde8h5z with the
same network/operator-file isolation, clean environment, disabled real keyring,
disposable state and fixed 900-second timeout. No runner-imposed slow skips.
Result: 3,889 passed, 38 explicitly skipped, zero failures, exit 0 in 286.24
seconds. All three Repo Doctor tests passed, including the unexpected-directory
refusal. This clears the previous 33 failures without removing research or
skipping failing checks. Existing warnings remain. Current production source
and Repo Doctor test hashes match the tested snapshot. Layout/workflow prose
was added after the snapshot freeze; no runtime code changed afterward.

Inventories/JUnit/summary are preserved under
docs/review_artifacts/treatment_full_suite_20261007/research_layout_corrected/.
CI, remote-host, companion integration and economic proof remain separate.
The 38 skips do not establish optional companion behavior. This low-risk
layout correction is accepted locally; financial release is not authorized.

No accounts, configuration, collector processes, orders, credentials,
publication or deployment changed.
