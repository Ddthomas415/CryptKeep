from __future__ import annotations

import ast
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
_DOMAIN_DIR = _ROOT / "shared" / "models" / "domain"
_MODULE_FILES = [
    "core.py",
    "connections.py",
    "market.py",
    "research.py",
    "trading.py",
    "risk.py",
    "ops.py",
]


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_domain_model_modules_exist_and_define_owned_models():
    for rel in _MODULE_FILES:
        path = _DOMAIN_DIR / rel
        assert path.exists()
        tree = _parse(path)

        class_count = sum(isinstance(node, ast.ClassDef) for node in tree.body)
        assert class_count >= 1

        owned_assignments = [
            node for node in tree.body if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "OWNED_MODELS" for target in node.targets
            )
        ]
        assert owned_assignments, f"OWNED_MODELS missing in {rel}"


def test_domain_model_modules_use_named_domain_boundaries():
    domain_init = _DOMAIN_DIR / "__init__.py"
    assert domain_init.exists()
    text = domain_init.read_text(encoding="utf-8")
    for module_name in ("core", "connections", "market", "research", "trading", "risk", "ops"):
        assert f"shared.models.domain.{module_name}" in text
