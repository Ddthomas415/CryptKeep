# Checkpoint file list (DRAFT, 2026-10-18)

Read-only proposal for a checkpoint commit. Nothing was staged, committed or deleted.
Generated with `generate_checkpoint_list.py` using `git --no-optional-locks status -uall`.

| Category | Files | Size | Proposed action |
|---|---|---|---|
| commit | 4,062 | 156.1 MB | Stage on a new branch `checkpoint/2026-10-18` |
| review_before_commit | 33 | 32.7 MB | Secret-pattern hits; see below |
| archive_outside_git | 9 | 389.6 MB | Copy to the archive folder with SHA256SUMS; do not commit |

Secret-pattern hits (values never printed):
- 30 files: "sk-" inside words (disk-, risk-, task-) - false positives.
- 2 files: "sk-" as a coin `id`/`slug` in CoinGecko/CMC JSON - very likely coin names.
- 3 test files: an assigned secret-like string - likely synthetic fixtures; a person should look.

Not in the list because git ignores them (decide separately):
- `phase1_research_copilot/` tracked copy at a new path (approved Oct 16), excluding `.env`, `.browser-access-token`, `.browser-compose-override.json`.
- `research/*/public_archive.sqlite` (4 files, about 7 MB): force-add or archive with hashes.
- Never commit: `.env`, `.env.private.local`, `config/user.yaml`, `.cbp_state/`, `.venv*`, `build/`, `dist/`, caches.

Before executing: Codex's cross-check must agree; the stale `.git/index.lock` must be removed (operator permission); run a full secret scan on the staged set; after commit, clone into an empty folder and run a test slice; push only after operator review.
