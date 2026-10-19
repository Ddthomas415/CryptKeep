# C4 independent review 1 of v1 - verdict BLOCKED

Provenance: final report returned by a separate reviewer subagent (general-purpose, no implementer
context) on 2026-10-19 UTC, transcribed by the implementer (Claude, Cowork) for audit. Content, numbers,
labels and verdict follow the reviewer's report; wording is lightly condensed in places, so treat this
as a faithful summary, not a byte-exact copy (the original exists only in the implementer's session). Reviewed
v1 files: pinned_run_inputs.py 09830b0e..., test_pinned_run_inputs.py cb3e7e15... . Its probe file is
`first_reviewer_probes.py` in this folder (written against v1). Claims below are the reviewer's;
the implementer independently reproduced F1, F2 and F3 (work log 2026-10-19T01:01:50Z).

---

Verdict: **BLOCKED** — two reproduced cases where the guard leaves/writes a `result.json` despite a
tampered pin. Input files unchanged.

## 1. Hash checks
- `pinned_run_inputs.py`: start 09830b0e…a984704 ✓, end ✓ (my working copy identical)
- `test_pinned_run_inputs.py`: start cb3e7e15…36833630 ✓, end ✓

## 2. Existing tests
`PYTHONDONTWRITEBYTECODE=1 <venv>/bin/python -m pytest -p no:cacheprovider -q tests/test_pinned_run_inputs.py`
(from c4_reviewer/repo): Python 3.12.3: **36 passed, 0 failed**; Python 3.13: **36 passed, 0 failed**.
What they assert: happy path (receipt exists/result absent inside compute; receipt file hashes,
revision, runtime; result equals return); 25 tamper cases → failure starting with expected reason and
`out/` absent; sums self-listing (relies on hash_mismatch of sums, not a dedicated check);
all-failures (only two hash mismatches); plan-hash mismatch; NaN plan; mid-compute change (receipt
stays, no result); compute error/non-dict/NaN result (no result); existing out_dir (FileExistsError,
empty). Not covered: symlinked root, FIFO, directory pin, compute mutating plan, compute writing
result.json, masked failures.

## 3. Claims
1. **Partially holds.** Hash/unlisted/missing/symlink/self-listing hold in probes, but unlisted file
   inside an unreadable subdir is accepted (os.walk silently skips, F4), and `"model": null` disables
   model pinning (F9).
2. **Does not hold.** Structural errors raise before any file check; sums mismatch skips member checks;
   first bad sums line stops parsing; pinned directory / empty package name / non-FileNotFound OSError
   in _check_set raise raw exceptions, not PinError (F5/F6).
3. **Holds.** Receipt `open("xb")`, flush, fsync before compute (parent dir not fsynced, F13, code-read).
4. **Does not hold.** Post-run `verify(plan)` uses the same dict compute received and can mutate:
   compute repointing `root` makes result.json get written with a tampered input in place (F1);
   compute-written `result.json` survives refusal (F2); plan file not re-checked after compute (F7).
   Compute-error → no result, NaN refusal, exclusive create: hold.
5. **Partially holds.** Inside root, symlinks refused; symlinks in the root path itself are followed
   (F3). lstat-then-open race on parents UNTESTED (content must still match hash). No escape from root
   found.
6. **Holds.** 36/36 on both; stated "reverted change" limit reproduced.

## 4. Findings
| id | sev | label | description | minimal repro |
|---|---|---|---|---|
| F1 | BLOCKER | SHOWN | Post-run check uses compute's (mutable) plan dict; compute repoints it → result.json written with tampered input still present | compute(p): write `TAMPERED` to data/excl.csv; `p["root"]=<pristine copy>`; return {} → run_pinned writes result.json. Fix: pass compute a deepcopy / re-verify from original. |
| F2 | BLOCKER | SHOWN | Compute-written `out/result.json` survives a PinError (e.g. `{"v":999}` stays on disk), so result.json existence ≠ verified | compute writes out/result.json, then tampers an input, returns |
| F3 | BLOCKER (claim 5 wording false; content still hash-checked) | SHOWN | Symlink in root path followed; run accepted | `plan["root"]=symlink→real root` |
| F4 | BLOCKER (claim 1 false for non-root runs; impact low) | SHOWN | Unreadable subdir in a set skipped silently; unlisted files inside accepted | `data/candles/locked/extra.json` unlisted, `chmod 000 locked`, run without DAC override (setpriv --bounding-set -dac_override,-dac_read_search) → verify ACCEPTED |
| F5 | NON-BLOCKING | SHOWN | FIFO listed in sums or pinned as input → `os.open` without O_NONBLOCK blocks forever (fail-closed but hang) | mkfifo data/fifo; pin it; verify timed out 6 s |
| F6 | NON-BLOCKING (claim 2) | SHOWN | Raw exceptions / masked failures | pinned dir → IsADirectoryError from os.fdopen (fd potentially leaked); packages {"":"1"} → ValueError; tampered sums + tampered member → only ['hash_mismatch:…SHA256SUMS']; missing prereg sha256 + changed source → only ['preregistration_pin_required'] |
| F7 | NON-BLOCKING | SHOWN | Plan file not re-verified after compute; edit during compute undetected (in-memory plan with original hash used) | compute rewrites plan.json → result written |
| F8 | NON-BLOCKING | SHOWN | Duplicate JSON keys accepted (last wins); pinned plan can mislead a human reader | append `, "model": null}` to valid plan + tamper weights → compute runs |
| F9 | NON-BLOCKING | SHOWN | `"model": null` treated as absent while `"runtime": null` refused; `"runtime": {}` enforces nothing silently | see probes |
| F10 | NON-BLOCKING | SHOWN | out_dir inside a pinned set: compute runs, post-check refuses (`unlisted_file:…/pin_receipt.json`) — fail-closed but wasted run, no up-front check | out=root/data/candles/out |
| F11 | NON-BLOCKING | SHOWN | Empty extra subdirectory in a set accepted | mkdir data/candles/emptydir |
| F12 | NON-BLOCKING | SHOWN | Trailing blank line in SHA256SUMS refused as bad_sums_line (strict, fail-closed) | append "\n" |
| F13 | NON-BLOCKING | CLAIMED (code-read) | `_write_new` fsyncs file but not out_dir; receipt directory entry not crash-durable | code lines 268-274 |
| F14 | NON-BLOCKING | UNTESTED | macOS case-insensitive FS: same file listable under two spellings; by reasoning no unlisted file escapes, but not tested on Linux | — |
| F15 | NON-BLOCKING | CLAIMED (disclosed) | Section A row 6 asks to verify "model revision"; here only a 40-hex label; identity by file hashes | — |

## 5. My probe tests
`first_reviewer_probes.py` — each asserts behaviour I consider correct (fail-closed) except `obs_*`
(records actual behaviour). Results identical on 3.12 and 3.13: **34 passed, 14 failed** (each failure
= a finding).
Passed: unlisted FIFO/hidden/nested file in set refused; symlinked subdir refused; nested listed file
accepted; CRLF sums accepted; BOM refused; `*` binary marker accepted; name with spaces accepted;
trailing-space name refused; duplicate entry refused; `sub/../A` refused; `../excl.csv` in sums refused;
single-space BSD-style line refused; same file pinned in two groups with different hashes refused; 14
wrong-type plan variants refused; compute tampering and dropping its plan entry refused; obs: empty
subdir accepted, trailing blank line refused, out_dir-in-set compute-then-no-result, reverted mid-run
change undetected.
Failed (findings): symlinked root (F3), pinned path is a directory (F6), FIFO listed in sums (hang, F5),
FIFO as pinned input (hang, F5), model null (F9), empty runtime (F9), empty package name (F6), duplicate
JSON keys (F8), sums mismatch hides member failures (F6), structural error hides file failures (F6),
compute repoints root (F1), compute-written result survives (F2), plan file changed during compute (F7),
unreadable subdirectory (F4).
Housekeeping: an early F4 attempt chmod-ed `/tmp/pytest-of-root` to o+rx (my own pytest temp root);
reverted to 700 and switched to setpriv + --basetemp inside my dir. Nothing else outside c4_reviewer/
touched.

## 6. Verdict: BLOCKED
F1/F2 produce a result.json while a pinned input is tampered (F1 by the guard itself, F2 left on disk),
contradicting claim 4; claims 2 and 5 as worded are false (F6, F3); claim 1 fails for an unreadable
subdirectory (F4). Minimal fixes before re-review: deep-copy plan for compute and re-verify from a
separate copy; re-hash the plan file after compute; refuse when result.json already exists (or write
atomically from a temp name); fix/narrow claims 2 and 5; `os.walk(onerror=...)`; O_NONBLOCK or
lstat-before-open.
