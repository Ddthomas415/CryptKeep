#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[CryptoBotPro] Installing into: $ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3.11+ and re-run."
  exit 1
fi

PYV="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "[CryptoBotPro] Python: $PYV"

if [ ! -d ".venv" ]; then
  echo "[CryptoBotPro] Creating virtualenv..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source ".venv/bin/activate"

python -m pip install --upgrade pip wheel setuptools

REQ=""
if [ -f "requirements.txt" ]; then
  REQ="requirements.txt"
elif [ -f "requirements/base.txt" ]; then
  REQ="requirements/base.txt"
fi

if [ -n "$REQ" ]; then
  echo "[CryptoBotPro] Installing dependencies from $REQ ..."
  python -m pip install -r "$REQ"
else
  echo "WARNING: No requirements file found. Skipping pip install."
fi

# Create Desktop launcher (.command) to avoid folder hopping
DESK="$HOME/Desktop"
LAUNCH="$DESK/CryptoBotPro.command"
cat > "$LAUNCH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# If you moved this file, fallback to current directory assumption:
if [ ! -f "$ROOT_DIR/dashboard/app.py" ]; then
  ROOT_DIR="$(pwd)"
fi
cd "$ROOT_DIR"
source ".venv/bin/activate"
python -m streamlit run dashboard/app.py --server.port 8501
EOF
chmod +x "$LAUNCH"

echo "[CryptoBotPro] Done."
echo "Launcher created: $LAUNCH"
echo "Double-click it (or right-click → Open) to start the dashboard."
