"""Read source; execute only selected unchanged methods on invented in-memory data."""
import ast
import __future__
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
GATE = "services/risk/live_risk_gates.py"
MATH = "services/markets/math_utils.py"
CALLER = "services/execution/_executor_submit.py"


def run():
    files = {p: (ROOT/p).read_bytes() for p in (GATE, MATH, CALLER)}
    tree = ast.parse(files[GATE])
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LiveRiskGates")
    cls.decorator_list = []  # Scaffolding only; no module import, dataclass or DB initialization.
    math_tree = ast.parse(files[MATH])
    helpers = [n for n in math_tree.body if isinstance(n, ast.FunctionDef)
               and n.name in ("decimal_value", "decimal_product")]
    assert len(helpers) == 2
    scope = {"Decimal": Decimal, "InvalidOperation": InvalidOperation,
             "_killswitch_file_on": lambda _: False}
    module = ast.fix_missing_locations(ast.Module(body=[*helpers, cls], type_ignores=[]))
    exec(compile(module, "selected_unchanged_gate_methods", "exec",
                 flags=__future__.annotations.compiler_flag), scope)

    class FakeDB:
        trades = 0
        killed = False
        def killswitch_on(self):
            return self.killed
        def day_row(self):
            return {"trades": self.trades, "realized_pnl_usd": 0}

    gate = scope["LiveRiskGates"]()
    gate.db = FakeDB()
    gate.limits = SimpleNamespace(max_daily_loss_usd=25, max_notional_per_trade_usd=25,
        max_trades_per_day=5, max_position_notional_usd=50, kill_switch_file="invented-unused")
    cases = []
    for current, side, price in ((40,"buy",25),(50,"buy",25),(None,"buy",25),
                                 (65,"sell",25),(0,"buy",26)):
        intent = {"symbol":"INVENTED/USD", "side":side, "qty":1, "price":price,
                  "position_notional_usd":current}
        ok, reason, meta = gate.check_live(it=intent, realized_pnl_usd=0)
        cases.append({"synthetic_current_position_usd":current, "side":side,
            "order_notional_usd":price,"post_trade_position_if_full_fill_usd":
                None if current is None else current+(price if side=="buy" else -price),
            "gate_allowed":ok,"reason":reason})
    assert [c["gate_allowed"] for c in cases] == [True,True,True,True,False]
    assert cases[-1]["reason"] == "MAX_NOTIONAL_PER_TRADE_EXCEEDED"
    chain = []
    for previous_trades in range(6):
        gate.db.trades = previous_trades
        ok,reason,_ = gate.check_live(it={"qty":1,"price":25,"symbol":"INVENTED/USD"},realized_pnl_usd=0)
        chain.append({"previous_daily_trades":previous_trades,"gate_allowed":ok,"reason":reason,
                      "counterfactual_exposure_if_full_fill_usd":(previous_trades+1)*25})
    assert [c["gate_allowed"] for c in chain] == [True]*5+[False]
    gate.db.trades=0;gate.db.killed=True
    assert gate.check_live(it={"qty":1,"price":25},realized_pnl_usd=0)[1] == "KILL_SWITCH_ON"

    check = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="check_live")
    caller = ast.parse(files[CALLER])
    call = next(n for n in ast.walk(caller) if isinstance(n,ast.Call)
                and isinstance(n.func,ast.Attribute) and n.func.attr=="check_live")
    supplied = next(k.value for k in call.keywords if k.arg=="it")
    assert isinstance(supplied,ast.Dict)
    result = {"scope":"selected actual gate methods with invented limits/DB; no production module import",
        "classification":"SHOWN: selected gate does not enforce its position cap",
        "independent_review":False,"gate_line":check.lineno,"caller_line":call.lineno,
        "position_cap_referenced_by_check_live":any(isinstance(n,ast.Attribute)
            and n.attr=="max_position_notional_usd" for n in ast.walk(check)),
        "caller_intent_fields":[k.value for k in supplied.keys],"synthetic_cap_usd":50,
        "cases":cases,"synthetic_daily_sequence":chain,
        "per_trade_and_kill_positive_controls_passed":True,
        "limit":"does not prove live mode, real holdings, fill, loss or absence of all downstream protections",
        "network_account_config_or_db_access":False,
        "source_sha256":{p:hashlib.sha256(raw).hexdigest() for p,raw in files.items()}}
    assert not result["position_cap_referenced_by_check_live"]
    assert set(result["caller_intent_fields"]) == {"qty","price","symbol"}
    assert all((ROOT/p).read_bytes()==raw for p,raw in files.items())
    return result


if __name__ == "__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
