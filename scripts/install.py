import sys
from pathlib import Path

# Make sure Python can find the core package
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

from core.symbols import ensure_default_symbol_map

ROOT = project_root
(ROOT / "data").mkdir(exist_ok=True)

print("Creating default symbol_map.json if missing...")
ensure_default_symbol_map()

print("\n=== Done! ===")
json_file = ROOT / "data" / "symbol_map.json"
if json_file.exists():
    print("File created successfully:")
    print(json_file.read_text())
else:
    print("File was NOT created - check errors above")
