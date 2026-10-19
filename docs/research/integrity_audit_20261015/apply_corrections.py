# Applies approved corrections C1-C6 (2026-10-15). Each old string must occur exactly once; originals preserved in originals/.
import json, hashlib, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[1]
def edit(path, pairs):
    p = R / path; t = p.read_text()
    for old, new in pairs:
        n = t.count(old)
        if n != 1: sys.exit(f"ABORT {path}: expected 1 occurrence, found {n}: {old[:60]!r}")
        t = t.replace(old, new)
    return p, t
edits = {}
edits["MULTI_SYMBOL_MANDATE.md"] = [(
 "- Checked on 2026-10-15: all 25 trade as Coinbase USD products. MATIC is delisted (successor POL), and XRP has a 904-day trading suspension gap.",
 "- Checked on 2026-10-15: 24 of the 25 trade as Coinbase USD products. MATIC-USD is delisted (last daily candle 2025-10-14) and POL-USD is its successor; XRP has a 904-day trading suspension gap. (C1 correction 2026-10-15; original wording in integrity_audit_20261015/originals/.)")]
edits["xs_momentum_20261012/README.md"] = [(
 "467 were used after excluding stablecoins and products with less than 90 days of history.",
 "467 were used after excluding stablecoins and products with less than 90 days of history.\n- **Data location (C6 note, 2026-10-15):** the raw candles are NOT in the repo. They live outside it on the laptop VM at `$HOME/xsdata/candles` (492 product files + `_products.json`); per-file SHA-256 prefixes are stored in `xs_momentum_result.json` (`candle_file_sha256_16`). If that folder is lost, E6 cannot be rerun from the repo alone.\n- **Status reminder:** the stored result still contains the known stale-price defect described above. It remains labelled DEFECTIVE until a corrected simulation is run.")]
S = [
 ("it should be read as corroboration of a modest, risk-shaped edge, not as evidence of hidden alpha",
  "it is consistent with these studies; it is not evidence of an edge, and the project's own DSR found no return edge over BTC"),
 ("Simpler models consistently beat complex ones out-of-sample in BTC",
  "One survey reports naive models beating more complex ones in some walk-forward tests, but it describes the evidence as mixed and the BTC-specific result as an unreplicated preprint"),
 ("but it trades about three round trips a week with costs unmodeled",
  "but it holds BTC on up to three conditional overnight sessions a week, with costs unmodeled"),
 ("At this account's fees that is on the order of 75–150% a year in drag.",
  "Its fee drag at this account's rates depends on how often the condition fires and was not computed."),
 ("Most academic rule studies assume 0.10–0.25% one-way",
  "Zarattini et al. test costs of 0.10%, 0.25% and 0.50%"),
 ("crypto momentum flips to reversal at roughly 4–6 weeks, especially in small coins",
  "crypto momentum flips to reversal from roughly 4–6 weeks"),
 ("The MVRV-style \"value\" factor of Cong et al.",
  "The \"value\" factor of Cong et al. (active addresses relative to market cap)"),
 ("The Fear & Greed Index is itself built from price momentum and volatility",
  "The Fear & Greed Index is built partly from price momentum and volatility, alongside social-media activity and market dominance"),
 ("and returns and volatility drive attention at least as much as the reverse",
  "and volatility and volume drive next-day attention"),
 ("Their typical value has been smaller drawdowns, such as −46% against about −72% for BTC in 2018",
  "Their typical value has been smaller losses, such as a −46% median fund return against about −72% for BTC in calendar 2018"),
 ("survivorship bias of tens of percent a year described above (",
  "survivorship bias of tens of percent a year reported by Ammann et al. above; the following guide describes building a dataset that includes defunct coins ("),
]
edits["crypto_trading_edges_survey_20261013.md"] = S
cites = json.load(open(R / "integrity_audit_20261015/cloud/citation_audit_combined.json"))
nv = [c for c in cites if c["verdict"] == "NOT_VERIFIABLE"]
ns = [c for c in cites if c["verdict"] in ("NOT_SUPPORTED",)]
note = ["", "## Audit note (2026-10-15; corrections C2–C5)", "",
 "Wording in eleven places above was narrowed to what the cited source states. The original text is preserved verbatim in `integrity_audit_20261015/originals/crypto_trading_edges_survey_20261013.md.orig`; per-citation results are in `integrity_audit_20261015/cloud/citation_audit_combined.json`.", "",
 f"- **Checked and supported:** {sum(c['verdict']=='SUPPORTED' for c in cites)} of {len(cites)} citations. **Checked and partly supported:** {sum(c['verdict']=='PARTLY_SUPPORTED' for c in cites)}. **Checked and contradicted by the source:** {sum(c['verdict']=='CONTRADICTED' for c in cites)} (the \"simpler models\" sentence, now corrected). **Checked and found unsupported:** {len(ns)}.",
 f"- **Not re-verified because the source was inaccessible from the audit sandbox ({len(nv)}).** These were NOT found unsupported; they simply could not be opened or located on 2026-10-15. Treat the attributed figures as unverified:"]
for c in nv: note.append(f"  - {c['label']} — {c['url']}")
note.append("- Checking was done by audit subagents (WebFetch/WebSearch), not line by line by a human.")
S.append(("\n__END__", ""))  # placeholder, not used
S.pop()
dry = "--apply" not in sys.argv
out = {}
for path, pairs in edits.items():
    p, t = edit(path, pairs)
    if path.startswith("crypto_trading"): t = t.rstrip("\n") + "\n" + "\n".join(note) + "\n"
    out[p] = t
for p, t in out.items():
    before = hashlib.sha256(p.read_bytes()).hexdigest()
    after = hashlib.sha256(t.encode()).hexdigest()
    print(("DRY " if dry else "APPLY ") + str(p.relative_to(R)), before, "->", after)
    if not dry: p.write_text(t)
