# Phase 270 — MSIX Packaging (Windows)

Artifacts:
- dist/CryptoBotPro.msix

Requirements:
- Windows SDK tools installed (MakeAppx.exe, signtool.exe).

Build:
1) Build the app bundle:
   - .\scripts\build_windows.ps1
2) Build the MSIX package:
   - .\scripts\build_msix.ps1
3) Sign the MSIX (recommended/required for broad distribution):
   - .\scripts\sign_msix.ps1

Identity fields:
- The MSIX Identity Publisher must match your signing certificate subject.
- Set env vars before build_msix.ps1 if needed:
  - CBP_PACKAGE_NAME (default: CryptoBotPro.Desktop)
  - CBP_PUBLISHER (default: CN=YOUR_PUBLISHER)
  - CBP_VERSION (default: 0.1.0.0)
  - CBP_DISPLAY_NAME (default: CryptoBotPro)
  - CBP_PUBLISHER_DISPLAY (default: CryptoBotPro)

Install test (local):
- .\scripts\install_msix.ps1

Icons:
- packaging/msix/Assets contains placeholders.
  Replace with real PNGs before shipping publicly.
