import re
from pathlib import Path

FILES_TO_FIX = [
    "services/storage/paper_trading_sqlite.py",
    "services/storage/trade_journal_sqlite.py",
    "services/execution/poller.py",
]

def fix_file(path: Path):
    text = path.read_text()
    
    # 1️⃣ Convert all tabs to 4 spaces
    text = text.replace("\t", "    ")
    
    # 2️⃣ Remove trailing whitespace
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    
    # 3️⃣ Ensure no empty lines have spaces
    text = re.sub(r"^\s+$", "", text, flags=re.MULTILINE)
    
    # 4️⃣ Optionally, insert pass in poller.py if empty (fixes SyntaxError)
    if "poller.py" in path.name and not text.strip():
        text = "pass\n"
    
    path.write_text(text)
    print(f"✅ Fixed {path}")

def main():
    for file_path in FILES_TO_FIX:
        path = Path(file_path)
        if path.exists():
            fix_file(path)
        else:
            print(f"⚠️ File not found: {path}")

if __name__ == "__main__":
    main()

