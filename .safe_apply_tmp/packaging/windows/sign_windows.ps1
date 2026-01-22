Param(
  [string]$ExePath = "dist\CryptoBotProDesktop\CryptoBotProDesktop.exe",
  [string]$InstallerPath = "CryptoBotProDesktop-Installer.exe",
  [string]$TimestampUrl = "http://timestamp.digicert.com"
)

# Requires:
# - signtool (Windows SDK / Visual Studio)
# - a code signing cert in the Windows cert store (or a .pfx + password flow if you prefer)
#
# Example:
#   powershell -ExecutionPolicy Bypass -File packaging\windows\sign_windows.ps1

function Sign-File($Path) {
  if (-not (Test-Path $Path)) {
    Write-Host "Missing: $Path"
    return
  }
  Write-Host "Signing: $Path"
  signtool sign /fd SHA256 /tr $TimestampUrl /td SHA256 /a $Path
  signtool verify /pa $Path
}

Sign-File $ExePath
Sign-File $InstallerPath
