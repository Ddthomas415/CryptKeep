param(
  [string]$DistDir = "dist",
  [string]$AppName = "CryptoBotPro"
)

$ErrorActionPreference = "Stop"

function Have-Env($name) {
  return [bool]([System.Environment]::GetEnvironmentVariable($name))
}

if (-not (Have-Env "WIN_SIGN_PFX_B64")) {
  Write-Host "SKIP: WIN_SIGN_PFX_B64 not set"
  exit 0
}
if (-not (Have-Env "WIN_SIGN_PFX_PASSWORD")) {
  Write-Host "SKIP: WIN_SIGN_PFX_PASSWORD not set"
  exit 0
}

# Find signtool
$signTool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if (-not $signTool) {
  Write-Host "ERROR: signtool.exe not found on runner. Install Windows SDK or adjust CI image."
  exit 1
}

# Decode PFX
$pfxPath = Join-Path $env:TEMP "signcert.pfx"
[IO.File]::WriteAllBytes($pfxPath, [Convert]::FromBase64String($env:WIN_SIGN_PFX_B64))

# Find exe(s)
$targetDir = Join-Path $DistDir $AppName
if (-not (Test-Path $targetDir)) {
  Write-Host "ERROR: target dist folder not found: $targetDir"
  exit 1
}

$exes = Get-ChildItem -Path $targetDir -Filter "*.exe" -Recurse
if ($exes.Count -eq 0) {
  Write-Host "ERROR: no exe found under: $targetDir"
  exit 1
}

# Timestamp server optional (recommended)
$ts = $env:WIN_SIGN_TIMESTAMP_URL
if (-not $ts) { $ts = "http://timestamp.digicert.com" }

foreach ($exe in $exes) {
  Write-Host "Signing: $($exe.FullName)"
  & $signTool.Source sign `
    /f $pfxPath `
    /p $env:WIN_SIGN_PFX_PASSWORD `
    /fd SHA256 `
    /tr $ts `
    /td SHA256 `
    $exe.FullName

  Write-Host "Verifying: $($exe.FullName)"
  & $signTool.Source verify /pa /v $exe.FullName
}

Write-Host "DONE: Windows signing complete."
