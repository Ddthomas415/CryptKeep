# Agent handoff v2, 2026-10-18 (supersedes claude_cowork_handoff_20261018.md)

Written by the outgoing Claude (Cowork) agent at the operator's request, after an independent review
found errors in that agent's work. Read this whole file before acting. It grants no authorization.
AGENTS.md, runtime_prompt.md and "Current correction scope" in REMAINING_TASKS.md control.
Status words: SHOWN = re-checked against current files; CLAIMED = stated, not verified; UNVERIFIED.

## A. Mistakes the previous agent made (do not repeat)
| Mistake | Rule that prevents it |
|---|---|
| Draft Module A simulator used today's close before trading at the open (look-ahead); its tests checked NAV but were described as checking cash | Write a leak test that scrambles future data and must change nothing; describe a test only by what its assertion checks |
| Stated causes before checking the code: named the wrong file (adapter vs companion_installer.py) and a tuple/list cause that cannot matter (canonical form is JSON) | Trace the cause to the exact line and prove it with a minimal reproduction before reporting |
| Audit spreadsheet credited all 6,421 recovered files to the _r2 folder; _r2 holds 6,414, the 4 databases + 3 archives are in recovery_supplement_20261018T192628Z | Every count gets its source path; recount from the manifest, never restate a summary |
| Overclaims: "at least 745" trials (747 is a convention-specific floor), fee screenshot as blanket blocker, "all secret hits cleared", lock ownership asserted unchecked, "unchanged counts" implying unchanged contents | Say only what was measured; counts are not contents; floors are not totals |
| VOLFC-1: trial ledger and data-reuse entries left undone although the pre-registration required them | A study is not finished until its required bookkeeping is written; list done/not done explicitly |
| VOLFC-1 run script loads a local model dir, writes a hard-coded revision and hashes weights afterwards; it does not enforce pre-registration, input checksums or model revision before forecasting | Runners must verify every pinned input (prereg hash, data hashes, exclusion file hash, model revision/weights hash) before computing, and fail closed |
| Pre-registration used the README release date (2025-10-20); the Hugging Face weights were first uploaded 2025-10-30, after week 1 began | Check primary-source availability dates (repo/commit history) before freezing a design |
| Logged "before the run" while the log write ran in parallel with the run | Ordering claims need sequential calls; never run a step and its precondition record in parallel |
| "Chronos does not beat 60-day vol": imprecise; it was slightly ahead but did not qualify | Report against the registered rule: "did not qualify", with the point estimate |
| Dismissed public sentiment data as no edge without testing | Untested ideas are UNTESTED, not rejected |
| SHA256SUMS that listed itself; a refused rm led to moving the wrong file | Exclude the sums file from itself; on a refused delete, stop and report, do not improvise |
| A subagent used curl after WebFetch was blocked | Never work around a blocked fetch; report it |

## B. Current state (SHOWN unless marked)
1. VOLFC-1 (Chronos-2 vs trailing 60-day volatility): verdict FAIL / did not qualify, independently
   re-verified by a reviewer (rankings, QLIKE, bootstrap). rho: B1 0.5123, EWMA 0.5283, Chronos 0.5217;
   Delta +0.00946 vs required +0.03; lower bound -0.00648. 214 evaluated markets, 4,999 market-week
   observations, 50 weekly clusters (not interchangeable quantities). Chronos inference itself was not
   reproduced: provenance UNVERIFIED. Do not switch to EWMA, do not retune or retest this window.
   Files: docs/research/chronos_vol_forecast_20261018/.
2. Two failing installer tests (tests/test_companion_stopped_recipe.py): diagnosis confirmed by the
   reviewer (7 saved v1 snapshots have 11 fields; current Snapshot serialization has 14; all 11 legacy
   fields match). Proposed bounded fix (not applied):
   ~/Documents/cryptkeep_data_archive/stopped_recipe_fix_proposal_20261018/. Its scratch-test results are
   CLAIMED, not reviewer-verified.
3. Companion install INCOMPLETE; previous attempt consumed. No retry/startup authorization.
4. Git: HEAD 620bc8dbe on codex/research-bundle-proof; 15bc4455a and 620bc8dbe not on GitHub (bundle in
   ~/Documents/cryptkeep_data_archive/git_bundle_20261018/). Stale 0-byte .git/index.lock (Oct 4).
   Most work since Sep 23 is uncommitted.
5. Off-machine backup: must include BOTH screened_recovery_20261018T190049Z_r2/ and
   recovery_supplement_20261018T192628Z/ with manifests, plus the git bundle. Operator upload CLAIMED.

## C. Work queue, in order (each item needs operator go-ahead where marked)
1. Correct the "Done / Protected the work" row of ~/Documents/cryptkeep_data_archive/codex_oct18_audit.xlsx
   (6,414 in _r2 + 7 assets in the supplement = 6,421 across both). Small, no approval needed beyond this file.
2. VOLFC-1 bookkeeping: add a NEW dated supplement next to
   docs/research/trial_ledger_reconciliation_20261015/ (do not edit the dated files): family VOLFC,
   1 candidate configuration, 2 baselines, verdict FAIL; data reuse D_XS used_by VOLFC-1, targets
   2025-10-27..2026-10-11, 214 markets, 4,999 observations, 50 clusters.
3. Installer v1 compatibility repair (operator approval required; HIGH risk): apply only the bounded
   fix, add permanent tamper regression tests, run the focused selection, independent review.
4. Optional: make run_volfc1.py fail closed on pinned inputs, for any future model study (no rerun of VOLFC-1).

## D. Decisions only the operator makes
Git lock removal / checkpoint commit / push; confirming uploads; Module A delisting and missing-day
rules; next research line (funding-rate pre-registration vs Module A); operating-contract draft adoption;
any market-data run; any new dependency in the repo.

## E. Standing limits
No live trading, Docker, server, account or credential access. Never read .env, .env.private.local,
.browser-access-token, .browser-compose-override.json, config/user.yaml (names and sizes only).
Do not modify verdicts, frozen criteria, manifests or artifacts. Append-only work log with `date -u` times.
Check the work-log mtime before editing to avoid colliding with Codex. Review before any push.
Work in bounded steps with a firm stop; do not stall waiting on Codex.
