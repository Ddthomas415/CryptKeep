# Named Public Recovery Supplement

## Objective And Scope

2026-10-18, active role ENGINEER, risk HIGH (secret-screening exceptions and
database consistency). User requested the next preservation steps after the
accepted selected-file recovery. Preserve the exact three excluded raw archives
and four named public databases, without changing the prior helper, originals,
collectors, Git state, private configuration or operational policy.

Implementation is READY_FOR_INDEPENDENT_REVIEW, not approval of a full backup.
No material assumption that a journaled database can be copied safely: eligibility
is checked at capture and again before sealing. Nonempty WAL, any rollback
journal, source mutation, symlinks or integrity failure refuse success.

## Shown Diagnosis

- All four exact public database headers identify SQLite WAL mode (read/write
  versions 2/2). Their current WAL files are zero bytes. SHM exists but is not
  copied or opened through SQLite. No source SQL connection is needed.
- `coinbase_hourly_last60d.tar.xz` was refused only for `cb/fetch.log`, containing
  exactly `done 395 273` plus newline (13 bytes).
- `coinbase_hourly_prior10m.tar.xz` was refused only for `cb2/fetch.log`, containing
  exactly `done 395 377` plus newline (13 bytes).
- CMC's July 12, 19 and 26 JSON files each match the key-shaped heuristic in the
  `SKHYx` row's third column. The saved `fetch_cmc_weekly.py:23` writes column 2
  from the public provider's `slug`, not a credential. Three exact member SHA256s
  and their enclosing archive SHA256 are pinned. This is a local schema/content
  false-positive finding, not universal credential clearance or a claim that an
  arbitrary `sk-...` string is safe.

## Implementation

New helper: `scripts/research/preserve_recovery_exclusions.py`.
New targeted tests: `tests/test_preserve_recovery_exclusions.py`.
Existing `build_recovery_copy.py` remains unchanged, SHA256
`8efaf5fc4e3ff508640fb038d6d2b1f74c7a30ece9ef1233449f491f051655a9`.

The helper supports only seven named assets. It uses the existing no-follow,
bounded, stable regular-file reader. The four databases must have WAL-mode
headers and empty/absent stable WAL; a rollback journal is always refused.
It copies exact main-file bytes into a fresh private destination and checks
`PRAGMA integrity_check` only on immutable staged/restored copies. It does not
connect to original databases or copy SHM. Source bytes and WAL state are checked
again before sealing; per-file checks are not a global atomic snapshot.

The archive exceptions are finite and content-bound: two exact public progress
lines at their exact paths/enclosing archives, plus three exact CMC member hashes.
For the latter, the one known public slug is masked only in temporary screening
memory; all other contents must pass the existing scanner. Neither stored
original nor recovery bytes are redacted, transformed or regenerated. Every
enclosing archive must match its original frozen SHA256. Traversal, links,
duplicate members, unsupported content, changed exceptions and other secret
matches remain refused. Existing blanket scanner rules are not edited.

A new archive contains the seven unchanged files, then is restored and hash
checked. All four staged and restored database copies must pass integrity checks.
A success manifest is written last. Failure leaves partial output for diagnosis;
no deletion, overwriting or automatic retry.

## Frozen Preflight

- Helper SHA256: `78096172f85a75dde24fc371ba79bdd38e1aaf8fe8eba26a1dc549b8596c3645`.
- Tests SHA256: `981514fcd279718542ceca0589a58d48236767604702e29a9a385e004c0d7b06`.
- VERIFIED_ENV command:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider tests/test_preserve_recovery_exclusions.py
```

Result: 15 passed in 0.23s, exit 0. First fixture run had two failures (a wrapper
argument collision and an unclosed fixture connection retaining WAL); both were
fixed before this frozen gate. No actual copy has run at this checkpoint.

## Proposed Bounded Invocation

Only after independent preflight review; normal external filesystem approval
still applies. ASSUMED_ENV for the unexecuted real destination/source stability.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -E -B -m scripts.research.preserve_recovery_exclusions --root /Users/baitus/Downloads/crypto-bot-pro --output /Users/baitus/Documents/cryptkeep_data_archive/recovery_supplement_20261018T192628Z
```

One new exclusive destination; both earlier recovery outputs remain untouched.
No original SQLite connection, new collection, market-data scoring, trading,
credential configuration, service startup, Git lock removal, commit or push.
This remains same-disk selected-file protection, not offsite/full environment
recovery or publication clearance. The original 41-exclusion receipt is retained
as history; a supplement can resolve seven paths without rewriting that receipt.

Required next proof: independent review of code, finite exceptions and consistency
contract; then actual command exit, restored byte hashes and saved integrity
results. No claim of actual preservation follows from synthetic tests alone.
