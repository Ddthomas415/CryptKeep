"""Synthetic encoding proof only, not installed Docker parser verification."""
import builtins
import io
import json
import os
import subprocess
import traceback

import pytest

from scripts.research import companion_existing_controller as core
from scripts.research import companion_install_env as encoder
from scripts.research import companion_runtime_adapter as adapter


BASE = ["SERVICE_TOKEN=synthetic-token", "POSTGRES_PASSWORD=synthetic-password",
        "MINIO_ACCESS_KEY=synthetic-access", "MINIO_SECRET_KEY=synthetic-secret"]


def pack(entries):
    return json.dumps(entries, ensure_ascii=True).encode("ascii")


def lines(data):
    return dict(line.split("=", 1) for line in data.decode("utf-8").split("\n")[:-1])


def test_exact_overrides_and_preservation():
    expected = {k: v for k, v in adapter.ENV_EXPECTED.items()
                if k not in {"POSTGRES_USER", "POSTGRES_DB"}}
    entries = BASE + [k + "=synthetic-old" for k in expected]
    entries += ["OTHER=keep", "EMPTY=", "MINIO_ROOT_USER=unchanged",
                "MINIO_ROOT_PASSWORD=unchanged-too"]
    result = lines(encoder.encode_environment(pack(entries)))
    assert result == {**dict(entry.split("=", 1) for entry in entries), **expected}
    assert "POSTGRES_USER" not in result and "POSTGRES_DB" not in result
    assert result["OPENAI_API_KEY"] == ""


def test_preserves_existing_database_identity():
    result = lines(encoder.encode_environment(pack(BASE + ["POSTGRES_USER=original", "POSTGRES_DB=custom"])))
    assert result["POSTGRES_USER"] == "original" and result["POSTGRES_DB"] == "custom"


@pytest.mark.parametrize("value", [" leading and trailing ", "#literal", "a=b=c",
                                    "'single' \"double\"", "\t tab \t", "NO_TRADING=false",
                                    "OPENAI_API_KEY=synthetic-key", "caf\u00e9 \U0001f512",
                                    "e\u0301", "\ufeffnot-a-file-bom"])
def test_values_are_lossless(value):
    entries = [entry.split("=", 1)[0] + "=" + value for entry in BASE]
    result = encoder.encode_environment(pack(entries + ["OTHER=" + value]))
    assert type(result) is bytes
    decoded = lines(result)
    for entry in entries:
        key, original = entry.split("=", 1)
        assert decoded[key] == original
    assert decoded["OTHER"] == value


@pytest.mark.parametrize("bad", [None, True, 1, {}, [], "NO_EQUALS", "=value", "1KEY=x",
                                 "BAD-KEY=x", " KEY=x", "K\u00e9Y=x", "KEY\uff1dx",
                                 "KEY=\0", "KEY=\r", "KEY=\n", "KEY=\ud800", "KEY=\udfff",
                                 "NO_TRADING=bad\nvalue", "OPENAI_API_KEY=\ud800"])
def test_rejects_invalid_entries(bad):
    assert_refused(pack(BASE + [bad]))


def assert_refused(raw):
    with pytest.raises(core.Refused) as caught:
        encoder.encode_environment(raw)
    error = caught.value
    assert error.args == ("install_environment_refused",)
    assert error.__cause__ is None and error.__context__ is None
    assert error.__suppress_context__ is True


@pytest.mark.parametrize("raw", [b"", None, "[]", bytearray(b"[]"), b"\xff", b"\xef\xbb\xbf[]",
                               b"[] []", b"[] trailing", b"{}", b"null", b"true", b"NaN",
                               b'["unterminated', b'{"K":1,"K":2}', b"[" * 2000 + b"]" * 2000])
def test_refuses_bad_payloads(raw):
    assert_refused(raw)


@pytest.mark.parametrize("index", range(4))
def test_required_missing_empty_and_duplicate(index):
    assert_refused(pack(BASE[:index] + BASE[index + 1:]))
    assert_refused(pack(BASE[:index] + [BASE[index].split("=", 1)[0] + "="] + BASE[index + 1:]))
    assert_refused(pack(BASE + [BASE[index]]))


def test_duplicates_cannot_hide_behind_overrides_or_json_escapes():
    assert_refused(pack(BASE + ["NO_TRADING=true", "NO_TRADING=false"]))
    assert_refused(pack(BASE + ["X=one", "X=two"]))
    raw = pack(BASE)[:-1] + b',"SERVICE_\\u0054OKEN=other"]'
    assert_refused(raw)


def test_byte_limit_is_inclusive():
    raw = pack(BASE)
    assert encoder.encode_environment(raw + b" " * (65_536 - len(raw)))
    assert_refused(raw + b" " * (65_537 - len(raw)))
    assert_refused(pack(BASE + ["X=" + "x" * 65_536]))


@pytest.mark.parametrize("raw", [b'["SYNTHETIC_PRIVATE_KEY=secret"',
                               pack(BASE + ["SYNTHETIC_PRIVATE_KEY=secret\ud800"]),
                               pack(BASE + ["SYNTHETIC_PRIVATE_KEY=secret\nNO_TRADING=false"])])
def test_exceptions_do_not_disclose_key_like_secrets(raw):
    with pytest.raises(core.Refused) as caught:
        encoder.encode_environment(raw)
    error = caught.value
    diagnostic = str(error) + repr(error) + "".join(traceback.format_exception(error))
    assert "SYNTHETIC_PRIVATE_KEY" not in diagnostic
    assert error.__context__ is None and error.__cause__ is None


def test_encoder_has_no_io(monkeypatch):
    raw = pack(BASE)
    def forbidden(*args, **kwargs):
        raise AssertionError("encoder attempted I/O")
    with monkeypatch.context() as patch:
        for owner, names in ((builtins, ("open", "print")), (io, ("open",)),
                             (os, ("open", "pipe", "read", "write")),
                             (subprocess, ("Popen", "run"))):
            for name in names:
                patch.setattr(owner, name, forbidden)
        result = encoder.encode_environment(raw)
    assert result.startswith(b"SERVICE_TOKEN=synthetic-token\n")
