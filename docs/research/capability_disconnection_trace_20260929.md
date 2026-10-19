# Capability disconnection trace - first pass

Role: AUDITOR. Date: 2026-09-29. Read-only runtime inspection.
This is a scoped inventory, not a full documentation audit or restoration approval.

## Evidence boundary

GitHub API confirmed master `580ca31ea983af6452a1e02ab8d4b51645e9b43c`.
Local classification/selection-decision docs, AI signal service, and market
intelligence module have no diff against that commit. Other local docs are dirty;
do not describe their content as published GitHub truth. GitHub issues, PR bodies,
wiki, all historical docs and deployed runtime were not comprehensively inspected.

## Findings and dispositions

| Capability | SHOWN evidence | Disposition and benefit |
|---|---|---|
| News, normalization, memory and orchestration | `ad18488df` removed the companion tree from tracking. `docs/COMPANION_REPO_DEPENDENCY.md` subsequently classifies it as optional/archived. Historical runtime checkpoint only reports partial chat operation. | Continue isolated recovery already underway. Restore source-backed event context for research; do not claim the original stack was fully operational. |
| Candidate discovery and symbol ranking | `docs/research/signal_discovery_classification.md` lists retained modules. `services/strategies/strategy_selector.py` still has the opt-in candidate advisor bridge. | Reuse for research candidate proposals rather than rebuilding discovery. End-to-end utility and current activity remain UNVERIFIED. |
| Autonomous strategy substitution | `42ef854c6` and `docs/decisions/strategy_selection_authority_decision.md` deliberately keep configured identity authoritative to prevent invalid identities silently falling back to another strategy. | Retain restriction. Adaptive research is not permission to restore unsafe execution substitution. A future validated selection policy requires explicit scope. |
| Social sentiment and liquidation context | `services/market_data/market_intelligence.py` returns null placeholder fields with `scaffold_only` labels. Introduction `2e4e5eac1` already contained placeholders. | Classify as never completed, not removed. Do not mistake dashboard presence for a working feed or prioritize speculative restoration. |
| AI model gate versus contextual research | `services/ai_engine/signal_service.py` returns `model_missing_pass_through` when model loading fails or no model exists. `fa879ad00` introduced an AI scaffold, not a regulatory-awareness pipeline. | Keep distinct from recovered research copilot. Enabling this hook does not restore news awareness or establish adaptation; no activation recommended. |

## Verification

Command: `.venv/bin/python -m pytest -q tests/test_strategy_discovery_hygiene_contract.py tests/test_strategy_selection_authority_decision_guard.py tests/test_companion_repo_dependency.py`

Result: **13 passed in 0.26s**. This proves targeted repository contracts only,
not live news delivery, predictive value, deployment health, or profitability.

## Prioritized follow-through

1. Complete the current isolated news parse/store/retrieve proof before activation.
2. Trace retained candidate outputs into research reports and historical outcome
   evaluation; reconnect only if a specific missing consumer is demonstrated.
3. Inspect remaining original-vision documents and Git history for event/macro,
   archive retrieval, operator recommendations, and feedback-loop coverage.
4. Reconcile published versus local documentation before changing canonical claims.

No identified component is approved for automatic execution, new campaigns, or
capital changes. Attribution of the original removal to a specific agent/user
authorization remains UNVERIFIED. Overall audit state: INCOMPLETE.
