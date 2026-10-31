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
