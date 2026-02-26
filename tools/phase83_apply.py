from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path
import datetime
import re
import shutil

from _bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)
ATTIC = ROOT / "attic" / ("phase83_apply_" + datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
ATTIC.mkdir(parents=True, exist_ok=True)

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def backup(rel: str):
    p = ROOT / rel
    if p.exists():
        dst = ATTIC / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)

def write(rel: str, content: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")

def patch_scripts_bootstrap():
    scripts = ROOT / "scripts"
    if not scripts.exists():
        return
    for p in scripts.glob("*.py"):
        t = read(p)
        if "from services." not in t and "import services" not in t:
            continue
        if "CBP_BOOTSTRAP" in t:
            continue
        lines = t.splitlines()
        i = 0
        if lines and lines[0].startswith("#!"):
            i = 1
        while i < len(lines) and lines[i].startswith("from __future__ import"):
            i += 1
        block = [
            "",
            "# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly",
            "from pathlib import Path",
            "import sys",
            "ROOT = Path(__file__).resolve().parents[1]",
            "if str(ROOT) not in sys.path:",
            "    sys.path.insert(0, str(ROOT))",
            "",
        ]
        backup(str(p.relative_to(ROOT)))
        p.write_text("\n".join(lines[:i] + block + lines[i:]) + "\n", encoding="utf-8")
        print(f"[ok] bootstrapped: {p.relative_to(ROOT)}")

def patch_refresh_market_rules_args():
    p = ROOT / "scripts" / "refresh_market_rules.py"
    if not p.exists():
        return
    t = read(p)
    if "ap.add_argument(\"--exchange\"" in t:
        return  # already patched
    backup("scripts/refresh_market_rules.py")
    # add aliases for your muscle-memory flags
    t = t.replace(
        'ap.add_argument("--venue", required=True, help="binance|gate|coinbase")',
        'ap.add_argument("--venue", default="", help="binance|gate|coinbase")\n'
        '    ap.add_argument("--exchange", default="", help="alias for --venue")'
    )
    t = t.replace(
        'ap.add_argument("--symbols", default="", help="comma-separated canonical symbols")',
        'ap.add_argument("--symbols", default="", help="comma-separated canonical symbols")\n'
        '    ap.add_argument("--symbol", default="", help="alias: single symbol")'
    )
    # normalize selection logic
    t = t.replace(
        "v = args.venue.lower().strip()",
        "v = (args.venue or args.exchange).lower().strip()"
    )
    t = t.replace(
        "symbols = [canonicalize(x) for x in args.symbols.split(\",\") if x.strip()] if args.symbols.strip() else DEFAULT.get(v, [\"BTC-USDT\"])",
        "raw = args.symbols.strip() or args.symbol.strip()\n"
        "    symbols = [canonicalize(x) for x in raw.split(\",\") if x.strip()] if raw else DEFAULT.get(v, [\"BTC-USDT\"])"
    )
    p.write_text(t, encoding="utf-8")
    print("[ok] patched args: scripts/refresh_market_rules.py")

def ensure_quantize():
    p = ROOT / "services" / "markets" / "quantize.py"
    if p.exists():
        return
    write("services/markets/quantize.py", """
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING, getcontext
from typing import Optional

getcontext().prec = 28

def _D(x: float) -> Decimal:
    return Decimal(str(x))

def _quantize_step(x: float, step: float, *, mode: str) -> float:
    if step is None or step <= 0:
        return float(x)
    dx = _D(float(x))
    ds = _D(float(step))
    q = dx / ds
    if mode == "floor":
        n = q.to_integral_value(rounding=ROUND_FLOOR)
    elif mode == "ceil":
        n = q.to_integral_value(rounding=ROUND_CEILING)
    else:
        raise ValueError("mode must be floor|ceil")
    return float(n * ds)

def quantize_amount(amount: float, qty_step: Optional[float]) -> float:
    # Always round DOWN size (safer)
    if not qty_step:
        return float(amount)
    return _quantize_step(float(amount), float(qty_step), mode="floor")

def quantize_price(price: float, price_tick: Optional[float], side: str) -> float:
    # Don't worsen price:
    # buy -> round DOWN (never pay more)
    # sell -> round UP (never sell for less)
    if not price_tick:
        return float(price)
    s = (side or "").strip().lower()
    mode = "floor" if s == "buy" else "ceil"
    return _quantize_step(float(price), float(price_tick), mode=mode)
""")
    print("[ok] added: services/markets/quantize.py")

def patch_place_order():
    rel = "services/execution/place_order.py"
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f"missing: {rel}")
    t = read(p)
    if "CBP_PHASE83_PRECISION" in t:
        print("[ok] place_order already Phase83-patched")
        return

    backup(rel)

    # 1) insert _estimate_market_price after _venue_norm_for_market_rules
    if "_estimate_market_price" not in t:
        m = re.search(r"def _venue_norm_for_market_rules\(ex: Any\) -> str:[\s\S]+?\n\n", t)
        if not m:
            raise SystemExit("could not locate _venue_norm_for_market_rules block")
        insert_at = m.end()
        helper = """
def _estimate_market_price(ex: Any, symbol: str, side: str) -> float | None:
    # Best-effort ticker estimate so MARKET orders still get notional-based risk checks.
    # buy -> ask (fallback last/close); sell -> bid (fallback last/close)
    try:
        tk = ex.fetch_ticker(symbol)
    except Exception:
        return None
    if not isinstance(tk, dict):
        return None
    s = (side or "").strip().lower()
    px = (tk.get("ask") or tk.get("last") or tk.get("close")) if s == "buy" else (tk.get("bid") or tk.get("last") or tk.get("close"))
    try:
        return float(px) if px is not None else None
    except Exception:
        return None

"""
        t = t[:insert_at] + helper + t[insert_at:]

    # 2) widen enforce return type
    t = t.replace(") -> Tuple[str, float | None]:", ") -> Tuple[str, float | None, float, float | None]:")

    # 3) compute notional for market orders (via ticker) + keep original for limits
    t = t.replace(
        "    notional = None\n    if price is not None:",
        "    est_px = None\n    notional = None\n    if price is not None:"
    )
    if "market_price_unavailable_for_risk_checks" not in t:
        t = t.replace(
            "    if price is not None:\n        try:\n            notional = float(amount) * float(price)\n        except Exception:\n            notional = None\n",
            "    if price is not None:\n        try:\n            notional = float(amount) * float(price)\n        except Exception:\n            notional = None\n"
            "    else:\n"
            "        if allow_market:\n"
            "            est_px = _estimate_market_price(ex, symbol, side)\n"
            "            if est_px is None:\n"
            "                raise RuntimeError('CBP_ORDER_BLOCKED:market_price_unavailable_for_risk_checks')\n"
            "            try:\n"
            "                notional = float(amount) * float(est_px)\n"
            "            except Exception:\n"
            "                notional = None\n"
        )

    # 4) insert precision rounding + re-check notional caps BEFORE validate call
    marker = "from services.markets.rules import validate as mr_validate"
    if marker not in t:
        raise SystemExit("could not locate market rules validate import")
    insert = f"""        # CBP_PHASE83_PRECISION: enforce tick/step rounding before validate+submit
        try:
            from services.markets.rules import get_rules as mr_get_rules  # type: ignore
            from services.markets.symbols import canonicalize  # type: ignore
            r = mr_get_rules(exec_db, venue, canonicalize(symbol), ttl_s=ttl_s, refresh_if_stale=True)
            if r is None:
                raise RuntimeError("market_rules_missing")
            from services.markets.quantize import quantize_amount, quantize_price  # type: ignore
            amount2 = quantize_amount(float(amount), getattr(r, "qty_step", None))
            if amount2 <= 0:
                raise RuntimeError("amount_rounding_zero")
            price2 = price
            if price is not None:
                price2 = quantize_price(float(price), getattr(r, "price_tick", None), side)

            # recompute notional after rounding (important for SELL rounding price up)
            notional = None
            if price2 is not None:
                notional = float(amount2) * float(price2)
            elif est_px is not None:
                notional = float(amount2) * float(est_px)

            if notional is not None and notional > float(max_order_notional):
                raise RuntimeError(f"order_notional_exceeds_limit notional={notional} max={max_order_notional}")
            if notional is not None and (daily_notional + notional) > float(max_daily_notional):
                raise RuntimeError(f"max_daily_notional daily={daily_notional} add={notional} max={max_daily_notional}")

            amount = float(amount2)
            price = float(price2) if price2 is not None else None
            notional = notional
        except Exception as e:
            raise RuntimeError(f"CBP_ORDER_BLOCKED:precision_enforce_failed:{type(e).__name__}:{e}")

        {marker}"""
    t = t.replace(marker, insert, 1)

    # 5) return adjusted amount/price
    t = t.replace("    return exec_db, notional", "    return exec_db, notional, float(amount), (float(price) if price is not None else None)")

    # 6) add rewrite helper + update callers
    if "_rewrite_create_order_call" not in t:
        helper2 = """
def _rewrite_create_order_call(args: tuple[Any, ...], kwargs: dict[str, Any], amount: float, price: float | None):
    a = list(args)
    k = dict(kwargs)
    # args path: (symbol, type, side, amount, price?, params?)
    if len(a) >= 4:
        a[3] = float(amount)
        if len(a) >= 5:
            a[4] = float(price) if price is not None else None
        else:
            if price is not None:
                k["price"] = float(price)
            else:
                k.pop("price", None)
        return tuple(a), k
    # kwargs path
    k["amount"] = float(amount)
    if price is not None:
        k["price"] = float(price)
    else:
        k.pop("price", None)
    return tuple(a), k

"""
        t = t.replace("def place_order(ex: Any, *args: Any, **kwargs: Any) -> Any:", helper2 + "def place_order(ex: Any, *args: Any, **kwargs: Any) -> Any:", 1)

    t = t.replace(
        "    exec_db, notional = _enforce_fail_closed(ex, symbol=symbol, side=side, amount=amount, price=price, params=params, order_type=otype)\n    o = ex.create_order(*args, **kwargs)",
        "    exec_db, notional, amount2, price2 = _enforce_fail_closed(ex, symbol=symbol, side=side, amount=amount, price=price, params=params, order_type=otype)\n    args2, kwargs2 = _rewrite_create_order_call(args, kwargs, amount2, price2)\n    o = ex.create_order(*args2, **kwargs2)"
    )
    t = t.replace(
        "    exec_db, notional = _enforce_fail_closed(ex, symbol=symbol, side=side, amount=amount, price=price, params=params, order_type=otype)\n    o = await ex.create_order(*args, **kwargs)",
        "    exec_db, notional, amount2, price2 = _enforce_fail_closed(ex, symbol=symbol, side=side, amount=amount, price=price, params=params, order_type=otype)\n    args2, kwargs2 = _rewrite_create_order_call(args, kwargs, amount2, price2)\n    o = await ex.create_order(*args2, **kwargs2)"
    )

    p.write_text(t, encoding="utf-8")
    print("[ok] patched: services/execution/place_order.py (Phase 83)")

def main():
    patch_scripts_bootstrap()
    patch_refresh_market_rules_args()
    ensure_quantize()
    patch_place_order()
    print("\nOK ✅ Phase 83 apply complete.")
    print(f"Backups: {ATTIC.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
