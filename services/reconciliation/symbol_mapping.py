from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.symbol_parse import split_symbol

@dataclass(frozen=True)
class SymbolMapRow:
    canonical_symbol: str
    exchange_symbol: str
    base: str
    quote: str

def build_symbol_rows(exchange: str, trading_cfg: Dict[str, Any]) -> List[SymbolMapRow]:
    exchange = exchange.lower()
    canon_syms = [str(s) for s in (trading_cfg.get("symbols") or [])]
    sym_maps = (trading_cfg.get("symbol_maps") or {}).get(exchange) or {}

    rows: List[SymbolMapRow] = []
    for c in canon_syms:
        ex_sym = sym_maps.get(c)
        if not ex_sym:
            # for coinbase, allow canonical passthrough (already policy)
            if exchange == "coinbase":
                ex_sym = c
            else:
                continue
        base, quote = split_symbol(str(ex_sym))
        rows.append(SymbolMapRow(canonical_symbol=c, exchange_symbol=str(ex_sym), base=base, quote=quote))
    return rows
