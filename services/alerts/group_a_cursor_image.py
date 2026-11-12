"""Persist an in-memory R3 cursor without giving SQLite a filesystem path."""

from contextlib import closing, contextmanager
import fcntl
from hashlib import sha256
import os
import secrets
import sqlite3
import stat

from services.alerts.group_a_cursor_schema import SCHEMA


IMAGE_NAME = "group_a_delivery.image"
EMPTY_IMAGE = b"CBP-GROUP-A-CURSOR-1\n"
_MAX_IMAGE = 16 * 1024 * 1024
_HEADER = len(EMPTY_IMAGE) + 32
_READ = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
_SCHEMA_QUERY = "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY name LIMIT 17"


def _validate_schema(connection):
    with closing(sqlite3.connect(":memory:")) as reference:
        for statement in SCHEMA.values():
            reference.execute(statement)
        expected = reference.execute(_SCHEMA_QUERY).fetchall()
    if connection.execute(_SCHEMA_QUERY).fetchall() != expected:
        raise ValueError("unsafe_alert_cursor_schema")


def _stamp(info, uid):
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600 or not len(EMPTY_IMAGE) <= info.st_size <= _MAX_IMAGE):
        raise ValueError("unsafe_alert_cursor_image")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _read(directory, uid):
    fd = os.open(IMAGE_NAME, _READ, dir_fd=directory)
    with os.fdopen(fd, "rb") as stream:
        before = _stamp(os.fstat(stream.fileno()), uid)
        raw = stream.read(_MAX_IMAGE + 1)
        if len(raw) != before[2] or _stamp(os.fstat(stream.fileno()), uid) != before:
            raise ValueError("alert_cursor_changed_during_read")
    if raw == EMPTY_IMAGE:
        return None, before
    digest, image = raw[len(EMPTY_IMAGE):_HEADER], raw[_HEADER:]
    if (not raw.startswith(EMPTY_IMAGE) or not image.startswith(b"SQLite format 3\x00")
            or image[18:20] != b"\x01\x01" or sha256(image).digest() != digest):
        raise ValueError("invalid_alert_cursor_image")
    return image, before


class _ImageConnection:
    def __init__(self, connection, directory, uid, current):
        self.connection = connection
        self.directory = directory
        self.uid = uid
        self.current = current

    def execute(self, *args):
        return self.connection.execute(*args)

    @property
    def image_bytes(self):
        return self.current[2]

    def checkpoint(self):
        for statement in SCHEMA.values():
            self.connection.execute(statement)
        self.connection.commit()
        return self.connection.serialize()

    def restore(self, image):
        self.connection.rollback()
        self.connection.deserialize(image)

    def commit(self):
        self.connection.commit()
        image = self.connection.serialize()
        data = EMPTY_IMAGE + sha256(image).digest() + image
        if len(data) > _MAX_IMAGE:
            raise ValueError("alert_cursor_image_capacity")
        name = ".cursor-" + secrets.token_hex(16)
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                if stream.write(data) != len(data):
                    raise OSError("short_alert_cursor_write")
                stream.flush()
                os.fsync(stream.fileno())
                intended = _stamp(os.fstat(stream.fileno()), self.uid)
                if intended != _stamp(os.stat(name, dir_fd=self.directory, follow_symlinks=False), self.uid):
                    raise ValueError("alert_cursor_temp_replaced")
                actual = os.stat(IMAGE_NAME, dir_fd=self.directory, follow_symlinks=False)
                if _stamp(actual, self.uid) != self.current:
                    raise ValueError("alert_cursor_replaced")
                os.replace(name, IMAGE_NAME, src_dir_fd=self.directory, dst_dir_fd=self.directory)
                saved = _stamp(os.stat(IMAGE_NAME, dir_fd=self.directory, follow_symlinks=False), self.uid)
                if saved[:4] != intended[:4]:
                    raise ValueError("alert_cursor_replace_unconfirmed")
                os.fsync(self.directory)
                self.current = saved
        finally:
            try:
                os.unlink(name, dir_fd=self.directory)
            except FileNotFoundError:
                pass


@contextmanager
def open_group_a_cursor_image(directory_fd):
    """Lock an independent descriptor for a caller-pinned, dedicated directory."""
    if type(directory_fd) is not int or directory_fd < 0:
        raise ValueError("invalid_alert_cursor_directory")
    fd = os.open(".", os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY, dir_fd=directory_fd)
    try:
        uid = os.geteuid()
        info = os.fstat(fd)
        if info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("unsafe_alert_cursor_directory")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        image, current = _read(fd, uid)
        with closing(sqlite3.connect(":memory:")) as connection:
            if image is not None:
                connection.deserialize(image)
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("PRAGMA temp_store=MEMORY")
            if connection.execute("PRAGMA database_list").fetchall() != [(0, "main", "")]:
                raise ValueError("unsafe_alert_cursor_schema")
            if image is not None:
                _validate_schema(connection)
            page_size, = connection.execute("PRAGMA page_size").fetchone()
            connection.execute(f"PRAGMA max_page_count={(_MAX_IMAGE - _HEADER) // page_size}")
            yield _ImageConnection(connection, fd, uid, current)
    finally:
        os.close(fd)
