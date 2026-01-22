#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m cryptobotpro doctor
python3 -m cryptobotpro install --venv

# Build .app bundle (windowed)
if [ -d ".venv" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

$PY -m pip install -r requirements-packaging.txt
$PY -m PyInstaller packaging/pyinstaller/cryptobotpro-macos.spec --noconfirm --clean

echo ""
echo "DONE (macOS): dist/CryptoBotPro.app"
echo ""
