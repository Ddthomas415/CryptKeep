Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

# REQUIREMENTS:
# - Windows SDK tools on PATH or known locations:
#   - MakeAppx.exe
#   - (optional) SignTool.exe for signing

function Find-Tool($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

$MakeAppx = Find-Tool "MakeAppx.exe"
if (-not $MakeAppx) {
  Write-Host "ERROR: MakeAppx.exe not found on PATH."
  Write-Host "Install Windows SDK (App Packaging Tools), then re-run."
  exit 2
}

# Ensure app bundle exists
$AppDir = "dist\CryptoBotPro"
$Exe = Join-Path $AppDir "CryptoBotPro.exe"
if (!(Test-Path $Exe)) {
  Write-Host "ERROR: Missing $Exe"
  Write-Host "Build first: .\scripts\build_windows.ps1"
  exit 2
}

# Stage folder
$StageRoot = "packaging\msix\stage"
if (Test-Path $StageRoot) { Remove-Item $StageRoot -Recurse -Force }
New-Item -ItemType Directory -Path $StageRoot | Out-Null

# Copy manifest template and assets
Copy-Item "packaging\msix\AppxManifest.xml" (Join-Path $StageRoot "AppxManifest.xml") -Force
New-Item -ItemType Directory -Path (Join-Path $StageRoot "Assets") | Out-Null
Copy-Item "packaging\msix\Assets\*" (Join-Path $StageRoot "Assets") -Force -ErrorAction SilentlyContinue

# Copy application bundle into stage under folder CryptoBotPro\
New-Item -ItemType Directory -Path (Join-Path $StageRoot "CryptoBotPro") | Out-Null
Copy-Item "$AppDir\*" (Join-Path $StageRoot "CryptoBotPro") -Recurse -Force

# Fill manifest placeholders from env or defaults
$PackageName = $env:CBP_PACKAGE_NAME
if ([string]::IsNullOrWhiteSpace($PackageName)) { $PackageName = "CryptoBotPro.Desktop" }

$Publisher = $env:CBP_PUBLISHER
if ([string]::IsNullOrWhiteSpace($Publisher)) { $Publisher = "CN=YOUR_PUBLISHER" }  # must match cert when signing for distribution

$Version = $env:CBP_VERSION
if ([string]::IsNullOrWhiteSpace($Version)) { $Version = "0.1.0.0" }  # MSIX requires 4-part version

$DisplayName = $env:CBP_DISPLAY_NAME
if ([string]::IsNullOrWhiteSpace($DisplayName)) { $DisplayName = "CryptoBotPro" }

$PublisherDisplay = $env:CBP_PUBLISHER_DISPLAY
if ([string]::IsNullOrWhiteSpace($PublisherDisplay)) { $PublisherDisplay = "CryptoBotPro" }

$ManifestPath = Join-Path $StageRoot "AppxManifest.xml"
$Xml = Get-Content $ManifestPath -Raw
$Xml = $Xml.Replace("__CBP_PACKAGE_NAME__", $PackageName)
$Xml = $Xml.Replace("__CBP_PUBLISHER__", $Publisher)
$Xml = $Xml.Replace("__CBP_VERSION__", $Version)
$Xml = $Xml.Replace("__CBP_DISPLAY_NAME__", $DisplayName)
$Xml = $Xml.Replace("__CBP_PUBLISHER_DISPLAY__", $PublisherDisplay)
Set-Content -Path $ManifestPath -Value $Xml -Encoding UTF8

# Build MSIX
$Out = "dist\CryptoBotPro.msix"
if (Test-Path $Out) { Remove-Item $Out -Force }

Write-Host "==> Packing MSIX"
& $MakeAppx pack /d $StageRoot /p $Out /o | Out-Host

Write-Host ""
Write-Host "DONE: $Out"
Write-Host "Next: sign it with .\scripts\sign_msix.ps1 (required for broad distribution)"
