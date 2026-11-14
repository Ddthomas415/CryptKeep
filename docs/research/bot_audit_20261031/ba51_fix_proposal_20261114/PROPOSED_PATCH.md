# BA-51 proposed fix (NOT applied; for Codex to apply, test and have reviewed)

Decision taken under the owner's delegation of 2026-11-14 ("take care of it", after the session 12 report):
option (a), **record the producer code identity, do not enforce it at read time.** Reason: spec section 4 requires
the ranking's code identity to be recorded "as R6"; the ranker, signal library, generator and universe hashes
(`FROZEN`) remain enforced, which is the identity the spec cares about. The owner may reverse this.

Reproduced by execution (`repro_ba51.py`, `repro_output.txt`): a valid artifact is accepted; after one comment line
is appended to `group_b_weekly_selection.py` the same artifact is refused with `selection_identity_or_week`.

## Change 1: `services/market_data/group_b_selection.py` (current sha256 prefix e5680a0cbd269679)

Replace, in `validate_selection` (line 116):
```python
            or artifact.get("code") != FROZEN or artifact.get("producer_code") != producer_identity()
```
with
```python
            or artifact.get("code") != FROZEN or not _recorded_producer_code(artifact.get("producer_code"))
```
and add, after `producer_identity()` (line 28):
```python
def _recorded_producer_code(value):
    """Recorded identity of the code that produced the file; not compared with the code now on disk."""
    return (type(value) is dict and sorted(value) == sorted(PRODUCER_FILES)
            and all(type(v) is str and re.fullmatch(r"[0-9a-f]{64}", v) for v in value.values()))
```
with `import re` added to the imports. `build_selection` (`group_b_weekly_selection.py` line 36) is unchanged: it
still records `producer_identity()` at build time, so every weekly file carries the exact producer code that made it.

Consequences, traced: `resolve_slot` accepts the published file after a producer edit; a same-week replacement is
still refused (the pinned hash is a separate check, unchanged); `build_selection --previous` accepts the old file;
`buy_selection_verdict` unchanged. The tamper check on the file itself (`sha256` over the body, line 112) is unchanged.

## Change 2: tests to add (draft file `test_ba51_producer_code_recorded_draft.py` in this folder; Codex copies into `tests/`)
1. A valid artifact is still accepted after a producer file changes (monkeypatch `producer_identity` to return
   different hashes, or write a scratch copy as in `repro_ba51.py`).
2. An artifact whose `producer_code` is missing, has a wrong key set, or a non-hex value is refused
   (`selection_identity_or_week`).
3. `build_selection` output carries `producer_code == producer_identity()` at build time (recording still works).

## Not changed
`FROZEN` enforcement; file `sha256`; same-week pin; slot continuity chain; consumer guards; any configuration.
