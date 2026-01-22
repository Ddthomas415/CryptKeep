; Inno Setup script template for CryptoBotPro
; Compile with Inno Setup on Windows.
; This installs the PyInstaller onedir output.

#define MyAppName "CryptoBotPro"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "CryptoBotPro"
#define MyAppExeName "CryptoBotPro.exe"

[Setup]
AppId={{C6A09B5B-5F8F-4C17-9D6D-4A19C0D5C0AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename={#MyAppName}-Setup
Compression=lzma
SolidCompression=yes

[Files]
; Point this to your dist output folder
Source: "..\..\dist\CryptoBotPro\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
