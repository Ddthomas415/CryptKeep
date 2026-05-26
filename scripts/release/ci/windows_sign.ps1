$ErrorActionPreference = "Stop"

# Inputs via env (recommended):
# - WIN_CERT_PFX_B64   (base64 of .pfx)
# - WIN_CERT_PASSWORD
# - WIN_TIMESTAMP_URL  (optional)
# - SIGNTOOL_PATH      (optional)
# Artifact to sign:
# - dist\CryptoBotPro\CryptoBotPro.exe

function Find-SignTool {
  if ($env:SIGNTOOL_PATH -and (Test-Path $env:SIGNTOOL_PATH)) { return $env:SIGNTOOL_PATH }
  $candidates = @(
    "$env:ProgramFiles (x86)\Windows Kits\10\bin\x64\signtool.exe",
    "$env:ProgramFiles\Windows Kits\10\bin\x64\signtool.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  return $null
}

if (-not $env:WIN_CERT_PFX_B64) { Write-Host "SKIP: WIN_CERT_PFX_B64 empty"; exit 0 }
if (-not $env:WIN_CERT_PASSWORD) { Write-Host "SKIP: WIN_CERT_PASSWORD empty"; exit 0 }

$signtool = Find-SignTool
if (-not $signtool) { throw "signtool.exe not found (install Windows SDK or set SIGNTOOL_PATH)" }

$exe = "dist\CryptoBotPro\CryptoBotPro.exe"
if (-not (Test-Path $exe)) { throw "EXE not found: $exe" }

$tmp = Join-Path $env:RUNNER_TEMP "codesign.pfx"
[IO.File]::WriteAllBytes($tmp, [Convert]::FromBase64String($env:WIN_CERT_PFX_B64))

$ts = $env:WIN_TIMESTAMP_URL
if (-not $ts) { $ts = "http://timestamp.digicert.com" }

Write-Host "Signing $exe with signtool..."
& $signtool sign /fd sha256 /td sha256 /tr $ts /f $tmp /p $env:WIN_CERT_PASSWORD $exe
& $signtool verify /pa /v $exe

Write-Host "DONE: signed $exe"
