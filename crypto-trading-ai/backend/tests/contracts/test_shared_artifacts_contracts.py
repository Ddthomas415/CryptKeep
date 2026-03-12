from scripts.generate_shared_schemas import SCHEMA_TARGETS, generate_schema_document
from scripts.validate_shared_mock_data import MOCK_TARGETS, validate_mock_payload


def test_shared_schemas_are_in_sync_with_backend_models() -> None:
    for filename, model in SCHEMA_TARGETS.items():
        generated = generate_schema_document(model)
        # Import inside test to keep this check close to runtime behavior.
        import json
        from pathlib import Path

        root = Path(__file__).resolve().parents[3]
        target = root / "shared" / "schemas" / filename
        existing = json.loads(target.read_text(encoding="utf-8"))
        assert existing == generated, f"{filename} is out of sync with {model.__name__}"


def test_shared_mock_data_matches_backend_contracts() -> None:
    for filename, model in MOCK_TARGETS.items():
        validate_mock_payload(filename, model)
