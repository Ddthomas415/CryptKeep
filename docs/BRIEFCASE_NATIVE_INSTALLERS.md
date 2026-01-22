# Phase 302 — Briefcase Native Installers (Optional)

What you get:
- Windows: MSI (default) or ZIP.
- macOS: DMG (default for GUI apps), ZIP, or PKG.

Why optional:
- Native packaging adds platform-specific prerequisites.
- Phase 300 (one-command installer + Desktop launcher) remains the most reliable default.

How:
1) Install briefcase into your existing .venv
   - macOS: bash installers/install_briefcase_extras.sh
   - Windows: powershell -ExecutionPolicy Bypass -File installers\install_briefcase_extras.ps1

2) Build package
   - macOS: bash packaging/briefcase/build_macos.sh
   - Windows: powershell -ExecutionPolicy Bypass -File packaging/briefcase/build_windows.ps1

Config:
- pyproject.toml contains [tool.briefcase] and app definition.
