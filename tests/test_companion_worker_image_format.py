"""Regression for observed Docker optional-key failure; no native commands."""
import hashlib
from pathlib import Path

from scripts.research import companion_install_docker as backend


def test_optional_entrypoint_uses_the_null_safe_index_expression():
    assert backend.WORKER_IMAGE_FORMAT == (
        backend.IMAGE_FORMAT[:-1] + ',"entrypoint_empty":{{not (index .Config "Entrypoint")}}}')
    assert ".Config.Entrypoint" not in backend.WORKER_IMAGE_FORMAT


def test_only_one_template_expression_changed_from_reviewed_backend():
    raw = Path(backend.__file__).read_bytes()
    new = b'not (index .Config "Entrypoint")'
    old = b'not .Config.Entrypoint'
    assert raw.count(new) == 1 and raw.count(old) == 0
    previous = raw.replace(new, old)
    assert hashlib.sha256(previous).hexdigest() == (
        "470783aa8f126bb5c73b0dc8f7373a00069050ceb89ec08bc95cd66c15199f84")
