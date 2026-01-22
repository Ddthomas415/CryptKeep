# Phase 315 — Local Tag Helper (safe)

Script:
- `python scripts/tag_release.py --tag vX.Y.Z [--run-tests] [--dry-run]`

Fail-closed checks:
- Must be inside a git repo
- Working tree must be clean
- `releases/RELEASE_NOTES.md` must exist
- Tag version must match `pyproject.toml` version
- Refuses if tag already exists
- Optional: runs pytest (only if `tests/` exists)

Examples:
- Validate only:
  - `python scripts/tag_release.py --tag v0.1.0 --dry-run`
- Validate + run tests + create local tag:
  - `python scripts/tag_release.py --tag v0.1.0 --run-tests`

It never pushes; you push manually:
- `git push origin v0.1.0`
