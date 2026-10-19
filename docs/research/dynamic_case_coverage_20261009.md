# Dynamic rerun coverage decision

Read-only case map: `research/research_corrections_20261009/dynamic_case_coverage_20261009_v1.json`.
All96originalcasekeys mapped, three source artifact byte hashes recorded.

| Coverage | Cases |
|---|---:|
| Corrected ten-month strategy outage paths, primary/stress fees | 18 |
| Last60days strict on older runner | 24 |
| Last60days outage on older runner | 24 |
| Prior10months strict on older runner | 24 |
| Prior10months BTC/ETH outage controls on older runner | 6 |

All18corrected marked endpoints match corresponding older reported endpoints.
This does not prove all internal decisions/ledgers match or qualify78othercases.
Those artifacts remain preserved; no silent restamping or merged runner identity.

The merge fix requires artifact manifest verification rather than economic
reexecution. The buy guard changes exposure during unavailable held opening
prices. Hold controls buy once from flat, while strict paths stop on missing held
opens before decisions; these are plausible unaffected categories, not yet
independently proved historical equivalence. Last60day no-gap claims likewise
need exact input/decision evidence before exemption from corrected reruns.

Next: independent disposition of these78cases using narrow invariants/input
checks, then rerun only cases lacking sufficient unaffected-path proof. Do not
start a96case replay solely to raise the test count or describe mapping as full
corrected replay. Profit conclusions remain historical diagnostic evidence only.

Acceptance: READY_FOR_INDEPENDENT_REVIEW for coverage map/disposition.

Superseding independent disposition: ACCEPTED_WITH_RISK. All96keys, three source
artifact hashes,775input hashes and18corrected balances verified. The78remaining
cases are invariant-exempt for this specific delta, not corrected-runner reruns:
24prior10monthstrict stop before unavailable held-open buy decisions;
6prior10monthoutagecontrols buy once from flat with valid initial opens;
48last60dayrecordedheldpaths have no unknown valuations and valid observed opens.
The whole last60dayuniverse is not gap-free; exemption is held-path evidence only.
Zero further economic reruns required for this delta. Full ledger equivalence,
complete96casecorrectedreplay and economic promotion are not asserted.
