# fix_config_editor_indent.py - Fixes unexpected indent on return line
from pathlib import Path

def fix_indent():
    file_path = Path("services/admin/config_editor.py")
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    lines = file_path.read_text(encoding="utf-8").splitlines()

    # Find the validate_user_yaml function and its return line
    in_func = False
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith("def validate_user_yaml"):
            in_func = True
        if in_func and stripped.startswith("return ") and "ok" in stripped:
            # This is likely the problematic return line
            # De-indent it to match function body level (usually 4 spaces)
            if line.startswith("    " * 2):  # if it's indented 8 spaces
                lines[i] = line.replace("        ", "    ", 1)  # reduce by 4 spaces
                print(f"Fixed indentation on line {i+1}: return line")
            elif line.startswith(" " * 8):  # 8 spaces
                lines[i] = "    " + line.lstrip()
                print(f"Fixed indentation on line {i+1}: return line")
            break

    # Also ensure no tabs in the whole file (convert to 4 spaces)
    fixed_lines = []
    for line in lines:
        # Replace tabs with 4 spaces
        fixed_line = line.expandtabs(4)
        fixed_lines.append(fixed_line)

    file_path.write_text("\n".join(fixed_lines) + "\n", encoding="utf-8")
    print("config_editor.py fixed. Now run:")
    print("  python3 -c \"from services.admin.config_editor import validate_user_yaml; print('OK')\"")

if __name__ == "__main__":
    fix_indent()