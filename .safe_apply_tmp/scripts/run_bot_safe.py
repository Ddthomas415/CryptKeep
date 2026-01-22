from services.strategies.strategy_registry import compute_signal
from services.strategies.registry import get_strategy
from services.strategies.base import MarketContext, PositionContext
from __future__ import annotations

import argparse
import sys

from services.preflight.preflight import run_preflight

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="binance")
    ap.add_argument("--symbols", default="BTC/USDT", help="Comma list")
    ap.add_argument("--force", action="store_true", help="Run even if preflight fails (NOT recommended)")
    args = ap.parse_args()

    syms = [s.strip().upper().replace("-", "/") for s in str(args.symbols).split(",") if s.strip()]
    pf = run_preflight(venue=args.venue, symbols=syms)
    print({"preflight_ok": pf.get("ok"), "dry_run": pf.get("dry_run"), "checks": pf.get("checks")})

    if (not pf.get("ok")) and (not args.force):
        # turn kill switch ON to be explicit
        try:
            from services.execution.kill_switch import set_kill_switch
            set_kill_switch(True, reason="preflight_failed")
        except Exception:
            pass
        raise SystemExit(2)

    # If passes, start runner
    from services.execution import strategy_runner  # type: ignore
    if hasattr(strategy_runner, "main"):
        return strategy_runner.main()
    if hasattr(strategy_runner, "run"):
        return strategy_runner.run()
    print("strategy_runner has no main/run; start it via your existing entrypoint.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

            # Phase 243: strategy-driven SELL block (paper-first). Idempotency prevents duplicates.
            # This block runs in addition to any existing exit logic.
            try:
                if bool(strategy_sell_ok):
                    from services.portfolio.position_accounting import list_positions
                    # check holdings
                    posrep = list_positions(limit=2000)
                    held_qty = 0.0
                    for r in (posrep.get('rows') or []):
                        if str(r.get('venue')) == str(venue).lower() and str(r.get('mode')) == str(mode).lower() and str(r.get('symbol')) == str(sym).upper():
                            held_qty = float(r.get('base_qty') or 0.0)
                            break
                    if held_qty > 0.0:
                        # create SELL intent (idempotent per bar)
                        if bool((cfg.get('execution_intents', {}) or {}).get('enabled', True)):
                            ir = intent_ledger.create_if_new(venue=venue, symbol=sym, side='sell', timeframe=tf, bar_ts_ms=bar_ts_ms, meta={'stage':'strategy_sell_block_phase243','mode':mode,'px':float(px),'held_qty':held_qty,'strategy':strategy_rep})
                            if bool(ir.get('created')):
                                iid = ir.get('intent_id')
                                pe = cfg.get('paper_execution', {}) if isinstance(cfg.get('paper_execution'), dict) else {}
                                # For now: SELL a notional equal to max_risk_per_trade_quote (simple + conservative)
                                risk = cfg.get('risk', {}) if isinstance(cfg.get('risk'), dict) else {}
                                qa = float(risk.get('max_risk_per_trade_quote', 20.0))
                                intent_ledger.mark(intent_id=str(iid), status='SENT', meta_patch={'px':float(px), 'quote_amount':qa, 'strategy':strategy_rep})
                                fill = simulate_market_fill(venue=venue, symbol=sym, side='sell', price=float(px), quote_amount=float(qa), fee_bps=float(pe.get('fee_bps',10.0)), slippage_bps=float(pe.get('slippage_bps',5.0)))
                                if bool(fill.get('ok')):
                                    record_trade(trade=fill, mode=mode, intent_id=str(iid))
                                    try:
                                        print({'stage':'position_apply_sell_strategy', 'detail': apply_fill(cfg=cfg, fill=fill, mode=mode, intent_id=str(iid))})
                                    except Exception as _e3:
                                        print({'stage':'position_apply_sell_strategy_error','symbol':sym,'error': f"{type(_e3).__name__}:{_e3}"})
                                    intent_ledger.mark(intent_id=str(iid), status='FILLED', meta_patch={'fill':fill, 'order_id':fill.get('order_id'), 'strategy':strategy_rep})
                                    print({'stage':'paper_fill_sell_strategy','symbol':sym,'intent_id':iid,'fill':fill,'strategy':strategy_rep})
                                else:
                                    intent_ledger.mark(intent_id=str(iid), status='FAILED', last_error=str(fill.get('reason','paper_fill_failed')), meta_patch={'fill':fill, 'strategy':strategy_rep})
                                    print({'stage':'paper_fill_sell_strategy_failed','symbol':sym,'intent_id':iid,'detail':fill,'strategy':strategy_rep})
            except Exception as _eSS:
                print({'stage':'strategy_sell_block_error','symbol':sym,'error': f"{type(_eSS).__name__}:{_eSS}"})
