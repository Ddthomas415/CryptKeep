# Remaining batch C: items 60-69

Role: AUDITOR. Full-content source review; no supplied scripts or tests executed. INCOMPLETE for runtime acceptance. Items refer to the frozen 89-item inventory before this pass.

| SHA-256 | Item | Disposition |
| --- | --- | --- |
| `c470527027f33cce3b78442c08e044f7063d4e4719b13e16041f4aabed6cf41b` | 60: 0035 full patch | Full patch, work-log claims and six test bodies read. Missing qualified orders suppress positive expectancy; split lots cap round-trip count. |
| `952e800572255fdcf861ddb2ec38781ff8bd3c934bb592f509136be8039b0b6e` | 61: 0036 full patch | Shared mismatch helper and three retirement tests read; report-only change, not automatic retirement on unknown evidence. |
| `59937cda49c4520c0b04a0f16b40a88fb843fc370c6b558b2602388dd501fbae` | 62: 0036 production diff | Full diff read; older qualification lacking counts still yields no mismatch, not independently established completeness. |
| `d8ee3b4b6ed5240ef3695c1c93d4990818605d5d982aa2d23b84c1fb4ecd7714` | 63: paper engine probe | Full script read; prints outcomes rather than asserts. CBP_STATE_DIR alone does not neutralize inherited database overrides. Not run. |
| `6db152705f92da090505719d20451ffcaf618026ec41d5133f4aaad087b9513b` | 64: 0037 production diff | Both consumers refuse missing finite positive reference instead of claiming zero. Limit references can remain below execution price. |
| `9ce8dd80216832ada2c151704725fa5cbf4c90952765b8d0c01da61eee0dc360` | 65: 0037 full patch | Full patch and parametrized test bodies read; helper/claim tests mock risk config and queue, not exchange integration. |
| `b15bf120725b1bc354516e3dfa1cdad98fdb16561b00bb3ddd26d4b1a9bce0e3` | 66: 0038 full patch | Full patch and seven test cases read; market safety reference ignores carried limit price, limit behavior preserved. |
| `70e5a6be827f72fffb80ea1b49e17a749bc6759a57727824d6fb101f86d3a9f9` | 67: 0038 production diff | Full diff read; reference selection only, not proof of later fill quote freshness. |
| `1e93cf8d419fbbd4a6d82be9951c0982bc60180c8f35406a88f7e484b6555f9f` | 68: 0039 full patch | Full patch, eight tests and changed fixtures read; TTL precedes fresh submit, remote-id evidence bypasses cancellation for recovery. |
| `9d5b45d332dd9afc5f44092163f07795073ea35c177d8964af761e429564d17a` | 69: 0039 production diff | Full diff read; no side distinction in TTL cancellation. Re-upsert resets timestamp, as disclosed in patch log. |

## Findings and evidence limits

- SHOWN: 0039 explicitly corrects the earlier 0037 severity claim: the legacy direct-submit consumer has no runnable entry point. Do not repeat it as a currently active canonical live bypass without new routing evidence.
- SHOWN: 0035/0036 compare counts and missing order identifiers, not every price, quantity, fee, currency and timestamp value. Their tests establish intended count/missing-row contracts, not full economic equivalence of evidence and journal.
- SHOWN: retirement mismatch is report-only and existing negative triggers remain active. A positive incomplete journal cannot establish positive expectancy for paper promotion under the added comparison. Other kernel retirement paths were explicitly outside these patches.
- SHOWN: 0039 tests use real temporary execution storage with fake client and mocked risk/freshness gates; they are not evidence that real order routing, risk gates or protected-exit behavior was exercised. The provided aged-intent tests are buys; existing sell fixture receives a fresh timestamp. Cancellation applies to both sides in the diff. Any safety disposition of aged protective exits requires dedicated integration evidence, not inference from these tests.
- SHOWN: reference-price and TTL float conversions catch TypeError/ValueError but not OverflowError. This is a source limitation, not an independently reproduced new operational incident here.
- UNVERIFIED: current deployment, real-exchange results, configuration and profitability. Supplied test totals remain CLAIMED; no tests rerun for this batch.
