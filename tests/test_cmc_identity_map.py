import hashlib
import json

import pytest
from scripts.research.build_cmc_identity_map import build


def test_only_proposals_mapped_and_evidence_checked(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("{}")
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps({"input_sha256": {str(source): hashlib.sha256(source.read_bytes()).hexdigest()},
                                   "rows": [{"cmc_id": 5117, "product": "OGN-USD", "source_snapshot": str(source),
                                             "status": "MATCHING_CHAIN_AND_CONTRACT_PROPOSAL"},
                                            {"cmc_id": 40925, "status": "KNOWN_MISMATCH"}]}))
    assert set(build(proposal)) == {"5117"}
    source.write_text("changed")
    with pytest.raises(ValueError, match="evidence changed"):
        build(proposal)
