# Independent review of ENTR-CB-1 identity map v2

Reviewer: separate Claude subagent with no part in building the map, launched 2026-10-19 ~06:06Z, finished ~06:26Z.
Inputs reviewed (read-only, hashes in section 1 of the report): identity_map.json 8e714542..., identity_adjudications_v2.json dc90b01d..., build_coinbase_identity_map.py 27d68bd4..., PREREGISTRATION_DRAFT.md a7fb3662..., 01_products.json 00e556cc..., 01_currencies.json 8de25dcc....
The report below is the reviewer's final message, verbatim. Its working files are alongside.

---

**Verdict: REJECTED.** Map v2 recomputes exactly as the builder wrote it, but it gives one entrant (CMC 23254) the wrong status. The builder's code also has a gap that misses alternate tickers, the map maps one coin to the wrong asset, and it never compares contract addresses as prereg §3.1 requires. Nothing outside `/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/map_reviewer/` was changed.

## 1. Hash checks (start and end identical)
- **identity_map.json:** `8e714542…f616e74b`. Matches the expected 8e714542.
- **identity_adjudications_v2.json:** `dc90b01d…16f30d1b5fd`. No expected value was given; it matches the input hash recorded inside the map.
- **PREREGISTRATION_DRAFT.md:** `a7fb3662…` matches.
- **Other inputs:** the hashes for control_ids (e2ad776f), products (00e556cc) and currencies (8de25dcc) match the map's recorded inputs.

## 2. Recomputation
My own code (`recompute.py`) applied the operator rule to the inputs and found **0 differences** in all 383 records.
- **Counts:** 162 mapped, 216 never_listed, 5 unknown. Entrants: 50 mapped, 57 never_listed, 0 unknown.
- **Consistency:** review.csv matches the map exactly, and all product lists match.
- **Shared Coinbase asset:** KNC is the target of two CMC IDs (1982 and 9444).

So the code does what its rule says; the errors below come from the rule and the adjudications, not from how the code ran.

## 3. Adjudications (53)
| CMC id | Symbol | Builder | Verdict | Source |
|---|---|---|---|---|
| 1455 | GNT (E) | mapped | agree (SHOWN): contract 0xa744…; GNT migrated to GLM | coinbase.com/th/price/golem |
| 1637 | RLC (E) | mapped | agree (SHOWN): 0x607F… is iExec RLC | coinbase.com/en-au/price/rlc |
| 1659 | GNO (E) | mapped | agree (SHOWN): CMC contract equals Coinbase contract 0x6810… | coinmarketcap.com/assets/gnosis-gno/ |
| 2777 | IOTX (E) | mapped | agree, with risk: Coinbase trades the legacy ERC-20 IOTX, and IoTeX docs give no direct 1:1 conversion to native | docs.iotex.io/blockchain/learn-iotex/the-iotx-token/iotx-token-contracts ; iotex.io/blog/coinbase-lists-iotx-blockchain |
| 18679 | XCN (E) | mapped | agree (SHOWN): Chain renamed to Onyxcoin, ticker kept | kucoin.com/news/en-kucoin-supports-the-chain-xcn-rebranding-20230207 |
| 8425 | JASMY (E) | mapped | agree (SHOWN): CMC contract equals 0x7420… | coinmarketcap.com/el/currencies/jasmy/ |
| 22691 | STRK (E) | mapped | agree (SHOWN): 0xCa14… is the Starknet token | coinbase.com/en-ca/price/starknet-token |
| 2874 | AOA (E) | never_listed | agree (SHOWN): Coinbase AURORA is the NEAR token, launched 2021-11-18, after AOA's 2020 entry | coinbase.com/price/aurora-near |
| **29210** | **JUP** | mapped (JUP) | **disagree (SHOWN):** Coinbase JUP is the Jupiter Project ERC-20 0x4B1E…, suspended 2023-09-06. Solana Jupiter (mint JUPyiw…) trades as **JUPITER**-USD, listed 2025-12-09 | coinbase.com/en-gb/price/jupiter ; docs.jup.ag/user-docs/more/jup-token ; blockchain.news/news/coinbase-suspends-trading-for-multi-vgx-ooki-ddx-jup-bond ; es.beincrypto.com/coinbase-pluma-jupiter-dic-2025-listado/ |
| 7080 | GALA | mapped | agree (SHOWN): Coinbase traded only V1 and disabled it 2023-05-12 | decrypt.co/139053/… |
| 9444 | KNC | mapped | agree (SHOWN): Coinbase KNC contract is new KNC 0xdeFA… | docs.kyberswap.com/governance/knc-token/knc-contract-addresses |
| 39125 | LIT | unknown | different project agreed; **status disagree (SHOWN):** Lighter is on Coinbase as LIGHTER (0x232C…) | coinbase.com/price/lighter |
| 39720 | EDGE | unknown | different project agreed; **status disagree (SHOWN):** edgeX is on Coinbase as EDGEX (0xB007…) | coinbase.com/price/edgex |
| 213 / 2090 / 3829 | MONA / LA / NEX | unknown | agree that these are different projects (CLAIMED: contracts in 01_currencies vs reviewer knowledge) | local data |
| 5567 | CELO→CGLD | mapped | agree (SHOWN): contract 0x471E… | coinbase.com/price/celo |
| 14101 | RON→RONIN | mapped | agree (SHOWN) | blog.roninchain.com/p/breaking-ron-listed-on-coinbase |
| 27075 | MNT→MANTLE | mapped | agree (SHOWN): contract 0x3c3a… | coinbase.com/zh/price/mantle |
| 28324 / 11156 | dYdX chain / ethDYDX | mapped / never_listed | agree on both (SHOWN): Coinbase says ERC-20 DYDX is not tradable and points to COSMOSDYDX | coinbase.com/zh/price/dydx |
| 2239 | LEND | never_listed | agree: absent from products (SHOWN); 100:1 ratio CLAIMED | local data |
| 2603 | NPXS | never_listed | agree (SHOWN): 1000:1 swap | kucoin.com/announcement/en-kucoin-completes-the-token-reduction-swap-of-pundix-from-nxps-to-pundix |
| 3871 | AB | never_listed | agree (SHOWN): AB is BSC 0x9503…, Coinbase NEWT is 0xD0eC… | coinmarketcap.com/currencies/newton/ |
| 31 other control adjudications | ETC, OMG, BNB, MATIC, HBAR, SNX, STX, YFII, DOT, EGLD, IMX, APE, GMT, OP, INJ, BLUR, BEAM, FET, BONK, WLD, AKT, FLOKI, POPCAT, VIRTUAL, IP, WAL, WLFI, ETHFI, XPL (+ GALA, KNC above) | mapped | agree, CLAIMED: Coinbase contract or network in 01_currencies matches my knowledge; not checked on the web | local data |

## 4. New findings
| # | Finding | Label | Rating |
|---|---|---|---|
| F1 | **23254 CORE (entrant, entry 2025-04-27) is never_listed but is on Coinbase.** Coinbase has `CORECHAIN` "Core" (network coredao, CORECHAIN-USD). Coinbase's page confirms it is tradable; the listing was announced for 2024-06-21. The builder missed it because its suffix list has no `-dao`. A correct map likely makes this entrant selection eligible. | SHOWN (01_currencies, 01_products; coinbase.com/en-ca/price/coredao-network; coincarp.com/nl/events/core-dao-new-listing-on-coinbase-pro/) | **BLOCKER** |
| F2 | **Systematic code gap:** script line 57 skips the alternate-ticker search whenever the CMC symbol matches a *different* Coinbase asset. This caused 29210 (wrong mapping), 39125 and 39720 (unknown instead of mapped). All three are control IDs. | SHOWN (code plus recomputation) | **BLOCKER** (systematic) |
| F3 | **Prereg §3.1 requires a contract-address check "where one exists"; the builder never compares contract addresses.** That check would have caught 29210. My reviewer-side comparison of all 162 mapped records found no other mismatch: 9 confirmed on the web (incl. KITE: CMC 38828 contract equals Coinbase 0x118B…), the rest CLAIMED from my knowledge. | SHOWN (gap) / CLAIMED (others) | **BLOCKER** (rule deviation) |
| F4 | **5690 RNDR is mapped only to RNDR products.** Coinbase suspended RNDR on 2025-06-26, but the same CMC asset (1:1 upgrade) trades as `RENDER`-USD. 5690 has 45 control selections up to 2026-08-16. The map will create a false unresolved exit (zero-recovery) and false exclusions after June 2025, which biases the control arm and so decision condition (3). The rule cannot express a Coinbase ticker change for the same asset. | SHOWN (crypto.news/render-price-drops-8-on-coinbase-delisting-fud/; 01_currencies) | **BLOCKER** (affects control arm) |
| F5 | 4172 LUNA (entrant) is never_listed while Coinbase traded WLUNA, the 1:1 ERC-20 bridge, until 2022-05-27. This is inconsistent with accepting the IOTX ERC-20. No outcome change: trading stopped before the 2022-09-18 entry. | SHOWN (theinformerpost…wluna-trading-suspensions) | NON-BLOCKING |
| F6 | 1982 and 9444 both map to KNC. Coinbase now holds the v2 contract. 1982's last selection (2021-02-07) is probably before Coinbase migrated; the migration date is UNVERIFIED. | SHOWN / UNVERIFIED | NON-BLOCKING |
| F7 | 1455 is mapped only to GNT-USDC, although Coinbase GLM-USD is its continuation after Nov 2020. This only matters if GNT-USDC stopped trading before the exit (Step B will show). | SHOWN / UNTESTED | NON-BLOCKING |
| F8 | Different-project ticker collisions get unknown (213, 2090, 3829), while different projects whose ticker is absent get never_listed (2874, 3871). This follows the literal rule; all five are control IDs. | SHOWN | NON-BLOCKING |
| F9 | Whether /products includes every delisted product is UNVERIFIED. Spot checks of UST, WLUNA, MIR, NU, KEEP, TRIBE, RGT, GALA, JUP, RNDR, VGX, DNT and CVC all found them. FTM is absent, which fits Coinbase saying Fantom is not tradable (it only had perpetual futures). Fuzzy name search of the other entrant never_listed IDs found no further hits. | partly SHOWN | NON-BLOCKING |

Three pages were blocked, so I continued without them: coinmarketcap.com/currencies/jupiter-ag/, coinmarketcap.com/currencies/core-dao/ and coinbase.com/price/core-dao (the permission request was not answered).

## 5. Why REJECTED, and corrections by CMC ID
- **23254:** never_listed → mapped, coinbase_base `CORECHAIN` (CORECHAIN-USD). This is an entrant.
- **29210:** mapped to JUP → mapped to `JUPITER` (JUPITER-USD). Drop JUP-USD, which is a different asset.
- **39125:** unknown → mapped to `LIGHTER` (LIGHTER-USD).
- **39720:** unknown → mapped to `EDGEX` (EDGEX-USD).
- **5690:** needs your decision. Either allow RENDER-USD as RNDR's continuation, or record that its post-2025-06-26 exits are knowingly treated as artefacts. Leaving it as is creates a false zero-recovery exit in the control arm.
- **Code (v3):**
  - Run the alternate-ticker search even when the CMC symbol collides with another Coinbase asset.
  - Show fuzzy name candidates for adjudication instead of relying on a fixed suffix list.
  - Add the contract-address comparison required by prereg §3.1.
- **Optional:** set a WLUNA versus IOTX ERC-20 policy (4172); this changes no outcome.

Freeze a corrected v3 and re-review it before Step B; v2 should not be used as is.

My files are in `/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/map_reviewer/`:
- recompute.py
- fuzzy.py
- alt_all.py
- mine.json
- mapped_contracts.txt

Sources:
- [Coinbase: Core (CORECHAIN)](https://www.coinbase.com/en-ca/price/coredao-network)
- [CoinCarp: Core DAO Coinbase listing](https://www.coincarp.com/nl/events/core-dao-new-listing-on-coinbase-pro/)
- [Coinbase: Jupiter (JUP)](https://www.coinbase.com/en-gb/price/jupiter)
- [Jupiter docs: JUP mint](https://docs.jup.ag/user-docs/more/jup-token)
- [BeInCrypto: Coinbase lists Jupiter](https://es.beincrypto.com/coinbase-pluma-jupiter-dic-2025-listado/)
- [Blockchain.news: Coinbase suspends JUP](https://blockchain.news/news/coinbase-suspends-trading-for-multi-vgx-ooki-ddx-jup-bond)
- [Coinbase: Lighter](https://www.coinbase.com/price/lighter)
- [Coinbase: edgeX](https://www.coinbase.com/price/edgex)
- [crypto.news: Coinbase suspends RNDR](https://crypto.news/render-price-drops-8-on-coinbase-delisting-fud/)
- [Decrypt: Coinbase and GALA V1](https://decrypt.co/139053/coinbase-wont-support-gala-games-v2-token-airdrop-why-not)
- [The Informer Post: Coinbase suspends WLUNA](https://theinformerpost.beehiiv.com/p/crypto-exchange-coinbase-announces-terrausd-ust-and-wrapped-terra-wluna-trading-suspensions-after-lu)
- [IoTeX token contracts](https://docs.iotex.io/blockchain/learn-iotex/the-iotx-token/iotx-token-contracts)
- [IoTeX: Coinbase listing](https://iotex.io/blog/coinbase-lists-iotx-blockchain)
- [KuCoin: XCN rebrand](https://kucoin.com/news/en-kucoin-supports-the-chain-xcn-rebranding-20230207)
- [CMC: JasmyCoin](https://coinmarketcap.com/el/currencies/jasmy/)
- [CMC: Gnosis](https://coinmarketcap.com/assets/gnosis-gno/)
- [CMC: Kite](https://coinmarketcap.com/ja/currencies/kite)
- [CMC: AB (Newton)](https://coinmarketcap.com/currencies/newton/)
- [Coinbase: Kite AI](https://www.coinbase.com/price/kite-ai)
- [Coinbase: iExec RLC](https://www.coinbase.com/en-au/price/rlc)
- [Coinbase: Golem](https://www.coinbase.com/th/price/golem)
- [Coinbase: Starknet](https://www.coinbase.com/en-ca/price/starknet-token)
- [Coinbase: Celo](https://www.coinbase.com/price/celo)
- [Ronin: RON listed on Coinbase](https://blog.roninchain.com/p/breaking-ron-listed-on-coinbase)
- [Coinbase: Mantle](https://www.coinbase.com/zh/price/mantle)
- [Coinbase: dYdX ERC-20](https://www.coinbase.com/zh/price/dydx)
- [Coinbase: Aurora](https://www.Coinbase.com/price/aurora-near)
- [KuCoin: NPXS to PUNDIX swap](https://kucoin.com/announcement/en-kucoin-completes-the-token-reduction-swap-of-pundix-from-nxps-to-pundix)
- [KyberSwap: KNC contracts](https://docs.kyberswap.com/governance/knc-token/knc-contract-addresses)
- [Coinbase: Fantom](https://www.coinbase.com/zh-sg/price/fantom)
- [TradingView: FTM-PERP suspension](https://in.tradingview.com/chart/FTMUSDT/Kae3hSy6-Breaking-Fantom-FTM-Faces-Turbulence-Amid-Coinbase-Delisting)
