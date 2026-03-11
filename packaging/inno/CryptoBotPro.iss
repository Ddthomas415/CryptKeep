; CryptoBotPro Windows Installer (Inno Setup)
; Build: iscc.exe packaging\inno\CryptoBotPro.iss
;
; This installer wraps the PyInstaller output folder: dist\CryptoBotPro\*
; Keep AppId stable across versions to get clean upgrades.

#define MyAppName "CryptoBotPro"
#define MyAppPublisher "CryptoBotPro"
#define MyAppExeName "CryptoBotPro.exe"
#define MyAppVersion "0.1.0"

[Setup]
; IMPORTANT: keep constant to avoid multiple Add/Remove entries when upgrading
; You can generate a GUID once and never change it.
AppId={{A9F7D3F1-0C3D-4E7B-9B3C-5E4A2B1C9D10}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
OutputDir=dist_installer
OutputBaseFilename=CryptoBotPro-Setup-{#MyAppVersion}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Copy the full PyInstaller dist folder
Source: "..\..\dist\CryptoBotPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
; Uninstaller shortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Optional Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
; Launch after install (optional)
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
