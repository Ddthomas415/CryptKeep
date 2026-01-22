import subprocess
from pathlib import Path
import sys

def main():
    project_root = Path(__file__).parent.resolve()
    print(f"Running patch runner in: {project_root}\n")

    patches = sorted(project_root.glob("phase*_patch.py"))

    if not patches:
        print("No patch files found. Exiting.")
        sys.exit(0)

    for patch_file in patches:
        print(f"Applying {patch_file.name}...")
        result = subprocess.run(["python3", str(patch_file)])
        if result.returncode != 0:
            print(f"Error applying {patch_file.name}. Stopping.")
            sys.exit(result.returncode)

    print("\nAll patches applied successfully.")

if __name__ == "__main__":
    main()

