"""Non-mutating identity-checked merge of frozen study groups."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

GROUPS = ("recovery", "ideas", "top10", "cmc")
IDENTITY = ("script_sha256", "shared_math_sha256", "original_source_sha256")


def merge(parts):
    if set(parts) != set(GROUPS):
        raise ValueError("all four groups required")
    base = copy.deepcopy(parts["recovery"])
    base["results"], base["input_sha256"] = {}, {}
    for group in GROUPS:
        item = parts[group]
        if any(item[key] != parts["recovery"][key] for key in IDENTITY):
            raise ValueError("mixed source identities")
        if not item["results"] or set(base["results"]) & set(item["results"]):
            raise ValueError("empty or duplicate study results")
        base["results"].update(copy.deepcopy(item["results"]))
        for directory, hashes in item["input_sha256"].items():
            if directory in base["input_sha256"] and base["input_sha256"][directory] != hashes:
                raise ValueError("conflicting input hashes")
            base["input_sha256"][directory] = copy.deepcopy(hashes)
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = {g: Path(str(args.prefix) + "." + g + ".json").read_bytes() for g in GROUPS}
    result = merge({g: json.loads(value) for g, value in raw.items()})
    result["group_artifact_sha256"] = {g: hashlib.sha256(value).hexdigest() for g, value in raw.items()}
    result["merge_source"] = Path(__file__).read_text()
    with args.out.open("x") as stream:
        json.dump(result, stream, allow_nan=False)
    print(json.dumps({"studies": list(result["results"])}))


if __name__ == "__main__":
    main()
