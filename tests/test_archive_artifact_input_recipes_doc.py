from __future__ import annotations

from pathlib import Path

from services.analytics.research_artifact_inventory import ARTIFACTS


REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs/research/archive_artifact_input_recipes.md"


def _normalized_doc() -> str:
    return " ".join(DOC.read_text(encoding="utf-8").split())


def test_archive_artifact_input_recipe_doc_tracks_archive_producer_contracts() -> None:
    text = _normalized_doc()
    archive_specs = [spec for spec in ARTIFACTS if spec.lane == "archive"]

    assert {spec.artifact_id for spec in archive_specs} == {
        "archive_walk_forward",
        "archive_parameter_sweep",
        "archive_parameter_sweep_triage",
    }

    for spec in archive_specs:
        assert f"`{spec.artifact_id}`" in text
        assert f"`{spec.producer_make_target}`" in text
        assert spec.producer_args_variable is not None
        assert f"`{spec.producer_args_variable}`" in text
        for required_input in spec.required_inputs:
            assert required_input in text


def test_archive_artifact_input_recipe_doc_pins_no_default_recipe_boundary() -> None:
    text = _normalized_doc()

    assert text.count("no accepted default recipe") >= 3
    assert "A bare Make target is not an accepted archive recipe" in text
    assert "No checked-in default parameter grid is accepted by this note." in text
    assert "No checked-in default archive row window is accepted by this note." in text


def test_archive_artifact_input_recipe_doc_preserves_non_authority_scope() -> None:
    text = _normalized_doc()

    for phrase in (
        "does not run research jobs",
        "fetch market data",
        "generate research artifacts",
        "change strategy configuration",
        "start campaigns",
        "change gates",
        "change live routing",
        "change execution",
        "create promotion evidence",
        "not campaign evidence",
        "not promotion evidence",
        "not execution inputs",
    ):
        assert phrase in text


def test_archive_artifact_input_recipe_doc_is_linked_from_backlog() -> None:
    backlog = (REPO / "REMAINING_TASKS.md").read_text(encoding="utf-8")

    assert "docs/research/archive_artifact_input_recipes.md" in backlog
