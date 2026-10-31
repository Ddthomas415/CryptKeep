"""Reuse the exact reviewed 23 handoff cases against fixed V6d bindings."""
import hashlib
from pathlib import Path

_source = Path(__file__).with_name("test_companion_v6c_handoff.py")
_raw = _source.read_bytes()
assert hashlib.sha256(_raw).hexdigest() == "81785505e39f40c9b36fa7c98ebc0bbafcd3957b0516387ca7f72d9e7defe958"
exec(compile(_raw.replace(b"v6c", b"v6d").replace(b"V6c", b"V6d"), str(__file__), "exec"), globals())
