# Commit and backup review, 2026-10-31 (owner decision 1; nothing committed or pushed)

Claude, read-only. Prepared so decision 1 needs only the owner's answer. Searches for earlier work: `git status`,
`git log`, `.gitignore`, `.git/info/exclude`, PROJECT_STATE.md decision 1, the 2026-09-03 chat summary (repo
visibility).

## What is not saved anywhere but the laptop (SHOWN)
- HEAD 389020130 (2026-10-19) on the local branch `checkpoint/2026-10-19`, 4 commits ahead of GitHub `origin/master`
  (last updated 2026-10-01). Not pushed.
- 5,546 working-tree entries (547 when untracked folders are collapsed): 59 modified tracked files and 5,487 new files,
  about 480 MiB in total.

| Group | Files | Size | Note |
|---|---:|---:|---|
| Code: `services/`, `scripts/`, `tests/`, `dashboard/`, `storage/`, `config/templates/` | 192 | 2.0 MiB | Mostly Codex's uncommitted work, some INCOMPLETE or ACCEPTED_WITH_RISK; Codex should confirm what is ready |
| Governance and checkpoints: AGENTS.md, PROJECT_STATE.md, work log, `docs/checkpoints/` | 102 | 4.5 MiB | Includes all POP rules and audits' pointers |
| Research text, scripts and small results: `docs/research/` | 253 | 21.6 MiB | All audits, diagnoses and their scripts |
| Review artifacts: `docs/review_artifacts/` | 1,214 | 20.5 MiB | Codex review evidence |
| ED-002 public inputs: `research/ed002_public_inputs/` | 3,765 | 45.8 MiB | Collected public data |
| Large data: 4 JSON files over 50 MiB (`research/multisymbol_baseline_v1/*_20261008.json`, `research/hourly_leader_earlier_raw_20261012.json`) and 5 archives in `docs/research/` | 9 | about 390 MiB | **`final_20261008.json` is 100.8 MiB, over GitHub's 100 MiB file limit: a push containing it is rejected** |

## Safety checks (SHOWN)
- `.env`, `.env.private.local` and `config/user.yaml` exist, are untracked and ignored; `.cbp_state/` is ignored;
  `.browser-access-token` and `.browser-compose-override.json` are absent (and are not in `.gitignore`).
- Credential-pattern scan of the 5,537 readable changed files (names and pattern types only, no values printed): 3
  matches, none a real secret: one test placeholder (twice: a test file and a copy inside a review archive) and a
  private-key header string with no key body inside a captured `curl` program file.
- Repository visibility: public as of 2026-09-03 (CLAIMED from a chat summary; not checked here, no GitHub access).

## Proposed plan (for the owner; each step needs approval)
1. Decide visibility: make the GitHub repository private first if research, audits and work logs should not be public.
2. Back up the large data outside git (an external drive or a private cloud folder), with the existing SHA256 lists;
   add `.gitignore` lines for those nine files. (Git LFS would be a new dependency and needs separate approval.)
3. Commit in separate commits on a new branch (not `master`): governance and checkpoints; research text and scripts;
   review artifacts and ED-002 inputs; Codex's code only after Codex confirms which changes are ready.
4. Review, then push the branch; merge only after review (owner's rule).
Interim, needing no git decision: Claude can package the governance, research text and scripts (about 26 MiB, no
secrets, no large data) as one archive for the owner to download to another device. Only on the owner's request.
