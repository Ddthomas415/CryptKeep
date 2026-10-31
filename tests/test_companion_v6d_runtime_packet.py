"""Same reviewed fourteen packet contracts against v6d inputs, native forbidden."""
import hashlib
from pathlib import Path

_source = Path(__file__).with_name("test_companion_v6c_runtime_packet.py")
_raw = _source.read_bytes()
assert hashlib.sha256(_raw).hexdigest() == "46ced3fff47f013bb4181eb57cb0de3b03a86b76982abc5432d54847a414ce55"
exec(compile(_raw.replace(b"v6c", b"v6d").replace(b"V6c", b"V6d"), str(__file__), "exec"), globals())


def test_witness_schema_adapter_is_explicit_not_new_native_evidence():
    out = recipe.derive()
    proof = out["provenance.json"]
    assert "image joined" in proof["witness_schema_adapter"]
    assert "not recaptured" in proof["source_provenance"]
    assert proof["direct_application_source_witnesses"] == 43
    assert proof["inherited_same_image_or_storage_pins"] == 89
