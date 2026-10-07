# Workflow signing-condition syntax correction

Active role ENGINEER. Risk HIGH (CI/release/secrets handling).
READY_FOR_INDEPENDENT_REVIEW. No publication or release performed.

Independent GATE Hume: ACCEPTED_WITH_RISK for the bounded18-condition rewrite,
no actionable finding. Read-only inspection, no independent test execution.
Review observed work-log absence before the parallel log edit completed; the
required entry is now present in this branch. No source changed after review.
GitHub parser/signing/release behavior still unverified. Next is PR validation,
not workflow dispatch, tagging or release.

Merged accounting commit90c9f097e has successful CI/sanity/governance/PyInstaller
checks. Four other workflows failed with no executed jobs: build-desktop-app,
release-desktop-app, release-publish, ci-signing. Source uses unsupported direct
secrets references in step if conditions. GitHub documentation explicitly forbids
this and recommends job env plus env condition references:
https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

This is source evidence of invalid conditions and a plausible pre-job failure
cause, not a captured GitHub parser annotation (none returned). No accounting
regression or actual signing/build failure claimed.

## Bounded correction

Four files only: compute identical secret-presence predicates as job-level
boolean readiness values; step if references those values as strings equal to
true. Existing OS checks, commands, secret names and step-scoped secret values,
actions, triggers, permissions, outputs and release dependencies unchanged.
No raw credentials exported to job scope. No signing requirement relaxed.

Eight history-independent regression cases pass in0.14s: identical readiness
predicates, platform checks, no direct secret conditions, defined/used flags,
and no raw-secret job export. Before finalizing reusable tests, a one-off
structural reconstruction compared full original/new YAML and passed all four
files; commands/triggers/perms unchanged. PyYAML parsing is not GitHub's workflow
expression validator. actionlint unavailable; actual GitHub validation remains
UNVERIFIED until published CI. No real secrets used or accessed, no signing,
build, dispatch, tag, release, account, config or collector operation performed.

Isolated branch codex/workflow-secret-gates-20261007, base90c9f097e.
Original dirty checkout untouched. Independent review requested. No full suite
rerun for syntax-only change; real signing/notarization remains unverified.
