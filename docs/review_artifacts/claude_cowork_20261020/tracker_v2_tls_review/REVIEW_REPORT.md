# Independent review: tracker v2 TLS trust fix (certifi CA bundle)

Reviewer workspace: `/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/tls_reviewer/`
Reviewed: `docs/research/paper_btc_eth_trend_v2_20261012/tracker.py` (sha256 572118ad...) and `test_tracker.py` (2cebe133...)
against `original/tracker.py` (71675322...) and `original/test_tracker.py` (3ac2cef1...). Date: 2026-10-20.

Labels: **SHOWN** = I reproduced it here. **CLAIMED** = from CONTEXT.md or the author. **UNVERIFIED** = nobody has shown it.

## Verdict: ACCEPTED_WITH_RISK

The code change is minimal and correct. It does not weaken security. With the same data, its outputs are identical to the
original's. Verification stays on and the certifi roots really load. Nothing falls back to unverified TLS.

The residual risk is operational. Nobody has shown that the 2026-10-19 failure was caused by missing CA roots, as opposed
to, for example, a TLS-intercepting proxy. If it was not, the next scheduled run fails the same way. It would fail loudly,
leave only the lock file and do no harm to the ledgers. The test gaps listed below do not block acceptance.

## Findings

1. **major (residual risk, not a code defect): the root cause is not established, so it is UNVERIFIED that the fix will work on the Mac.**
   - The error text is CLAIMED: the author relays it from an auditor and has not seen the run log.
   - SHOWN: the exact string `CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate` comes out of two different setups:
     - missing roots (the original tracker with `SSL_CERT_FILE`/`SSL_CERT_DIR` pointing nowhere, demo [C]/[F]);
     - an untrusted intercepting CA (the fixed tracker, demo [B]/[F]).
   - SHOWN: the "only `.lock`" footprint does not identify the cause either. Any exception in `fetch()` after the lock is
     opened leaves the same footprint.
   - CLAIMED: the README says live dry runs on 2026-10-12 succeeded, but the interpreter used is not recorded. If they used
     the same `.venv`, that contradicts the missing-roots hypothesis.
   - CLAIMED: the CMC precedent ("runtime default verify paths absent") supports the hypothesis.
   - How to close this is in "Right proof" below.
2. **minor (trade-off): trust is now certifi-only.**
   - SHOWN (stdlib `ssl.create_default_context` source, 3.12 and 3.13): passing `cafile=` skips `load_default_certs()`.
     So `SSL_CERT_FILE`, `SSL_CERT_DIR` and OpenSSL's default paths are ignored.
   - SHOWN, demo [B]/[F]: with the test CA in `SSL_CERT_FILE`, the original fetch succeeds and the fixed fetch fails.
   - Consequences:
     - Behind an intercepting proxy, the fix does not help. Unlike the original, it also cannot be rescued with an env var;
       that would need a code change.
     - The outcome when it fails is unchanged: a loud failure, only `.lock` written, no ledger writes.
     - Env-injected trust can no longer redirect a public-data fetch, which is arguably a hardening.
   - General knowledge, not SHOWN here: python.org builds' OpenSSL does not read the macOS keychain. So neither the old
     nor the new version used keychain trust, and nothing is lost on that front.
   - This does not matter for a fetcher of public candles. It matters only if the scheduled environment uses a private-CA proxy.
3. **info (positive): verification is real and harder to defeat than the original's.**
   - SHOWN on both 3.12 and 3.13: `tls_context()` gives `CERT_REQUIRED`, `check_hostname=True` and `x509_ca=137`.
     137 equals the number of PEM blocks in certifi 2026.2.25's `cacert.pem` (272,441 bytes). This matches the CLAIMED
     size and count for the Mac's copy.
   - SHOWN real handshakes over loopback inside a network namespace with no external interfaces:
     - an untrusted CA is rejected ([A]);
     - a hostname mismatch is rejected ([E]);
     - the real `fetch()` rejects a MITM that presents a valid-looking cert for `api.exchange.coinbase.com` from an untrusted CA ([F]);
     - positive control: `fetch()` succeeds once the server's CA is in the bundle ([F]).
   - SHOWN [D]: if something sets `ssl._create_default_https_context = ssl._create_unverified_context` process-wide,
     the original accepts the untrusted server and the fixed tracker still rejects it.
   - SHOWN by AST and grep: the fixed source has no `os.environ`/`getenv`, no new CLI flags (3 `add_argument`, unchanged),
     and no `CERT_NONE`, `check_hostname`, `verify_mode`, `Purpose` or unverified-context code.
4. **minor (test gaps): three of my mutations survive the full 30-test suite, and the source-scan test is literal-string only.**
   - M3, an env-gated bypass via `setattr`, survives. The tests catch it only when the env var is set during testing (M3b).
   - M4, a silent fallback to default roots when certifi is missing, survives.
   - M8, which broadens trust to certifi plus system roots, survives.
   - M1 (`Purpose.CLIENT_AUTH`, which silently turns verification off) gets past T3, the source scan, but T1 and T2 catch it.
   - SHOWN by AST and grep: none of these patterns is in the actual change.
   - Optional hardening:
     - an AST assertion that `tls_context` is exactly `return ssl.create_default_context(cafile=certifi.where())`;
     - an assertion that `tracker.py` contains no `environ`;
     - a subprocess test that importing the tracker fails without certifi.
5. **minor: certifi is now a hard dependency at import.**
   - SHOWN: in an interpreter without certifi, the fixed tracker exits 1 with `ModuleNotFoundError` on every path,
     including the "waiting" path. It fails before creating the state dir or the lock. The original ran and wrote `.lock`.
   - Failing loudly is preferable here. The obvious silent fallback (M4) would not weaken security, because it is still
     verified, but it would quietly reproduce the 2026-10-19 failure mode. Failing at import writes nothing.
   - SHOWN: a missing, garbage or empty bundle also fails before any request, leaving only `.lock`
     (`FileNotFoundError` / `ssl.SSLError`).
   - The module docstring still says `Usage: python3 tracker.py ...` without mentioning the `.venv`/certifi requirement.
     The README is not in the inputs, so whether the docs mention it is UNVERIFIED.
   - CLAIMED: certifi is pinned in `requirements-pinned.txt:37` and installed in the Mac `.venv`.
6. **info: the only behavioural change is the TLS context.**
   - SHOWN by AST comparison of every top-level statement:
     - the only differences are the `import` lines (`ssl` added, `import certifi`), the new `tls_context()` and `fetch()`;
     - `fetch()` is AST-identical to the original once exactly `ctx = tls_context()` and the `context=ctx` keyword are removed;
     - the module docstring and all other functions are identical: `replay`, `sync`, `main` (lock), `load_ledgers`,
       `write_all`, decision logic.
   - SHOWN end to end with synthetic Coinbase-format candles served by a fake `urlopen`, on both 3.12 and 3.13:
     - original and fixed produce byte-identical ledgers and `state.json`;
     - both send the same URLs in the same order (2 requests);
     - this holds for both scenarios tested, a run at 2026-10-26 00:47Z and a counterfactual run at 2026-10-19 00:47Z.
   - Unchanged: retries (4 attempts, 2/4/6 s back-off), the 30 s timeout and lock placement.
   - The context is built once per run at about 22 ms (SHOWN, py3.12).
7. **info: what the new tests assert, and how they fail on the original.**
   - All three fail on the original tracker (SHOWN), though T1 fails for an incidental reason.
   - T1 `test_fetch_uses_verified_tls_with_certifi_bundle` asserts:
     - `create_default_context` is called exactly once, with no positional args and only `cafile=certifi.where()`;
     - the context has `CERT_REQUIRED` and `check_hostname is True`, and `x509_ca > 0`;
     - two `urlopen` calls, both with that same context and timeout 30, for BTC-USD and ETH-USD on `https://api.exchange.coinbase.com/`.
     - The name matches. On the original it fails with `AttributeError` because `T.ssl` is absent, but mutations show its
       assertions catch the real properties (author's no-cafile case; my M1, M5 and M7).
   - T2 `test_certificate_failure_writes_nothing_and_never_falls_back_to_unverified` asserts:
     - `main()` raises `URLError` matching `CERTIFICATE_VERIFY_FAILED`;
     - exactly 4 `urlopen` calls are made, each with `CERT_REQUIRED` and `check_hostname=True`;
     - the state dir contains only `.lock`.
     - Scope of "never falls back": only contexts passed to `urlopen`, and only over the 4 attempts on BTC's first window.
     - On the original it fails with `TypeError`, because its fake `urlopen` requires a `context` keyword.
   - T3 `test_no_unverified_tls_path_in_source` asserts that 5 literal strings are absent, that there is exactly one
     `urlopen(` and that `context=ctx` is present. The name claims more than this literal check proves (see finding 4).
8. **info: no conflict with the documented guarantees.**
   - The append-only ledgers, anomaly halt, lock, gap/invalid-data refusal and `reconstructed` flag are in code the change
     does not touch (SHOWN by AST). The 27 pre-existing tests pass unchanged (SHOWN).
   - SHOWN with synthetic data: the next successful run at the CLAIMED schedule time, 2026-10-26 00:47Z, records:
     - the 2026-10-18 decisions as `reconstructed=true` (lag 168.78 h);
     - the 2026-10-19 executions and the 10-19 to 10-24 marks as `reconstructed=true`;
     - the 10-25 marks and decisions as `reconstructed=false`.
   - This is correct per the guarantee and is a consequence of the outage, not of the change.
   - The 10-18 decision is already more than 24 h late as of today, so even an earlier run records it as reconstructed.
     Whether to run earlier is the operator's call.
9. **info (pre-existing, unchanged, out of scope): `fetch()` puts the raw `+00:00` from `isoformat()` into the query string without percent-encoding.**
   - SHOWN: a form-style parser turns `+` into a space. My first fake `urlopen` hit exactly this.
   - The line is identical in the original. The CLAIMED successful dry runs on 10-12 suggest the endpoint accepts it.
   - Noted only because it sits next to the changed line.

## Commands run and results (all under the reviewer workspace)

| # | Command (abridged) | Result |
|---|---|---|
| 1 | `cd tls_review_input && sha256sum -c ../tls_review_input.sha256` (at start and again at end) | 13/13 OK both times; inputs unmodified (SHOWN) |
| 2 | `python3.12/3.13 -m venv venvX; pip install pytest certifi==2026.2.25` | py 3.12.3 and 3.13.16, OpenSSL 3.0.13, certifi 2026.02.25, pytest 9.1.1; same `cacert.pem` sha256 fc9165a1... in both |
| 3 | `diff -u original/tracker.py repo_fixed/.../tracker.py` (and the test file) | Changes: imports, `tls_context()`, `ctx = tls_context()`, `context=ctx`; 3 tests appended |
| 4 | `unshare -rn venvX/bin/python -B -m pytest -p netguard -q test_tracker.py` on fixed (py3.12, py3.13) | **30 passed** on each; NETGUARD attempts=0 (source: pytest output) |
| 5 | Same, with `SSL_CERT_FILE=/nonexistent SSL_CERT_DIR=/nonexistent` (no default roots, as on the Mac) | 30 passed on each; attempts=0 |
| 6 | Original tracker + original tests (py3.12, py3.13) | 27 passed on each |
| 7 | Original tracker + new tests (py3.12, py3.13) | 3 failed (T1 `AttributeError` no `T.ssl`; T2 `TypeError` missing `context`; T3 `'context=ctx' in src` false), 27 passed |
| 8 | Author's `author_mutation_script.py` (layout rebuilt, run under `unshare -rn`) | Reproduced: all 6 variants fail at least one new test ("no cafile" is caught only by T1; "unverified fallback on retry" only by T2 and T3) |
| 9 | `scripts/ast_compare.py original fixed` | Only the imports, `tls_context` and `fetch` differ; `fetch` minus the TLS additions equals the original; docstring identical |
| 10 | `unshare -rn ... scripts/tls_handshake_demo.py` (py3.12, py3.13) | All 14 expected outcomes hold (log: `handshake_demo_py3.1{2,3}.log`) |
| 11 | `unshare -rn ... scripts/e2e_equivalence.py` (py3.12, py3.13) | Ledgers and `state.json` byte-identical, original vs fixed; reconstructed labels as in finding 8 (log: `e2e_py3.1{2,3}.log`) |
| 12 | Fixed and original tracker CLI under `venv_nocertifi`, `--start 2099-01-04` | Original: exit 0, writes `.lock`. Fixed: exit 1 `ModuleNotFoundError: No module named 'certifi'`, no state dir |
| 13 | `unshare -rn ... scripts/broken_bundle.py` (py3.12, py3.13) | missing → `FileNotFoundError`, garbage → `SSLError PEM lib`, empty → `SSLError NO_CERTIFICATE_OR_CRL_FOUND`; 0 `urlopen` calls; only `.lock` |
| 14 | `unshare -rn ... scripts/my_mutations.py` (py3.12, py3.13) | See table below (log: `my_mutations_py3.1{2,3}.log`) |
| 15 | netguard positive control: `urlopen('https://127.0.0.1:9/')` with the guard loaded, in the netns | Blocked, attempts=1, so the guard is not vacuous |
| 16 | `grep` of the test call sites | `run()` always passes `candles`, so `fetch` is never reached. Direct network-path calls exist only in T1 (`T.fetch`) and T2 (`T.main`), and both monkeypatch `urlopen` |

The handshake demo [10] used a throwaway test CA made with `openssl` in `pki/`. All TCP stayed on loopback inside
`unshare -rn`, where the namespace has only `lo`. For [F], connections were redirected to loopback before any name
lookup, so no DNS happened. The first version of the demo gave two false results because urllib (3.12+) caches a global
opener whose `HTTPSHandler` builds its default context once (SHOWN in the stdlib source). I fixed the harness by
resetting the opener before each call and re-ran it. Only the corrected run's results are reported.

Python 3.13 note (SHOWN): `create_default_context` adds `VERIFY_X509_STRICT|VERIFY_X509_PARTIAL_CHAIN` and a TLS 1.2
minimum. The default context does this too, so it is not specific to this change. The Mac runs 3.12.10 (CLAIMED).

## Reviewer's mutations (distinct from the author's), results identical on py3.12 and py3.13

T1 = fetch_uses_verified_tls, T2 = certificate_failure..., T3 = no_unverified_tls_path_in_source.

| Mutant | Suite result | Caught by |
|---|---|---|
| M1 `create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=...)`: verification off, no banned string | 2 failed / 28 passed | T1, T2 (T3 misses it) |
| M2 `context=ctx if attempt == 0 else None`: retries use the default context | 1 failed / 29 passed | T2 only |
| M3 env-gated `setattr(c,'check_hostname',False); setattr(c,'verify_mode',VerifyMode(0))`, env unset | 30 passed | **none (survives)** |
| M3b same mutant with `TRACKER_TLS_INSECURE=1` set during testing | 2 failed / 28 passed | T1, T2 |
| M4 `try: import certifi except ImportError: certifi=None` and `cafile=... if certifi else None` | 30 passed | **none (survives)** |
| M5 `capath=os.path.dirname(certifi.where())` (loads 0 roots) | 1 failed / 29 passed | T1 only |
| M6 retries 4 → 1 (non-TLS behaviour) | 1 failed / 29 passed | T2 only |
| M7 `https://` → `http://` (plaintext downgrade) | 1 failed / 29 passed | T1 only |
| M8 `c.load_default_certs()` added (trust = certifi + system/`SSL_CERT_FILE`) | 30 passed | **none (survives)** |

NETGUARD attempts=0 in every mutant run. Counts are from the pytest summary lines in `my_mutations_py3.1{2,3}.log`.

## Is a live network run needed? Right proof

- **To accept the code change: no.** Correctness, security properties and output equivalence are SHOWN offline
  (findings 3, 6, 7 and 8). I made no request to Coinbase or any market-data endpoint, and only pip touched the network.
- **To accept that the operational failure is fixed: yes, in the end.** That proof belongs to the operator, on the Mac,
  in the scheduled interpreter. In order:
  1. Offline: `./.venv/bin/python -c "import ssl,certifi; print(ssl.get_default_verify_paths()); print(ssl.create_default_context().cert_store_stats()); print(ssl.create_default_context(cafile=certifi.where()).cert_store_stats())"`.
     The missing-roots hypothesis predicts `x509_ca` of 0 for the default context and 137 for certifi.
  2. Inspect the environment the scheduler actually runs with (`HTTPS_PROXY`, `SSL_CERT_FILE`, any sandbox or proxy).
     A private-CA intercepting proxy would defeat this fix (finding 2).
  3. Run `./.venv/bin/python -B -m pytest docs/research/paper_btc_eth_trend_v2_20261012/test_tracker.py` in that `.venv`.
     The expected result is 30 passed.
  4. The definitive evidence is the next scheduled run (2026-10-26 00:47Z, CLAIMED) or a manual run the operator
     authorizes, producing ledger files and `state.json` with no `CERTIFICATE_VERIFY_FAILED`.

## Remains UNVERIFIED

- The cause of the 2026-10-19 failure. The error text is CLAIMED via an auditor, and missing roots vs. a proxy is not
  distinguished.
- Whether the Mac `.venv` lacks default roots. This is CLAIMED via the CMC precedent, and the 10-12 dry-run interpreter
  is unknown.
- Whether `api.exchange.coinbase.com`'s current chain anchors in certifi 2026.2.25. Weak evidence only: common public
  roots are present (ISRG X1/X2, GTS R1/R4, DigiCert Global Root CA/G2, Amazon Root CA 1, USERTrust RSA, GlobalSign).
- Behaviour on the macOS python.org 3.12.10 build and its bundled OpenSSL. I tested Linux CPython 3.12.3 and 3.13.16
  with OpenSSL 3.0.13.
- That `original/*` are the current repo files and that the `repo_fixed/` dependencies are byte-identical to the
  operator repo. CLAIMED; I could only check the provided hashes.
- The certifi pin and installation in the Mac `.venv` (CLAIMED), the CMC logger code and its tests (CLAIMED; not in the
  inputs), and the README/docs (not in the inputs).
