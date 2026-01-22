# Phase 313 — Release Notes Generator

Files:
- CHANGELOG.md (source of human-written change notes)
- scripts/generate_release_notes.py (deterministic generator)
- releases/RELEASE_NOTES.md (output file)
- .github/workflows/release-publish.yml uses body_path=RELEASE_NOTES.md

CLI:
- `python scripts/generate_release_notes.py --tag v0.1.0`
- `python scripts/generate_release_notes.py --tag v0.1.0 --manifest-glob "releases/release_manifest_*.json"`

Changelog format:
- `## [X.Y.Z] - YYYY-MM-DD` sections
- Any content under that header is included verbatim in the release notes “Changes” section.

Manifest summary:
- Reads one or more release_manifest_*.json files
- Adds a top-artifacts table with SHA-256 hashes (exact distributable bits)
