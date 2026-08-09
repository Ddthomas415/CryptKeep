from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_makefile_has_alignment_targets():
    txt = (ROOT / "Makefile").read_text(encoding="utf-8", errors="replace")
    assert "doctor-strict:" in txt
    assert "alignment: check-alignment" in txt
    assert "check-alignment:" in txt
    assert "check-alignment-list:" in txt
    assert "check-alignment-list-json:" in txt
    assert "check-alignment-json:" in txt
    assert "check-alignment-json-fast:" in txt
    assert "validate-quick:" in txt
    assert "validate-json-quick:" in txt
    assert "validate-json-fast:" in txt
    assert "validate-json:" in txt
    assert "validate:" in txt
    assert "pre-release-sanity:" in txt
    assert "pre-release-sanity-quick:" in txt
    assert "pre-release-sanity-json-quick:" in txt
    assert "pre-release-sanity-json-fast:" in txt
    assert "test:" in txt
    assert "scripts/check_repo_alignment.py" in txt
    assert "scripts/check_repo_alignment.py --list-tests" in txt
    assert "scripts/check_repo_alignment.py --list-tests --json" in txt
    assert "scripts/check_repo_alignment.py --json" in txt
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1" in txt
    assert "scripts/validate.py --quick --json" in txt
    assert "CBP_VALIDATE_SKIP_PYTEST=1" in txt
    assert "scripts/validate.py --json" in txt
    assert "scripts/validate.py --quick" in txt
    assert "scripts/pre_release_sanity.py" in txt
    assert "scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports" in txt
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1" in txt
    assert "scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in txt
    assert "operator-next-actions-passive:" in txt
    assert "operator-next-actions-passive-json:" in txt
    assert "--action-source passive_operator_evidence" in txt
    assert "--exclude-reason host_side_reference" in txt
    assert "record-operator-arm-to-halt-replay:" in txt
    assert "scripts/check_operator_arm_to_halt_replay.py --json --evidence-dest $(OPERATOR_ARM_TO_HALT_REPLAY_EVIDENCE_DEST)" in txt
    assert "record-execution-cost-stack:" in txt
    assert "scripts/report_execution_cost_stack.py --write-default-artifact" in txt
    assert "smoke-exchange-sandbox:" in txt
    assert "scripts/smoke_exchange.py $(EXCHANGE_SANDBOX_SMOKE_ARGS)" in txt
    assert "backup-state:" in txt
    assert "scripts/backup_state.py backup --dest $(STATE_BACKUP_DEST)" in txt
    assert "record-manual-strategy-performance-decision:" in txt
    assert "--target manual_strategy_performance_decision" in txt
    assert "record-composite-hybrid-paper-decision:" in txt
    assert "--target composite_hybrid_paper_advancement_decision" in txt
    assert "record-funding-extreme-persistent-campaign-decision:" in txt
    assert "--target funding_extreme_persistent_campaign_decision" in txt
    assert "record-hetzner-state-migration-checkpoint:" in txt
    assert "--target hetzner_canonical_state_migration" in txt
    assert "record-paper-to-shadow-first-hour-checkpoint:" in txt
    assert "--target paper_to_shadow_first_hour_rehearsal" in txt
    assert "record-backup-restore-drill-checkpoint:" in txt
    assert "--target state_backup_restore_drill" in txt
    assert "record-server-secrets-rotation-checkpoint:" in txt
    assert "--target server_secrets_rotation_drill" in txt
