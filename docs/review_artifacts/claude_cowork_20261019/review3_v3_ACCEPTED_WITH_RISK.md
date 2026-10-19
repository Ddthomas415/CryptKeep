# C4 independent review 3 of v3 - verdict ACCEPTED_WITH_RISK

Provenance: final report returned by a third, separate reviewer subagent (neither earlier reviewer; no
implementer reasoning) on 2026-10-19 UTC after a rate-limit interruption and resume, transcribed by the
implementer (Claude, Cowork) for audit. Content, numbers, labels and verdict follow the reviewer's
report; wording is lightly condensed in places (faithful summary, not a byte-exact copy). Reviewed v3
files: pinned_run_inputs.py 6baef879..., test_pinned_run_inputs.py b49b1a35... . Probe file:
`third_reviewer_probes.py`; mutation harness: `third_reviewer_mutate.py` (this folder). The implementer
did NOT re-run this reviewer's findings (work log 2026-10-19T03:57:55Z).

---

No blocker. The guard never computed and never wrote result.json on a tampered or invalid pin inside
the stated trust boundary. The only refused run check_output still accepts needs compute to forge a
correctly linked result.json deliberately (disclosed). Claims 3 and 5 are overstated, without weakening
fail-closed behaviour. Nothing outside the reviewer's directory modified; no mounts left.

## 1. Hash checks
Module 6baef879…ebae8 and tests b49b1a35…ae674 matched at start, after the resume, and at end.

## 2. Shipped tests
`PYTHONDONTWRITEBYTECODE=1 timeout 600 <venv>/bin/python -m pytest -p no:cacheprovider -q --basetemp=<mydir>/bt_shipped_<v> tests/test_pinned_run_inputs.py`:
3.12.3 **94 passed**; 3.13.16 **94 passed**. v2 suite on v3: 57 passed / 2 failed on both — not
regressions (old reason name case_duplicate_sums_entry → colliding_sums_entry; F4 test hooks os.scandir,
which v3 never calls; v3 still refuses that case, and a real-permission version is refused in probes).

## 3. Earlier probe suites on v3 (same on 3.12 and 3.13)
First reviewer: 42 pass / 6 fail, none a defect; every failing case still refuses without computing
(3 reason renames, 2 obsolete observations now fixed, 1 accepted design choice).
Second reviewer: 50 pass / 24 fail; all want_* pass; implementer's count (22 obs_*, 2 ok_*) correct:
18 obsolete observations now fixed; 2 reason-name changes (still refused); 4 hooks that cannot fire on
v3, each checked as covered elsewhere (ok_swap ×2 → shipped test_file_swapped_between_stat_and_open_is_refused,
which asserts its hook fired; obs_linked_compute_result_plus_failed_refusal uses the old _write_new
signature → covered by shipped test_r5 and finding G1; obs_parent_swapped_to_symlink hooks os.lstat →
covered by shipped test_r8 and real-swap probes).

## 4. Claims and earlier findings
| Item | Status | Evidence |
|---|---|---|
| C1/R1 | holds | r1 tests; second reviewer's want_* pass; mutants M11-M13, M21-M23 caught |
| C2/R2 | holds | r2 tests; recreated out_dir got a new inode 50/50; inode reuse impossible while the guard holds the dir open |
| C3/R3 | partial | true for Exception; KeyboardInterrupt during post-run leaves no refused.json (G3); failed final result.json write not recorded (G2) |
| C4/R4 | holds | r4 test; mutant M16 caught |
| C5/R5-R6 | partial | holds while rename works; if compute makes out_dir unwritable, a forged result.json stays and check_output accepts (G1; deliberate forging only) |
| C6/R7 | holds | real bind mount refused; nested-sets probe |
| C7/R8 | holds in code | ELOOP/ENOTDIR/EACCES/EMFILE probes; symlink + O_DIRECTORY|O_NOFOLLOW gives ENOTDIR on this kernel (mapped); root and per-dir identity checks not exercised by shipped tests (G9) but work in probes |
| C8/R9 | partial | plan contents and deep JSON covered (depth 500-50000 → PinError); raw exceptions remain for odd arguments and deep directory trees (G4) |
| C9/R10 | holds | r10 test; mutant M17 caught |
| C10/R11 | holds | brute force over every single code point: 0 key mismatches |
| C11/R13 | holds | docstring |
| C12 | 94 pass SHOWN; 18 mutants CLAIMED and consistent | reviewer's own 30 mutants: 24 caught, 6 survived (G9) |
| C13 | holds | section 3 |
| C14 | holds | docstring |
| R12 | holds | v3 counts correct |
| F1-F13 | hold | F12 strict by design |
| F14 | partial | collision logic shown; real case-insensitive FS UNTESTED |

## 5. New findings (all NON-BLOCKING)
| Id | Label | Finding |
|---|---|---|
| G1 | SHOWN | Compute (without DAC capabilities) writes a correctly linked forged result.json, tampers an input, chmod 0500 out_dir → set-aside rename and refusal write both fail; run raises PinError hash_mismatch but out_dir holds receipt + forged result and check_output accepts. Contradicts claim 5's "result.json is still gone"; needs deliberate forging (disclosed); an accidental result.json is rejected |
| G2 | SHOWN | Failures writing result.json after all checks pass are not recorded: partial write → raw OSError, partial result.json, no refused.json (check_output rejects as bad_json); fsync EIO after full write → run_pinned raises yet check_output accepts the genuine output |
| G3 | SHOWN | KeyboardInterrupt during post-run checks leaves only the receipt, no refused.json (check_output rejects) |
| G4 | SHOWN | Raw exceptions before compute, nothing created: NUL in out_dir/plan_path (ValueError); check_output(None) (TypeError); 1200-deep directory tree in a set (RecursionError from verify; recorded properly if compute creates it); plan_path that is a FIFO blocks run_pinned indefinitely |
| G5 | SHOWN | Availability regression from v2: intermediate directory with search (x) but not read permission now refused as unreadable (v3 opens directories read-only); fails closed |
| G6 | SHOWN | check_output accepts receipt forms run_pinned never writes (e.g. verified_utc "2026-10-19", relinked); within the no-secret-key limit |
| G7 | SHOWN (3.12 only) | With a raised sys.setrecursionlimit, run_pinned writes a 20000-deep result.json that default-limit consumers reject as bad_json; on 3.13 refused as result_not_encodable |
| G8 | SHOWN | file_sha256(root, PurePosixPath("../x")) or an absolute PurePosixPath hashes a file outside root (path check only for strings); unreachable via verify/run_pinned (plans yield strings); same line in v2 |
| G9 | SHOWN | Test gaps: shipped suite still passes with root identity check (M01), per-dir open identity (M03), _read_at identity (M14), O_EXCL/O_NOFOLLOW on writes (M20), receipt file-hash hex check (M29) removed; probes catch M01/M03; nobody tests M14/M20/M29; M27 redundant |

## 6. My probes
`third_reviewer_probes.py`: **75 passed on 3.12.3 and 75 on 3.13.16** (two of the reviewer's own probe
mistakes fixed first: a wrong expected file count, a recursion depth set too low). Groups: open-chain
error paths (30× each, fd count unchanged); swaps (root replaced → root_replaced; intermediate dir
swapped → symlink_or_replaced / replaced_while_opening; no leaks); fd leaks across run_pinned and
check_output; real permissions with capabilities dropped; check_output on real runs (all combinations
pass with expected plan hash and return exactly the payload; G6, G7); set-aside (first free name, no
symlink target touched, 100 collisions still refused; G1); out_dir identity (recreated → refused; moved
away and back → accepted; moved into a set → unlisted_directory; identical receipt bytes → accepted);
creating out_dir (dangling symlinks never written through); nested sets; collision key (0 misses); deep
plan values; deep directory trees (G4); interrupts, write failures, file_sha256 (G2, G3, G8).

## 7. Verdict: ACCEPTED_WITH_RISK
Not blocked: every tampered/invalid pin tried was refused before or after compute without result.json;
every real run passed check_output; the only refused run accepted (G1) needs deliberate forging
(disclosed); overstated claims (3, 5, "any exception" part of 8) don't weaken fail-closed behaviour.
Residual risks: no secret key (G1, G6) — always pass expected_plan_sha256; reverted changes undetected;
compute is trusted same-process code, not sandboxed; source pins hash files on disk, not the running
code (code-read); runtime pins are version strings; model revision is a label; raw exceptions or a hang
for odd arguments (G4); durable results reported as failed on fsync failure (G2); search-only
directories now refused (G5); test gaps (G9: add tests for root and per-dir identity, _read_at identity,
O_EXCL on writes, receipt file-hash check). Not tested: macOS (O_DIRECTORY/errno, APFS normalisation),
real case-insensitive FS, NFS/overlay, real crashes or power loss.
