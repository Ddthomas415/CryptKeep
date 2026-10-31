"""The staged API does not accidentally authorize the legacy install CLI."""
import hashlib
import json
import os

import pytest

from scripts.research import companion_installer as install
from scripts.research import companion_install_docker as native
from tests.test_companion_running_storage import running_manifest


@pytest.mark.parametrize('apply', [False, True])
def test_v5_cli_cannot_construct_backend_lock_or_receipt(tmp_path, monkeypatch, capsys, apply):
    data = running_manifest()
    data['schema'] = 'companion-staged-update-v5'
    raw = install.canonical(data)
    path = tmp_path / 'synthetic-manifest.json'
    path.write_bytes(raw)
    receipt = tmp_path / 'must-not-exist.jsonl'

    def forbidden(*args, **kwargs):
        pytest.fail('v5 CLI must not create a backend, lock or receipt')

    monkeypatch.setattr(native, 'DockerInstallBackend', forbidden)
    monkeypatch.setattr(install.core, 'Receipt', forbidden)
    monkeypatch.setattr(os, 'open', forbidden)
    argv = ['--manifest', str(path), '--reviewed-manifest-sha256', hashlib.sha256(raw).hexdigest()]
    if apply:
        argv += ['--apply-install', '--receipt', str(receipt)]
    assert install.main(argv) == (1 if apply else 0)
    result = json.loads(capsys.readouterr().out)
    assert result['state'] == ('INCOMPLETE' if apply else 'READY_FOR_INDEPENDENT_REVIEW')
    assert not receipt.exists()
    if not apply:
        assert result['actions_executed'] is False
        assert result['startup_authorized'] is False
