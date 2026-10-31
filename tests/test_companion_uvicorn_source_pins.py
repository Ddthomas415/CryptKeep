"""Exact installed-source read support, not general Uvicorn package access."""
import pytest

from scripts.research import companion_docker_transport as transport
from scripts.research.companion_existing_controller import Refused


@pytest.mark.parametrize("suffix", ["main.py", "config.py", "importer.py", "server.py", "lifespan/on.py"])
def test_reviewed_uvicorn_paths_can_be_pinned(suffix):
    transport._path("/usr/local/lib/python3.11/site-packages/uvicorn/" + suffix)


@pytest.mark.parametrize("suffix", ["__init__.py", "lifespan/off.py", "secrets.py",
    "../httpx/_client.py", "config.py/extra", "main.pyc", "main.py/../config.py"])
def test_other_uvicorn_paths_remain_refused(suffix):
    with pytest.raises(Refused):
        transport._path("/usr/local/lib/python3.11/site-packages/uvicorn/" + suffix)
