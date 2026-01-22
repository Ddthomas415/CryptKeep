import subprocess
from pathlib import Path

patch_dir = Path(__file__).parent
for patch_file in sorted(patch_dir.glob("phase*_patch.py")):
    print(f"Applying {patch_file.name}...")
    subprocess.run(["python3", str(patch_file)], check=True)

print("All patches applied successfully.")

