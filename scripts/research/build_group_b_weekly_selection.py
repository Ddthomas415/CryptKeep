"""Build from already captured public inputs only. Never fetches or starts a job."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from services.analytics.group_b_weekly_selection import build_selection, publish_selection
from services.market_data.group_b_selection import MAX_BYTES
from storage.exit_event_journal import _decode_payload


def read_json(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input_too_large")
    return _decode_payload(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, help="JSON object with an ordered inputs array")
    parser.add_argument("--rank-at", required=True, help="Monday 00:05 UTC; input availability is retained")
    parser.add_argument("--previous", help="Last published selection, omitted only for initial bootstrap")
    parser.add_argument("--output-directory", required=True)
    args = parser.parse_args(argv)
    artifact = build_selection(inputs=read_json(args.inputs)["inputs"], rank_at=args.rank_at,
                               generated_at=datetime.now(timezone.utc).isoformat(),
                               previous=read_json(args.previous) if args.previous else None)
    path = publish_selection(artifact, args.output_directory)
    print(str(path))
    print(artifact["sha256"])
    return 0


if __name__ == "__main__":
    main()
