import json

import pytest

from scripts.research import run_low_value_top100_v2 as corrected
from scripts.research import test_low_value_top100 as original


def row(identity, slug):
    return [identity, "X", slug, 60, .5, 2e6, 1e9, 10, "2018-01-01", ["defi"]]


def test_all_eleven_instruments_excluded_even_when_tags_are_missing():
    mapping = json.loads((corrected.ARTIFACTS / "instrument_correction_v2.json").read_text())
    snapshot = {item["id"]: row(item["id"], item["slug"]) for item in mapping["exclusions"]}
    snapshot.update({3964: row(3964, "reserve-rights"), 6953: row(6953, "frax-share"),
                     1518: row(1518, "maker"), 2539: row(2539, "ren")})
    before = {key: value[:] for key, value in snapshot.items()}
    view = corrected.corrected_view([snapshot], mapping)
    assert set(view[0]) == {3964, 6953, 1518, 2539}
    assert snapshot == before
    assert original.choose(view, 0)["under_1"] == [1518, 2539, 3964, 6953]


def test_identity_mismatch_fails_instead_of_ticker_guess():
    mapping = {"exclusions": [{"id": 5777, "slug": "renbtc"}]}
    with pytest.raises(ValueError, match="slug mismatch"):
        corrected.corrected_view([{5777: row(5777, "unrelated-asset")}], mapping)


def test_no_rank_backfill_or_price_rewrite_and_weights_use_corrected_members():
    mapping = {"exclusions": [{"id": 3717, "slug": "wrapped-bitcoin"}]}
    a, b = row(10, "real-altcoin"), row(11, "outside-top100")
    b[3] = 101
    snapshot = {3717: row(3717, "wrapped-bitcoin"), 10: a, 11: b}
    view = corrected.corrected_view([snapshot], mapping)
    chosen = original.choose(view, 0)["ranks_51_100"]
    assert chosen == [10]
    assert view[0][10] is a and view[0][11][3] == 101
    result = original.cycle(chosen, view[0], view[0], view[0])
    assert result["members"][0]["allocation"] == 1000


def test_duplicate_map_ids_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        corrected.corrected_view([], {"exclusions": [{"id": 1, "slug": "a"}, {"id": 1, "slug": "a"}]})
