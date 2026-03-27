from pathlib import Path


def test_makefile_exposes_runtime_and_checkpoint_test_lanes() -> None:
    text = Path("Makefile").read_text(encoding="utf-8")
    pytest_ini = Path("pytest.ini").read_text(encoding="utf-8")

    assert "test-runtime:" in text
    assert "pytest -q -m runtime tests" in text
    assert "test-checkpoints:" in text
    assert "pytest -q -m checkpoint tests" in text
    assert "markers =" in pytest_ini
    assert "runtime: runtime and product behavior tests" in pytest_ini
    assert "checkpoint: repo hygiene and checkpoint-format tests" in pytest_ini


def test_docs_explain_validation_lanes() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    workflow = Path("docs/REPO_ALIGNMENT_WORKFLOW.md").read_text(encoding="utf-8")

    assert "make test-runtime" in readme
    assert "make test-checkpoints" in readme
    assert "make test-runtime" in workflow
    assert "make test-checkpoints" in workflow
