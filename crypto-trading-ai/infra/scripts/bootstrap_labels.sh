#!/usr/bin/env bash
set -euo pipefail

labels=(
  "type:feature|1f6feb|Feature work"
  "type:bug|d73a4a|Bug fix"
  "type:infra|5319e7|Infrastructure work"
  "type:test|0e8a16|Testing work"
  "type:docs|0052cc|Documentation"
)

for row in "${labels[@]}"; do
  IFS='|' read -r name color desc <<<"$row"
  gh label create "$name" --color "$color" --description "$desc" 2>/dev/null || true
done
