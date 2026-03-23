# Phase 1 runtime checkpoint (partial)

## Completed
- Service-token auth enforced across reviewed non-health Phase 1 routes
- Shared config defines `service_token`
- Gateway auth works for clients
- Gateway forwards auth to orchestrator
- Repo-root import path fix allows crypto-edge store access
- Authenticated `/v1/chat` returns `200`
- Crypto-edge data is present in the response

## Remaining partial state
- OpenAI-backed reasoning/chat is still falling back
- `assistant_status.fallback = true`
- `chat_status.fallback = true`

## Confirmed root cause
- `OPENAI_API_KEY` is empty in:
  - gateway container
  - orchestrator container

## Not a current blocker anymore
- Route auth
- Gateway→orchestrator auth propagation
- Crypto-edge `ModuleNotFoundError`

## Move forward
1. Set `OPENAI_API_KEY` in `phase1_research_copilot/.env` locally
2. Rebuild `gateway` and `orchestrator`
3. Re-run authenticated `/v1/chat`
4. Confirm:
   - `assistant_status.fallback = false`
   - `chat_status.fallback = false`
