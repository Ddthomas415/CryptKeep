import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MOCK_DIR = ROOT / "shared" / "mock-data"
OUTPUT_DIR = ROOT / "build" / "seeded"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        "dashboard.json",
        "explain-sol.json",
        "exchanges.json",
        "settings.json",
        "risk-summary.json",
    ]

    manifest: dict[str, object] = {"seeded_files": []}

    for filename in files:
        source = MOCK_DIR / filename
        target = OUTPUT_DIR / filename

        data = json.loads(source.read_text(encoding="utf-8"))
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

        manifest["seeded_files"].append(
            {
                "name": filename,
                "source": str(source),
                "target": str(target),
            }
        )

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"Seeded {len(files)} demo files into {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
