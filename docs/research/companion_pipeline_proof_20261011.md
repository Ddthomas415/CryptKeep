# Companion Pipeline Proof

Scope: bounded local integration proof, not production restoration or dashboard activation.

Added real RSS parsing, recovered HTML normalization functions, recovered document-model validation, and authenticated HTTPX/FastAPI ASGI request serialization. Extended the existing disposable PostgreSQL/Qdrant-local persistence test to exercise this input through store/retrieve routes, preserve content/source/date identity and test denied auth, index failure, canonical retry and index reopen. Routes are test adapters; recovered functions run through the existing AST harness, not historical full-service startup. Source is a synthetic example.org fixture, not authentic external news. Object storage and semantic retrieval quality are not proven.

Installed dependencies only in /private/tmp/cryptkeep-intelligence-proof-20261011; project environment unchanged. Real dependency run:42passed,2opt-in persistence tests skipped. Explicit persistence opt-in run:3cleanup tests passed,2persistence cases failed before database initialization with Bad CPU type in executable. Existing /usr/local/bin/initdb is x86_64; host is arm64. No disposable cluster started and no production database touched.

Implementation of the proof is READY_FOR_INDEPENDENT_REVIEW; durable integration remains BLOCKED on native PostgreSQL executable availability. No complete pipeline, authentic feed, production auth/startup, service deployment or dashboard connectivity claim. Do not repeat existing date/index repairs. Native dependency decision requested before host software changes.

Independent review: ACCEPTED_WITH_RISK for test implementation/documentation only, no blockers. Reviewer ran22passed2skipped direct slice and46passed2skipped expanded feed/news selection; counts differ from parent's42passed2skipped selection. Broader reviewer collection lacked yaml in the isolated environment; not a full-suite pass. Real persistence remains BLOCKED, opt-in not independently rerun.

## Native dependency and persistence completion

User approved native test dependencies. Homebrew installs failed on unavailable platform bottles/dependencies; no PostgreSQL service or default cluster was created. Built official PostgreSQL17.11 source in /private/tmp with SHA256 dd27f2b3c59e73ed14aa3324901242bf69a032a6347805f274e6260322d42979, matching formula source checksum. Private prefix /private/tmp/cryptkeep-native-postgresql17; initdb verified arm64. Optional ICU/readline/zlib omitted for this disposable test build. This is not a production database installation.

Initial native test startup failed because macOS Unix socket path exceeded103bytes. Use a new short --basetemp path for each run (pytest clears an existing basetemp; never point it at valuable data):

```sh
PATH=/private/tmp/cryptkeep-native-postgresql17/bin:/usr/bin:/bin:/usr/sbin:/sbin CBP_TEST_MEMORY_PERSISTENCE=1 /private/tmp/cryptkeep-intelligence-proof-20261011/bin/python -B -m pytest -q --basetemp=/private/tmp/cbp-pg-proof-UNIQUE tests/test_companion_memory_persistence.py
```

Parent result:5passed in2.39s, no skips. Both owned clusters separately checked with pg_ctl status: no server running. Real PostgreSQL/local-Qdrant persistence, index failure/retry and reopen now proven for this synthetic/AST/ASGI boundary only. Original database installations and project environment unchanged. Temporary binaries can disappear on OS cleanup; this is a reproducible test recipe, not durable deployment. READY_FOR_INDEPENDENT_REVIEW of execution proof.

Execution proof independently ACCEPTED_WITH_RISK: reviewer reproduced5passed2.29s with approved unsandboxed run and verified both review-owned clusters stopped. Source archive checksum is parent-verified only, not independently checked. Earlier BLOCKED status is superseded for this bounded persistence test, not for production restoration.
