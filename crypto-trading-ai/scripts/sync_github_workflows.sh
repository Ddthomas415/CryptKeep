#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/infra/github/workflows"
TARGET_DIR="${ROOT_DIR}/.github/workflows"

mkdir -p "${TARGET_DIR}"

if ! compgen -G "${SOURCE_DIR}/*.yml" > /dev/null; then
  echo "No workflow files found in ${SOURCE_DIR}" >&2
  exit 1
fi

for source_file in "${SOURCE_DIR}"/*.yml; do
  target_file="${TARGET_DIR}/$(basename "${source_file}")"
  cp "${source_file}" "${target_file}"
  echo "Synced $(basename "${source_file}")"
done

# Remove target workflow files that no longer exist in source.
for target_file in "${TARGET_DIR}"/*.yml; do
  [[ -e "${target_file}" ]] || continue
  source_file="${SOURCE_DIR}/$(basename "${target_file}")"
  if [[ ! -f "${source_file}" ]]; then
    rm -f "${target_file}"
    echo "Removed stale $(basename "${target_file}")"
  fi
done

echo "Workflow sync complete."
