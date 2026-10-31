"""Offline startup-profile acceptance checks; no native commands."""
import pytest

from docs.review_artifacts.companion_continuation_20261021.capture_startup_profile import inspect_format, profile_ok


def row():
    return {"command_matches": True, "entrypoint_empty": True, "workdir_matches": True,
        "SERVICE_MODULE": [True, None], "SERVICE_PORT": [True, None], "PYTHONPATH": [True, None],
        "PATH": [True, None], "WEB_CONCURRENCY": [None], "FORWARDED_ALLOW_IPS": [None],
        "BASH_ENV": [None], "ENV": [None], "uvicorn_overrides": [None]}


def test_default_profile():
    assert profile_ok(row(), requires_repo_import_path=False)


@pytest.mark.parametrize("key,value", [("SERVICE_MODULE", [False, None]), ("SERVICE_PORT", [None]),
    ("SERVICE_MODULE", [True, True, None]), ("WEB_CONCURRENCY", [False, None]),
    ("WEB_CONCURRENCY", [True, True, None]), ("PATH", [False, None]),
    ("BASH_ENV", [False, None]), ("uvicorn_overrides", [True, None]),
    ("command_matches", False), ("entrypoint_empty", False), ("workdir_matches", False)])
def test_unsafe_or_ambiguous_profile_not_accepted(key, value):
    record = row()
    record[key] = value
    assert not profile_ok(record, requires_repo_import_path=False)


def test_explicit_safe_worker_count():
    record = row()
    record["WEB_CONCURRENCY"] = [True, None]
    assert profile_ok(record, requires_repo_import_path=False)


def test_app_directory_import_does_not_require_repository_path():
    record = row()
    record["PYTHONPATH"] = [None]
    assert profile_ok(record, requires_repo_import_path=False)
    assert not profile_ok(record, requires_repo_import_path=True)


def test_template_exports_no_credential_fields_or_environment_values():
    template = inspect_format("memory_retrieval.main", "8007")
    assert "{{json .Config.Env}}" not in template and "{{.}}" not in template
    assert "SERVICE_TOKEN" not in template and "PASSWORD" not in template and "API_KEY" not in template
    assert '"UVICORN_"' in template and "WEB_CONCURRENCY=1" in template
