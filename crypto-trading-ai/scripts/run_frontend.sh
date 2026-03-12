#!/usr/bin/env bash
set -euo pipefail
cd frontend
pnpm dev --host 0.0.0.0 --port 3000
