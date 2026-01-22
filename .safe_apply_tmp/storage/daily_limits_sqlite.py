from pathlib import Path
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "daily_limits.sqlite"

print("Daily limits storage initialized:", DB_PATH)
