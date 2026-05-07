from __future__ import annotations

import os
import threading

from services.os import file_utils


def test_atomic_write_uses_unique_temp_files_per_call(tmp_path, monkeypatch):
    target = tmp_path / "status.json"
    barrier = threading.Barrier(2)
    seen_sources: list[str] = []
    errors: list[BaseException] = []
    real_replace = os.replace

    def _replace(src, dst):
        seen_sources.append(os.fspath(src))
        barrier.wait(timeout=5)
        return real_replace(src, dst)

    monkeypatch.setattr(file_utils.os, "replace", _replace)

    def _writer(payload: str) -> None:
        try:
            file_utils.atomic_write(target, payload)
        except BaseException as exc:  # pragma: no cover - assertion consumes this path
            errors.append(exc)

    t1 = threading.Thread(target=_writer, args=("first",))
    t2 = threading.Thread(target=_writer, args=("second",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors
    assert len(seen_sources) == 2
    assert len(set(seen_sources)) == 2
    assert target.read_text(encoding="utf-8") in {"first", "second"}


def test_atomic_write_bytes_uses_unique_temp_files_per_call(tmp_path, monkeypatch):
    target = tmp_path / "status.bin"
    barrier = threading.Barrier(2)
    seen_sources: list[str] = []
    errors: list[BaseException] = []
    real_replace = os.replace

    def _replace(src, dst):
        seen_sources.append(os.fspath(src))
        barrier.wait(timeout=5)
        return real_replace(src, dst)

    monkeypatch.setattr(file_utils.os, "replace", _replace)

    def _writer(payload: bytes) -> None:
        try:
            file_utils.atomic_write_bytes(target, payload)
        except BaseException as exc:  # pragma: no cover - assertion consumes this path
            errors.append(exc)

    t1 = threading.Thread(target=_writer, args=(b"first",))
    t2 = threading.Thread(target=_writer, args=(b"second",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors
    assert len(seen_sources) == 2
    assert len(set(seen_sources)) == 2
    assert target.read_bytes() in {b"first", b"second"}
