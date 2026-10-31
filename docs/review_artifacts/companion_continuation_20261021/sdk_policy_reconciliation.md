# Bounded SDK Evidence Findings

2026-10-21. Independent AUDITOR Plato. Offline source inspection and hashing only.
Disposition: INCOMPLETE for installed policies, not a rejection of accepted code.

SHOWN: all23 saved source copies match the October16 report. Current restricted
memory source SHA25635fc51165e44dba1ab8d28e783285f51f392b01f814096f3950ce720995504a3
matches the continuation pin. Qdrant arguments disable environment proxies and
redirects; captured HTTPX transport defaults to zero retries. S3 construction
uses proxies={} and total_max_attempts=1; captured Botocore transport passes
retries=False to urllib3. Missing bucket/collection refuses under read-only
startup rather than creating resources. None requires another implementation.

UNVERIFIED: the complete Botocore needs-retry and S3 region-redirect handler
registration chain, installed normal startup/import hooks and actual derivative
image bytes. Botocore endpoint.py lines350ff dispatches needs-retry events; the
saved subset does not establish every registered handler. A transport-level
no-retry setting alone is not end-to-end no-replay evidence.

Source pointers:
- phase1_research_copilot/memory_retrieval/main.py:72,94,118.
- companion_installed_policy_20261016/*httpx___transports__default.py.source.txt:147.
- companion_installed_policy_20261016/*botocore__httpsession.py.source.txt:464.
- companion_installed_policy_20261016/*botocore__endpoint.py.source.txt:350.
- tests/test_companion_probe_policy.py:450 identifies the captured-constructor
  regression boundary; it substitutes forwarding, not complete SDK initialization.
- scripts/research/companion_install_docker.py:236 source-only build provenance.
- preparation_actual_id_disposition.json:89 excludes independently reverified
  image-layer/per-file bytes from that prior review.

Historical SDK captures came from the original memory container. COPY-only
derivatives inherit parent dependencies, but original-container writable-layer
bytes are not automatically immutable-parent-image evidence. Do not copy that
one container's policy record onto all four derivative images. Bind applicable
files to each real image/subject before issuing installed-policy review records.

Parent independently rehashed23 saved sources and checked candidate witness
lineage, full-body hash and exact excerpt, exit0. Local archive55records/54verified;
no runtime acceptance or full-suite claim. Candidate SHA256:
56aee572ae72837a859c81f0c5fa70d35ab9ac5dd71128754d57c1df98762cd1.
No native calls, services, storage queries, credentials or tests run in this pass.
