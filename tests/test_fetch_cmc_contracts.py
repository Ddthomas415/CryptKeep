"""Offline tests for the CMC contract-address fetcher (fake network)."""
import csv
import hashlib
import json

import pytest

from scripts.research import fetch_cmc_contracts as f


def body(cmc_id, slug, symbol, *addresses, error="0"):
    return json.dumps({"status": {"error_code": error},
                       "data": {"id": int(cmc_id), "slug": slug, "symbol": symbol,
                                "platforms": [{"contractAddress": a, "contractPlatform": "Ethereum"} for a in addresses]}}).encode()


def write_ids(tmp_path, rows):
    path = tmp_path / "ids.csv"
    with open(path, "w", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=["cmc_id", "symbol", "slug", "why"])
        w.writeheader()
        w.writerows(rows)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


ROWS = [{"cmc_id": "1", "symbol": "AAA", "slug": "aaa", "why": "mapped"},
        {"cmc_id": "2", "symbol": "RNDR", "slug": "render-token", "why": "mapped"},
        {"cmc_id": "3", "symbol": "NAT", "slug": "native", "why": "mapped"}]
BODIES = {"1": body("1", "aaa", "AAA", "0xAbC", ""), "2": body("2", "render", "RENDER", "0x6de", "rndriz"),
          "3": body("3", "native", "NAT")}


class Fake:
    def __init__(self, script=None):
        self.urls, self.script = [], dict(script or {})

    def __call__(self, url):
        self.urls.append(url)
        if len(self.urls) in self.script:
            return self.script[len(self.urls)]
        return 200, BODIES[url.rsplit("=", 1)[1]]


def run(tmp_path, extra=(), get=None):
    ids, sha = write_ids(tmp_path, ROWS)
    return f.main(["--ids", str(ids), "--ids-sha256", sha, "--output-dir", str(tmp_path / "out"), *extra],
                  get=get or Fake(), sleep=lambda s: None)


def test_fetch_saves_every_body_with_hash_and_parse_extracts_contracts(tmp_path):
    fake = Fake()
    assert run(tmp_path, get=fake)["remaining"] == 0 and len(fake.urls) == 3
    lines = [json.loads(l) for l in (tmp_path / "out" / "requests.jsonl").read_text().splitlines()]
    for line in lines:
        data = (tmp_path / "out" / line["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == line["sha256"] and line["http_status"] == 200
    run(tmp_path, ["--parse"])
    doc = json.loads((tmp_path / "out" / "cmc_contracts.json").read_text())
    assert doc["schema"] == "entr-cb1-cmc-contracts-v1" and doc["problems"] == []
    assert doc["assets"]["1"]["contracts"] == ["0xAbC"]  # empty address dropped
    assert doc["assets"]["2"]["contracts"] == ["0x6de", "rndriz"] and doc["assets"]["3"]["contracts"] == []
    assert doc["renamed_since_list"] == {"2": {"list_symbol": "RNDR", "list_slug": "render-token",
                                               "cmc_symbol": "RENDER", "cmc_slug": "render"}}


def test_rerun_skips_ids_already_saved_and_retries_transient_failures(tmp_path):
    fake = Fake({2: (429, b"slow"), 3: (None, b"NETWORK_ERROR")})
    run(tmp_path, get=fake)
    assert len(fake.urls) == 5  # id 2 took three attempts
    again = Fake()
    assert run(tmp_path, get=again)["remaining"] == 0 and again.urls == []


def test_a_wrong_id_or_error_body_is_a_problem_not_a_record(tmp_path):
    BODIES_BAD = dict(BODIES, **{"1": body("99", "aaa", "AAA", "0x1"), "3": body("3", "native", "NAT", error="500")})

    def get(url):
        return 200, BODIES_BAD[url.rsplit("=", 1)[1]]
    run(tmp_path, get=get)
    run(tmp_path, ["--parse"])
    doc = json.loads((tmp_path / "out" / "cmc_contracts.json").read_text())
    assert set(doc["assets"]) == {"2"} and len(doc["problems"]) == 2


def test_cap_pinning_and_subset_rules(tmp_path):
    assert run(tmp_path, ["--max-requests", "2"])["stopped"] == "request_cap"
    ids, sha = write_ids(tmp_path, ROWS)
    with pytest.raises(SystemExit):
        f.main(["--ids", str(ids), "--ids-sha256", "0" * 64, "--output-dir", str(tmp_path / "o2")], get=Fake())
    with pytest.raises(SystemExit):
        f.main(["--ids", str(ids), "--ids-sha256", sha, "--output-dir", str(tmp_path / "o3"), "--only", "1,77"], get=Fake())


def test_changed_saved_body_refuses_parse(tmp_path):
    run(tmp_path)
    raw = sorted((tmp_path / "out" / "raw").iterdir())[0]
    raw.write_bytes(raw.read_bytes() + b" ")
    with pytest.raises(SystemExit):
        run(tmp_path, ["--parse"])
