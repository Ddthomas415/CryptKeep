Param(
  [Parameter(Mandatory=$true)][string]$FilePath,
  [Parameter(Mandatory=$false)][string]$PfxPath = "",
  [Parameter(Mandatory=$false)][string]$PfxPassword = "",
  [Parameter(Mandatory=$false)][string]$CertThumbprint = "",
  [Parameter(Mandatory=$false)][string]$TimeStampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $FilePath)) {
  Write-Host "File not found: $FilePath"
  exit 2
}

# Requires SignTool (Windows SDK / Visual Studio). See docs/SIGNING_DISTRIBUTION.md.
# Choose one:
#  A) Sign with a PFX
#  B) Sign with a cert in Windows cert store (thumbprint)

if ($PfxPath -ne "") {
  if (-not (Test-Path $PfxPath)) { Write-Host "PFX not found: $PfxPath"; exit 2 }
  Write-Host "[Windows] Signing with PFX..."
  signtool sign /fd SHA256 /f "$PfxPath" /p "$PfxPassword" /tr "$TimeStampUrl" /td SHA256 "$FilePath"
}
elseif ($CertThumbprint -ne "") {
  Write-Host "[Windows] Signing with cert store thumbprint..."
  signtool sign /fd SHA256 /sha1 "$CertThumbprint" /tr "$TimeStampUrl" /td SHA256 "$FilePath"
}
else {
  Write-Host "Provide either -PfxPath (and -PfxPassword) or -CertThumbprint."
  exit 2
}

Write-Host "[Windows] Verifying signature..."
signtool verify /pa /v "$FilePath"

Write-Host "[Windows] Done."
