#!/usr/bin/env bash
set -euo pipefail
rm -rf .pytest_cache .ruff_cache __pycache__ */__pycache__
echo "OK: local caches cleared"
