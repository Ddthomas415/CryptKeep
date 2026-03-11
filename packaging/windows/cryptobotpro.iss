; CryptoBotPro Inno Setup Script (Phase 329)
; Build requires Inno Setup (ISCC.exe). This script packages the PyInstaller --onedir output.

#define MyAppName "CryptoBotPro"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Crypto Bot Pro"
#define MyAppExeName "CryptoBotPro.exe"
#define SourceDir "dist\CryptoBotPro"

[Setup]
AppId={{D8F0D6BB-2C0E-4F3B-9C52-1A2EECE3E4D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
Compression=lzma
SolidCompression=yes
OutputDir=dist_installers
OutputBaseFilename=CryptoBotPro-Setup
SetupIconFile=
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
; Include everything from PyInstaller onedir output
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
