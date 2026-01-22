from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from services.os.app_paths import state_root
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from services.admin.config_editor import load_user_yaml
from storage.daily_limits_sqlite import DailyLimitsSQLite

# ... all the rest of your pnl_harvester.py code here unchanged ...
