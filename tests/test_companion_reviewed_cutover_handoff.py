"""Synthetic internal-token handoff only; no live credentials or native calls."""
import json
from types import SimpleNamespace

import pytest

from docs.review_artifacts.companion_continuation_20261021.execute_reviewed_cutover import (
    handoff, inputs, parse_inputs, parse_token, source_format,
)
from scripts.research.companion_runtime_adapter import token_from_pipe


def test_frozen_original_refuses_changed_consumers():
    with pytest.raises(ValueError, match="reviewed_consumer_changed"):
        inputs()


def test_owned_pipe_consumed_by_existing_reader_once():
    calls = []

    def invoke(argv):
        calls.append(argv)
        fd = int(argv[argv.index("--token-fd") + 1])
        assert token_from_pipe(fd) == "synthetic-internal-token"
        return 17

    assert handoff("synthetic-internal-token", ["--example"], invoke) == 17
    assert len(calls) == 1 and "synthetic-internal-token" not in repr(calls)


def test_exact_source_only():
    template = source_format(SimpleNamespace(id="a" * 64, image="sha256:" + "b" * 64))
    assert "SERVICE_TOKEN" in template and "running" in template
    assert "API_KEY" not in template and "PASSWORD" not in template
    assert "{{json .Config.Env}}" not in template


def test_token_json_framing_preserves_printable_payload():
    assert parse_token(json.dumps("SERVICE_TOKEN=synthetic=token!").encode() + b"\n\n") == "synthetic=token!"


@pytest.mark.parametrize("raw", [b"", b"not-json", b'"wrong=synthetic"\n', b'"SERVICE_TOKEN="\n',
    b'"SERVICE_TOKEN=has space"\n', b'"SERVICE_TOKEN=has\\nnewline"\n',
    b'"SERVICE_TOKEN=synthetic"\n"SERVICE_TOKEN=duplicate"\n',
    json.dumps("SERVICE_TOKEN=" + "x" * 4097).encode(),
    json.dumps("SERVICE_TOKEN=" + chr(233)).encode()])
def test_invalid_or_ambiguous_token_refused(raw):
    with pytest.raises((ValueError, json.JSONDecodeError)):
        parse_token(raw)
