$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "ERROR: .venv not found. Run: py scripts\install.py"
  exit 1
}
& $py -m streamlit run dashboard\app.py --server.port 8501
