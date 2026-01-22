from __future__ import annotations
import csv
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_normalize import normalize_symbol
from storage.evidence_signals_sqlite import EvidenceSignalsSQLite

ALLOWED_SIDES = {"buy","sell","long","short","flat"}

# ... (keep your _now_iso, _parse_ts, _safe_float, _safe_int, _cfg, ensure_source, ingest_event, ingest_csv functions unchanged)
