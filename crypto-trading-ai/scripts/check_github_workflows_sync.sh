#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/infra/github/workflows"
TARGET_DIR="${ROOT_DIR}/.github/workflows"

if ! compgen -G "${SOURCE_DIR}/*.yml" > /dev/null; then
  echo "No source workflow files found in ${SOURCE_DIR}" >&2
  exit 1
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "Missing target workflow directory ${TARGET_DIR}" >&2
  echo "Run: bash scripts/sync_github_workflows.sh" >&2
  exit 1
fi

status=0

for source_file in "${SOURCE_DIR}"/*.yml; do
  file_name="$(basename "${source_file}")"
  target_file="${TARGET_DIR}/${file_name}"

  if [[ ! -f "${target_file}" ]]; then
    echo "Missing target workflow: ${target_file}" >&2
    status=1
    continue
  fi

  if ! cmp -s "${source_file}" "${target_file}"; then
    echo "Workflow drift detected for ${file_name}" >&2
    diff -u "${source_file}" "${target_file}" || true
    status=1
  fi
done

for target_file in "${TARGET_DIR}"/*.yml; do
  [[ -e "${target_file}" ]] || continue
  file_name="$(basename "${target_file}")"
  source_file="${SOURCE_DIR}/${file_name}"
  if [[ ! -f "${source_file}" ]]; then
    echo "Extra target workflow not present in source: ${target_file}" >&2
    status=1
  fi
done

if [[ ${status} -ne 0 ]]; then
  echo "Workflow directories are not in sync." >&2
  echo "Run: bash scripts/sync_github_workflows.sh" >&2
  exit ${status}
fi

echo "Workflow directories are in sync."
