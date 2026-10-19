# Local Keyword Deployment

## Objective

Activate the accepted keyword retrieval source in the existing local memory and
orchestrator services. Preserve their environment, mounts, loopback bindings and
storage. No trading, campaign, paid-model or collector changes.

## Procedure

The one-shot operator script is
`/private/tmp/cryptkeep_retrieval_deploy_20261011.py`. Its minimal image overlay
copies only memory_retrieval/main.py, shared/tools.py and orchestrator/main.py
onto each service's existing image. Original images are retained for rollback.
Private configuration snapshots are written with mode 0600 in a mode 0700
temporary directory; these include credentials and must not be shared or committed.

Only memory and orchestrator are recreated with dependencies excluded. The
script checks research-only mode, local bindings and expected network before
launch. It refuses paid-model credentials. Failed verification restores the old
images and environment. It does not remove containers belonging to other services
or touch existing database/object-store/vector volumes.

## Required Proof

- Authenticated memory retrieval returns BTC keyword matches; an unmatched
  term returns none; unauthenticated retrieval is rejected.
- Authenticated explanation returns keyword citations explicitly marked as
  not semantically verified, and execution remains disabled.
- Environment, mounts and ports remain identical; unrelated container identity
  and start times remain unchanged.

Targeted source regression slice: 31 passed, 90 deprecation warnings.
Operator script syntax compilation passed. Deployment outcome and independent
review are recorded in the work log and a separate receipt.

## Limits

Keyword relevance is not semantic understanding or a validated trading edge.
This is a local deployment, not sustained-health or production-readiness proof.
The private override is required to recreate this particular deployment; a
later generic Compose rebuild could replace it. Rollback images are retained,
but a rollback drill is not part of the successful deployment path.
