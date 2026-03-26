import os
import sys
from pathlib import Path

os.environ.setdefault("OWNER_API_TOKEN", "test-owner-token")
os.environ.setdefault("TRADER_API_TOKEN", "test-trader-token")
os.environ.setdefault("ANALYST_API_TOKEN", "test-analyst-token")
os.environ.setdefault("VIEWER_API_TOKEN", "test-viewer-token")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
