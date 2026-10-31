"""Offline captured-method tests, not execution of the installed SDK or services."""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_companion_probe_policy import loaded


CAPTURE = Path(__file__).resolve().parents[1] / "docs/review_artifacts/companion_continuation_20261021/installed_facts_capture"


def methods(filename, expected, class_name, names, namespace):
    data = (CAPTURE / filename).read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected
    original = next(n for n in ast.parse(data).body if isinstance(n, ast.ClassDef) and n.name == class_name)
    selected = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == set(names)
    cls = ast.ClassDef(name=class_name, bases=[], keywords=[], body=selected, decorator_list=[])
    tree = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    exec(compile(tree, filename, "exec"), namespace)
    return namespace[class_name]


def request_loop(status=301, *, error_code="PermanentRedirect", transport_error=None):
    calls = {"send": 0, "events": 0, "head_bucket": 0, "sleep": []}
    logger = SimpleNamespace(debug=lambda *a, **kw: None)
    redirect_type = methods("77_utils.py", "9dc1042a8bf342d70327f59df2e0b47186322b499c1b699a5d218697f4e5cb65",
                            "S3RegionRedirectorv2", {"redirect_from_error", "get_bucket_region"},
                            {"logger": logger, "ArnParser": SimpleNamespace(is_arn=lambda value: False),
                             "ClientError": RuntimeError})
    redirect = redirect_type()
    redirect._cache = {}

    def head_bucket(**kwargs):
        calls["head_bucket"] += 1
        return {"ResponseMetadata": {"HTTPHeaders": {"x-amz-bucket-region": "us-east-1"}}}

    redirect._client = SimpleNamespace(head_bucket=head_bucket, _ruleset_resolver=SimpleNamespace(
        construct_endpoint=lambda **kw: SimpleNamespace(url="http://minio:9000", properties={})))
    redirect.set_request_url = lambda old, new: new
    endpoint_type = methods("66_endpoint.py", "6c9e33c2c281196f665df6df2da22f593114bf1eb4edcd14abc5454bbcedef58",
                            "Endpoint", {"_send_request", "_needs_retry"},
                            {"logger": logger, "time": SimpleNamespace(sleep=calls["sleep"].append),
                             "first_non_none_response": lambda values: next((v for v in values if v is not None), None)})
    endpoint = endpoint_type()
    model = SimpleNamespace(name="HeadBucket", service_model=SimpleNamespace(
        service_id=SimpleNamespace(hyphenize=lambda: "s3")))
    request = {"url": "http://minio:9000/raw-docs", "context": {
        "s3_redirect": {"bucket": "raw-docs", "params": {"Bucket": "raw-docs"}}, "client_region": "us-east-1"}}
    initial = (SimpleNamespace(status_code=status), {"Error": {"Code": error_code},
                                                   "ResponseMetadata": {"HTTPHeaders": {}}})
    success = (SimpleNamespace(status_code=200), {"ResponseMetadata": {"HTTPHeaders": {}}})

    def send(*args):
        calls["send"] += 1
        if calls["send"] == 1:
            return (None, transport_error) if transport_error else (initial, None)
        return success, None

    def emit(event, **kwargs):
        calls["events"] += 1
        # Standard max-attempt refusal is None; the separate captured redirect
        # handler may still authorize replay and perform a nested HeadBucket.
        return [None, redirect.redirect_from_error(kwargs["request_dict"], kwargs["response"], kwargs["operation"])]

    endpoint._update_retries_context = lambda *a: None
    endpoint.create_request = lambda *a: SimpleNamespace(reset_stream=lambda: None)
    endpoint._get_response = send
    endpoint._event_emitter = SimpleNamespace(emit=emit)
    return endpoint, request, model, initial, calls


def test_unmodified_captured_loop_replays_and_performs_fallback_head():
    endpoint, request, model, initial, calls = request_loop()
    assert endpoint._send_request(request, model)[0].status_code == 200
    assert calls["send"] == 2 and calls["head_bucket"] == 1 and calls["sleep"] == [0]


@pytest.mark.parametrize("status,code", [(301, "301"), (302, "302"), (307, "307"),
                                        (400, "PermanentRedirect"), (500, "InternalError"),
                                        (503, "SlowDown"), (200, "PermanentRedirect")])
def test_restricted_loop_never_dispatches_retry_or_nested_request(loaded, status, code):
    endpoint, request, model, initial, calls = request_loop(status, error_code=code)
    client = SimpleNamespace(_endpoint=endpoint)
    assert loaded.memory_retrieval._single_attempt_s3(client) is client
    assert endpoint._send_request(request, model) is initial
    assert calls == {"send": 1, "events": 0, "head_bucket": 0, "sleep": []}
    assert initial[1]["ResponseMetadata"]["RetryAttempts"] == 0


def test_restricted_transport_error_is_not_retried_and_original_error_propagates(loaded):
    error = OSError("synthetic transport failure")
    endpoint, request, model, _, calls = request_loop(transport_error=error)
    loaded.memory_retrieval._single_attempt_s3(SimpleNamespace(_endpoint=endpoint))
    with pytest.raises(OSError) as caught:
        endpoint._send_request(request, model)
    assert caught.value is error
    assert calls == {"send": 1, "events": 0, "head_bucket": 0, "sleep": []}


def test_restricted_success_and_ordinary_client_isolation(loaded):
    endpoint, request, model, initial, calls = request_loop(200, error_code="")
    ordinary, other_request, other_model, _, other_calls = request_loop()
    ordinary_hook = ordinary._needs_retry
    loaded.memory_retrieval._single_attempt_s3(SimpleNamespace(_endpoint=endpoint))
    assert endpoint._send_request(request, model) is initial
    assert calls["send"] == 1 and calls["events"] == 0
    assert ordinary._needs_retry == ordinary_hook
    ordinary._send_request(other_request, other_model)
    assert other_calls["send"] == 2 and other_calls["head_bucket"] == 1


@pytest.mark.parametrize("endpoint", [None, SimpleNamespace(), SimpleNamespace(_needs_retry=None)])
def test_missing_retry_control_closes_client_and_fails_sanitized(loaded, endpoint):
    closed = []
    with pytest.raises(RuntimeError, match="^restricted_s3_retry_control_unavailable$"):
        loaded.memory_retrieval._single_attempt_s3(SimpleNamespace(_endpoint=endpoint, close=lambda: closed.append(True)))
    assert closed == [True]


def test_unwritable_or_ignored_control_is_refused(loaded):
    class ReadOnly:
        @property
        def _needs_retry(self):
            return lambda *a: True

    class Ignored(ReadOnly):
        @ReadOnly._needs_retry.setter
        def _needs_retry(self, value):
            pass

    for endpoint in (ReadOnly(), Ignored()):
        with pytest.raises(RuntimeError, match="^restricted_s3_retry_control_unavailable$"):
            loaded.memory_retrieval._single_attempt_s3(SimpleNamespace(_endpoint=endpoint, close=lambda: None))


@pytest.mark.parametrize("probe", [False, True])
def test_failed_installation_does_not_publish_restricted_cache(loaded, monkeypatch, probe):
    memory = loaded.memory_retrieval
    loaded.settings.memory_read_only_startup = not probe
    monkeypatch.setattr(memory, "probe_active", lambda: probe)
    closed = []
    monkeypatch.setattr(loaded.boto, "client", lambda *a, **kw: SimpleNamespace(close=lambda: closed.append(True)))
    with pytest.raises(RuntimeError, match="^restricted_s3_retry_control_unavailable$"):
        memory._s3_client()
    assert memory._restricted_s3 is None and memory._s3 is None and closed == [True]
