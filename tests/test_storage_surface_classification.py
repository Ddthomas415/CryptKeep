from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

QUARANTINED_STORES = {
    "storage/fill_reconciler_store_sqlite.py": "quarantined_retained_schema",
    "storage/order_idempotency_sqlite.py": "quarantined_retained_schema",
    "storage/order_tracker_store_sqlite.py": "quarantined_retained_schema",
}


def _python_files(root: str) -> list[Path]:
    base = REPO / root
    if base.is_file():
        return [base]
    return sorted(base.rglob("*.py"))


def test_storage_surface_classification_doc_covers_quarantined_stores() -> None:
    doc = (REPO / "docs/architecture/storage_surface_classification.md").read_text(encoding="utf-8")
    for rel, classification in QUARANTINED_STORES.items():
        assert (REPO / rel).is_file(), rel
        assert f"`{rel}` | `{classification}`" in doc


def test_quarantined_storage_schemas_have_no_production_importers() -> None:
    """The retained schemas may stay on disk, but new callers require a reviewed
    storage-consolidation decision before they become runtime authorities."""
    patterns = [
        r"storage\.fill_reconciler_store_sqlite",
        r"storage\.order_idempotency_sqlite",
        r"storage\.order_tracker_store_sqlite",
        r"\bFillReconcilerStore\b",
        r"\bOrderIdempotencyStore\b",
        r"\bOrderTrackerStore\b",
    ]
    roots = [
        "services",
        "scripts",
    ]

    hits: list[str] = []
    for path in [file for root in roots for file in _python_files(root)]:
        rel = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if re.search(pattern, text):
                hits.append(rel)
                break

    assert hits == []
