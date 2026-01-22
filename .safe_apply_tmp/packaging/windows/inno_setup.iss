; Crypto Bot Pro Desktop — Inno Setup script template
; Build first: python scripts/build_desktop.py
; Then open this .iss in Inno Setup and Compile.

[Setup]
; Optional: auto-sign installer during compile (requires configured sign tool)
; See Inno Setup docs: [Setup]: SignTool
SignTool=signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a $f

AppName=Crypto Bot Pro Desktop
AppVersion=1.0.0
DefaultDirName={pf}\CryptoBotProDesktop
DefaultGroupName=Crypto Bot Pro Desktop
OutputBaseFilename=CryptoBotProDesktop-Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\..\dist\CryptoBotProDesktop\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Crypto Bot Pro Desktop"; Filename: "{app}\CryptoBotProDesktop.exe"
Name: "{group}\Uninstall Crypto Bot Pro Desktop"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\CryptoBotProDesktop.exe"; Description: "Launch Crypto Bot Pro Desktop"; Flags: nowait postinstall skipifsilent
