#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required (https://cli.github.com/)" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh auth is required. Run: gh auth login" >&2
  exit 1
fi

labels=(
  "type:feature|1f6feb|Feature work"
  "type:bug|d73a4a|Bug fix"
  "type:infra|5319e7|Infrastructure work"
  "type:test|0e8a16|Testing work"
  "type:docs|0052cc|Documentation"
  "area:frontend|fbca04|Frontend"
  "area:backend|bfd4f2|Backend"
  "area:database|c5def5|Database"
  "area:workers|f9d0c4|Workers"
  "area:devops|7057ff|DevOps"
  "area:observability|bfe5bf|Observability"
  "area:security|d4c5f9|Security"
  "area:qa|0e8a16|QA"
  "phase:0|ededed|Foundation"
  "phase:1|c2e0c6|Research MVP"
  "phase:2|fef2c0|Connections and onboarding"
  "phase:3|f9d0c4|Paper trading"
  "phase:4|d4c5f9|Live approval"
  "phase:5|ffd8b5|Hardening"
  "phase:6|bfdadc|Automation and ops"
  "priority:p0|b60205|Highest priority"
  "priority:p1|d93f0b|Important"
  "priority:p2|fbca04|Later"
  "status:backlog|ededed|Backlog"
  "status:ready|0e8a16|Ready to start"
  "status:in-progress|1d76db|In progress"
  "status:review|5319e7|In review"
  "status:done|0e8a16|Done"
)

for entry in "${labels[@]}"; do
  IFS='|' read -r name color description <<< "$entry"

  if gh label view "$name" >/dev/null 2>&1; then
    gh label edit "$name" --color "$color" --description "$description" >/dev/null
    echo "updated: $name"
  else
    gh label create "$name" --color "$color" --description "$description" >/dev/null
    echo "created: $name"
  fi
done

echo "label bootstrap complete"
