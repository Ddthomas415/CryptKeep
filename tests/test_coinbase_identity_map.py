"""Offline tests for the ENTR-CB-1 identity-map builder v3 (synthetic Coinbase and CMC records)."""
import csv
import json

import pytest

from scripts.research import build_coinbase_identity_map as m


def prod(pid, status="online"):
    base, quote = pid.split("-")
    return {"id": pid, "base_currency": base, "quote_currency": quote, "status": status}


def cur(cid, name, *networks):
    return {"id": cid, "name": name, "supported_networks": [{"id": n, "contract_address": a} for n, a in networks]}


PRODUCTS = [prod("KNOWN-USD"), prod("EDGE-USD"), prod("EDGEX-USD"), prod("CORECHAIN-USD"), prod("JUP-USD", "delisted"),
            prod("JUPITER-USD"), prod("RNDR-USD", "delisted"), prod("RENDER-USD"), prod("ONLYBTC-BTC"),
            prod("NATIVE-USD"), prod("FAKE-USD")]
CURRENCIES = [cur("KNOWN", "Known Coin", ("ethereum", "0xAAA")), cur("EDGE", "Definitive", ("base", "0xED6")),
              cur("EDGEX", "Edgex", ("ethereum", "0xB00")), cur("CORECHAIN", "Core", ("coredao", "")),
              cur("JUP", "Jupiter", ("ethereum", "0x4B1")), cur("JUPITER", "Jupiter", ("solana", "JUPyiw")),
              cur("RNDR", "Render Token", ("ethereum", "0x6de")), cur("RENDER", "Render Network", ("solana", "rndriz")),
              cur("ONLYBTC", "Only Btc"), cur("NATIVE", "Native", ("native", "")), cur("FAKE", "Fake", ("ethereum", "0xF00"))]
IDS = [{"cmc_id": "1", "symbol": "KNOWN", "slug": "known-coin"}, {"cmc_id": "2", "symbol": "EDGE", "slug": "edgex"},
       {"cmc_id": "3", "symbol": "CORE", "slug": "core-dao"}, {"cmc_id": "4", "symbol": "JUP", "slug": "jupiter-ag"},
       {"cmc_id": "5", "symbol": "RNDR", "slug": "render-token"}, {"cmc_id": "6", "symbol": "ONLYBTC", "slug": "only-btc"},
       {"cmc_id": "7", "symbol": "ABSENT", "slug": "absent"}, {"cmc_id": "8", "symbol": "NATIVE", "slug": "native"},
       {"cmc_id": "9", "symbol": "FAKE", "slug": "fake"}]
CONTRACTS = {"1": {"contracts": ["0xaaa"]}, "2": {"contracts": ["0xb00"]}, "3": {"contracts": []},
             "4": {"contracts": ["JUPyiw"]}, "5": {"contracts": ["0x6DE", "rndriz"]}, "8": {"contracts": ["0x123"]},
             "9": {"contracts": ["0xbeef"]}}
ADJ = {"2": {"decision": "mapped", "coinbase_base": "EDGEX", "reason": "edgeX is EDGEX"},
       "3": {"decision": "mapped", "coinbase_base": "CORECHAIN", "reason": "Core DAO is CORECHAIN"},
       "4": {"decision": "mapped", "coinbase_base": "JUPITER", "reason": "Solana Jupiter is JUPITER"}}


def build(adj=ADJ, contracts=CONTRACTS, ids=IDS):
    return m.build(ids, PRODUCTS, CURRENCIES, adj, contracts)


def test_alternates_are_checked_even_when_the_ticker_exists_under_another_project():
    plain = m.build(IDS, PRODUCTS, CURRENCIES, {}, None)
    assert plain["2"]["status"] == "unknown" and plain["2"]["alternate_candidates"] == ["EDGEX"]  # v2 skipped this
    assert plain["3"]["alternate_candidates"] == ["CORECHAIN"]  # name equals the slug's first word
    assert plain["4"]["alternate_candidates"] == ["JUPITER"]
    out = build()
    assert out["2"]["status"] == "mapped" and [p["id"] for p in out["2"]["products"]] == ["EDGEX-USD"]
    assert out["4"]["coinbase_base"] == "JUPITER" and [p["id"] for p in out["4"]["products"]] == ["JUPITER-USD"]


def test_embedded_ticker_is_a_candidate_and_a_ticker_alone_never_maps():
    ids = [{"cmc_id": "20", "symbol": "LUNA", "slug": "terra"}]
    products = [prod("WLUNA-USD", "delisted")]
    out = m.build(ids, products, [cur("WLUNA", "Wrapped Thing", ("ethereum", "0x1"))], {}, None)
    assert out["20"]["status"] == "unknown" and out["20"]["alternate_candidates"] == ["WLUNA"]
    ids = [{"cmc_id": "21", "symbol": "SAME", "slug": "other-project"}]
    out = m.build(ids, [prod("SAME-USD")], [cur("SAME", "Unrelated Name")], {}, None)
    assert out["21"]["status"] == "unknown" and out["21"]["reason"] == "name_slug_mismatch_unadjudicated"


def test_whole_name_equal_to_the_slugs_first_word_is_a_candidate():
    ids = [{"cmc_id": "30", "symbol": "BSV", "slug": "bitcoin-sv"}]
    out = m.build(ids, [prod("BTC-USD")], [cur("BTC", "Bitcoin", ("bitcoin", ""))], {}, None)
    assert out["30"]["alternate_candidates"] == ["BTC"] and out["30"]["status"] == "unknown"


def test_a_coin_listed_on_its_own_network_is_not_comparable_even_with_bridged_contracts():
    ids = [{"cmc_id": "31", "symbol": "ZEC", "slug": "zcash"}]
    currencies = [cur("ZEC", "Zcash", ("base", "0xB200"), ("zcash", ""))]
    out = m.build(ids, [prod("ZEC-USD")], currencies, {}, {"31": {"contracts": ["0xother"]}})
    assert out["31"]["contract_check"] == {"ZEC": "not_comparable"} and out["31"]["status"] == "mapped"


def test_avalanche_style_0x_prefixed_lowercased_id_matches_and_placeholders_never_match():
    ids = [{"cmc_id": "40", "symbol": "AVAX", "slug": "avalanche"}, {"cmc_id": "41", "symbol": "PH", "slug": "ph"}]
    currencies = [cur("AVAX", "Avalanche", ("avacchain", "0xfvweahmx")), cur("PH", "Ph", ("chain", "0x" + "e" * 40))]
    out = m.build(ids, [prod("AVAX-USD"), prod("PH-USD")], currencies, {},
                  {"40": {"contracts": ["FvwEAhmx", "0xabc"]}, "41": {"contracts": ["0x" + "E" * 40, "0x99"]}})
    assert out["40"]["contract_check"] == {"AVAX": "match"}
    assert out["41"]["contract_check"] == {"PH": "not_comparable"}  # the only Coinbase address is a placeholder


def test_plain_statuses_are_unchanged():
    out = build()
    assert out["1"]["status"] == "mapped" and out["1"]["reason"] == "exact_name_slug"
    assert out["6"] == {"cmc_id": 6, "symbol": "ONLYBTC", "slug": "only-btc", "status": "never_listed",
                        "reason": "no_usd_usdc_usdt_product"}
    assert out["7"]["status"] == "never_listed" and out["7"]["reason"] == "absent_from_products"


def test_contract_check_outcomes():
    out = build()
    assert out["1"]["contract_check"] == {"KNOWN": "match"}  # case-insensitive
    assert out["3"]["contract_check"] == {"CORECHAIN": "not_comparable"}  # Coinbase lists its own network
    assert out["8"]["contract_check"] == {"NATIVE": "not_comparable"} and out["8"]["status"] == "mapped"
    assert out["9"]["contract_check"] == {"FAKE": "mismatch"}
    assert out["9"]["status"] == "unknown" and out["9"]["reason"].startswith("contract_mismatch")


def test_the_v2_jupiter_error_is_caught_by_the_contract_check():
    adj = dict(ADJ)
    adj["4"] = {"decision": "mapped", "reason": "same project"}  # v2: mapped to the ticker JUP
    out = build(adj)
    assert out["4"]["contract_check"] == {"JUP": "mismatch"} and out["4"]["status"] == "unknown"


def test_contract_override_needs_an_explicit_reason():
    adj = dict(ADJ, **{"9": {"decision": "mapped", "reason": "x", "contract_override": "legacy token, issuer-documented"}})
    ids = [r if r["cmc_id"] != "9" else {"cmc_id": "9", "symbol": "FAKE", "slug": "fake-other"} for r in IDS]
    out = build(adj, ids=ids)
    assert out["9"]["status"] == "mapped" and out["9"]["contract_override"].startswith("legacy")


def test_missing_cmc_contract_data_makes_a_mapped_id_unknown():
    contracts = {k: v for k, v in CONTRACTS.items() if k != "1"}
    out = build(contracts=contracts)
    assert out["1"]["status"] == "unknown" and out["1"]["reason"].startswith("cmc_contract_data_missing")


def test_continuation_is_annotated_but_not_applied_without_an_adjudication():
    out = build()
    assert out["5"]["status"] == "mapped" and [p["id"] for p in out["5"]["products"]] == ["RNDR-USD"]
    assert out["5"]["continuation_candidates"] == ["RENDER"]


def test_continuation_adjudication_unions_products_when_every_base_matches_cmc_contracts():
    adj = dict(ADJ, **{"5": {"decision": "mapped", "coinbase_bases": ["RNDR", "RENDER"], "reason": "1:1 migration"}})
    out = build(adj)
    assert [p["id"] for p in out["5"]["products"]] == ["RENDER-USD", "RNDR-USD"]
    assert out["5"]["contract_check"] == {"RNDR": "match", "RENDER": "match"}
    assert "continuation_candidates" not in out["5"]


@pytest.mark.parametrize("bases,contracts5", [(["RNDR", "RENDER"], ["0x6de"]),      # RENDER not listed by CMC
                                              (["RNDR", "NOPE"], ["0x6de", "rndriz"]),  # base without products
                                              (["RENDER"], ["0x6de", "rndriz"])])       # drops the mapped base
def test_continuation_is_refused_unless_fully_supported(bases, contracts5):
    adj = dict(ADJ, **{"5": {"decision": "mapped", "coinbase_bases": bases, "reason": "1:1 migration"}})
    contracts = dict(CONTRACTS, **{"5": {"contracts": contracts5}})
    with pytest.raises(ValueError):
        build(adj, contracts)


def test_bad_alternate_adjudication_is_refused():
    with pytest.raises(ValueError):
        build(dict(ADJ, **{"2": {"decision": "mapped", "coinbase_base": "KNOWN", "reason": "not a candidate"}}))
    with pytest.raises(ValueError):
        build(dict(ADJ, **{"2": {"decision": "never_listed"}}))


def test_shared_base_is_annotated():
    ids = IDS + [{"cmc_id": "10", "symbol": "KNOWN", "slug": "known-coin"}]
    out = build(ids=ids, contracts=dict(CONTRACTS, **{"10": {"contracts": ["0xaaa"]}}))
    assert out["1"]["shares_coinbase_base_with"] == ["10"] and out["10"]["shares_coinbase_base_with"] == ["1"]


def test_main_records_input_hashes_and_writes_review_columns(tmp_path):
    files = {"ids.csv": None, "products.json": PRODUCTS, "currencies.json": CURRENCIES,
             "adj.json": {"adjudications": ADJ}, "contracts.json": {"schema": "entr-cb1-cmc-contracts-v1", "assets": CONTRACTS}}
    with open(tmp_path / "ids.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cmc_id", "symbol", "slug"])
        w.writeheader()
        w.writerows(IDS)
    for name, doc in files.items():
        if doc is not None:
            (tmp_path / name).write_text(json.dumps(doc))
    args = ["--ids", str(tmp_path / "ids.csv"), "--products", str(tmp_path / "products.json"),
            "--currencies", str(tmp_path / "currencies.json"), "--adjudications", str(tmp_path / "adj.json"),
            "--cmc-contracts", str(tmp_path / "contracts.json"), "--output-dir", str(tmp_path / "out")]
    m.main(args)
    doc = json.loads((tmp_path / "out" / "identity_map.json").read_text())
    assert doc["schema"] == "entr-cb1-identity-map-v3" and len(doc["inputs"]) == 5
    rows = list(csv.DictReader(open(tmp_path / "out" / "review.csv")))
    assert {r["cmc_id"]: r["contract_check"] for r in rows}["9"] == "FAKE=mismatch"
    with pytest.raises(FileExistsError):
        m.main(args)
