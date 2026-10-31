# Commit plan, prepared 2026-10-31 (owner decision 1: private first; text and code in git; large data outside git)

Nothing here has been run. Order agreed by the owner: (1) the owner makes the GitHub repository private and says so;
(2) back up the large data; (3) commits on a new branch; (4) Codex confirms its code before group D is committed;
(5) owner reviews, then the branch is pushed. Earlier backups: git bundles of 2026-10-18 and 2026-10-19 exist in the
connected archive folder `cryptkeep_data_archive`, on the same disk as the repository (they do not protect against
losing the laptop).

| List | Files | Size | Note |
|---|---:|---:|---|
| `A_governance_checkpoints.txt` | 110 | 4.5 MiB | AGENTS.md, PROJECT_STATE.md, work log, checkpoints, this plan |
| `B_research_text_scripts.txt` | 257 | 22.5 MiB | Tracker v2 code moved to D for Codex to confirm |
| `C_review_artifacts_ed002_inputs.txt` | 4,979 | 66.3 MiB | Review evidence and collected public data |
| `D_code_for_codex_to_confirm.txt` | 195 | 2.0 MiB | Commit only after Codex confirms what is ready |
| `E_large_data_outside_git.txt` | 9 | 389.6 MiB | Back up outside git; add to `.gitignore` |
| `F_other_docs.txt` | 4 | small | Notes, incident report, licence text |

Large-data backup (owner; replace the destination with an external drive or private cloud folder):
```sh
cd ~/Downloads/crypto-bot-pro
DEST="/Volumes/YOUR_DRIVE/cryptkeep_large_data_20261031"
while read -r f; do mkdir -p "$DEST/$(dirname "$f")" && cp -p "$f" "$DEST/$f"; done < docs/checkpoints/commit_plan_20261031/E_large_data_outside_git.txt
(cd "$DEST" && shasum -a 256 $(cat ~/Downloads/crypto-bot-pro/docs/checkpoints/commit_plan_20261031/E_large_data_outside_git.txt) > SHA256SUMS)
```

Commits (after the repository is private; run on the Mac by Codex or the owner):
```sh
cd ~/Downloads/crypto-bot-pro
P=docs/checkpoints/commit_plan_20261031
git switch -c backup/2026-10-31
cat $P/E_large_data_outside_git.txt >> .gitignore
git add .gitignore && git add --pathspec-from-file=$P/A_governance_checkpoints.txt && git commit -m "docs: POP rules, project state, checkpoints and work log through 2026-10-31"
git add --pathspec-from-file=$P/B_research_text_scripts.txt && git commit -m "research: audits, diagnoses and scripts through 2026-10-31"
git add --pathspec-from-file=$P/C_review_artifacts_ed002_inputs.txt && git commit -m "data: review artifacts and ED-002 public inputs"
git add --pathspec-from-file=$P/F_other_docs.txt && git commit -m "docs: notes, incident report, licence text"
# Group D only after Codex confirms: git add --pathspec-from-file=$P/D_code_for_codex_to_confirm.txt && git commit -m "..."
git status --short | head    # expect only group D (and anything Codex holds back)
# After the owner's review: git push -u origin backup/2026-10-31
```

## Group D: committed as an unreviewed backup (2026-10-31, Codex unavailable; owner: "resolve or document")
Committed on `backup/2026-10-31` so it is not only on the laptop. **Not reviewed or confirmed by Codex; do not merge as
is.** The 195 files are exactly `D_code_for_codex_to_confirm.txt` (checked against `git status` before committing: no
file added or missing); no credential values (pattern scan; the one match is a placeholder test key).

Test status (Claude, 2026-10-31, SHOWN): run on a copy of the working tree with Python 3.12 and a temporary state
directory; no `.env`, `config/user.yaml` or `.git` in the copy.
| Set | Result |
|---|---|
| D's 52 non-companion test files (trading safety, research, dashboards) | 1,602 passed, 0 failed |
| Whole suite (1,136 files) | 8,850 passed, 175 failed, 35 skipped, 1 collection error |
| ... caused by group D (pass on the same copy without D) | 2 guard tests (below) |
| ... companion tests (`tests/test_companion_*`, 72 files in D) | 130 failed, 1 collection error: most report review packets whose pinned inputs changed after review (`*_input_changed`, `source_refresh_drift`, `reviewed_consumer_changed`); some need files at fixed laptop paths or the `bs4` package (not installed here) |
| ... other failures, with or without D | 43: mostly tests that need git, `make`, systemd or files at fixed laptop paths; one is `test_no_legacy_state_paths`, tripped by already-committed `scripts/research/pinned_run_inputs.py` |

What Codex must do before any of group D is merged:
1. `tests/test_live_intent_queue_boundary.py` fails: four files name the live-queue tables next to SQL writes instead
   of going through `storage/live_intent_queue_sqlite.py`: `scripts/research/synthetic_exit_checkpoint.py` (a
   "disposable" prototype with no database path of its own; it updates `live_consumer_state` on a connection it is
   given), `scripts/research/synthetic_funding_observations.py`, `scripts/research/synthetic_live_position_cap.py` and
   `services/analytics/funding_observations.py`. Without group D there are none.
   Route them through the queue store, or rename the prototype tables; do not widen the guard without review.
2. `tests/test_no_direct_create_order.py` fails: `tests/test_exchange_client_retry_flow.py` lines 72 and 105 call
   `create_order` in a test stub. Change the stub so the guard passes; do not exempt it silently.
3. Companion chain: re-freeze or revert the review packets whose inputs changed, then rerun `tests/test_companion_*`.
4. Say which items are ready (ACCEPTED, INCOMPLETE, ACCEPTED_WITH_RISK per `docs/PROJECT_STATE.md`); split them into
   reviewable pull requests; independent review before merge (AGENTS.md).
