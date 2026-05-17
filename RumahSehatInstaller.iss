[Setup]
#include "version.iss"
AppId={{B1A4B0F7-7F1F-4B8C-99EB-1BF5B5C93D6B}
AppName=Lancar Dynamic Admin
AppVersion={#MyAppVersion}
AppPublisher=Lancar Dinamic
DefaultDirName={autopf}\LancarDinamicAdmin
DefaultGroupName=Lancar Dynamic Admin
OutputDir=dist
OutputBaseFilename=LancarDinamicAdmin_Setup_v{#MyAppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\LancarDinamicAdmin.exe
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\LancarDinamicAdmin\*"; DestDir: "{app}"; Excludes: "settings.json,*.db,*.db-shm,*.db-wal,invoices\*,backups\*,logs\*,__pycache__\*,*.pyc,*.pdf,legacy_ui\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Lancar Dynamic Admin"; Filename: "{app}\LancarDinamicAdmin.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\Lancar Dynamic Admin"; Filename: "{app}\LancarDinamicAdmin.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\LancarDinamicAdmin.exe"; Description: "{cm:LaunchProgram,Lancar Dynamic Admin}"; Flags: nowait postinstall skipifsilent
