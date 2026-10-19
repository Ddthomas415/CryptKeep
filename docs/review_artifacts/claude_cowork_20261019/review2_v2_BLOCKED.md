# C4 independent review 2 of v2 - verdict BLOCKED

Provenance: final report returned by a second, separate reviewer subagent (not the first reviewer; no
implementer reasoning) on 2026-10-19 UTC, transcribed by the implementer (Claude, Cowork) for audit.
Content, numbers, labels and verdict follow the reviewer's report; wording is lightly condensed in
places (faithful summary, not a byte-exact copy). Reviewed v2 files: pinned_run_inputs.py 89127f47...,
test_pinned_run_inputs.py 5e79e78f... . Probe file: `second_reviewer_probes.py` in this folder (written
against v2). The implementer independently reproduced R1 and R2 (work log 2026-10-19T01:24:29Z).

---

**Verdict: BLOCKED** — `check_output()` accepts output directories that no guarded run produced (meets
the stated BLOCKER rule). No case found where the guard computes, or writes a result, on a tampered or
invalid pin within its stated trust boundary.

## 1. Hash checks
Both files matched expected hashes at start and end; review input not modified; tested module copy
byte-identical (empty diff).

## 2. Shipped tests
`PYTHONDONTWRITEBYTECODE=1 timeout 300 <venv>/bin/python -m pytest -p no:cacheprovider -q --basetemp=<mydir> tests/test_pinned_run_inputs.py`:
Python 3.12.3 **59 passed**; Python 3.13.16 **59 passed**. v1's own 36 tests on v2: 35 pass, 1 fail
(renamed reason unreadable_or_symlink → symlink_refused; still refused before compute). Valid plan
produces the same receipt from v1 and v2.

## 3. First reviewer's 48 probes on v2
41 pass / 7 fail (both versions); none a real defect; guard never wrote result.json in any of the 7:
3 reason-name changes (symlinked root → root_not_canonical; inputs=None → bad_inputs; input_sets dict
→ bad_input_sets), 2 obsolete v1 observations (empty extra subdirectory now refused, F11; out_dir in a
set now refused before compute, F10), 2 design choices ((a) set_members_not_checked; (b) compute's own
result.json left in place, run refused). The implementer's 4/2/2 breakdown double-counts; clean split
3/2/2 (R12).

## 4. Claims and F1-F14
Fixed: deep copy + guard's own plan for the post-run check (incl. nested mutation); canonical root;
os.walk onerror (tested with real permissions 000/100/400 via setpriv); regular-file check before open,
O_NONBLOCK, inode match after open, no fd leak (200 failing verifies, fd count unchanged); structural +
file failures reported together; set_members_not_checked; plan re-hashed after compute; duplicate JSON
keys refused (nested too); model null and empty runtime refused; unlisted directories refused.
Partial: "only pin_receipt.json" enforced only as "nothing else" (missing/altered receipt not caught,
R2); refused.json not written on some post-compute errors (R3); check_output link check (R1); out_dir
check misses bind mounts (R7); case duplicates (R11); directory fsync (R10). F12 still strict; F15
disclosed. Claim 3 (59 on both) true. Reverted-change limit reproduced for an input file and for a file
created and deleted inside a pinned set.

## 5. New findings
| id | sev | label | finding |
|---|---|---|---|
| R1 | **BLOCKER** | SHOWN | check_output accepts directories no guarded run produced: receipt only `{"schema":"pinned-run-receipt-v1"}` + result linking only receipt_sha256 passes (plan-hash compare None == None); a well-formed hand-made pair also passes (no unkeyed check can stop that); contradicts docstring ("confirms a completed guarded run", "linked to … its plan hash") |
| R2 | NON-BLOCKING | SHOWN | Guard doesn't check its receipt survived: compute deleting/editing it, replacing it with a directory, or rmtree(out)+mkdir → guard still writes result.json and returns success (check_output rejects) |
| R3 | NON-BLOCKING | SHOWN | 200,000-deep result → raw RecursionError in _encode, no refused.json; compute deleting out_dir → raw FileNotFoundError (both fail closed) |
| R4 | NON-BLOCKING | SHOWN | Relative plan_path/out_dir re-resolved after compute; os.chdir redirects re-hash and result write (check_output rejects both dirs) |
| R5 | NON-BLOCKING | SHOWN (simulated) | Compute writes a correctly linked result.json, tampers an input, refused.json write fails (simulated disk full; _write_refusal swallows) → check_output accepts the refused run (needs forged link; outside trust boundary) |
| R6 | NON-BLOCKING | SHOWN | Compute-created refused.json keeps compute's content (run still refused, check_output rejects) |
| R7 | NON-BLOCKING | SHOWN | out_dir via a bind mount of a pinned set not caught before compute (post-run refuses with unlisted_directory); case-insensitive FS equivalent UNTESTED |
| R8 | NON-BLOCKING | SHOWN (simulated race) | Parent dir swapped for a symlink between symlink check and lstat/open is followed; inode check covers only the last component; content must still match its pin |
| R9 | NON-BLOCKING | SHOWN | Raw exceptions remain (all fail closed): NUL in root (ValueError); lone surrogate path (UnicodeEncodeError); deeply nested plan/result (RecursionError); check_output on missing dir (FileNotFoundError) |
| R10 | NON-BLOCKING | SHOWN | out_dir's entry in its parent and parents created by mkdir(parents=True) never fsynced; crash durability UNTESTED |
| R11 | NON-BLOCKING | SHOWN; macOS effect UNVERIFIED | NFC/NFD spellings of one name both accepted; casefold wrongly refuses names distinct on Linux (A-USD vs a-usd, straße vs strasse) |
| R12 | NON-BLOCKING | SHOWN | Claim 4 breakdown doesn't add up (see section 3) |
| R13 | NON-BLOCKING | SHOWN | Any extra file (e.g. .DS_Store) makes check_output reject; only one result.json allowed, so a runner like run_volfc1.py that also writes CSVs must return everything in the dict |
Not tested: macOS/case-insensitive FS, overlayfs inode stability, real disk-full/crash, background
thread left by compute, Windows.

## 6. My probes
`second_reviewer_probes.py`: 74 tests, 68 pass / 6 fail (same on 3.12.3 and 3.13.16). `want_*` assert
desired behaviour (failure = finding), `obs_*` record behaviour, `ok_*` assert a fix holds. Failures:
want_check_output_rejects_receipt_without_plan_hash (R1); want_run_refuses_when_compute_removes_or_alters_receipt
×4 (R2); want_deeply_nested_result_is_refused_with_refused_json (R3). The ok_* group (check_output
rejections, compute-action refusals, plan input, root spellings, file access, unreadable directories,
set structure, out_dir placement, failure ordering, v1/v2 receipt equality) all passed; obs_* recorded
R1-R11 evidence plus: reverted change inside a set undetected; plan replaced by identical bytes accepted;
two sets on one directory refuse each other's sums; compute replacing out_dir with a symlink sends
result.json to the target and check_output accepts it (receipt present too).

## 7. Design choices
(a) accept: no trusted hash to check members against; run refused; gap named explicitly; cost is
diagnostic only. (b) accept with risk: deleting compute's file would destroy evidence; check_output
rejects in two independent ways; risks remain for anyone checking result.json existence instead of
check_output (the F2 failure; a naive run_volfc1.py port would hit it) and R5. Cheap hardening: rename
compute's file (e.g. result.json.unguarded) and state check_output is the only acceptance test.

## 8. Verdict: BLOCKED
Reason R1. Holds: no tampered/invalid pin led to compute or a guard-written result within the trust
boundary; shipped tests pass on both. To clear: validate receipt structure in check_output (64-hex
plan_sha256, files dict, verified_utc) and require the link to carry a matching 64-hex plan_sha256;
reword the docstring (rejects incomplete/refused/mismatched directories, not a defence against
hand-made files). Recommended same pass: R2 (re-check receipt bytes and out_dir identity), R3 (catch
all exceptions after compute), R4 (absolute paths at entry), fix claim 4's count.
