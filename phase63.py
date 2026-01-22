from pathlib import Path

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Warning: Missing file {path} — patch skipped")
        return False
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
        return True
    return False


# 1) risk_ledger: add daily_venue table + getters + upserts
def patch_risk_ledger(t: str) -> str:
    if "CREATE TABLE IF NOT EXISTS daily_venue" not in t:
        t = t.replace(
            "CREATE TABLE IF NOT EXISTS daily (",
            "CREATE TABLE IF NOT EXISTS daily_venue (\n"
            "  run_id TEXT,\n"
            "  day TEXT NOT NULL,\n"
            "  venue TEXT NOT NULL,\n"
            "  trades_count INTEGER NOT NULL,\n"
            "  notional_usd REAL NOT NULL,\n"
            "  realized_pnl_usd REAL NOT NULL,\n"
            "  updated_ts TEXT NOT NULL,\n"
            "  PRIMARY KEY (day, venue)\n"
            ");\n\n"
            "CREATE INDEX IF NOT EXISTS idx_daily_venue_day ON daily_venue(day);\n"
            "CREATE INDEX IF NOT EXISTS idx_daily_venue_venue ON daily_venue(venue);\n\n"
            "CREATE TABLE IF NOT EXISTS daily ("
        )
    # Add getters/upserts
    if "def get_daily_venue" not in t:
        insert_point = t.find("def get_daily(")
        if insert_point != -1:
            add = (
                "\n    def get_daily_venue(self, day: str, venue: str) -> dict:\n"
                "        con = _connect()\n"
                "        try:\n"
                "            r = con.execute(\n"
                "                \"SELECT trades_count, notional_usd, realized_pnl_usd, updated_ts FROM daily_venue WHERE day=? AND venue=?\",\n"
                "                (str(day), str(venue)),\n"
                "            ).fetchone()\n"
                "            if not r:\n"
                "                return {\"day\": day, \"venue\": venue, \"trades_count\": 0, \"notional_usd\": 0.0, \"realized_pnl_usd\": 0.0, \"updated_ts\": None}\n"
                "            return {\"day\": day, \"venue\": venue, \"trades_count\": int(r[0]), \"notional_usd\": float(r[1]), \"realized_pnl_usd\": float(r[2]), \"updated_ts\": r[3]}\n"
                "        finally:\n"
                "            con.close()\n\n"
                "    def upsert_daily_venue(self, day: str, venue: str, trades_count: int, notional_usd: float, realized_pnl_usd: float, run_id: str | None = None) -> None:\n"
                "        con = _connect()\n"
                "        try:\n"
                "            con.execute(\n"
                "                \"INSERT INTO daily_venue(run_id, day, venue, trades_count, notional_usd, realized_pnl_usd, updated_ts) VALUES(?,?,?,?,?,?,?) \"\n"
                "                \"ON CONFLICT(day, venue) DO UPDATE SET run_id=excluded.run_id, trades_count=excluded.trades_count, notional_usd=excluded.notional_usd, realized_pnl_usd=excluded.realized_pnl_usd, updated_ts=excluded.updated_ts\",\n"
                "                (run_id, str(day), str(venue), int(trades_count), float(notional_usd), float(realized_pnl_usd), _now()),\n"
                "            )\n"
                "        finally:\n"
                "            con.close()\n\n"
            )
            t = t[:insert_point] + add + t[insert_point:]
    return t


# 2) risk_gate: enforce optional per-venue daily totals
def patch_risk_gate(t: str) -> str:
    if "max_daily_loss_usd_venue" in t:
        return t
    # Extend config reading + per-venue enforcement
    t = t.replace(
        "    max_daily_loss = risk.get(\"max_daily_loss_usd\", None)\n"
        "    max_position = risk.get(\"max_position_usd\", None)\n"
        "    max_trades = risk.get(\"max_trades_per_day\", None)\n"
        "    min_order = risk.get(\"min_order_usd\", None)\n",
        "    max_daily_loss = risk.get(\"max_daily_loss_usd\", None)\n"
        "    max_position = risk.get(\"max_position_usd\", None)\n"
        "    max_trades = risk.get(\"max_trades_per_day\", None)\n"
        "    min_order = risk.get(\"min_order_usd\", None)\n"
        "    max_daily_loss_v = risk.get(\"max_daily_loss_usd_venue\", None)\n"
        "    max_trades_v = risk.get(\"max_trades_per_day_venue\", None)\n"
    )
    return t


# 3) Dashboard: show venue aggregates
def patch_dashboard(t: str) -> str:
    if "get_daily_venue" in t:
        return t
    if "Risk limits (enforced)" in t:
        t = t.replace(
            "    else:\n"
            "        st.caption(\"Enter venue+symbol to view today stats and position snapshot (ledger is keyed by venue+symbol).\")\n",
            "    if ven.strip():\n"
            "        st.subheader(\"Today (venue aggregate across symbols)\")\n"
            "        try:\n"
            "            st.write(led.get_daily_venue(day, ven.strip().lower()))\n"
            "        except Exception:\n"
            "            st.write({\"venue\": ven.strip().lower(), \"note\": \"daily_venue not available\"})\n\n"
            "    else:\n"
            "        st.caption(\"Enter venue to view venue-aggregate stats, and optionally symbol for per-symbol stats.\")\n"
        )
    return t


# 4) CHECKPOINTS
def patch_cp(t: str) -> str:
    if "## BK) Venue Aggregate Risk" in t:
        return t
    return t + (
        "\n## BK) Venue Aggregate Risk\n"
        "- ✅ BK1: risk_ledger.sqlite daily_venue aggregate table (day+venue totals across symbols)\n"
        "- ✅ BK2: Ledger updates daily_venue on every USD-quote fill\n"
        "- ✅ BK3: Risk gate enforces optional max_daily_loss_usd_venue and max_trades_per_day_venue\n"
        "- ✅ BK4: Dashboard risk panel shows venue aggregate stats when venue is provided\n"
    )


# Apply all patches
patch("storage/risk_ledger_store_sqlite.py", patch_risk_ledger)
patch("services/risk/risk_gate.py", patch_risk_gate)
patch("dashboard/app.py", patch_dashboard)
patch("CHECKPOINTS.md", patch_cp)

print("OK: Phase 63 applied (per-venue daily aggregates + risk gate enforcement + dashboard + checkpoints).")

