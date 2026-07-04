# Companion Repo Dependency Decision

Date: 2026-07-03

## Finding

The root repo references `phase1_research_copilot/` in docs, smoke scripts, and
tests, but `git ls-files phase1_research_copilot` shows no tracked companion
source in this repository.

`docs/GOLDEN_PATH.md` currently classifies `phase1_research_copilot/` as
archived research tooling. `docs/REPO_LAYOUT.md` describes it as a companion
subsystem, not part of the required root install/run/test baseline.

## Decision

Treat `phase1_research_copilot/` as a sidecar/archived companion, not a
required root runtime dependency.

## Policy

- Root paper/research/shadow operation must not require the sidecar tree.
- Tests that require the sidecar must skip cleanly when it is absent.
- Smoke scripts may report "not installed" instead of failing the root runtime.
- Do not add new required root commands that depend on the sidecar unless it is
  vendored or documented as an explicit external prerequisite.

## Open Follow-Up

If the companion becomes active product scope again, choose one path:

- vendor it into the repo with CI coverage
- document it as an external prerequisite with install/run commands
- remove stale root references and keep it archived
