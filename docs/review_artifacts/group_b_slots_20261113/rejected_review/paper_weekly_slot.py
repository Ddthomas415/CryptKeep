"""Default-off Group B slot reader. Never imports or executes a ranker."""
import json
import os
from pathlib import Path
import re
import stat

from services.market_data.group_b_selection import MAX_BYTES, POLICY, UNIVERSE, finite, instant, validate_selection, weekly_name
from storage.exit_event_journal import _decode_payload

STATE_KEY = "group_b_weekly_slot_v1"


def _paper_only(cfg):
    p = cfg.get("_paper_entry_policy") or {}
    return (p.get("live_enabled") is False and p.get("armed") is False
            and p.get("enabled") is True and p.get("require_fresh_snapshot_quotes") is True
            and p.get("use_ccxt_fallback") is False and p.get("quote_currency") == "USD"
            and cfg.get("venue") == "coinbase" and cfg.get("auto_select_best_venue") is False
            and cfg.get("position_aware") is True and cfg.get("sell_full_position") is True
            and cfg.get("order_type") == "market"
            and cfg.get("paper_entry_sizing") == "available_cash_v1")


def resolve_slot(*, cfg, sdb, qdb, pdb, accounting, limits, now):
    """Retain ownership until actual fills AND old-scope accounting settle.

    Ranking failure is not a rotation instruction. Even damaged input/state
    cannot remove the actual held/pending symbols from exit service.
    """
    fallback = [s for s in cfg.get("symbols", []) if s in UNIVERSE]
    result = {"symbols": fallback, "allow_buy": False, "rotation_symbols": [],
              "reason": "slot_unknown", "selection_sha256": None}
    evidence_ok = True
    held, pending, seen = [], [], []
    try:
        snap = pdb.slot_snapshot()
        held = [row["symbol"] for row in snap["positions"]]
        pending = list(snap["open_order_symbols"])
        pending += [row["symbol"] for row in qdb.slot_open_intents()]
        # Rejected durable exits remain owed even when generic intent state is terminal.
        pending += [row["symbol"] for row in qdb.list_paper_exits()]
        for row in snap["positions"]:
            finite(row["qty"], low=0)
        if any(s not in UNIVERSE for s in held + pending) or len(set(held)) > 1:
            raise ValueError("unsupported_slot_ownership")
    except Exception:
        evidence_ok = False
    known = [s for s in held + pending if type(s) is str and re.fullmatch(r"[A-Z0-9]{1,30}/USD", s)]
    result["symbols"] = list(dict.fromkeys(known + fallback))
    try:
        option = cfg["group_b_selection"]
        if (type(option) is not dict or option.get("policy") != POLICY
                or type(option.get("slot")) is not int or not 1 <= option["slot"] <= 3
                or not _paper_only(cfg)):
            raise ValueError("slot_policy_or_paper_guard")
        slot = option["slot"]
        raw_state = sdb.get(STATE_KEY)
        state = _decode_payload(raw_state) if raw_state else None
        if state is not None:
            if (state["slot"] != slot or state["strategy_id"] != cfg["strategy_id"]
                    or state["active_symbol"] not in UNIVERSE
                    or type(state["managed_symbols"]) is not list
                    or any(s not in UNIVERSE for s in state["managed_symbols"])):
                raise ValueError("slot_state_identity")
            seen = state["managed_symbols"]
            active = state["active_symbol"]
        else:
            if len(fallback) != 1:
                raise ValueError("single_slot_config_required")
            active = held[0] if held else fallback[0]
        if held:
            # The ledger, not a desired/persisted flat symbol, owns the slot.
            seen = list(dict.fromkeys(seen + [active]))
            active = held[0]
        result["symbols"] = list(dict.fromkeys(known + [active]))
        # Refresh every retired scope before allowing a new symbol to spend proceeds.
        seen = list(dict.fromkeys(seen + known + [active]))
        unsettled = any([accounting.refresh(venue="coinbase", symbol=s, strategy=cfg["strategy_id"],
                                           limits=limits)["unsettled"] for s in seen])
        directory = Path(option["directory"])
        if not directory.is_absolute():
            raise ValueError("absolute_selection_path_required")
        path = directory / weekly_name(now)
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("regular_selection_file_required")
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("selection_too_large")
        artifact = validate_selection(_decode_payload(raw.decode("utf-8")), now=now)
        if state is not None:
            if state["rank_at"] == artifact["rank_at"]:
                if state["selection_sha256"] != artifact["sha256"]:
                    raise ValueError("same_week_replacement_refused")
            elif (instant(state["rank_at"]) > instant(artifact["rank_at"])
                  or artifact["previous_slots"][slot - 1] != state["target"]
                  or artifact["previous_sha256"] != state["selection_sha256"]):
                raise ValueError("slot_continuity_mismatch")
        if not evidence_ok:
            raise ValueError("slot_ledger_or_queue_unknown")
        target = artifact["slots"][slot - 1]
        if not held and not pending and not unsettled and target is not None:
            active = target
        state = {"slot": slot, "strategy_id": cfg["strategy_id"], "active_symbol": active,
                 "managed_symbols": list(dict.fromkeys(seen + [active])),
                 "rank_at": artifact["rank_at"], "selection_sha256": artifact["sha256"], "target": target}
        # Persist identity before any emission. A failed write cannot authorize a BUY.
        sdb.set(STATE_KEY, json.dumps(state, sort_keys=True, allow_nan=False))
        result.update(symbols=list(dict.fromkeys(known + [active])),
                      allow_buy=target is not None and active == target and not held and not pending and not unsettled,
                      rotation_symbols=[s for s in held if s != target],
                      reason="current_ranking", selection_sha256=artifact["sha256"])
    except Exception as exc:
        result["reason"] = str(exc) if type(exc) is ValueError else type(exc).__name__
    return result


def valuation_symbol(*, pdb, sdb):
    """Never mark a flat placeholder while a rotated coin is actually held."""
    try:
        rows = pdb.slot_snapshot()["positions"]
        if rows:
            if len(rows) != 1 or rows[0]["symbol"] not in UNIVERSE:
                return None
            finite(rows[0]["qty"], low=0)
            return rows[0]["symbol"]
        state = _decode_payload(sdb.get(STATE_KEY))
        symbol = state["active_symbol"]
        return symbol if symbol in UNIVERSE else None
    except Exception:
        return None
