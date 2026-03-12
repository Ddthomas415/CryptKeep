# GitHub Bootstrap Pack

This repo includes a lightweight bootstrap kit for GitHub labels, milestones, and issue import index.

## Files
- `scripts/bootstrap_github_labels.sh`
- `scripts/bootstrap_github_milestones.sh`
- `docs/GITHUB_LABELS_BOOTSTRAP.csv`
- `docs/GITHUB_MILESTONES_BOOTSTRAP.csv`
- `docs/MASTER_ISSUE_INDEX.csv`

## Prerequisites
- GitHub CLI installed: `gh`
- Authenticated session: `gh auth login`
- Run from a checked-out repository with GitHub remote configured

## Usage
1. Create or update labels:
```bash
./scripts/bootstrap_github_labels.sh
```

2. Create milestones (idempotent):
```bash
./scripts/bootstrap_github_milestones.sh
```

3. Use `docs/MASTER_ISSUE_INDEX.csv` as the source for issue creation/import in your tracker tooling.

## Suggested project columns
- Backlog
- Ready
- In Progress
- Review
- Done

## Suggested sequencing
1. Bootstrap labels
2. Bootstrap milestones
3. Import or create M1 issues first
4. Add M2 once M1 is stable
5. Keep M3/M4 backlog-gated until paper trading is validated
