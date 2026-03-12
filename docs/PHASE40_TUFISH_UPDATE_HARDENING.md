# Phase 40 — TUF-style hardening for update manifests (tuf-ish)

Adds:
- Expiry enforcement: meta.expires_ts
- Anti-rollback local state: data/update_state.json
  - last_accepted_version (future use)
  - last_manifest_sha256
- Key rotation: supports multiple Ed25519 public keys
- Optional strictness: updates.require_signature=true to reject unsigned/unverified manifests
- Multi-role metadata validation: roles.root/targets/timestamp/snapshot
- Threshold signatures per role (unique signer count must meet role.threshold)
- Root/key rotation policy validation (min_signatures + max_key_age_days)

Files:
- services/update/update_state.py
- services/update/tufish.py
- scripts/release_validate_manifest.py

Config (template additions):
updates:
  require_signature: false
  public_keys_paths: []
  state_path: data/update_state.json

Notes:
- Signature verification needs `cryptography` installed.
- This remains “check only” (no auto-download/install).
- Validator flags:
  - `--require_roles`
  - `--require_role_signatures`
  - `--require_rotation_policy`
