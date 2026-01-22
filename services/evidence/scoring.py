from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.security.exchange_factory import make_exchange
from services.security.credential_store import get_exchange_credentials
from storage.evidence_signals_sqlite import EvidenceSignalsSQLite

# ... (keep your _now, _side_to_sign, score_signal_forward_return functions unchanged)
