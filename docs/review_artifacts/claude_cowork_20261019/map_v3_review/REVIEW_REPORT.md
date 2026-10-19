# Independent re-review of ENTR-CB-1 identity map v3

Reviewer: separate Claude subagent with no part in building the map, ran 2026-10-19 06:53:53Z-07:04:22Z (first and last transcript timestamps).
Inputs reviewed read-only (hashes in section 1 of the report): identity_map.json 06402231..., review.csv 6dd106c1..., build_coinbase_identity_map.py 8a9cfd72..., identity_adjudications_v3.json f8ef0a7b..., cmc_contracts.json 7f59f692... with its 190 raw bodies, PREREGISTRATION_DRAFT.md a7fb3662..., 01_products.json 00e556cc..., 01_currencies.json 8de25dcc....
The report below is the reviewer's final message, verbatim. Its working files are alongside (pytest temp dir omitted).

---

**Verdict: ACCEPTED_WITH_RISK.** I found no blockers. The v3 map recomputes exactly from its inputs, all four v2 blockers are fixed, and both operator rules were applied as stated. The risks below are known consequences of the operator's continuation rule, plus a few gaps in the code that change no outcome. No input file was modified (SHOWN: hashes were the same at start and end). All my work is in `/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/map_v3_reviewer/`.

## 1. Hash checks (all SHOWN)
- **Map and builder:** identity_map.json `0640223172fc…`, review.csv `6dd106c1…`, the builder `8a9cfd72…` (the copy in `entr/scripts/research/` has the same hash), adjudications `f8ef0a7b…`, cmc_contracts.json `7f59f692…` and the prereg `a7fb3662…` all match what you gave me.
- **Recorded inputs:** the five hashes in the map's `inputs` field match these files.
- **Raw CMC data:** all 190 raw bodies match SHA256SUMS and requests.jsonl (hash and byte count). Log entries run 1–190 with no gaps, all HTTP 200, one per ID, matching the 190 IDs in cmc_contract_ids.csv (165 mapped, 22 adjudicated never_listed, 3 adjudicated unknown).

## 2. Recomputation (SHOWN)
- **My own code** (`recompute.py`, does not import the builder): **0 differences** across 383 records. I compared status, bases, products with their status, alternate candidates and the contract check.
- **review.csv:** all 383 rows agree with the map.
- **Builder tests:** 18 passed.
- **Raw CMC parse** (`parse_cmc.py`): 0 differences from cmc_contracts.json. As a cross-check, CMC's second contract list (`supplyDetails.contracts`) adds no address beyond `platforms`.

**Counts** (from `recompute.py` on control_ids_v2.csv and entrant_ids_v2.csv):

| | mapped | never_listed | unknown |
|---|---|---|---|
| All 383 IDs | 165 | 215 (193 absent from products, 22 adjudicated) | 3 (213, 2090, 3829) |
| 107 entrant IDs | 51 | 56 | 0 |
| 133 entrant selections | 62 | 71 | 0 |

- **Contract checks on the 165 mapped records:** 114 match, 48 not_comparable, 3 mismatch. All 3 mismatches carry an override.
- **Never_listed check:** for all 215, the CMC ticker is absent from every Coinbase product (SHOWN).

## 3. v2 blockers
| | Status | Evidence |
|---|---|---|
| F1 | Resolved | 23254 is now mapped to CORECHAIN (CORECHAIN-USD online). The contract check is not_comparable because Coinbase lists it on its own coredao network and CMC lists only the 0xeeee placeholder. SHOWN. |
| F2 | Resolved | The code now runs the alternate search for every record that is not an exact match. 29210→JUPITER, 39125→LIGHTER and 39720→EDGEX each have a contract match. SHOWN. |
| F3 | Resolved | `apply_contracts_and_continuations` is implemented, and no mapped ID lacks CMC data. SHOWN. |
| F4 | Resolved | 5690 maps to both RNDR and RENDER. Both contract checks match (0x6de037ef… and rndrizKT3M…). SHOWN. |

## 4. Overrides and the continuation
- **1455 GNT: justified.**
  - Coinbase's GNT record is 0xa7447644…. CMC 1455 now lists 0x7DD9c5… (SHOWN), which is Coinbase's GLM contract (SHOWN in my contract cross-index).
  - The selection list still calls it GNT with slug golem-network-tokens, so CMC 1455 is Golem across both tokens.
  - 9 selections, 2019-04-07 to 2020-11-15 (SHOWN).
- **7080 GALA V1: justified.** Coinbase's record is named "Gala V1" with contract 0x15D4c048… (SHOWN). CMC 7080 lists 0xd1d2Eb1B…, which I believe is the V2 contract (CLAIMED).
- **1982 legacy KNC: justified.**
  - CMC 1982 is now "KNCL" with contract 0xdd974d5c… (SHOWN).
  - Its last selection was 2021-02-07, so its last exit was 2021-03-07 (SHOWN).
  - Exchanges migrated KNC on 2021-06-21 (Kraken, SHOWN). Coinbase's own migration date is UNVERIFIED.
- **5690: meets operator rule 2 exactly.** CMC 5690 lists both Coinbase tickers' contracts (SHOWN).
- **No missed rule-2 case.** My cross-index matched every CMC contract against all 511 Coinbase currencies. It found only three CMC IDs whose contracts match a Coinbase asset other than the mapped one: 1455→GLM (CMC lists no GNT contract), 17799→WAXL (the native AXL side has no contract) and 28321→MATIC. The 28321 match is only through 0x…1010, Polygon's native system address, not MATIC's token contract.
- **Rule correctly not applied:** 3890 MATIC→POL, where CMC 3890 lists only MATIC contracts (SHOWN).

## 5. Findings
| # | Finding | Label | Rating |
|---|---|---|---|
| N1 | **35626 IP:** CMC 35626 is now "Data Network (DATA)". Coinbase's IP is delisted and DATA-USD is online on the same "story" network. The rename was 1:1 on 2026-06-25, and Coinbase paused IP around 2026-07-06. Rule 2 cannot apply because neither side has a contract. **No effect:** the last selection exit was 2026-03-29. | SHOWN (raw body; 01_currencies; KuCoin; Crypto Briefing) | NON-BLOCKING |
| N2 | **14101 RON:** Coinbase listed WRON (1:1 wrapper) on 2026-04-30 and retired RONIN around 2026-05-12. The last RON exit was 2025-03-30, so there is no effect. | SHOWN (Ronin blog) | NON-BLOCKING |
| N3 | **17799 AXL:** the candidate search still skips exact matches. Running it on all records found one second Coinbase asset for the same coin: WAXL, whose contract CMC lists under 17799. **No effect:** native AXL was added on Coinbase on 2023-02-07, before the entrant's 2024-01-07 entry. Disclose it. | SHOWN (TechFlow; Axelar blog) | NON-BLOCKING |
| N4 | **28321 POL (entrant, entry 2024-09-15)** maps to POL only. If POL-USD's first daily candle is after 2024-09-14, Step B will exclude this selection. The POL listing date is UNVERIFIED. This is operator rule 2 working as written. | SHOWN / UNVERIFIED | NON-BLOCKING: check in Step B |
| N5 | **No continuation by rule:** 3890 MATIC (last selection 2024-12-08), 1455 GNT and 7080 GALA. Exits after their last candle will count as zero-recovery. This follows the operator's decision; it needs acknowledgement. | SHOWN | NON-BLOCKING |
| N6 | **Placeholder list misses native stand-ins:** 0x…1010, "0" (ALGO and TAO), `0x1::aptos_coin::aptoscoin` (APT and MOVE), TON's EQAAAA…M9c, and Mantle's 0xdeaddead…0000. None changed a status; the only cross-asset match they create is 28321↔MATIC. | SHOWN | NON-BLOCKING |
| N7 | **4172:** entrant_ids_v2.csv calls it LUNC while control_ids_v2.csv says LUNA. It is never_listed either way. Treating WLUNA as a different asset agrees with the contract evidence: CMC 4172 does not list WLUNA's 0xd2877702…, while CMC 2777 does list Coinbase's IOTX ERC-20. This settles v2's F5 inconsistency. | SHOWN | NON-BLOCKING |
| N8 | **The 48 not_comparable records are acceptable:** 32 are on Coinbase's own network only, 12 have no contract on either side, 3 have a Coinbase own-network entry plus extra Base-network contracts (ZEC, SOL, HYPE), and 1 has a contract on Coinbase but none at CMC (ENJ). All names agree. 11419 is "Gram (prev. Toncoin)" (ton.org) and 35626 is Story renamed, both SHOWN. 5805 AVAX matches only after stripping a leading 0x, and that match is correct. I found no wrong mapping among the 165. | SHOWN | — |
| N9 | **The 18 new adjudications** (17 never_listed plus 23254): I agree with all of them. Coinbase names show the projects are clearly different (SHOWN); judgments like "BSV is not BTC" are CLAIMED. | SHOWN / CLAIMED | — |
| N10 | **Missed-listing hunt on the 56 never_listed entrants:** the widened candidate search and a looser fuzzy name match against all 511 Coinbase currencies found nothing new. Web checks: SSV, RUNE and FXS (Frax) are not tradable on Coinbase's exchange (SHOWN); GMX's page could not confirm (UNVERIFIED). Every USD-quoted Coinbase product has a currency record, so the name matching has no blind spot (SHOWN). | SHOWN / UNVERIFIED | — |

## Corrections by CMC ID
None are required. Optional before or during Step B:
- Add the N6 native stand-ins to the placeholder list.
- Disclose 17799 (AXL and WAXL) and 35626 (IP renamed to DATA).
- Check POL-USD's first candle against 2024-09-14 for 28321.
- Acknowledge N5.

Sources:
- [KuCoin: Story (IP) renamed to Data Network (DATA)](https://www.kucoin.com/announcement/ph-kucoin-will-support-the-rename-of-story-ip-to-data-network-data-300626)
- [Crypto Briefing: Coinbase suspends IP-PERP during the Data Network rebrand](https://cryptobriefing.com/coinbase-suspends-ip-perp-futures-data-network-rebrand/)
- [Ronin blog: Coinbase is listing wrapped RON](https://blog.roninchain.com/p/coinbase-is-listing-wrapped-ron)
- [Kraken: Kyber KNC token migration](https://support.kraken.com/articles/4401758213268-kyber-knc-token-migration)
- [TechFlow: Coinbase adds AXL on the Axelar network](https://www.techflowpost.com/en-US/newsletter/24948)
- [Axelar: What is wAXL](https://axelar.network/blog/what-is-waxl-identifying-the-wrapped-erc-20-axl-token-by-ticker)
- [The Informer Post: Coinbase adds WAXL](https://theinformerpost.beehiiv.com/p/coinbase-adds-support-for-little-known-altcoin-project-and-delists-four-crypto-assets)
- [Coinbase: ssv.network not tradable](https://www.coinbase.com/zh-sg/price/ssv-network)
- [Coinbase: THORChain not tradable](https://www.coinbase.com/en-ca/price/thorchain)
- [Coinbase: Frax (prev. FXS)](https://www.coinbase.com/how-to-buy/frax-share)
- [Coinbase: GMX](https://www.coinbase.com/price/gmx)
- [The Informer Post: Coinbase adds POL to its listing roadmap](https://theinformerpost.beehiiv.com/p/coinbase-adds-upcoming-polygon-native-token-pol-to-listing-roadmap-ahead-of-septembers-matic-rebrand)
