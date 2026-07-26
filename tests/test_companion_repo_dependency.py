from __future__ import annotations

from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]


def test_phase1_companion_backend_is_profile_gated_in_compose() -> None:
    compose = yaml.safe_load((REPO / "docker/docker-compose.yml").read_text(encoding="utf-8"))
    backend = compose["services"]["backend"]
    dashboard = compose["services"]["dashboard"]

    assert backend["profiles"] == ["phase1-companion"]
    assert "phase1_research_copilot" in backend["working_dir"]
    assert "depends_on" not in dashboard


def test_companion_dependency_decision_documents_compose_profile() -> None:
    doc = (REPO / "docs/COMPANION_REPO_DEPENDENCY.md").read_text(encoding="utf-8")
    assert "phase1-companion" in doc
    assert "Root Docker startup must not require the sidecar" in doc
