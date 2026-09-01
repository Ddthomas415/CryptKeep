# Backup Artifact Secret Scan False Positive - 2026-08-31

Status: fix ready for independent review.

## Finding

SHOWN: full-state backup and manifest verification succeeded for
`/private/tmp/cbp-state-backup-20260831T0538Z/cbp-state-backup-20260831T054203Z`.

SHOWN: the first backup-artifact secret scan failed with six
`sensitive_key_unredacted` findings at `capital_authority`, each with a string
length of `4`.

SHOWN by targeted inspection: every flagged `capital_authority` value was the
literal sentinel `"none"` in operator-briefing JSON files.

Root cause: the sensitive-key classifier treats any key containing `auth` as
sensitive, so `capital_authority` is intentionally scanned. The redaction
classifier accepted `None`, an empty string, and `"<redacted>"`, but did not
accept the explicit string sentinel `"none"`.

## Change

`services/audit/jsonl_secret_scan.py::_is_safely_redacted()` now treats the
string sentinel `"none"` as safely redacted, case-insensitively.

Scope boundary: sensitive-key classification is unchanged; byte-pattern
scanning is unchanged; real secret values under `capital_authority`,
`api_key`, `token`, or other sensitive-looking keys remain findings.

## Verification

- `./.venv/bin/python -m pytest -q tests/test_backup_artifact_secret_scan.py tests/test_operator_event_secret_scan.py tests/test_platform_event_secret_scan.py`
  - SHOWN: `18 passed`.
- `./.venv/bin/python -m pytest -q tests/test_backup_artifact_secret_scan.py tests/test_operator_event_secret_scan.py tests/test_platform_event_secret_scan.py tests/test_checkpoints_repo_path_references_exist.py tests/test_checkpoints_tail_contract.py tests/test_operator_reporting_backlog_worklog_sync.py`
  - SHOWN: `23 passed`.
- `./.venv/bin/python scripts/check_backup_artifact_secrets.py --json /private/tmp/cbp-state-backup-20260831T0538Z/cbp-state-backup-20260831T054203Z`
  - SHOWN: `ok=true`, `finding_count=0`, `files_scanned=664`,
    `text_files_scanned=572`.

## Risk

Security-sensitive scanner behavior changed, but the accepted sentinel list was
only widened for the explicit non-secret value `"none"`.

Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
