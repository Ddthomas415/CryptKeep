$ErrorActionPreference = "Stop"

$Python = $env:PYTHON_BIN
if (-not $Python) {
  if (Test-Path ".\.venv\Scripts\python.exe") {
    $Python = ".\.venv\Scripts\python.exe"
  } else {
    $Python = "python"
  }
}

& $Python "scripts\run_dashboard.py" --open @args
