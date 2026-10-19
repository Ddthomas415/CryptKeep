# Independent stopped-recipe compatibility review

Reviewer: Plato, separate GATE subagent `01a15172-d375-7d31-80b2-90043f636708`.
Returned 2026-10-18 UTC. Recorded by the implementing thread without changing
the review disposition. Reviewed scope: the v1 projection and added regressions,
not the entirety of the pre-existing untracked files.

## Disposition: ACCEPTED_WITH_RISK

No blocking findings in the bounded compatibility fix.

- SHOWN: v1 checks all three newer fields against defaults before comparing
  exactly the 11 legacy keys. Saved snapshots are not filtered. Extra or missing
  saved keys still fail.
- SHOWN: all seven tamper cases reject with
  `reconciliation_fingerprint_mismatch`. Each nondefault newer field rejects.
- SHOWN: v2 bypasses projection and retains full-snapshot comparison. Valid v2
  passes. Missing, extra and altered fields reject.
- SHOWN: capture4's seven snapshots match independently recomputed legacy fields.
  Its source-manifest hash binding matches. Output remains unpaired, unauthorized
  for installation and incompatible with the executable plan loader.

## Independent verification

VERIFIED_ENV, repository cwd:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_companion_stopped_recipe.py tests/test_collect_companion_recreation_metadata.py
```

Exit 0, **50 passed in 0.40s**. The reviewer did not independently rerun the
implementer's baseline 22-pass/2-fail result.

SHA256 values were identical before and after the independent checks:

| File | SHA256 |
| --- | --- |
| `scripts/research/collect_companion_recreation_metadata.py` | `494803eb4e279efeb6c961c4833de43c388a63df7fc5c63382cdb2ce80c0c2ea` |
| `tests/test_companion_stopped_recipe.py` | `f3f750308c6752f5773dac6a15c8500e219586ea64646150323dc1d5687d2c30` |
| `tests/test_collect_companion_recreation_metadata.py` | `0a7f8eef53070e071d7b78ef0d4950b288415c02901b63c962ca838fb3346a8e` |
| capture4 observation | `13c51c9f49a1e16cd767e2f51d21c84d045f31e210d238f67fc9c7909d55a78f` |
| source manifest | `bac2f4636753237279858c2119630be12531d8d27f6967868d72e9cbac940093` |
| original proposal diff | `f299204a0308e38ec280fee9103120e4a43573ad3db0d0a8d50a6d767c1ec96d` |

## Limits

Capture4 lacks a retained final payload. Internal consistency is not
authenticated capture provenance or runtime equivalence. No Docker, services,
credentials, network or operational commands were used. Tests used synthetic
temporary fixtures only. Runtime remains UNVERIFIED and is not approved.
