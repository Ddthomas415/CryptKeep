#!/bin/bash
set -u

# Manual repo audit helper
# Read-only by default
# Writes timestamped outputs under .cbp_state/audit_reports/
# Human Review Required:
# - interpreting findings
# - deciding what to delete, keep, or refactor

TS="$(date +%Y%m%d_%H%M%S)"
BASE_DIR=".cbp_state/audit_reports"
mkdir -p ""
STATE_ROOT=".cbp_state/audit_reports"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$STATE_ROOT/repo_audit_$STAMP"
mkdir -p "$OUT_DIR" || exit 1
SUMMARY="$OUT_DIR/00_summary.txt"
FAILED_LIST="$OUT_DIR/failed_checks.txt"
[ -n "$OUT_DIR" ] || exit 1
[ -n "$SUMMARY" ] || exit 1
[ -n "$FAILED_LIST" ] || exit 1
: > "$FAILED_LIST"
mkdir -p "$OUT_DIR"

MODE="${1:-full}"   # quick | full
: > "$FAILED_LIST"

score=100
SCORE_LOG="$OUT_DIR/score_deductions.txt"
: > "$SCORE_LOG"

count_file_lines() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo 0
    return
  fi
  grep -vE '^#|^$' "$file" | wc -l | tr -d ' '
}

deduct() {
  local points="$1"
  local reason="${2:-unspecified}"
  score=$((score - points))
  if [ "$score" -lt 0 ]; then
    score=0
  fi
  echo "-${points}: ${reason}" >> "$SCORE_LOG"
}

flag_check() {
  local name="$1"
  local severity="$2"
  local threshold="$3"
  local penalty="$4"
  local count
  count="$(count_file_lines "$OUT_DIR/${name}.txt")"

  if [ "$count" -gt "$threshold" ]; then
    echo "[$severity] $name => $count hits (threshold: $threshold)"
    deduct "$penalty" "$name above threshold ($count > $threshold)"
  else
    echo "[OK] $name => $count hits"
  fi
}

flag_check_exit() {
  local name="$1"
  local severity="$2"
  local penalty="$3"
  local file="$OUT_DIR/${name}.txt"
  local rc

  rc="$(grep '^# EXIT_CODE:' "$file" | awk '{print $3}' | tail -1)"
  [ -z "$rc" ] && rc=999

  if [ "$rc" -ne 0 ]; then
    echo "[$severity] $name failed (exit=$rc)"
    deduct "$penalty" "$name failed (exit=$rc)"
  else
    echo "[OK] $name"
  fi
}

# Prefer timeout only when it matches the active architecture.
# On macOS, Homebrew timeout/gtimeout can be x86_64 and force child processes
# into the wrong architecture under Rosetta. In that case, disable timeout.
TIMEOUT_BIN=""
if command -v gtimeout >/dev/null 2>&1; then
  GTIMEOUT_PATH="$(command -v gtimeout)"
  if ! file "$GTIMEOUT_PATH" 2>/dev/null | grep -q 'x86_64'; then
    TIMEOUT_BIN="$GTIMEOUT_PATH"
  fi
fi
if [ -z "$TIMEOUT_BIN" ] && command -v timeout >/dev/null 2>&1; then
  TIMEOUT_PATH="$(command -v timeout)"
  if ! file "$TIMEOUT_PATH" 2>/dev/null | grep -q 'x86_64'; then
    TIMEOUT_BIN="$TIMEOUT_PATH"
  fi
fi

# Exclude big/noisy dirs from grep/find passes
FIND_EXCLUDES=(
  -not -path "./.git/*"
  -not -path "./.venv/*"
  -not -path "./.venv_x86_backup_*/*"
  -not -path "./attic/*" -not -path "./.cbp_state/audit_reports/*"
)

GREP_EXCLUDES=(
  --exclude-dir=.git
  --exclude-dir=.venv --exclude-dir=.venv_x86_backup_20260224_133111
  --exclude-dir=attic
  --exclude=manual_repo_audit.sh
  --exclude=manual_repo_audit.sh.pre_*
)

log() {
  printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"
}

run_with_timeout() {
  local secs="$1"
  shift
  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" "$secs" "$@"
  else
    "$@"
  fi
}

record_failure() {
  local name="$1"
  local rc="$2"
  echo "$name (exit=$rc)" >> "$FAILED_LIST"
}

run_check() {
  local name="$1"
  local timeout_s="$2"
  shift 2
  local outfile="$OUT_DIR/${name}.txt"
  local start end rc

  start="$(date +%s)"
  log "RUN $name"

  {
    echo "# CHECK: $name"
    echo "# TIMEOUT: ${timeout_s}s"
    echo "# CMD: $*"
    echo
    run_with_timeout "$timeout_s" "$@"
  } >"$outfile" 2>&1
  rc=$?

  end="$(date +%s)"
  {
    echo
    echo "# EXIT_CODE: $rc"
    echo "# DURATION_SEC: $((end-start))"
  } >>"$outfile"

  if [ "$rc" -ne 0 ]; then
    record_failure "$name" "$rc"
  fi

  return 0
}

run_shell_check() {
  local name="$1"
  local timeout_sec="$2"
  local cmd="$3"

  local outfile="$OUT_DIR/${name}.txt"
  local start end duration exit_code

  start=$(date +%s)
  log "RUN $name"

  {
    echo "# CHECK: $name"
    echo "# TIMEOUT: ${timeout_sec}s"
    echo "# CMD: $cmd"
    echo
  } >"$outfile"

  run_with_timeout "$timeout_sec" /bin/bash -c "$cmd" >>"$outfile" 2>&1
  exit_code=$?

  end=$(date +%s)
  duration=$((end - start))

  {
    echo
    echo "# EXIT_CODE: $exit_code"
    echo "# DURATION_SEC: $duration"
  } >>"$outfile"

  if [ "$exit_code" -ne 0 ]; then
    echo "$name (exit=$exit_code)" >>"$FAILED_LIST"
  fi

  return 0
}

# -------- 1. Repo / tree hygiene --------
run_check git_status 20 git status --short
run_check git_log 20 git log --oneline --decorate -10
run_shell_check repo_doctor_strict 60 'python3 tools/repo_doctor.py --strict'
run_shell_check find_bak 20 'find . \( -path "./.git" -o -path "./.venv" -o -path "./attic" -o -path "./.cbp_state/audit_reports" -o -path "./.venv_x86_backup_20260224_133111" \) -prune -o -type f -name "*.bak" -print | sort'
run_shell_check find_pycache 20 'find . \( -path "./.git" -o -path "./.venv" -o -path "./attic" -o -path "./.cbp_state/audit_reports" -o -path "./.venv_x86_backup_20260224_133111" \) -prune -o -type d -name "__pycache__" -print | sort'
run_shell_check find_pyc 20 'find . \( -path "./.git" -o -path "./.venv" -o -path "./attic" -o -path "./.cbp_state/audit_reports" -o -path "./.venv_x86_backup_20260224_133111" \) -prune -o -type f -name "*.pyc" -print | sort'

# -------- 2. Structure / boundaries --------
run_shell_check top_level 20 'find . -maxdepth 1 -mindepth 1 | sort'
run_shell_check services_dirs 20 'find services -maxdepth 2 -type d | sort'
run_shell_check tests_top 20 'find tests -maxdepth 1 -type f | sort'
run_shell_check tools_top 20 'find tools -maxdepth 1 -type f | sort'
run_shell_check workflows 20 'find .github/workflows -maxdepth 1 -type f | sort'

# -------- 3. Duplicate / overlap families --------
run_shell_check overlap_dirs 20 'find services -maxdepth 2 -type d | grep -E "strategy|strategies|market_data|marketdata|paper|paper_trader|storage" || true'
run_shell_check overlap_refs 45 'grep -RniE "services/(strategy|strategies|market_data|marketdata|paper|paper_trader|storage)" services tests scripts --exclude="*.pyc" --exclude="manual_repo_audit.sh" --exclude="manual_repo_audit.sh.*" 2>/dev/null || true'

# -------- 4. Security / config hygiene --------
run_shell_check env_files 20 'find . -maxdepth 4 \( -name ".env" -o -name ".env.*" \) -not -path "./.git/*" | sort'

run_shell_check local_paths 45 'grep -RniI --exclude="*.pyc" "/Users/" docs services tests 2>/dev/null || true'

if [ "$MODE" = "full" ]; then
  run_shell_check secret_patterns 90 'grep -RniE "OPENAI_API_KEY|DATABASE_URL|MINIO_SECRET_KEY|MINIO_ACCESS_KEY|SECRET_KEY|API_KEY|TOKEN=" . '"${GREP_EXCLUDES[*]}"' 2>/dev/null || true'
  run_shell_check private_keys 45 'grep -RniE "BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|BEGIN PRIVATE KEY" . '"${GREP_EXCLUDES[*]}"' 2>/dev/null || true'
  run_shell_check secret_entropy 45 'grep -RniE "[A-Za-z0-9+/=_-]{32,}" . '"${GREP_EXCLUDES[*]}"' 2>/dev/null || true'
else
  cat > "$OUT_DIR/secret_patterns.txt" <<EOF
# CHECK: secret_patterns
# SKIPPED_IN_MODE: $MODE
# EXIT_CODE: 0
# DURATION_SEC: 0
EOF
  cat > "$OUT_DIR/private_keys.txt" <<EOF
# CHECK: private_keys
# SKIPPED_IN_MODE: $MODE
# EXIT_CODE: 0
# DURATION_SEC: 0
EOF
  cat > "$OUT_DIR/secret_entropy.txt" <<EOF
# CHECK: secret_entropy
# SKIPPED_IN_MODE: $MODE
# EXIT_CODE: 0
# DURATION_SEC: 0
EOF
fi

# -------- 5. CI / automation / deployment --------
run_check makefile_head 20 sed -n '1,220p' Makefile
run_shell_check workflow_dump 45 'for f in .github/workflows/*; do echo "===== $f ====="; sed -n "1,260p" "$f"; echo; done'
run_shell_check automation_files 20 'find . -maxdepth 3 -type f | grep -E "docker|compose|run_.*\.(sh|ps1)$|requirements" | sort || true'

# -------- 6. Testing / validation --------
if [ "$MODE" = "quick" ]; then
  run_shell_check pytest_collect 90 './.venv/bin/python -m pytest --collect-only -q'
else
  run_shell_check pytest_collect 180 './.venv/bin/python -m pytest --collect-only -q'
  run_shell_check test_repo_doctor 90 'pytest -q tests/test_repo_doctor_strict.py'
  run_shell_check test_user_stream 90 'pytest -q tests/test_user_stream_ws.py'
  run_shell_check test_dedupe 90 'pytest -q tests/test_order_dedupe_store.py tests/test_order_dedupe_unknown.py'
  run_shell_check test_evidence_collector 120 'pytest -q tests/test_run_paper_strategy_evidence_collector.py'
fi

# -------- 7. Strategy / evidence alignment --------
run_shell_check evidence_files 20 'ls -lah .cbp_state/data/strategy_evidence 2>/dev/null || true'
run_shell_check decision_records 20 'ls -lah docs/strategies/decision_record_*.md 2>/dev/null || true'
run_check presets_head 20 sed -n '1,220p' services/strategies/presets.py
run_shell_check latest_decision_record 20 'LATEST="$(ls docs/strategies/decision_record_*.md 2>/dev/null | sort | tail -1)"; [ -n "$LATEST" ] && sed -n "1,260p" "$LATEST" || true'

# -------- 8. Observability / debugging --------
run_shell_check observability_services 20 'find services -type f | grep -E "log|diagnostic|health|watchdog|supervisor|debug" | sort || true'
run_shell_check observability_scripts 20 'find scripts -type f | grep -E "diagnostic|doctor|repair|watchdog|supervisor" | sort || true'

# -------- 9. Summary --------
{
  echo "Repo Audit Summary"
  echo "=================="
  echo "Mode: $MODE"
  echo "Output dir: $OUT_DIR"
  echo

  echo "=== CRITICAL ==="
  flag_check secret_patterns HIGH 0 30
  flag_check private_keys HIGH 0 40

  echo
  echo "=== IMPORTANT ==="
  flag_check secret_entropy WARN 5 10
  flag_check overlap_dirs WARN 3 10
  flag_check overlap_refs WARN 10 5

  echo
  echo "=== HYGIENE ==="
  flag_check find_bak WARN 0 5
  flag_check find_pycache WARN 0 5
  flag_check find_pyc WARN 0 5

  echo
  echo "=== TESTING ==="
  flag_check_exit pytest_collect HIGH 20

  echo
  echo "=== QUICK COUNTS ==="
  echo "  .bak files:       $(count_file_lines "$OUT_DIR/find_bak.txt")"
  echo "  __pycache__ dirs: $(count_file_lines "$OUT_DIR/find_pycache.txt")"
  echo "  .pyc files:       $(count_file_lines "$OUT_DIR/find_pyc.txt")"
  echo "  env files:        $(count_file_lines "$OUT_DIR/env_files.txt")"

  echo
  echo "=== FAILED CHECKS ==="
  if [ -s "$FAILED_LIST" ]; then
    sed 's/^/  - /' "$FAILED_LIST"
    deduct 10 "one or more checks failed"
  else
    echo "  (none)"
  fi

  echo
  echo "=== REPO HEALTH SCORE ==="
  echo "Score: $score / 100"
  if [ -s "$SCORE_LOG" ]; then
    echo
    echo "Deductions:"
    sed 's/^/  /' "$SCORE_LOG"
  fi

  echo
  echo "=== ACTION PLAN ==="
  echo "1. Fix HIGH severity issues immediately"
  echo "2. Review secret hits manually before treating them as leaks"
  echo "3. Clean repo artifacts (.bak, pyc, caches)"
  echo "4. Resolve duplicate module families"
  echo "5. Investigate failed checks by exit code, not line count"

  echo
  echo "=== MANUAL REVIEW CHECKLIST ==="
  echo "[ ] Active backup files outside archive paths"
  echo "[ ] Active __pycache__/pyc artifacts"
  echo "[ ] Duplicate module families / ownership"
  echo "[ ] Secret/config exposure"
  echo "[ ] CI branch / workflow alignment"
  echo "[ ] Pytest collection health"
  echo "[ ] Strategy evidence / decision record alignment"
} >"$SUMMARY"



# -------- 10. Code quality / duplication --------
run_shell_check py_todos 20 'grep -RniE "TODO|FIXME|HACK|XXX" services tests scripts tools 2>/dev/null || true'
run_shell_check large_py_files 20 'find services tests scripts tools -type f -name "*.py" -exec wc -l {} + | sort -nr | head -50'
run_shell_check duplicate_functions 45 'python3 tools/find_duplicate_functions.py 2>/dev/null || true'

# -------- 11. Dependency / architecture --------
run_shell_check imports_graph 60 'python3 -m pip show grimp >/dev/null 2>&1 && python3 tools/import_graph_audit.py || true'
run_shell_check circular_imports 60 'python3 tools/circular_import_check.py 2>/dev/null || true'
run_shell_check orphan_dirs 20 'find . -maxdepth 2 -type d | grep -E "attic|prototype|experimental|archive|backup" || true'

# -------- 12. Security / CI / automation --------
run_shell_check ci_secrets 30 'grep -RniE "secrets\\.|AWS_|TOKEN|KEY|PASSWORD" .github/workflows 2>/dev/null || true'
run_shell_check insecure_defaults 45 'grep -RniE --exclude="manual_repo_audit.sh" --exclude="manual_repo_audit.sh.*" --exclude="*.pyc" "localhost|0.0.0.0|debug=True|allow_origins|CORS|SECRET_KEY|MINIO_|DATABASE_URL" services scripts config docker crypto-trading-ai .env.example 2>/dev/null || true'
run_shell_check branch_refs 20 'grep -RniE "main|master" .github/workflows Makefile scripts docker 2>/dev/null || true'
run_shell_check shell_scripts 60 'command -v shellcheck >/dev/null 2>&1 && find . -type f \( -name "*.sh" -o -name "run_*" \) -print0 | xargs -0 shellcheck || true'

# -------- 13. Tests / governance / evidence --------
run_shell_check test_inventory 20 'find tests -type f | sort'
run_shell_check flaky_markers 20 'grep -RniE "xfail|skip|flaky|sleep\\(" tests 2>/dev/null || true'
run_shell_check targeted_green 120 'python3 -m pytest -q tests/test_user_stream_ws.py tests/test_order_dedupe_store.py tests/test_order_dedupe_unknown.py tests/test_run_paper_strategy_evidence_collector.py'
run_shell_check governance_docs 20 'find docs/governance docs/strategies -type f | sort'
run_shell_check absolute_paths 30 'grep -Rni "/Users/" docs 2>/dev/null || true'
run_shell_check checklist_pending 20 'grep -n "\\- \\[ \\]" docs/governance/governance_checklist.md 2>/dev/null || true'
run_shell_check strategy_evidence 20 'ls -lah .cbp_state/data/strategy_evidence 2>/dev/null || true'
run_shell_check decision_records_all 20 'ls -lah docs/strategies/decision_record_*.md 2>/dev/null || true'
run_shell_check strategy_truth 20 'grep -RniE "paper_thin|synthetic_only|freeze|improve" docs/strategies docs/governance 2>/dev/null || true'

# -------- 14. Performance hotspot heuristics --------
run_shell_check async_loops 30 'grep -RniE "while not .*is_set|asyncio\\.sleep\\(0\\)|run_forever|poll" services scripts 2>/dev/null || true'
run_shell_check sqlite_hotspots 30 'grep -RniE "sqlite|execute\\(|executemany\\(|commit\\(" services storage scripts 2>/dev/null || true'

log "DONE"
echo
echo "Audit output written to: $OUT_DIR"
echo "Start with: $SUMMARY"
