# CMC Certificate Trust Repair

SHOWN: the Python 3.12 runtime reports no existing default CA file or directory. Its installed certifi CA bundle is available. The October 11 manual capture failed with CERTIFICATE_VERIFY_FAILED; that degraded artifact remains unchanged.

The v3 logger now explicitly loads certifi roots into a default SSL context for all default HTTP requests, including book capture. Certificate verification and hostname verification remain required. Failures are retained as evidence; no insecure retry exists. Original v1/v2 loggers and all snapshots remain unchanged. New snapshots record the CA bundle hash and TLS policy alongside the changed collector hash. This does not prove historical data authenticity or expand accepted scoring hashes.

Verification: logger and snapshot-evidence tests, 17 passed. Separate review required before operational capture. No system trust-store, credentials, schedules or trading settings changed.

Injected test/custom transports are labeled CUSTOM_TRANSPORT_UNVERIFIED without a CA hash. Independent review caught the earlier unconditional label; that defect was corrected before operational capture.

Status: ACCEPTED_WITH_RISK, independently reviewed narrow transport/provenance repair. Reviewer reproduced 17 passing tests. Fresh public capture at 2026-10-11 14:45:51 UTC returned OBSERVED, exit 0; preserved as v2_2026-10-11_144551_385110Z_a0abc038d34c4124833750850f0703b4.json. This is one successful manual capture, not unattended scheduler proof. Earlier degraded capture remains unchanged; inventory requires a new chained seal for added snapshots before bounded analysis.
