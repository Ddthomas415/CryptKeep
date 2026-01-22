import os

files = {
    "storage/execution_report_sqlite.py": "# Phase 167: execution report store + strategy logging + UI\n# Add your code here\n",
    "services/execution/handoff_pack.py": "# Phase 168: handoff pack exporter + UI download\n# Add your code here\n",
    "scripts/bootstrap.py": "# Phase 169: bootstrap installer + desktop launchers\n# Add your code here\n",
    "desktop_app/desktop_entry.py": "# Phase 170: PyInstaller desktop builds + hook + docs\n# Add your code here\n",
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    first_line = content.splitlines()[0]
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            file_text = f.read()
        if first_line not in file_text:
            with open(filepath, "a") as f:
                f.write("\n" + content)
            print(f"OK: {first_line[2:]} applied.")
        else:
            print(f"Skipped: {first_line[2:]} already exists.")
    else:
        with open(filepath, "a") as f:
            f.write(content)
        print(f"OK: {first_line[2:]} applied.")

